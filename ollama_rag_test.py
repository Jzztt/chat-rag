import os
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


OLLAMA_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DB_PATH = "./chroma_db"
DATA_DIR = "data/pdfs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3


print("🚀 Initializing Ollama RAG System...")

print(f"📊 Loading embedding model: {EMBEDDING_MODEL}")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"}   # đổi "cuda" nếu có GPU
)

print(f"🤖 Connecting to Ollama model: {OLLAMA_MODEL}")
llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.7)


Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

loader = DirectoryLoader(
    path=DATA_DIR,
    glob="*.pdf",
    loader_cls=PyPDFLoader
)
documents = loader.load()
print(f"✅ Loaded {len(documents)} documents (mỗi trang PDF ≈ 1 Document).")

print(f"✂️  Splitting (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
)
chunks = splitter.split_documents(documents)
print(f"✅ Created {len(chunks)} chunks")


print("\n💾 Creating vector store with ChromaDB...")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=CHROMA_DB_PATH
)
print("✅ Vector store created and persisted")

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": TOP_K, "fetch_k": max(12, TOP_K * 4)}
)


def format_docs(docs):
    return "\n\n---\n\n".join(d.page_content for d in docs)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Bạn là trợ lý RAG. Trả lời ngắn gọn, dựa trên ngữ cảnh. "
     "Nếu không đủ thông tin trong ngữ cảnh, hãy nói bạn không biết.\n\n"
     "{context}"),
    ("human", "{question}")
])

rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)
print("✅ RAG chain ready!")


def ask_question(question: str):
    print(f"\n{'='*60}\n❓ Question: {question}\n{'='*60}")
    answer = rag_chain.invoke(question)
    print(f"\n🤖 Answer:\n{answer}")

    # Lấy nguồn (documents) riêng để in citation
    docs = retriever.invoke(question)
    print("\n📄 Sources:")
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page", "?")
        preview = d.page_content[:100].replace("\n", " ")
        print(f"  [{i}] {src} (page {page})")
        print(f"      Preview: {preview}...")
    return answer


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎉 RAG System Ready! Testing with sample queries...")
    print("="*60)

    sample_queries = [
        "What is Python and who created it?",
        "Explain what RAG is and how it works",
        "What libraries are used for machine learning in Python?",
    ]
    for q in sample_queries:
        ask_question(q)

    print("\n" + "="*60)
    print("💬 Interactive Mode - Ask your questions! (exit/quit/q to stop)")
    print("="*60)

    while True:
        try:
            user_q = input("\n🗣️  Your question: ").strip()
            if user_q.lower() in {"exit", "quit", "q"}:
                print("\n👋 Goodbye!")
                break
            if not user_q:
                print("⚠️  Please enter a question")
                continue
            ask_question(user_q)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("💡 Make sure Ollama is running: ollama serve")
