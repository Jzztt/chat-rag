"""
Enhanced RAG System with Gemini-style File Search
Features:
- Advanced file indexing with metadata
- Hybrid search (vector + BM25)
- Citation and grounding support
- File management system
- Cross-encoder re-ranking
- Query expansion
- Retrieval evaluation
- Smart & parent-child chunking
- Monitoring & logging
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

from sentence_transformers import CrossEncoder, util


# =========================
# Metadata & Config
# =========================

@dataclass
class FileMetadata:
    """Enhanced file metadata tracking"""
    file_id: str
    filename: str
    filepath: str
    file_type: str
    file_size: int
    file_hash: str
    indexed_at: str
    chunk_count: int
    page_count: Optional[int] = None
    author: Optional[str] = None
    title: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class RAGConfig:
    """Configuration for RAG system"""
    ollama_model: str = "llama3.2:3b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_db_path: str = "./chroma_db"
    file_index_path: str = "./file_index.json"
    data_dir: str = "data"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3
    temperature: float = 0.7
    device: str = "cpu"
    enable_citations: bool = True
    hybrid_search_weights: Tuple[float, float] = (0.5, 0.5)  # (vector, bm25)

    # Retrieval quality features
    use_reranker: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    enable_query_expansion: bool = True
    similarity_threshold: float = 0.3      # Ngưỡng để coi là "liên quan"
    use_parent_child_chunking: bool = True

    # Logging
    log_file: Optional[str] = "logs/rag_queries.jsonl"


# =========================
# File Index
# =========================

class FileIndexManager:
    """Manages file indexing and metadata"""

    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.index: Dict[str, FileMetadata] = {}
        self.load_index()

    def load_index(self):
        """Load file index from disk"""
        if self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.index = {
                    k: FileMetadata(**v) for k, v in data.items()
                }
            print(f"📋 Loaded index with {len(self.index)} files")

    def save_index(self):
        """Save file index to disk"""
        if not self.index_path.parent.exists():
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            data = {k: v.to_dict() for k, v in self.index.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_file_hash(self, filepath: Path) -> str:
        """Calculate file hash for change detection"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def add_file(
        self,
        filepath: Path,
        chunk_count: int,
        page_count: Optional[int] = None
    ) -> FileMetadata:
        """Add or update file in index"""
        file_hash = self.get_file_hash(filepath)
        file_id = f"file_{file_hash[:12]}"

        metadata = FileMetadata(
            file_id=file_id,
            filename=filepath.name,
            filepath=str(filepath),
            file_type=filepath.suffix,
            file_size=filepath.stat().st_size,
            file_hash=file_hash,
            indexed_at=datetime.now().isoformat(),
            chunk_count=chunk_count,
            page_count=page_count
        )

        self.index[file_id] = metadata
        return metadata

    def is_file_indexed(self, filepath: Path) -> bool:
        """Check if file is already indexed and unchanged"""
        file_hash = self.get_file_hash(filepath)
        for meta in self.index.values():
            if meta.filepath == str(filepath) and meta.file_hash == file_hash:
                return True
        return False

    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed files"""
        total_size = sum(m.file_size for m in self.index.values())
        total_chunks = sum(m.chunk_count for m in self.index.values())

        by_type = defaultdict(int)
        for meta in self.index.values():
            by_type[meta.file_type] += 1

        return {
            "total_files": len(self.index),
            "total_size_mb": total_size / (1024 * 1024),
            "total_chunks": total_chunks,
            "by_type": dict(by_type)
        }


# =========================
# Document Processing
# =========================

class DocumentProcessor:
    """Handles document loading and processing with enhanced metadata"""

    def __init__(self, data_dir: str, file_index: FileIndexManager):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_index = file_index

    def load_documents(self, force_reindex: bool = False) -> List[Document]:
        """Load documents with smart change detection"""
        print(f"📂 Loading documents from: {self.data_dir}")

        loaders_config = [
            ("**/*.pdf", PyPDFLoader, "PDF"),
            ("**/*.docx", Docx2txtLoader, "DOCX"),
            ("**/*.txt", TextLoader, "TXT"),
        ]

        all_docs: List[Document] = []
        files_to_process = []

        # Scan for files
        for glob_pattern, loader_cls, doc_type in loaders_config:
            files = list(self.data_dir.glob(glob_pattern))
            for filepath in files:
                if force_reindex or not self.file_index.is_file_indexed(filepath):
                    files_to_process.append((filepath, loader_cls, doc_type))

        if not files_to_process and not force_reindex:
            print("✅ All files already indexed, skipping...")
            return []

        print(f"🔄 Processing {len(files_to_process)} new/changed files...")

        # Load new/changed files
        for filepath, loader_cls, doc_type in files_to_process:
            try:
                loader = loader_cls(str(filepath))
                docs = loader.load()

                if docs:
                    # Enhance metadata
                    for doc in docs:
                        doc.metadata.update({
                            "filename": filepath.name,
                            "filepath": str(filepath),
                            "file_type": doc_type,
                            "indexed_at": datetime.now().isoformat()
                        })

                    all_docs.extend(docs)
                    print(f"  ✓ Loaded {filepath.name} ({len(docs)} pages)")

            except Exception as e:
                print(f"  ⚠ Error loading {filepath.name}: {e}")

        print(f"✅ Total new documents loaded: {len(all_docs)}")
        return all_docs

    # Smart splitter
    def create_smart_splitter(
        self,
        chunk_size: int,
        chunk_overlap: int
    ) -> RecursiveCharacterTextSplitter:
        """Create context-aware splitter"""
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Multiple blank lines
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentence ends
                "? ",
                "! ",
                "; ",
                ", ",
                " ",
                ""
            ],
            keep_separator=True
        )

    # Parent-child chunking
    def create_parent_child_chunks(
        self,
        documents: List[Document],
        child_size: int,
        child_overlap: int,
    ) -> List[Document]:
        """Create hierarchical parent-child chunks"""
        parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_size,
            chunk_overlap=child_overlap
        )

        all_chunks: List[Document] = []
        for doc in documents:
            parents = parent_splitter.split_documents([doc])
            for parent in parents:
                children = child_splitter.split_documents([parent])
                for child in children:
                    child.metadata["parent_content"] = parent.page_content[:500]
                    all_chunks.append(child)

        return all_chunks

    def split_documents(
        self,
        documents: List[Document],
        chunk_size: int,
        chunk_overlap: int,
        use_parent_child: bool = False
    ) -> List[Document]:
        """Split documents into chunks with enhanced metadata"""
        print(f"✂️  Splitting documents (size={chunk_size}, overlap={chunk_overlap})")

        if use_parent_child:
            chunks = self.create_parent_child_chunks(
                documents,
                child_size=chunk_size,
                child_overlap=chunk_overlap
            )
        else:
            splitter = self.create_smart_splitter(chunk_size, chunk_overlap)
            chunks = splitter.split_documents(documents)

        # Add chunk-specific metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"chunk_{i}"
            chunk.metadata["chunk_index"] = i

        print(f"✅ Created {len(chunks)} chunks")

        # Update file index
        files_chunks: Dict[str, int] = defaultdict(int)
        for chunk in chunks:
            filepath = chunk.metadata.get("filepath")
            if filepath:
                files_chunks[filepath] += 1

        for filepath, count in files_chunks.items():
            page_count = None
            if any(c.metadata.get("page") for c in chunks if c.metadata.get("filepath") == filepath):
                pages = [c.metadata.get("page", 0) for c in chunks if c.metadata.get("filepath") == filepath]
                page_count = max(pages) if pages else None

            self.file_index.add_file(Path(filepath), count, page_count)

        self.file_index.save_index()

        return chunks


# =========================
# Hybrid Search
# =========================

class HybridSearchManager:
    """Manages hybrid search (Vector + BM25)"""

    def __init__(self, embeddings: HuggingFaceEmbeddings, persist_dir: str,
                 weights: Tuple[float, float] = (0.5, 0.5)):
        self.embeddings = embeddings
        self.persist_dir = persist_dir
        self.weights = weights
        self.vectorstore: Optional[Chroma] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.hybrid_retriever: Optional[EnsembleRetriever] = None

    def create_vectorstore(self, chunks: List[Document]) -> Chroma:
        """Create vector store"""
        print(f"\n💾 Creating vector store at: {self.persist_dir}")

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )

        # Create BM25 retriever for keyword search
        self.bm25_retriever = BM25Retriever.from_documents(chunks)

        print("✅ Vector store and BM25 index created")
        return self.vectorstore

    def load_vectorstore(self, chunks: Optional[List[Document]] = None) -> Chroma:
        """Load existing vector store"""
        print(f"\n📥 Loading existing vector store from: {self.persist_dir}")

        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings
        )

        # BM25 needs to be recreated (can't be persisted)
        if chunks:
            self.bm25_retriever = BM25Retriever.from_documents(chunks)

        print("✅ Vector store loaded")
        return self.vectorstore

    def get_hybrid_retriever(self, top_k: int):
        """Get hybrid retriever combining vector and BM25 search"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")

        # Vector retriever
        vector_retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": top_k, "fetch_k": top_k * 4}
        )

        # Configure BM25
        if self.bm25_retriever:
            self.bm25_retriever.k = top_k

            # Create ensemble retriever
            self.hybrid_retriever = EnsembleRetriever(
                retrievers=[vector_retriever, self.bm25_retriever],
                weights=list(self.weights)
            )
            print(f"🔍 Hybrid search enabled (vector: {self.weights[0]}, bm25: {self.weights[1]})")
            return self.hybrid_retriever
        else:
            print("⚠️  BM25 not available, using vector search only")
            return vector_retriever


# =========================
# Citation Manager
# =========================

class CitationManager:
    """Manages citations and grounding"""

    @staticmethod
    def format_citation(doc: Document, index: int) -> str:
        """Format document as citation"""
        source = doc.metadata.get("filename", "unknown")
        page = doc.metadata.get("page")
        citation = f"[{index}] {source}"
        if page:
            citation += f" (page {page})"
        return citation

    @staticmethod
    def create_grounded_context(docs: List[Document]) -> str:
        """Create context with inline citations"""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            citation = CitationManager.format_citation(doc, i)
            content = doc.page_content.strip()
            context_parts.append(f"[Source {i}] {content}\n{citation}")
        return "\n\n---\n\n".join(context_parts)


# =========================
# Re-ranker & Logger
# =========================

class ReRanker:
    """Cross-encoder re-ranking layer"""

    def __init__(self, model_name: str, device: str = "cpu"):
        print(f"🎯 Loading re-ranker: {model_name} on {device}")
        self.model = CrossEncoder(model_name, device=device)

    def rerank(self, query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
        if not docs:
            return docs
        pairs = [[query, doc.page_content] for doc in docs]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in ranked[:top_k]]


class RAGLogger:
    def __init__(self, log_file: str = "logs/rag_queries.jsonl"):
        self.log_file = log_file
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

    def log_query(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        eval_scores: Optional[Dict[str, float]],
        duration: float
    ):
        """Log query for analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer_preview": answer[:300],
            "source_count": len(sources),
            "eval_scores": eval_scores,
            "duration_seconds": duration,
            "sources": [
                {
                    "filename": s.get("filename"),
                    "page": s.get("page"),
                    "similarity": s.get("similarity")
                }
                for s in sources
            ]
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# =========================
# RAG System
# =========================

class RAGSystem:
    """Enhanced RAG System with Gemini-style features"""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.file_index = FileIndexManager(config.file_index_path)
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all RAG components"""
        print("🚀 Initializing Enhanced RAG System...\n")

        load_dotenv()

        # Initialize embeddings
        print(f"📊 Loading embedding model: {self.config.embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model,
            model_kwargs={"device": self.config.device}
        )

        # Initialize LLM
        print(f"🤖 Connecting to Ollama model: {self.config.ollama_model}")
        self.llm = OllamaLLM(
            model=self.config.ollama_model,
            temperature=self.config.temperature
        )

        # Initialize managers
        self.doc_processor = DocumentProcessor(
            self.config.data_dir,
            self.file_index
        )
        self.search_manager = HybridSearchManager(
            self.embeddings,
            self.config.chroma_db_path,
            self.config.hybrid_search_weights
        )
        self.citation_manager = CitationManager()

        # Re-ranker & logger
        self.reranker: Optional[ReRanker] = None
        if self.config.use_reranker:
            self.reranker = ReRanker(
                model_name=self.config.reranker_model,
                device=self.config.device
            )

        self.logger: Optional[RAGLogger] = None
        if self.config.log_file:
            self.logger = RAGLogger(self.config.log_file)

        self.retriever = None
        self.prompt_template: Optional[ChatPromptTemplate] = None
        self.format_func = None

    # ---------- Setup ----------

    def setup(self, force_rebuild: bool = False):
        """Setup vector store and RAG chain"""
        vectorstore_exists = Path(self.config.chroma_db_path).exists()

        if vectorstore_exists and not force_rebuild:
            print("\n📦 Existing vector store found")
            all_docs = self._reload_all_documents()

            if all_docs:
                chunks = self.doc_processor.split_documents(
                    all_docs,
                    self.config.chunk_size,
                    self.config.chunk_overlap,
                    use_parent_child=self.config.use_parent_child_chunking
                )
                self.search_manager.load_vectorstore(chunks)
            else:
                self.search_manager.load_vectorstore()
        else:
            # Load and process documents
            documents = self.doc_processor.load_documents(force_reindex=True)

            if not documents:
                raise ValueError(f"No documents found in {self.config.data_dir}")

            # Split into chunks
            chunks = self.doc_processor.split_documents(
                documents,
                self.config.chunk_size,
                self.config.chunk_overlap,
                use_parent_child=self.config.use_parent_child_chunking
            )

            # Create vector store
            self.search_manager.create_vectorstore(chunks)

        # Setup retriever
        self.retriever = self.search_manager.get_hybrid_retriever(self.config.top_k)

        # Build prompt/format
        self._build_chain()

        # Show index stats
        stats = self.file_index.get_file_stats()
        print(f"\n📊 File Index Stats:")
        print(f"  • Total files: {stats['total_files']}")
        print(f"  • Total size: {stats['total_size_mb']:.2f} MB")
        print(f"  • Total chunks: {stats['total_chunks']}")
        print(f"  • By type: {stats['by_type']}")

        print("\n✅ Enhanced RAG System ready!\n")

    def _reload_all_documents(self) -> List[Document]:
        """Force reload all documents from file index"""
        all_docs: List[Document] = []

        for file_id, meta in self.file_index.index.items():
            filepath = Path(meta.filepath)
            if not filepath.exists():
                print(f"⚠️ File not found: {filepath}")
                continue

            # Load based on file type
            loader_map = {
                '.pdf': PyPDFLoader,
                '.docx': Docx2txtLoader,
                '.txt': TextLoader
            }

            loader_cls = loader_map.get(meta.file_type)
            if loader_cls:
                try:
                    docs = loader_cls(str(filepath)).load()
                    # Restore metadata
                    for doc in docs:
                        doc.metadata.update({
                            "filename": meta.filename,
                            "filepath": str(filepath),
                            "file_type": meta.file_type,
                            "file_id": file_id
                        })
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"⚠️ Error loading {filepath}: {e}")

        return all_docs

    def _build_chain(self):
        """Build prompt template giống Gemini File Search (không dùng Runnable chain nữa)"""

        if self.config.enable_citations:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "Bạn là trợ lý RAG. Trả lời ngắn gọn, dựa trên ngữ cảnh. "
                 "Nếu không đủ thông tin trong ngữ cảnh, hãy nói bạn không biết.\n\n"
                 "{context}"),
                ("human", "{question}")
            ])
            format_func = self.citation_manager.create_grounded_context
        else:
            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    (
                        "Bạn là trợ lý RAG thông minh. Hãy trả lời câu hỏi dựa trên NGỮ CẢNH bên dưới.\n"
                        "- Ưu tiên dùng nội dung trong ngữ cảnh.\n"
                        "- Trả lời ngắn gọn, chính xác, có cấu trúc.\n"
                        "- Nếu ngữ cảnh không đủ trả lời, hãy nói rõ: "
                        "\"Tài liệu bạn cung cấp không có (hoặc rất ít) thông tin trực tiếp về câu hỏi này\" "
                        "trước khi dùng kiến thức chung.\n"
                        "- Không bịa đặt thông tin.\n"
                        "- Luôn trả lời bằng tiếng Việt.\n\n"
                        "Ngữ cảnh:\n"
                        "{context}"
                    )
                ),
                ("human", "{question}")
            ])
            format_func = lambda docs: "\n\n---\n\n".join(d.page_content for d in docs)

        self.prompt_template = prompt
        self.format_func = format_func

    # ---------- Query expansion & evaluation ----------

    def expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms using LLM"""
        expansion_prompt = f"""Nhiệm vụ: Mở rộng câu hỏi để tìm kiếm tốt hơn

Câu hỏi gốc: {query}

Hãy tạo 3 câu hỏi tương tự với từ đồng nghĩa và cách diễn đạt khác.
Chỉ trả về các câu hỏi, mỗi câu một dòng, không giải thích.

VD:
Input: Vue.js là gì?
Output:
Vue.js là gì?
Giải thích về Vue.js framework
Định nghĩa và khái niệm Vue.js

Bây giờ hãy mở rộng:"""

        expanded = self.llm.invoke(expansion_prompt)
        # Ghép query gốc + các biến thể để gửi vào retriever
        return f"{query}\n{expanded}"

    def evaluate_retrieval(self, query: str, docs: List[Document]) -> Dict[str, float]:
        """Evaluate retrieval quality bằng cosine similarity"""
        if not docs:
            return {
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "min_similarity": 0.0,
                "relevant_count": 0
            }

        query_emb = self.embeddings.embed_query(query)
        doc_embs = [self.embeddings.embed_query(doc.page_content) for doc in docs]

        similarities = [util.cos_sim(query_emb, doc_emb).item() for doc_emb in doc_embs]

        return {
            "avg_similarity": sum(similarities) / len(similarities),
            "max_similarity": max(similarities),
            "min_similarity": min(similarities),
            "relevant_count": sum(1 for s in similarities if s > 0.5)
        }

    # ---------- Main ask() ----------

    def ask(self, question: str, show_sources: bool = True) -> Dict[str, Any]:
        """Ask a question with enhanced retrieval quality + logging"""
        if not self.retriever or not self.prompt_template or not self.format_func:
            raise ValueError("RAG system not setup. Call setup() first.")

        print(f"\n{'='*70}")
        print(f"❓ Question: {question}")
        print('='*70)

        start_time = time.time()

        # 1️⃣ Query expansion
        retrieval_query = question
        if self.config.enable_query_expansion:
            retrieval_query = self.expand_query(question)

        # 2️⃣ Initial retrieval (vector + BM25 hybrid)
        initial_docs: List[Document] = self.retriever.invoke(retrieval_query)

        # 3️⃣ Re-ranking (cross-encoder)
        if self.reranker:
            docs = self.reranker.rerank(question, initial_docs, top_k=self.config.top_k)
        else:
            docs = initial_docs[: self.config.top_k]

        # 4️⃣ Evaluate retrieval
        eval_scores = self.evaluate_retrieval(question, docs)

        # Nếu hoàn toàn không liên quan
        if not docs or eval_scores["max_similarity"] < self.config.similarity_threshold:
            answer = "Không tìm thấy thông tin liên quan trong tài liệu."
            duration = time.time() - start_time

            result = {
                "question": question,
                "answer": answer,
                "sources": [],
                "confidence": "low",
                "eval_scores": eval_scores,
            }

            if self.logger:
                self.logger.log_query(question, answer, [], eval_scores, duration)

            print(f"\n🤖 Answer (low confidence):\n{answer}")
            return result

        # 5️⃣ Build context & generate answer
        context = self.format_func(docs)
        messages = self.prompt_template.format_messages(
            context=context,
            question=question
        )

        answer = self.llm.invoke(messages)
        duration = time.time() - start_time

        print(f"\n🤖 Answer:\n{answer}")

        # 6️⃣ Prepare sources with similarity scores
        sources: List[Dict[str, Any]] = []
        if show_sources:
            query_emb = self.embeddings.embed_query(question)
            for i, doc in enumerate(docs, 1):
                doc_emb = self.embeddings.embed_query(doc.page_content)
                sim = util.cos_sim(query_emb, doc_emb).item()

                citation = self.citation_manager.format_citation(doc, i)
                preview = doc.page_content[:150].replace("\n", " ")

                print(f"\n📚 Source {i}: {citation}")
                print(f"   Preview: {preview}...")
                print(f"   Similarity: {sim:.3f}")

                sources.append({
                    "citation": citation,
                    "filename": doc.metadata.get("filename", "unknown"),
                    "page": doc.metadata.get("page"),
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "content": doc.page_content,
                    "similarity": sim
                })

        # 7️⃣ Logging
        if self.logger:
            self.logger.log_query(question, answer, sources, eval_scores, duration)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "confidence": "medium" if eval_scores["max_similarity"] < 0.6 else "high",
            "eval_scores": eval_scores
        }

    # ---------- Other utilities ----------

    def list_files(self):
        """List all indexed files"""
        print("\n📁 Indexed Files:")
        print("="*70)

        for file_id, meta in self.file_index.index.items():
            print(f"\n  • {meta.filename}")
            print(f"    Type: {meta.file_type} | Size: {meta.file_size/1024:.1f} KB")
            print(f"    Chunks: {meta.chunk_count} | Pages: {meta.page_count or 'N/A'}")
            print(f"    Indexed: {meta.indexed_at[:19]}")

    def search_in_file(self, question: str, filename: str) -> Dict[str, Any]:
        """Search within a specific file"""
        print(f"\n🔍 Searching in: {filename}")

        # Get initial docs (trong toàn bộ corpus)
        retrieval_query = self.expand_query(question) if self.config.enable_query_expansion else question
        all_docs = self.retriever.invoke(retrieval_query)

        # Filter theo filename
        filtered_docs = [d for d in all_docs if d.metadata.get("filename") == filename]

        if not filtered_docs:
            return {
                "question": question,
                "answer": f"Không tìm thấy kết quả trong file {filename}",
                "sources": []
            }

        # Create filtered context
        if self.config.enable_citations:
            context = self.citation_manager.create_grounded_context(filtered_docs)
        else:
            context = "\n\n---\n\n".join(d.page_content for d in filtered_docs)

        prompt = (
            f"Nội dung sau đây đến từ file: {filename}\n\n"
            f"{context}\n\n"
            f"Câu hỏi: {question}\n"
            f"Hãy trả lời ngắn gọn, chính xác dựa trên nội dung file này."
        )
        answer = self.llm.invoke(prompt)

        print(f"\n🤖 Answer: {answer}")

        sources = [{
            "citation": self.citation_manager.format_citation(doc, i),
            "content": doc.page_content
        } for i, doc in enumerate(filtered_docs, 1)]

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "file": filename
        }

    def interactive_mode(self):
        """Enhanced interactive mode"""
        print("\n" + "="*70)
        print("💬 Interactive Mode - Enhanced RAG System")
        print("Commands:")
        print("  • list - Show indexed files")
        print("  • stats - Show system statistics")
        print("  • search:filename your question - Search in specific file")
        print("  • exit/quit/q - Stop")
        print("="*70)

        while True:
            try:
                user_input = input("\n🗣️  Your input: ").strip()

                if user_input.lower() in {"exit", "quit", "q"}:
                    print("\n👋 Goodbye!")
                    break

                if user_input.lower() == "list":
                    self.list_files()
                    continue

                if user_input.lower() == "stats":
                    stats = self.file_index.get_file_stats()
                    print(f"\n📊 System Statistics:")
                    print(json.dumps(stats, indent=2, ensure_ascii=False))
                    continue

                if user_input.startswith("search:"):
                    parts = user_input.split(" ", 1)
                    if len(parts) == 2:
                        filename = parts[0].split(":")[1]
                        question = parts[1]
                        result = self.search_in_file(question, filename)
                        print("\n🤖 Answer:", result["answer"])
                    else:
                        print("⚠️  Usage: search:filename your question")
                    continue

                if not user_input:
                    print("⚠️  Please enter a question")
                    continue

                result = self.ask(user_input)
                # Answer đã được in trong ask()

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    # ---------- Evaluation metrics ----------

    def calculate_metrics(self, test_queries: List[Dict[str, Any]], k: int = 3) -> Dict[str, float]:
        """
        test_queries = [
            {"query": "Vue.js là gì?", "expected_file": "vuejs.pdf"},
            ...
        ]
        """
        metrics = {
            "precision@k": [],
            "recall@k": [],
            "mrr": [],
            "avg_similarity": []
        }

        for item in test_queries:
            q = item["query"]
            expected_file = item["expected_file"]

            retrieval_query = self.expand_query(q) if self.config.enable_query_expansion else q
            docs = self.retriever.invoke(retrieval_query)[:k]

            # precision/recall
            relevant = [d for d in docs if d.metadata.get("filename") == expected_file]
            precision = len(relevant) / max(len(docs), 1)
            recall = 1.0 if relevant else 0.0

            # MRR
            rr = 0.0
            for rank, d in enumerate(docs, start=1):
                if d.metadata.get("filename") == expected_file:
                    rr = 1.0 / rank
                    break

            eval_scores = self.evaluate_retrieval(q, docs)

            metrics["precision@k"].append(precision)
            metrics["recall@k"].append(recall)
            metrics["mrr"].append(rr)
            metrics["avg_similarity"].append(eval_scores["avg_similarity"])

        return {k: (sum(v) / len(v) if v else 0.0) for k, v in metrics.items()}


# =========================
# Main
# =========================

def main():
    """Main entry point"""
    config = RAGConfig(
        enable_citations=True,
        hybrid_search_weights=(0.6, 0.4),      # Favor vector search slightly
        use_reranker=True,
        enable_query_expansion=True,
        similarity_threshold=0.3,
        use_parent_child_chunking=True,
        log_file="logs/rag_queries.jsonl"
    )

    rag = RAGSystem(config)
    rag.setup(force_rebuild=False)

    # Test queries
    print("\n" + "="*70)
    print("🎉 Testing Enhanced RAG System...")
    print("="*70)

    sample_queries = [
        "Tổng hợp kiến thức Vuejs",
        "Python là gì và ai tạo ra nó?",
    ]

    for query in sample_queries:
        rag.ask(query)

    # Interactive mode
    rag.interactive_mode()


if __name__ == "__main__":
    main()
