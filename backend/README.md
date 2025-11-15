# Chat RAG Backend API

Backend API chuyên nghiệp cho hệ thống Chat RAG, được xây dựng với FastAPI, tích hợp RAG system với Ollama và ChromaDB.

## Tính năng

- ✅ RESTful API đầy đủ cho chat, conversations, projects, files
- ✅ Tích hợp RAG system với hybrid search (vector + BM25)
- ✅ Quản lý projects và conversations
- ✅ Upload và index files (PDF, DOCX, TXT)
- ✅ Database SQLite với SQLAlchemy ORM
- ✅ CORS middleware cho frontend
- ✅ Error handling và logging
- ✅ API documentation tự động (Swagger/ReDoc)

## Cấu trúc dự án

```
backend/
├── app/
│   ├── core/           # Cấu hình và database
│   │   ├── config.py   # Settings
│   │   └── database.py # Database connection
│   ├── models/         # Database models
│   │   ├── project.py
│   │   ├── conversation.py
│   │   └── source.py
│   ├── routers/        # API endpoints
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   ├── projects.py
│   │   ├── upload.py
│   │   └── sources.py
│   ├── services/       # Business logic
│   │   └── rag_service.py
│   └── main.py         # FastAPI app
├── requirements.txt
└── README.md
```

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

### 3. Cấu hình môi trường

Tạo file `.env` trong thư mục `backend/`:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Database
DATABASE_URL=sqlite:///./chat_rag.db

# RAG Settings
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 4. Khởi động Ollama

Đảm bảo Ollama đang chạy:

```bash
ollama serve
```

Và đã tải model:

```bash
ollama pull llama3.2:3b
```

## Chạy ứng dụng

### Development mode

```bash
cd backend
python -m app.main
```

Hoặc sử dụng uvicorn trực tiếp:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Sau khi khởi động server, truy cập:

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

### Conversations

- `GET /api/v1/conversations/{id}` - Lấy conversation theo ID

### Upload

- `POST /api/v1/upload?project_id={id}` - Upload và index files

### Sources

- `GET /api/v1/sources?project_id={id}` - Lấy danh sách sources
- `DELETE /api/v1/sources/{id}?project_id={id}` - Xóa source

## Ví dụ sử dụng

### Tạo project

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "Test project"
  }'
```

### Upload file

```bash
curl -X POST "http://localhost:8000/api/v1/upload?project_id={project_id}" \
  -F "files=@document.pdf"
```

### Chat

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "project_id": "{project_id}"
  }'
```

## Database

Database SQLite được tạo tự động tại `chat_rag.db` khi chạy lần đầu.

Để reset database:

```bash
rm chat_rag.db
python -m app.main
```

## Troubleshooting

### Lỗi kết nối Ollama

- Đảm bảo Ollama đang chạy: `ollama serve`
- Kiểm tra `OLLAMA_BASE_URL` trong `.env`

### Lỗi import RAG system

- Đảm bảo file `gemini-file-search.py` ở thư mục root của dự án
- Kiểm tra các dependencies trong `requirements.txt`

### Lỗi CORS

- Thêm frontend URL vào `CORS_ORIGINS` trong `.env`

## Development

### Code structure

- **Models**: SQLAlchemy models cho database
- **Routers**: FastAPI route handlers
- **Services**: Business logic và tích hợp RAG
- **Core**: Configuration và database setup

### Thêm endpoint mới

1. Tạo router trong `app/routers/`
2. Import và include trong `app/main.py`
3. Thêm tests nếu cần

## License

MIT
