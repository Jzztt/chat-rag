import sys
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough


OLLAMA_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
CHROMA_DB_PATH = Path("chroma_db")
COLLECTION_NAME = "rag_documents"
TOP_K = 10


def load_vector_store():
    if not CHROMA_DB_PATH.exists():
        print(f"[ERROR] Không tìm thấy thư mục vector store tại {CHROMA_DB_PATH}.")
        print("Hãy chạy `python ingest.py` để xây dựng dữ liệu trước khi truy vấn.")
        sys.exit(1)

    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}  # đổi "cuda" nếu có GPU
    )

    print(f"[INFO] Opening ChromaDB collection '{COLLECTION_NAME}' tại {CHROMA_DB_PATH.resolve()}")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DB_PATH),
    )

    try:
        collection_count = vectorstore._collection.count()  # type: ignore[attr-defined]
    except Exception:
        collection_count = "unknown"
    print(f"[INFO] Loaded vector store với {collection_count} entries.")
    return vectorstore


def build_rag_chain():
    print("[INFO] Initializing Ollama RAG System...")
    vectorstore = load_vector_store()

    print(f"[INFO] Connecting to Ollama model: {OLLAMA_MODEL}")
    llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.7, streaming=True)

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": TOP_K, "fetch_k": max(12, TOP_K * 4)},
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
    )
    print("[INFO] RAG chain ready!")
    return rag_chain, retriever
def ask_question(rag_chain, retriever, question: str):
    print(f"\n{'='*60}\n[QUESTION] {question}\n{'='*60}")
    print("\n[ANSWER]\n", end="", flush=True)

    streamed_answer_parts = []
    try:
        for chunk in rag_chain.stream(question):
            streamed_answer_parts.append(chunk)
            print(chunk, end="", flush=True)
    except Exception as error:
        print(f"\n[ERROR] Streaming failed: {error}")
        return ""

    answer = "".join(streamed_answer_parts).strip()
    print()  # newline kết thúc phần trả lời

    docs = retriever.invoke(question)
    print("\n[SOURCES]")
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page", "?")
        preview = d.page_content[:100].replace("\n", " ")
        print(f"  [{i}] {src} (page {page})")
        print(f"      Preview: {preview}...")
    return answer


if __name__ == "__main__":
    rag_chain, retriever = build_rag_chain()

    print("\n" + "="*60)
    print("[INFO] Interactive Mode - Ask your questions! (exit/quit/q to stop)")
    print("="*60)

    while True:
        try:
            user_q = input("\nYour question: ").strip()
            if user_q.lower() in {"exit", "quit", "q"}:
                print("\nGoodbye!")
                break
            if not user_q:
                print("Please enter a question")
                continue
            ask_question(rag_chain, retriever, user_q)
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Tip: Make sure Ollama is running: ollama serve")
