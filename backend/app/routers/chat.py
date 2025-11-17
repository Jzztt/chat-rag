"""Chat API Router"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import time
from app.core.database import get_db
from app.models.conversation import Conversation, Message
from app.models.project import Project
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    project_id: str
    enable_llm_decision: Optional[bool] = True  # LLM decides if RAG is needed
    enable_multi_hop: Optional[bool] = True  # Enable multi-hop reasoning
    max_hops: Optional[int] = 2  # Maximum number of search hops


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    conversation_id: str
    confidence: Optional[str] = "medium"
    eval_scores: Optional[dict] = None


@router.post("")
async def send_message_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a chat message and get streaming RAG response"""
    # Validate project exists
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get or create conversation
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if this is the first message in conversation
    is_first_message = False
    if not conversation:
        # Create new conversation with temporary title
        conversation = Conversation(
            project_id=request.project_id,
            title="New Conversation"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        is_first_message = True
    else:
        # Check if conversation has no messages yet
        message_count = db.query(Message).filter(Message.conversation_id == conversation.id).count()
        is_first_message = message_count == 0
    
    # Save conversation_id and other needed values before entering generator
    conversation_id = conversation.id
    chroma_db_path = project.chroma_db_path
    
    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.question
    )
    db.add(user_message)
    db.commit()
    
    # Note: Don't close db here - FastAPI dependency will handle it
    # We'll create a new session in the generator for database operations
    
    async def generate_stream():
        """Generator function for streaming response"""
        # Start timing
        request_start_time = time.time()
        rag_start_time = None
        rag_end_time = None
        streaming_start_time = None
        streaming_end_time = None
        
        # Create a new database session for this generator
        from app.core.database import SessionLocal
        db_session = SessionLocal()
        
        full_answer = ""
        sources = []
        confidence = "medium"
        eval_scores = {}
        
        try:
            # Stream RAG response with enhanced features
            rag_start_time = time.time()
            for chunk_data in rag_service.ask_question_stream(
                project_id=request.project_id,
                chroma_db_path=chroma_db_path,
                question=request.question,
                show_sources=True,
                enable_llm_decision=request.enable_llm_decision,
                enable_multi_hop=request.enable_multi_hop,
                max_hops=request.max_hops
            ):
                if chunk_data.get("type") == "chunk":
                    # Stream text chunk
                    chunk_text = chunk_data.get("content", "")
                    full_answer += chunk_text
                    
                    # Mark streaming start time on first chunk
                    if streaming_start_time is None:
                        streaming_start_time = time.time()
                        rag_end_time = time.time()  # RAG processing ends when streaming starts
                    
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk_text})}\n\n"
                
                elif chunk_data.get("type") == "done":
                    # Final response with sources
                    full_answer = chunk_data.get("answer", full_answer)
                    sources = chunk_data.get("sources", [])
                    confidence = chunk_data.get("confidence", "medium")
                    eval_scores = chunk_data.get("eval_scores", {})
                    
                    # Calculate timing
                    streaming_end_time = time.time()
                    if rag_end_time is None:
                        rag_end_time = streaming_end_time
                    if streaming_start_time is None:
                        streaming_start_time = rag_end_time
                    
                    # Calculate timing metrics
                    total_time = streaming_end_time - request_start_time
                    rag_time = rag_end_time - rag_start_time if rag_start_time else 0
                    streaming_time = streaming_end_time - streaming_start_time if streaming_start_time else 0
                    db_time = 0  # Database operations are fast, can be calculated if needed
                    
                    timing_info = {
                        "total_ms": round(total_time * 1000, 2),
                        "rag_ms": round(rag_time * 1000, 2),
                        "streaming_ms": round(streaming_time * 1000, 2),
                        "total_s": round(total_time, 2)
                    }
                    
                    # Save assistant message to database using new session
                    # Include debug metadata in sources
                    message_metadata = {
                        "used_rag": chunk_data.get("used_rag", True),
                        "hops": chunk_data.get("hops", 1),
                        "timing": timing_info
                    }
                    # Add metadata to sources if sources exist, otherwise create metadata-only source
                    sources_with_metadata = sources.copy() if sources else []
                    if sources_with_metadata:
                        sources_with_metadata[0] = {**sources_with_metadata[0], **message_metadata}
                    else:
                        # If no sources, add metadata as first item
                        sources_with_metadata.append(message_metadata)
                    
                    assistant_message = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_answer,
                        sources=sources_with_metadata
                    )
                    db_session.add(assistant_message)
                    
                    # Auto-generate conversation title from first message
                    if is_first_message:
                        try:
                            # Reload conversation in new session
                            conversation = db_session.query(Conversation).filter(
                                Conversation.id == conversation_id
                            ).first()
                            
                            if conversation:
                                generated_title = rag_service.generate_conversation_title(
                                    project_id=request.project_id,
                                    chroma_db_path=chroma_db_path,
                                    first_message=request.question
                                )
                                conversation.title = generated_title
                        except Exception as e:
                            print(f"Warning: Failed to generate title: {e}")
                            # Reload conversation if not already loaded
                            if not conversation:
                                conversation = db_session.query(Conversation).filter(
                                    Conversation.id == conversation_id
                                ).first()
                            if conversation:
                                conversation.title = request.question[:50] + "..." if len(request.question) > 50 else request.question
                    
                    db_session.commit()
                    
                    # Send final response with enhanced metadata (timing already calculated above)
                    yield f"data: {json.dumps({
                        'type': 'done',
                        'answer': full_answer,
                        'sources': sources,
                        'conversation_id': conversation_id,
                        'confidence': confidence,
                        'eval_scores': eval_scores,
                        'used_rag': chunk_data.get('used_rag', True),
                        'hops': chunk_data.get('hops', 1),
                        'timing': timing_info
                    })}\n\n"
                
                elif chunk_data.get("type") == "error":
                    # Error occurred
                    error_msg = chunk_data.get("error", "Unknown error")
                    yield f"data: {json.dumps({
                        'type': 'error',
                        'error': error_msg,
                        'answer': chunk_data.get('answer', '')
                    })}\n\n"
                    break
        
        except Exception as e:
            db_session.rollback()
            error_msg = str(e)
            yield f"data: {json.dumps({
                'type': 'error',
                'error': error_msg,
                'answer': f'Lỗi khi xử lý câu hỏi: {error_msg}'
            })}\n\n"
        finally:
            # Always close the session
            db_session.close()
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

