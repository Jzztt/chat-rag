"""RAG Service - Integrates with gemini-file-search.py"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document

# Add project root directory to path to import RAG system
# rag_service.py is at: backend/app/services/rag_service.py
# gemini-file-search.py is at: root/gemini-file-search.py
# So we need to go up 3 levels from backend/app/services to get to root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import RAG system - need to handle the dash in filename
import importlib.util
rag_module_path = project_root / "gemini-file-search.py"

if not rag_module_path.exists():
    raise FileNotFoundError(
        f"RAG system file not found at: {rag_module_path}\n"
        f"Please ensure gemini-file-search.py exists in the project root directory."
    )

spec = importlib.util.spec_from_file_location("rag_system", rag_module_path)
rag_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rag_module)

RAGSystem = rag_module.RAGSystem
RAGConfig = rag_module.RAGConfig


class RAGService:
    """Service for managing RAG operations per project"""
    
    _instances: Dict[str, RAGSystem] = {}
    
    def __init__(self):
        """Initialize RAG service"""
        pass
    
    def get_rag_system(self, project_id: str, chroma_db_path: str) -> RAGSystem:
        """Get or create RAG system for a project"""
        if project_id not in self._instances:
            config = RAGConfig(
                chroma_db_path=str(chroma_db_path),
                file_index_path=f"./file_index_{project_id}.json",
                data_dir=str(Path(chroma_db_path).parent / "pdfs"),
                ollama_model="llama3.2:3b",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                chunk_size=500,
                chunk_overlap=50,
                top_k=3,
                temperature=0.7,
                device="cpu",
                enable_citations=True,
                hybrid_search_weights=(0.6, 0.4),
                use_reranker=True,
                enable_query_expansion=True,
                similarity_threshold=0.3,
                use_parent_child_chunking=True,
                log_file=f"logs/rag_queries_{project_id}.jsonl"
            )
            
            rag = RAGSystem(config)
            rag.setup(force_rebuild=False)
            self._instances[project_id] = rag
        
        return self._instances[project_id]
    
    def ask_question(
        self,
        project_id: str,
        chroma_db_path: str,
        question: str,
        show_sources: bool = True
    ) -> Dict[str, Any]:
        """Ask a question using RAG system (similar to ask() in gemini-file-search.py)"""
        try:
            rag = self.get_rag_system(project_id, chroma_db_path)
            result = rag.ask(question, show_sources=show_sources)
            
            # Format sources for API response (similar to gemini-file-search.py format)
            formatted_sources = []
            for source in result.get("sources", []):
                formatted_sources.append({
                    "chunk_id": source.get("chunk_id", ""),
                    "citation": source.get("citation", ""),
                    "filename": source.get("filename", "unknown"),
                    "filepath": source.get("filename", ""),
                    "file_type": Path(source.get("filename", "")).suffix,
                    "similarity": round(source.get("similarity", 0.0), 4),
                    "page": source.get("page"),
                    "content": source.get("content", ""),
                    "content_preview": source.get("content", "")[:200]
                })
            
            # Return full result similar to gemini-file-search.py
            return {
                "question": result.get("question", question),
                "answer": result.get("answer", ""),
                "sources": formatted_sources,
                "confidence": result.get("confidence", "medium"),
                "eval_scores": result.get("eval_scores", {})
            }
        except Exception as e:
            # Enhanced error handling
            error_msg = str(e)
            print(f"Error in ask_question for project {project_id}: {error_msg}")
            
            # Return error response
            return {
                "question": question,
                "answer": f"Lỗi khi xử lý câu hỏi: {error_msg}",
                "sources": [],
                "confidence": "low",
                "error": error_msg
            }
    
    def _needs_rag_decision(self, rag, question: str) -> bool:
        """LLM Decision Layer: Determine if external knowledge (RAG) is needed"""
        try:
            decision_prompt = f"""Bạn là trợ lý AI thông minh. Hãy đánh giá xem câu hỏi sau có cần thông tin từ tài liệu bên ngoài (external knowledge) để trả lời chính xác không?

Câu hỏi: "{question}"

Trả lời chỉ bằng một từ:
- "yes" nếu cần thông tin từ tài liệu (ví dụ: câu hỏi về nội dung cụ thể, định nghĩa, hướng dẫn trong tài liệu)
- "no" nếu có thể trả lời bằng kiến thức chung (ví dụ: câu hỏi toán học đơn giản, câu hỏi chung chung)

Trả lời:"""
            
            decision = rag.llm.invoke(decision_prompt).strip().lower()
            needs_rag = decision.startswith("yes") or "yes" in decision
            
            print(f"🤔 LLM Decision: {'RAG needed' if needs_rag else 'Direct answer'}")
            return needs_rag
        except Exception as e:
            print(f"Warning: Error in RAG decision, defaulting to RAG: {e}")
            return True  # Default to RAG if decision fails
    
    def _generate_search_queries(self, rag, question: str, context: str = "") -> list[str]:
        """Generate optimized search queries using LLM (better than simple expansion)"""
        try:
            if context:
                prompt = f"""Dựa trên câu hỏi và ngữ cảnh hiện tại, hãy tạo 2-3 câu hỏi tìm kiếm tối ưu để tìm thêm thông tin liên quan.

Câu hỏi gốc: {question}

Ngữ cảnh hiện tại:
{context[:500]}

Hãy tạo các câu hỏi tìm kiếm ngắn gọn, cụ thể, tập trung vào thông tin còn thiếu.
Mỗi câu hỏi một dòng, không đánh số, không giải thích."""
            else:
                prompt = f"""Hãy tạo 2-3 câu hỏi tìm kiếm tối ưu từ câu hỏi sau để tìm thông tin trong tài liệu.

Câu hỏi gốc: {question}

Hãy tạo các câu hỏi ngắn gọn, cụ thể, sử dụng từ khóa quan trọng.
Mỗi câu hỏi một dòng, không đánh số, không giải thích.

Ví dụ:
Input: HTML là gì?
Output:
HTML là gì
Định nghĩa HTML
Ngôn ngữ đánh dấu HTML

Bây giờ hãy tạo queries:"""
            
            queries_text = rag.llm.invoke(prompt).strip()
            # Parse queries (split by newlines, filter empty)
            queries = [q.strip() for q in queries_text.split('\n') if q.strip()]
            
            # Always include original question
            if question not in queries:
                queries.insert(0, question)
            
            print(f"🔍 Generated {len(queries)} search queries")
            return queries[:3]  # Limit to 3 queries
        except Exception as e:
            print(f"Warning: Error generating queries, using original: {e}")
            return [question]
    
    def _needs_more_search(self, rag, question: str, context: str, current_docs: list) -> bool:
        """Check if more search is needed (feedback loop)"""
        try:
            if not current_docs:
                return True  # Need search if no docs found
            
            # Check if context is sufficient
            prompt = f"""Đánh giá xem thông tin hiện tại có đủ để trả lời câu hỏi không.

Câu hỏi: {question}

Thông tin hiện có:
{context[:800]}

Trả lời chỉ bằng một từ:
- "yes" nếu cần tìm thêm thông tin
- "no" nếu đã đủ thông tin

Trả lời:"""
            
            decision = rag.llm.invoke(prompt).strip().lower()
            needs_more = decision.startswith("yes") or "yes" in decision
            
            return needs_more
        except Exception as e:
            print(f"Warning: Error checking if more search needed: {e}")
            return False  # Default to no more search
    
    def ask_question_stream(
        self,
        project_id: str,
        chroma_db_path: str,
        question: str,
        show_sources: bool = True,
        enable_llm_decision: bool = True,
        enable_multi_hop: bool = True,
        max_hops: int = 2
    ):
        """Ask a question with streaming response - Enhanced with LLM Decision & Multi-hop Reasoning"""
        try:
            rag = self.get_rag_system(project_id, chroma_db_path)
            
            # Check if RAG system is ready
            if not rag.retriever or not rag.prompt_template or not rag.format_func:
                raise ValueError("RAG system not setup. Call setup() first.")
            
            # ===== STEP 1: LLM Decision Layer =====
            use_rag = True
            if enable_llm_decision:
                use_rag = self._needs_rag_decision(rag, question)
            
            if not use_rag:
                # Direct answer without RAG
                print("💡 Using direct LLM answer (no RAG needed)")
                direct_prompt = f"Trả lời câu hỏi sau một cách ngắn gọn, chính xác:\n\n{question}"
                full_answer = ""
                for chunk in rag.llm.stream(direct_prompt):
                    if chunk:
                        chunk_text = str(chunk)
                        full_answer += chunk_text
                        yield {
                            "type": "chunk",
                            "content": chunk_text
                        }
                
                yield {
                    "type": "done",
                    "answer": full_answer,
                    "sources": [],
                    "confidence": "medium",
                    "eval_scores": {},
                    "used_rag": False
                }
                return
            
            # ===== STEP 2: Multi-hop RAG Flow =====
            all_docs = []
            all_context = ""
            hop_count = 0
            query_emb = None
            
            while hop_count < max_hops:
                hop_count += 1
                print(f"🔄 RAG Hop {hop_count}/{max_hops}")
                
                # Generate search queries (LLM-based, better than simple expansion)
                if hop_count == 1:
                    queries = self._generate_search_queries(rag, question)
                else:
                    # For subsequent hops, generate queries based on what's missing
                    queries = self._generate_search_queries(rag, question, all_context)
                
                # Retrieve documents for all queries
                hop_docs = []
                for query in queries:
                    retrieved = rag.retriever.invoke(query)
                    hop_docs.extend(retrieved)
                
                # Remove duplicates (by content)
                seen_contents = {doc.page_content[:100] for doc in all_docs}
                new_docs = [doc for doc in hop_docs if doc.page_content[:100] not in seen_contents]
                all_docs.extend(new_docs)
                
                # Re-rank if enabled
                if rag.config.use_reranker and all_docs and hasattr(rag, 'reranker') and rag.reranker:
                    docs_to_rerank = all_docs[:15] if len(all_docs) > 15 else all_docs
                    reranked = rag.reranker.rerank(question, docs_to_rerank, top_k=rag.config.top_k)
                    reranked_ids = {id(d) for d in reranked}
                    all_docs = reranked + [d for d in all_docs if id(d) not in reranked_ids][:rag.config.top_k]
                else:
                    all_docs = all_docs[:rag.config.top_k]
                
                # Build context
                context = rag.format_func(all_docs)
                all_context = context
                
                # Check if more search is needed (feedback loop)
                if enable_multi_hop and hop_count < max_hops:
                    needs_more = self._needs_more_search(rag, question, context, all_docs)
                    if not needs_more:
                        print(f"✅ Sufficient context found after {hop_count} hop(s)")
                        break
                    print(f"🔍 Need more search, continuing to hop {hop_count + 1}")
                else:
                    break
            
            docs = all_docs
            
            # 3. Quick similarity check (skip full evaluation for speed)
            # Compute query embedding once and reuse it
            eval_scores = {}
            query_emb = None
            if docs:
                try:
                    from sentence_transformers import util
                    query_emb = rag.embeddings.embed_query(question)
                    # Only check first doc for quick confidence estimate
                    first_doc_emb = rag.embeddings.embed_query(docs[0].page_content)
                    max_sim = util.cos_sim(query_emb, first_doc_emb).item()
                    eval_scores = {"max_similarity": max_sim, "avg_similarity": max_sim}
                except Exception as e:
                    print(f"Error computing similarity: {e}")
                    eval_scores = {"max_similarity": 0.5, "avg_similarity": 0.5}
            
            # 4. Build context & messages
            context = rag.format_func(docs)
            messages = rag.prompt_template.format_messages(
                context=context,
                question=question
            )
            
            # 5. Stream answer from LLM immediately (don't wait for source processing)
            full_answer = ""
            for chunk in rag.llm.stream(messages):
                if chunk:
                    chunk_text = str(chunk)
                    full_answer += chunk_text
                    yield {
                        "type": "chunk",
                        "content": chunk_text
                    }
            
            # 6. Prepare sources (optimized - reuse query embedding from step 3)
            formatted_sources = []
            if show_sources and docs:
                from sentence_transformers import util
                
                # Reuse query_emb from step 3 if available, otherwise compute once
                if query_emb is None:
                    query_emb = rag.embeddings.embed_query(question)
                
                # Process sources (limit to top 5 for speed, or all if fewer)
                max_sources = min(5, len(docs))
                for i, doc in enumerate(docs[:max_sources], 1):
                    try:
                        # Only compute similarity if not already computed in eval_scores
                        if i == 1 and eval_scores.get("max_similarity"):
                            sim = eval_scores["max_similarity"]
                        else:
                            doc_emb = rag.embeddings.embed_query(doc.page_content)
                            sim = util.cos_sim(query_emb, doc_emb).item()
                        
                        citation = rag.citation_manager.format_citation(doc, i) if hasattr(rag, 'citation_manager') else f"[{i}] {doc.metadata.get('filename', 'unknown')}"
                        
                        formatted_sources.append({
                            "chunk_id": doc.metadata.get("chunk_id", ""),
                            "citation": citation,
                            "filename": doc.metadata.get("filename", "unknown"),
                            "filepath": doc.metadata.get("filename", ""),
                            "file_type": Path(doc.metadata.get("filename", "")).suffix,
                            "similarity": round(sim, 4),
                            "page": doc.metadata.get("page"),
                            "content": doc.page_content,
                            "content_preview": doc.page_content[:200]
                        })
                    except Exception as e:
                        print(f"Error processing source {i}: {e}")
                        # Add source without similarity if error
                        formatted_sources.append({
                            "chunk_id": doc.metadata.get("chunk_id", ""),
                            "citation": f"[{i}] {doc.metadata.get('filename', 'unknown')}",
                            "filename": doc.metadata.get("filename", "unknown"),
                            "filepath": doc.metadata.get("filename", ""),
                            "file_type": Path(doc.metadata.get("filename", "")).suffix,
                            "similarity": 0.0,
                            "page": doc.metadata.get("page"),
                            "content": doc.page_content,
                            "content_preview": doc.page_content[:200]
                        })
            
            # 7. Send final metadata
            confidence = "medium" if eval_scores.get("max_similarity", 0) < 0.6 else "high"
            yield {
                "type": "done",
                "answer": full_answer,
                "sources": formatted_sources,
                "confidence": confidence,
                "eval_scores": eval_scores,
                "used_rag": True,
                "hops": hop_count
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error in ask_question_stream for project {project_id}: {error_msg}")
            yield {
                "type": "error",
                "error": error_msg,
                "answer": f"Lỗi khi xử lý câu hỏi: {error_msg}"
            }
    
    def generate_conversation_title(self, project_id: str, chroma_db_path: str, first_message: str) -> str:
        """Generate a concise title for conversation from first message using LLM"""
        try:
            rag = self.get_rag_system(project_id, chroma_db_path)
            
            # Use LLM to generate a short, descriptive title
            title_prompt = f"""Tạo một tiêu đề ngắn gọn (tối đa 6-8 từ) cho cuộc trò chuyện dựa trên câu hỏi đầu tiên sau đây.

Câu hỏi: {first_message}

Yêu cầu:
- Tiêu đề phải ngắn gọn, rõ ràng, dễ hiểu
- Chỉ trả về tiêu đề, không giải thích thêm
- Nếu câu hỏi quá dài, hãy tóm tắt thành tiêu đề ngắn gọn
- Tiêu đề phải bằng tiếng Việt

Tiêu đề:"""
            
            title = rag.llm.invoke(title_prompt).strip()
            
            # Clean up title - remove quotes, extra spaces
            title = title.strip('"\'')
            title = ' '.join(title.split())
            
            # Limit length
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Fallback if title is empty or too short
            if not title or len(title) < 3:
                # Fallback to smart truncation
                words = first_message.split()
                if len(words) > 8:
                    title = ' '.join(words[:8]) + "..."
                else:
                    title = first_message[:50] + "..." if len(first_message) > 50 else first_message
            
            return title
        except Exception as e:
            # Fallback to simple truncation if LLM fails
            print(f"Warning: Failed to generate title with LLM: {e}")
            if len(first_message) > 50:
                return first_message[:47] + "..."
            return first_message
    
    def index_file(
        self,
        project_id: str,
        chroma_db_path: str,
        file_path: Path
    ) -> Dict[str, Any]:
        """Index a new file into the RAG system"""
        # Get file hash first
        import hashlib
        file_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        file_hash_str = file_hash.hexdigest()
        
        # Get or create RAG system
        rag = self.get_rag_system(project_id, chroma_db_path)
        
        # Check if file is already indexed
        file_index = rag.file_index
        already_indexed = file_index.is_file_indexed(file_path)
        
        if not already_indexed:
            # File is new or changed, need to reload documents and rebuild
            print(f"🔄 Indexing new/changed file: {file_path.name}")
            
            # Load new documents (this will detect new/changed files)
            documents = rag.doc_processor.load_documents(force_reindex=False)
            
            if documents:
                # Split into chunks
                chunks = rag.doc_processor.split_documents(
                    documents,
                    rag.config.chunk_size,
                    rag.config.chunk_overlap,
                    use_parent_child=rag.config.use_parent_child_chunking
                )
                
                print(f"✅ Created {len(chunks)} chunks from new documents")
                
                # Check if vectorstore exists
                vectorstore_exists = Path(rag.config.chroma_db_path).exists()
                
                if vectorstore_exists:
                    # Load existing vectorstore
                    try:
                        rag.search_manager.load_vectorstore(chunks)
                        vectorstore = rag.search_manager.vectorstore
                        
                        if vectorstore and chunks:
                            # Add new chunks to existing vectorstore
                            print(f"➕ Adding {len(chunks)} new chunks to existing vectorstore...")
                            vectorstore.add_documents(chunks)
                            print("✅ Chunks added successfully")
                        
                        # Recreate BM25 retriever with all documents
                        existing_docs = rag._reload_all_documents()
                        if existing_docs:
                            all_docs = existing_docs + documents
                        else:
                            all_docs = documents
                        
                        # Recreate BM25 with all documents
                        from langchain_community.retrievers import BM25Retriever
                        all_chunks_for_bm25 = rag.doc_processor.split_documents(
                            all_docs,
                            rag.config.chunk_size,
                            rag.config.chunk_overlap,
                            use_parent_child=rag.config.use_parent_child_chunking
                        )
                        rag.search_manager.bm25_retriever = BM25Retriever.from_documents(all_chunks_for_bm25)
                        rag.search_manager.bm25_retriever.k = rag.config.top_k
                        
                    except Exception as e:
                        print(f"⚠️ Error adding to existing vectorstore: {e}")
                        print("🔄 Rebuilding vectorstore from scratch...")
                        # Fallback: rebuild from scratch
                        existing_docs = rag._reload_all_documents()
                        if existing_docs:
                            all_docs = existing_docs + documents
                        else:
                            all_docs = documents
                        
                        all_chunks = rag.doc_processor.split_documents(
                            all_docs,
                            rag.config.chunk_size,
                            rag.config.chunk_overlap,
                            use_parent_child=rag.config.use_parent_child_chunking
                        )
                        rag.search_manager.create_vectorstore(all_chunks)
                else:
                    # Create new vectorstore
                    print("🆕 Creating new vectorstore...")
                    rag.search_manager.create_vectorstore(chunks)
                
                # Setup retriever
                rag.retriever = rag.search_manager.get_hybrid_retriever(rag.config.top_k)
                print("✅ RAG system updated with new file")
            else:
                # No new documents found (shouldn't happen if file is new)
                print("⚠️ No new documents found, file may already be indexed")
                rag.setup(force_rebuild=False)
        else:
            # File already indexed, just reload
            print(f"ℹ️ File {file_path.name} already indexed")
            rag.setup(force_rebuild=False)
        
        # Get file metadata from index
        file_index = rag.file_index
        
        # Find metadata in index
        metadata = None
        for file_id, meta in file_index.index.items():
            if meta.filepath == str(file_path) or meta.file_hash == file_hash_str:
                metadata = meta
                break
        
        if metadata:
            return {
                "file_id": metadata.file_id,
                "filename": metadata.filename,
                "filepath": metadata.filepath,
                "file_type": metadata.file_type,
                "file_size": metadata.file_size,
                "chunk_count": metadata.chunk_count,
                "page_count": metadata.page_count,
                "indexed_at": metadata.indexed_at
            }
        
        # If not found, return basic info
        return {
            "file_id": f"file_{file_hash_str[:12]}",
            "filename": file_path.name,
            "filepath": str(file_path),
            "file_type": file_path.suffix,
            "file_size": file_path.stat().st_size,
            "chunk_count": 0,
            "page_count": None,
            "indexed_at": None
        }
    
    def get_sources(self, project_id: str, chroma_db_path: str) -> List[Dict[str, Any]]:
        """Get all indexed sources for a project"""
        rag = self.get_rag_system(project_id, chroma_db_path)
        
        sources = []
        for file_id, meta in rag.file_index.index.items():
            sources.append({
                "id": file_id,
                "filename": meta.filename,
                "filepath": meta.filepath,
                "file_type": meta.file_type,
                "file_size": meta.file_size,
                "indexed_at": meta.indexed_at,
                "chunk_count": meta.chunk_count,
                "page_count": meta.page_count
            })
        
        return sources
    
    def delete_source(
        self,
        project_id: str,
        chroma_db_path: str,
        source_id: str
    ) -> bool:
        """Delete a source from the index"""
        rag = self.get_rag_system(project_id, chroma_db_path)
        
        if source_id in rag.file_index.index:
            del rag.file_index.index[source_id]
            rag.file_index.save_index()
            return True
        
        return False
    
    def list_files(self, project_id: str, chroma_db_path: str) -> List[Dict[str, Any]]:
        """List all indexed files for a project (similar to gemini-file-search.py)"""
        rag = self.get_rag_system(project_id, chroma_db_path)
        
        files = []
        for file_id, meta in rag.file_index.index.items():
            files.append({
                "id": file_id,
                "filename": meta.filename,
                "filepath": meta.filepath,
                "file_type": meta.file_type,
                "file_size": meta.file_size,
                "file_size_mb": meta.file_size / (1024 * 1024),
                "chunk_count": meta.chunk_count,
                "page_count": meta.page_count,
                "indexed_at": meta.indexed_at,
                "file_hash": meta.file_hash
            })
        
        return files
    
    def get_file_stats(self, project_id: str, chroma_db_path: str) -> Dict[str, Any]:
        """Get statistics about indexed files (similar to gemini-file-search.py)"""
        rag = self.get_rag_system(project_id, chroma_db_path)
        stats = rag.file_index.get_file_stats()
        
        return {
            "total_files": stats["total_files"],
            "total_size_mb": round(stats["total_size_mb"], 2),
            "total_chunks": stats["total_chunks"],
            "by_type": stats["by_type"]
        }
    
    def search_in_file(
        self,
        project_id: str,
        chroma_db_path: str,
        question: str,
        filename: str
    ) -> Dict[str, Any]:
        """Search within a specific file (similar to gemini-file-search.py)"""
        rag = self.get_rag_system(project_id, chroma_db_path)
        result = rag.search_in_file(question, filename)
        
        # Format sources for API response
        formatted_sources = []
        for source in result.get("sources", []):
            formatted_sources.append({
                "citation": source.get("citation", ""),
                "filename": filename,
                "content": source.get("content", "")
            })
        
        return {
            "question": result.get("question", question),
            "answer": result.get("answer", ""),
            "sources": formatted_sources,
            "file": result.get("file", filename)
        }
    
    def get_file_details(
        self,
        project_id: str,
        chroma_db_path: str,
        source_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific file"""
        rag = self.get_rag_system(project_id, chroma_db_path)
        
        if source_id not in rag.file_index.index:
            return None
        
        meta = rag.file_index.index[source_id]
        return {
            "id": meta.file_id,
            "filename": meta.filename,
            "filepath": meta.filepath,
            "file_type": meta.file_type,
            "file_size": meta.file_size,
            "file_size_mb": round(meta.file_size / (1024 * 1024), 2),
            "file_hash": meta.file_hash,
            "chunk_count": meta.chunk_count,
            "page_count": meta.page_count,
            "indexed_at": meta.indexed_at,
            "author": meta.author,
            "title": meta.title
        }
    
    def rebuild_index(
        self,
        project_id: str,
        chroma_db_path: str,
        force_rebuild: bool = False
    ) -> Dict[str, Any]:
        """Rebuild the RAG index for a project"""
        # Remove existing instance to force rebuild
        if project_id in self._instances:
            del self._instances[project_id]
        
        # Get new instance with rebuild
        rag = self.get_rag_system(project_id, chroma_db_path)
        rag.setup(force_rebuild=force_rebuild)
        
        # Get stats after rebuild
        stats = self.get_file_stats(project_id, chroma_db_path)
        
        return {
            "message": "Index rebuilt successfully",
            "stats": stats
        }
    
    def close_rag_system(self, project_id: str):
        """Close and remove RAG system instance (to release file handles)"""
        if project_id in self._instances:
            rag = self._instances[project_id]
            try:
                # Close vectorstore connections if possible
                if hasattr(rag, 'search_manager') and rag.search_manager.vectorstore:
                    vectorstore = rag.search_manager.vectorstore
                    # Try to close ChromaDB connection
                    if hasattr(vectorstore, '_client'):
                        # ChromaDB client cleanup
                        try:
                            # Delete the client to release connections
                            del vectorstore._client
                        except:
                            pass
                    # Clear vectorstore reference
                    rag.search_manager.vectorstore = None
                
                # Clear other references
                if hasattr(rag, 'retriever'):
                    rag.retriever = None
                if hasattr(rag, 'search_manager'):
                    rag.search_manager.bm25_retriever = None
                    rag.search_manager.hybrid_retriever = None
                
            except Exception as e:
                print(f"Warning: Error closing RAG system for project {project_id}: {e}")
            finally:
                # Remove from instances dict
                del self._instances[project_id]
                print(f"✅ Closed RAG system for project {project_id}")
                
                # Force garbage collection to release file handles
                import gc
                gc.collect()


# Global RAG service instance
rag_service = RAGService()

