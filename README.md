# Chat RAG Demo (Offline Indexing Architecture)

## Cấu trúc dự án

- `ollama_rag_test.py`: Script demo RAG online (giữ nguyên theo yêu cầu).
- `ingest.py`: Pipeline offline để xử lý tài liệu và xây dựng vector store.
- `configs/default.yaml`: Cấu hình pipeline (đường dẫn dữ liệu, embedding, chunking...).
- `rag_pipeline/`: Thư viện nội bộ.
  - `config.py`: Định nghĩa cấu hình, nạp YAML.
  - `logging_utils.py`: Thiết lập logging.
  - `document_loader.py`: Strategy tải tài liệu (hiện hỗ trợ PDF).
  - `chunking.py`: Bộ chia nhỏ văn bản với cấu hình tuỳ biến.
  - `embedding.py`: Khởi tạo mô hình embedding (Strategy pattern).
  - `vector_store.py`: Truy cập và lưu trữ vào Chroma.
  - `pipeline.py`: Bộ điều phối offline (Template Method).
- `artifacts/`, `logs/`, `chroma_db/`: Sinh ra trong quá trình chạy.

## Quy trình offline

1. Đặt PDF vào `data/pdfs`.
2. Chạy `python ingest.py` (hoặc `python ingest.py --config <file_config>`).
3. Pipeline sẽ:
   - Tải tài liệu (Strategy loader).
   - Tiền xử lý & chia chunk.
   - Khởi tạo embedding tiếng Việt miễn phí (`intfloat/multilingual-e5-small`).
   - Ghi vào ChromaDB (`chroma_db`).
   - Ghi manifest `artifacts/ingest_manifest.json`.

## Mở rộng

- Thay đổi mô hình embedding/thiết bị trong YAML.
- Thêm loader mới (DOCX, TXT) bằng cách triển khai Strategy mới.
- Tùy chỉnh chunking/Vector store (ví dụ FAISS) thông qua cấu hình và lớp quản lý tương ứng.

## Lưu ý

- Pipeline offline độc lập với script online hiện có; `ollama_rag_test.py` sẽ dùng cùng thư mục `chroma_db` với cấu hình mới (`intfloat/multilingual-e5-small` + `llama3.2:3b`).
- Đảm bảo cài dependencies từ `requirements.txt` trong môi trường riêng để tránh xung đột.

