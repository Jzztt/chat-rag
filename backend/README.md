# Chat RAG Backend API

Backend API chuyên nghiệp cho hệ thống Chat RAG, được xây dựng với FastAPI, tích hợp RAG system với Ollama và ChromaDB.

## ✨ Tính năng

- ✅ **RESTful API đầy đủ** cho chat, conversations và knowledge base
- ✅ **Streaming Chat Responses** - Real-time streaming giống ChatGPT
- ✅ **LLM Decision Layer** - LLM tự quyết định có cần RAG hay không
- ✅ **Multi-hop Reasoning** - Tìm kiếm và tinh chỉnh ngữ cảnh nhiều lần
- ✅ **Hybrid Search** - Kết hợp vector search (semantic) và BM25 (keyword)
- ✅ **Cross-encoder Re-ranking** - Cải thiện độ chính xác retrieval
- ✅ **Query Expansion** - Mở rộng câu hỏi với synonyms và related terms
- ✅ **Parent-Child Chunking** - Chia tài liệu theo cấu trúc phân cấp
- ✅ **Global Knowledge Base** - Một kho tài liệu dùng chung cho mọi cuộc trò chuyện
- ✅ **Upload và Index Files** - Hỗ trợ PDF, DOCX, TXT, MD
- ✅ **Source Management** - Quản lý nguồn tài liệu (giống NotebookLM)
- ✅ **Database SQLite** với SQLAlchemy ORM
- ✅ **CORS middleware** cho frontend
- ✅ **Error handling và logging** đầy đủ
- ✅ **API documentation tự động** (Swagger/ReDoc)
- ✅ **Performance Metrics** - Timing và debug information

## 📁 Cấu trúc dự án

```
backend/
├── app/
│   ├── core/              # Cấu hình và database
│   │   ├── config.py      # Settings và environment variables
│   │   └── database.py    # Database connection và session
│   ├── models/            # Database models (SQLAlchemy)
│   │   ├── conversation.py # Conversation và Message models
│   │   └── source.py      # Source (file) model
│   ├── routers/          # API endpoints
│   │   ├── chat.py        # Chat streaming endpoint
│   │   ├── conversations.py # Conversation CRUD
│   │   ├── upload.py      # File upload và indexing
│   │   └── sources.py     # Source management
│   ├── services/         # Business logic
│   │   └── rag_service.py # RAG system integration
│   └── main.py           # FastAPI app entry point
├── migrations/           # Database migrations
├── requirements.txt      # Python dependencies (đã tối ưu)
└── README.md
```

## 🚀 Cài đặt

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

**Lưu ý**: `requirements.txt` đã được tối ưu, chỉ chứa các packages cần thiết:

- FastAPI & Uvicorn
- SQLAlchemy & Pydantic
- Langchain (chỉ packages cần thiết)
- ChromaDB, Sentence Transformers, Ollama
- PyPDF, Rank-BM25

### 3. Cấu hình môi trường

Tạo file `.env` trong thư mục `backend/`:

```env
# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Settings (comma-separated hoặc JSON array)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Database
DATABASE_URL=sqlite:///./chat_rag.db

# File Upload Settings
MAX_UPLOAD_SIZE=52428800  # 50MB

# Ollama Settings
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434

# Embedding Settings
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
ollama serve
```

Và đã tải model:

```bash
ollama pull llama3.2:3b
```

## 🏃 Chạy ứng dụng

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

## 📚 API Documentation

Sau khi khởi động server, truy cập:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API Endpoints

### Chat (Streaming)

- `POST /api/v1/chat` - Gửi câu hỏi và nhận phản hồi streaming (SSE)
  - **Request Body**:
    ```json
    {
      "question": "Câu hỏi của bạn",
      "conversation_id": "uuid (optional)",
      "enable_llm_decision": true, // LLM quyết định có cần RAG
      "enable_multi_hop": true, // Bật multi-hop reasoning
      "max_hops": 2 // Số lần tìm kiếm tối đa
    }
    ```
  - **Response**: Server-Sent Events (SSE) stream
    - `chunk`: Text chunks khi LLM generate
    - `done`: Kết quả cuối cùng với metadata (used_rag, hops, timing)

### Conversations

- `GET /api/v1/conversations` - Lấy danh sách conversations
- `POST /api/v1/conversations` - Tạo conversation mới
- `GET /api/v1/conversations/{conversation_id}` - Lấy conversation theo ID
- `PATCH /api/v1/conversations/{conversation_id}` - Cập nhật title của conversation
- `DELETE /api/v1/conversations/{conversation_id}` - Xóa conversation

### Upload

- `POST /api/v1/upload?conversation_id={id}` - Upload và index files (conversation_id optional để attach)
  - **Body**: `multipart/form-data` với field `files[]`
  - **Supported formats**: PDF, DOCX, TXT, MD

### Sources

- `GET /api/v1/sources?conversation_id={id}` - Lấy danh sách sources (conversation_id optional để filter)
- `GET /api/v1/sources/stats` - Lấy thống kê sources
- `GET /api/v1/sources/{source_id}` - Lấy chi tiết source
- `POST /api/v1/sources/{source_id}/search` - Tìm kiếm trong file
- `POST /api/v1/sources/rebuild?force=false` - Rebuild index
- `DELETE /api/v1/sources/{source_id}?conversation_id={id}` - Xóa source (optional validate theo conversation)

## 💡 Ví dụ sử dụng

### Upload file

```bash
curl -X POST "http://localhost:8000/api/v1/upload?conversation_id={conversation_id}" \
  -F "files=@document.pdf"
```

### Chat (Streaming)

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "conversation_id": "{conversation_id}",
    "enable_llm_decision": true,
    "enable_multi_hop": true,
    "max_hops": 2
  }'
```

**Frontend (JavaScript)**:

```javascript
const eventSource = new EventSource(
  `http://localhost:8000/api/v1/chat?question=${encodeURIComponent(
    question
  )}&conversation_id=${conversationId}`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'chunk') {
    // Hiển thị text chunk
    console.log(data.content);
  } else if (data.type === 'done') {
    // Kết quả cuối cùng
    console.log('Answer:', data.answer);
    console.log('Used RAG:', data.used_rag);
    console.log('Hops:', data.hops);
    console.log('Timing:', data.timing);
  }
};
```

### Lấy sources theo conversation

```bash
curl "http://localhost:8000/api/v1/sources?conversation_id={conversation_id}"
```

## 🗄️ Database

Database SQLite được tạo tự động tại `chat_rag.db` khi chạy lần đầu.

### Schema

- **Conversations**: Danh sách các cuộc trò chuyện
- **Messages**: Lưu trữ messages trong conversations với metadata (used_rag, hops, timing)
- **Sources**: Quản lý files thuộc knowledge base (tùy chọn gắn với conversation)

### Reset database

```bash
rm chat_rag.db
python -m app.main
```

## 🔧 Troubleshooting

### Lỗi kết nối Ollama

- Đảm bảo Ollama đang chạy: `ollama serve`
- Kiểm tra `OLLAMA_BASE_URL` trong `.env`
- Kiểm tra model đã được tải: `ollama list`

### Lỗi import RAG system

- Đảm bảo file `gemini-file-search.py` ở thư mục root của dự án
- Kiểm tra các dependencies trong `requirements.txt`
- Đảm bảo đã cài đặt `rank-bm25`: `pip install rank-bm25`

### Lỗi CORS

- Thêm frontend URL vào `CORS_ORIGINS` trong `.env`
- Kiểm tra format: comma-separated hoặc JSON array

### Lỗi PermissionError khi xóa dữ liệu knowledge base

- Đảm bảo ChromaDB connection đã được đóng trước khi xóa
- Hệ thống tự động retry với delay tăng dần
- Nếu vẫn lỗi, thử đóng server và xóa thủ công

### Lỗi "NOT NULL constraint failed"

- Đảm bảo đã chạy migration nếu có thay đổi schema
- Kiểm tra foreign key constraints trong models

## 🎯 Tính năng nâng cao

### LLM Decision Layer

LLM tự quyết định có cần RAG hay không dựa trên câu hỏi:

- Câu hỏi chung chung → Direct LLM answer (nhanh hơn)
- Câu hỏi cần tài liệu → Sử dụng RAG

### Multi-hop Reasoning

Hệ thống có thể tìm kiếm nhiều lần để cải thiện kết quả:

1. Tìm kiếm ban đầu với câu hỏi gốc
2. LLM đánh giá kết quả và tạo câu hỏi follow-up
3. Tìm kiếm lại với câu hỏi mới
4. Kết hợp kết quả để tạo câu trả lời cuối cùng

### Performance Optimization

- **Skipping query expansion** cho câu hỏi đơn giản
- **Limited re-ranking** (top 10 documents)
- **Parallel source processing**
- **Quick similarity check** để quyết định có cần RAG

### Debug Information

Mỗi response bao gồm:

- `used_rag`: Có sử dụng RAG hay không
- `hops`: Số lần tìm kiếm (multi-hop)
- `timing`: Thời gian xử lý (total, RAG, streaming)

## 🔒 Bảo mật

- ✅ Không có secrets/credentials hardcoded
- ✅ Sử dụng environment variables cho config
- ✅ `.gitignore` đã được cấu hình đầy đủ
- ✅ Database files và logs được ignore
- ✅ File indexes và temporary files được ignore

## 📝 Development

### Code structure

- **Models**: SQLAlchemy models cho database với relationships
- **Routers**: FastAPI route handlers với dependency injection
- **Services**: Business logic và tích hợp RAG system
- **Core**: Configuration và database setup

### Thêm endpoint mới

1. Tạo router trong `app/routers/`
2. Import và include trong `app/main.py`
3. Thêm models nếu cần trong `app/models/`
4. Cập nhật API documentation

### Testing

```bash
# Chạy server
uvicorn app.main:app --reload

# Test API với curl hoặc Postman
# Hoặc sử dụng Swagger UI tại /docs
```

## 📦 Dependencies

Xem `requirements.txt` để biết danh sách đầy đủ. Các packages chính:

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **SQLAlchemy**: ORM
- **Pydantic**: Data validation
- **Langchain**: RAG framework
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embeddings
- **Ollama**: LLM
- **PyPDF**: PDF processing
- **Rank-BM25**: Keyword search

## 📄 License

MIT
