# 🚀 LLM-Powered Intelligent Query-Retrieval System

A production-ready document processing and intelligent query system designed for insurance, legal, HR, and compliance domains.

## ✨ Features

- **Multi-format Document Processing**: PDF, DOCX, TXT, Email files
- **Semantic Search**: Vector-based similarity search using OpenAI embeddings
- **Intelligent Chunking**: Smart text segmentation with overlap
- **RESTful API**: Complete FastAPI-based backend
- **Vector Storage**: FAISS (local) or Pinecone (cloud) support
- **Database Integration**: SQLAlchemy with PostgreSQL/SQLite
- **Docker Support**: Containerized deployment
- **Production Ready**: Logging, error handling, monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Document Proc  │    │  Vector Store   │
│                 │    │                 │    │                 │
│  - REST API     │◄──►│  - Text Extract │◄──►│  - FAISS Index  │
│  - Auth         │    │  - Chunking     │    │  - Embeddings   │
│  - Validation   │    │  - Metadata     │    │  - Search       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Query Engine  │    │   OpenAI API    │
│                 │    │                 │    │                 │
│  - Documents    │    │  - Query Proc   │    │  - Embeddings   │
│  - Chunks       │    │  - Results      │    │  - GPT-3.5      │
│  - Logs         │    │  - Explanations │    │  - Summaries    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key
- PostgreSQL (optional, SQLite by default)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd llm-query-system
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run with startup script**
   ```bash
   chmod +x startup.sh
   ./startup.sh
   ```

### Docker Deployment

```bash
# Start with Docker Compose
docker-compose up -d

# Access the API
curl http://localhost:8000/health
```

## 📚 API Documentation

### Document Upload
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Query Documents
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the insurance coverage details?",
    "max_results": 5,
    "similarity_threshold": 0.7
  }'
```

### List Documents
```bash
curl "http://localhost:8000/api/v1/documents"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_URL` | Database connection string | `sqlite:///./query_system.db` |
| `MAX_FILE_SIZE` | Maximum file upload size | `52428800` (50MB) |
| `CHUNK_SIZE` | Text chunk size | `1000` |
| `VECTOR_DIMENSION` | Embedding dimension | `1536` |

### Vector Store Options

- **FAISS (Local)**: Default, no external dependencies
- **Pinecone (Cloud)**: Set `USE_PINECONE=true` in `.env`

## 📊 System Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### System Statistics
```bash
curl http://localhost:8000/api/v1/stats
```

## 🛠️ Development

### Project Structure
```
llm-query-system/
├── api/                 # API endpoints
├── models/              # Database and Pydantic models
├── services/            # Business logic
├── utils/               # Utility functions
├── uploads/             # Document storage
├── vector_index/        # FAISS index files
└── main.py             # Application entry point
```

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .
```

## 🔒 Security

- **API Key Management**: Environment variables for sensitive data
- **File Validation**: Type and size restrictions
- **Input Sanitization**: Safe filename handling
- **Error Handling**: No sensitive data in error messages

## 📈 Performance

- **Async Processing**: Non-blocking document processing
- **Vector Optimization**: Efficient similarity search
- **Database Indexing**: Optimized queries
- **Caching**: FAISS index persistence

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the API docs at `/docs`
- **Issues**: Report bugs via GitHub issues
- **Discussions**: Use GitHub discussions for questions

---

**Built with ❤️ using FastAPI, OpenAI, and FAISS** 