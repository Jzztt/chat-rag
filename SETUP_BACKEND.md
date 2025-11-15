# Hướng dẫn thiết lập Backend

## Tổng quan

Backend đã được xây dựng với FastAPI, tích hợp RAG system hiện có. Backend cung cấp RESTful API đầy đủ cho frontend.

## Cấu trúc Backend

```
backend/
├── app/
│   ├── core/              # Cấu hình cốt lõi
│   │   ├── config.py       # Settings và environment variables
│   │   └── database.py     # Database connection và session
│   ├── models/            # SQLAlchemy models
│   │   ├── project.py     # Project model
│   │   ├── conversation.py # Conversation và Message models
│   │   └── source.py      # Source file model
│   ├── routers/           # API endpoints
│   │   ├── chat.py        # Chat endpoints
│   │   ├── conversations.py # Conversation endpoints
│   │   ├── projects.py    # Project CRUD
│   │   ├── upload.py      # File upload
│   │   └── sources.py     # Source management
│   ├── services/          # Business logic
│   │   └── rag_service.py # RAG system integration
│   └── main.py            # FastAPI application
├── requirements.txt       # Python dependencies
├── run.py                 # Script để chạy server
└── README.md              # Tài liệu chi tiết
```

## Yêu cầu hệ thống

- Python 3.9+
- Ollama đã cài đặt và đang chạy
- Model `llama3.2:3b` đã được tải trong Ollama

## Cài đặt

### 1. Tạo virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

**Lưu ý**: Quá trình cài đặt có thể mất vài phút do các thư viện ML lớn (sentence-transformers, torch, etc.)

### 3. Cấu hình môi trường

Tạo file `.env` trong thư mục `backend/`:

```env
# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS Origins (comma-separated, không có khoảng trắng)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Database
DATABASE_URL=sqlite:///./chat_rag.db

# File Upload
MAX_UPLOAD_SIZE=52428800
ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.md

# RAG Settings
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DEVICE=cpu

# RAG Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=3
TEMPERATURE=0.7
SIMILARITY_THRESHOLD=0.3

# Logging
LOG_LEVEL=INFO
```

### 4. Khởi động Ollama

Đảm bảo Ollama đang chạy:

```bash
# Terminal 1: Khởi động Ollama server
ollama serve

# Terminal 2: Tải model (nếu chưa có)
ollama pull llama3.2:3b
```

## Chạy Backend

### Development mode

```bash
cd backend
python run.py
```

Hoặc:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Kiểm tra Backend

Sau khi khởi động, truy cập:

- **API Root**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Projects

- `GET /api/v1/projects` - Lấy danh sách projects
- `POST /api/v1/projects` - Tạo project mới
- `GET /api/v1/projects/{id}` - Lấy project theo ID
- `PUT /api/v1/projects/{id}` - Cập nhật project
- `DELETE /api/v1/projects/{id}` - Xóa project

### Chat

- `POST /api/v1/chat` - Gửi câu hỏi và nhận phản hồi RAG

**Request body:**
```json
{
  "question": "Câu hỏi của bạn",
  "project_id": "project-id",
  "conversation_id": "conversation-id" // optional
}
```

**Response:**
```json
{
  "answer": "Câu trả lời từ RAG",
  "sources": [...],
  "conversation_id": "conversation-id"
}
```

### Conversations

- `GET /api/v1/conversations/{id}` - Lấy conversation theo ID

### Upload

- `POST /api/v1/upload?project_id={id}` - Upload và index files

**Form data:**
- `files`: File[] (multipart/form-data)

### Sources

- `GET /api/v1/sources?project_id={id}` - Lấy danh sách sources
- `DELETE /api/v1/sources/{id}?project_id={id}` - Xóa source

## Workflow sử dụng

1. **Tạo Project**: Tạo project mới để quản lý documents
2. **Upload Files**: Upload PDF/DOCX/TXT files vào project
3. **Chat**: Gửi câu hỏi về documents đã upload
4. **Quản lý**: Xem conversations, sources, và quản lý projects

## Troubleshooting

### Lỗi: "Connection refused" khi gọi Ollama

- Kiểm tra Ollama đang chạy: `ollama serve`
- Kiểm tra `OLLAMA_BASE_URL` trong `.env`

### Lỗi: "Module not found" khi import RAG system

- Đảm bảo file `gemini-file-search.py` ở thư mục root của dự án
- Kiểm tra đường dẫn trong `rag_service.py`

### Lỗi: CORS khi gọi API từ frontend

- Thêm frontend URL vào `CORS_ORIGINS` trong `.env`
- Đảm bảo không có khoảng trắng trong danh sách

### Lỗi: Database locked

- Đảm bảo chỉ có một instance backend đang chạy
- Kiểm tra file `chat_rag.db` không bị lock

### Lỗi: File upload failed

- Kiểm tra file size < 50MB
- Kiểm tra file extension trong `ALLOWED_EXTENSIONS`
- Kiểm tra project_id có tồn tại

## Database

Database SQLite được tạo tự động tại `chat_rag.db` khi chạy lần đầu.

**Reset database:**
```bash
rm backend/chat_rag.db
python backend/run.py
```

## Logs

Logs được lưu tại:
- Application logs: Console output
- RAG query logs: `logs/rag_queries_{project_id}.jsonl`

## Performance Tips

1. **GPU**: Nếu có GPU, đổi `DEVICE=cuda` trong `.env`
2. **Workers**: Tăng số workers trong production mode
3. **Chunk size**: Điều chỉnh `CHUNK_SIZE` và `CHUNK_OVERLAP` theo nhu cầu
4. **Top K**: Điều chỉnh `TOP_K` để cân bằng độ chính xác và tốc độ

## Security Notes

- Backend hiện tại không có authentication
- Nên thêm authentication trước khi deploy production
- Validate và sanitize user inputs
- Giới hạn file upload size và types

## Next Steps

1. Thêm authentication (JWT, OAuth2)
2. Thêm rate limiting
3. Thêm caching cho embeddings
4. Thêm monitoring và metrics
5. Thêm tests (pytest)
6. Dockerize application

