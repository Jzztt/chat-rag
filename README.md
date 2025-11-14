# Chat RAG Demo (Offline Indexing Architecture)

## Cấu trúc dự án

- `ollama_rag_test.py`: Script demo RAG online với streaming output.
- `ingest.py`: Pipeline offline để xử lý tài liệu và xây dựng vector store.
- `configs/default.yaml`: Cấu hình pipeline (đường dẫn dữ liệu, embedding, chunking, PDF processing...).
- `rag_pipeline/`: Thư viện nội bộ.
  - `config.py`: Định nghĩa cấu hình, nạp YAML.
  - `logging_utils.py`: Thiết lập logging.
  - `document_loader.py`: Strategy tải tài liệu (hỗ trợ PDF với text/table/images).
  - `pdf_processor.py`: Xử lý PDF nâng cao (extract tables, OCR images).
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
   - **Xử lý PDF**: Extract text, tables (nếu bật), OCR images (nếu bật).
   - Tiền xử lý & chia chunk.
   - Khởi tạo embedding tiếng Việt miễn phí (`intfloat/multilingual-e5-small`).
   - Ghi vào ChromaDB (`chroma_db`).
   - Ghi manifest `artifacts/ingest_manifest.json`.

## Xử lý PDF nâng cao

Pipeline hỗ trợ 3 loại xử lý PDF:

1. **Text only** (mặc định): Dùng `PyPDFLoader` để extract text.
2. **Text + Tables**: Dùng `pdfplumber` để extract tables và chuyển thành markdown/text.
3. **Text + Images**: Dùng `pdf2image` + `pytesseract` để OCR images.

Cấu hình trong `configs/default.yaml`:

```yaml
pdf_processing:
  extract_text: true      # Luôn bật
  extract_tables: false   # Bật để extract tables
  extract_images: false   # Bật để OCR images
  ocr_language: "vie+eng" # Ngôn ngữ OCR (pytesseract)
  table_format: "markdown" # Format table: "markdown" hoặc "csv"
```

**Dependencies cho tính năng nâng cao:**
- Table extraction: `pip install pdfplumber`
- Image OCR: `pip install pdf2image pytesseract` (cần cài Tesseract OCR engine)

## Mở rộng

- Thay đổi mô hình embedding/thiết bị trong YAML.
- Thêm loader mới (DOCX, TXT) bằng cách triển khai Strategy mới.
- Tùy chỉnh chunking/Vector store (ví dụ FAISS) thông qua cấu hình và lớp quản lý tương ứng.

## Lưu ý

- Pipeline offline độc lập với script online hiện có; `ollama_rag_test.py` sẽ dùng cùng thư mục `chroma_db`.
- Đảm bảo cài dependencies từ `requirements.txt` trong môi trường riêng để tránh xung đột.
- Khi bật table/image extraction, thời gian xử lý sẽ lâu hơn đáng kể.
