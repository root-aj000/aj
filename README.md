# Vibe Coding AI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

**Local-first AI coding assistant** that combines static analysis, graph databases, vector embeddings, and LLM reasoning to provide intelligent code search, debugging, and refactoring assistance.

## ✨ Features

- 🔍 **Semantic Code Search** - Find code using natural language queries
- 🐛 **Intelligent Debugging** - Locate bugs, analyze root causes, generate fixes
- 💬 **AI Chat Assistant** - Ask questions about your codebase
- 📊 **Code Health Analysis** - Track quality metrics and bug hotspots
- 🕸️ **Graph Exploration** - Visualize call graphs and dependencies
- 🔒 **Privacy-First** - All data stays local (except LLM API calls)
- ⚡ **Fast & Scalable** - Handle large codebases efficiently

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd vibe-agent

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download BGE-M3 model (~2GB, one-time)
python ../models/download_bge_m3.py

# Configure
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Frontend setup
cd ../frontend
npm install

# Start backend
cd ../backend
uvicorn src.app.main:app --reload

# Start frontend (in new terminal)
cd frontend
npm run dev
```

Visit `http://localhost:3000` 🎉

## 📖 Usage

[view full documentation](docs/USER_GUIDE.md)

**Index your code:**
```bash
curl -X POST http://localhost:8000/index/start \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/your/repo"}'
```

**Search semantically:**
```bash
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication logic", "top_k": 10}'
```

**Debug an error:**
```bash
curl -X POST http://localhost:8000/debug/error \
  -H "Content-Type: application/json" \
  -d '{"error": {"error_type": "TypeError", "error_message": "...", ...}}'
```

## 🏗️ Architecture

```
Frontend (Next.js) 
    ↓
Backend API (FastAPI)
    ↓
┌────────┬──────────┬─────────┬────────┐
Indexing  Retrieval  Agents    Memory
    ↓         ↓         ↓         ↓
Neo4j    FAISS     Gemini   SQLite
```

[Full architecture docs](docs/ARCHITECTURE.md)

**Tech Stack:**
- Backend: Python, FastAPI, Tree-sitter, sentence-transformers
- Frontend: Next.js 14, TypeScript, TailwindCSS, Zustand
- Databases: Neo4j, FAISS, SQLite
- AI: Google Gemini, BGE-M3 embeddings

## 📊 System Components

| Component | Description | Status |
|-----------|-------------|--------|
| **Indexing Pipeline** | File discovery, AST parsing, chunking | ✅ Complete |
| **Intelligence Layer** | Static analysis, health scoring | ✅ Complete |
| **Graph Systems** | Neo4j ASG, call graphs | ✅ Complete |
| **Embeddings** | BGE-M3 local embeddings, FAISS | ✅ Complete |
| **Retrieval** | Hybrid semantic+graph search | ✅ Complete |
| **Memory** | Error tracking, conversations | ✅ Complete |
| **Agents** | 7 specialized AI agents | ✅ Complete |
| **LLM Integration** | Gemini API client | ✅ Complete |
| **Backend API** | 5 route modules, Swagger docs | ✅ Complete |
| **Frontend UI** | Pages & components | ✅ Complete |
| **Testing** | Unit & integration tests | 🔄 Partial |
| **Documentation** | User guide, architecture | ✅ Complete |

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
```

## 📚 Documentation

- [User Guide](docs/USER_GUIDE.md) - Installation, usage, troubleshooting
- [Architecture](docs/ARCHITECTURE.md) - System design, components, data flow
- [API Reference](http://localhost:8000/docs) - Swagger documentation (when running)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- Built with [Tree-sitter](https://tree-sitter.github.io/)
- Embeddings by [BGE-M3](https://huggingface.co/BAAI/bge-m3)
- LLM by [Google Gemini](https://ai.google.dev/)
- Vector search by [FAISS](https://github.com/facebookresearch/faiss)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for developers who love their local privacy**
