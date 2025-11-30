# Vibe Coding AI Agent - User Guide

## 🚀 Quick Start

### Prerequisites

**Required:**
- Python 3.10+
- Node.js 18+
- Git

**Optional (for full functionality):**
- Redis (for background tasks)
- Neo4j (for graph features)

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd vibe-agent
```

2. **Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download BGE-M3 model (one-time, ~2GB)
python ../models/download_bge_m3.py
```

3. **Configuration:**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings:
# - GEMINI_API_KEY=your_api_key_here
# - TARGET_REPO_PATH=/path/to/your/code
# - Other settings as needed
```

4. **Frontend Setup:**
```bash
cd ../frontend

# Install dependencies
npm install
```

## 🎯 Basic Usage

### Start the Backend

```bash
cd backend
uvicorn src.app.main:app --reload
```

Backend will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Index Your Codebase

**Via API:**
```bash
curl -X POST http://localhost:8000/index/start \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/your/code"}'
```

**Via Frontend:**
1. Navigate to Settings
2. Enter repository path
3. Click "Start Indexing"
4. Monitor progress in real-time

### Search Your Code

**Semantic Search:**
```bash
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application=json" \
  -d '{"query": "authentication logic", "top_k": 10}'
```

Returns relevant code chunks ranked by semantic similarity.

### Debug an Error

**Via API:**
```bash
curl -X POST http://localhost:8000/debug/error \
  -H "Content-Type: application/json" \
  -d '{
    "error": {
      "error_type": "TypeError",
      "error_message": "Cannot read property of undefined",
      "file_path": "src/main.py",
      "line_number": 42,
      "stack_trace": "..."
    },
    "auto_fix": true
  }'
```

Returns bug locations, root cause analysis, and optional fix suggestions.

## 💬 Chat Interface

The chat interface provides AI-powered code assistance:

1. **Ask Questions:**
   - "How does authentication work?"
   - "Explain this function: processUserData"
   - "What are the dependencies of api/routes.py?"

2. **Debug Errors:**
   - Paste error messages
   - Get bug locations and explanations
   - Request automated fixes

3. **Refactoring:**
   - "Suggest improvements for utils.py"
   - "How can I optimize this function?"

## 📊 Features

### Code Intelligence
- **Static Analysis**: Detect code smells, complexity issues
- **Health Scoring**: Per-file and per-function health metrics
- **Bug Hotspots**: Identify high-risk code areas

### Graph Exploration
- **Call Graphs**: Visualize function relationships
- **Dependency Tracking**: Understand import dependencies
- **Impact Analysis**: See what code is affected by changes

### Memory & Learning
- **Error Tracking**: Remember past bugs and fixes
- **Resolution History**: Learn from successful patches
- **Conversation Continuity**: Maintain context across sessions

## 🔧 Advanced Configuration

### Environment Variables

Key settings in `.env`:

```bash
# LLM Configuration
GEMINI_API_KEY=your_key_here
LLM_MODEL_TYPE=gemini-2.0-flash-exp
LLM_FALLBACK_MODEL=gemini-1.5-pro

# Embedding Configuration
USE_LOCAL_EMBEDDINGS=true
EMBEDDING_MODEL_PATH=../models/bge-m3

# Database Configuration
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Indexing Configuration
CHUNK_SIZE=400
CHUNK_OVERLAP=70
```

### Customizing Indexing

Edit exclusion patterns in code or via API configuration.

### Adjusting Search

Modify ranking weights in `src/retrieval/ranking.py`:
```python
SEMANTIC_WEIGHT = 0.60  # Adjust based on needs
GRAPH_WEIGHT = 0.25
HEALTH_WEIGHT = 0.10
RECENCY_WEIGHT = 0.05
```

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.10+)
- Verify dependencies: `pip install -r requirements.txt`
- Check `.env` file exists and has correct values

### Indexing fails
- Verify `TARGET_REPO_PATH` exists
- Check file permissions
- Look for errors in console output

### Embeddings error
- Ensure BGE-M3 model is downloaded
- Check `EMBEDDING_MODEL_PATH` in `.env`
- Verify sufficient disk space (~2GB for model)

### Neo4j connection error
- Start Neo4j: `neo4j start`
- Check connection settings in `.env`
- Verify username/password

## 📚 Learn More

- **Architecture**: See `docs/architecture.md`
- **API Reference**: Visit `http://localhost:8000/docs`
- **Contributing**: See `CONTRIBUTING.md`

## 🆘 Support

For issues or questions:
1. Check existing GitHub issues
2. Review documentation
3. Open a new issue with details
