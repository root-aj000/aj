# Vibe Coding AI Agent - Architecture Documentation

## System Overview

Vibe Agent is a local-first AI coding assistant that combines:
- **Static code analysis** for deep code understanding
- **Graph databases** for relationship tracking
- **Vector embeddings** for semantic search
- **LLM reasoning** for intelligent responses
- **Multi-agent orchestration** for complex tasks

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                  │
│  Chat UI │ Code Viewer │ Graph Explorer │ Index Dashboard  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────┴────────────────────────────────────────┐
│                     Backend API (FastAPI)                    │
│   /index │ /search │ /chat │ /debug │ /graph              │
└──┬───────┬────────┬─────────┬─────────┬─────────────────────┘
   │       │        │         │         │
   ▼       ▼        ▼         ▼         ▼
┌──────┐ ┌────────┐ ┌───────┐ ┌──────┐ ┌─────────┐
│Index │ │Retriev │ │ Agent │ │Memory│ │Reasoning│
│ ing  │ │  al    │ │Orches.│ │      │ │ Engine  │
└──┬───┘ └───┬────┘ └───┬───┘ └──┬───┘ └────┬────┘
   │         │          │        │          │
   ▼         ▼          ▼        ▼          ▼
┌─────┐  ┌────────┐  ┌─────┐  ┌──────┐  ┌────────┐
│Files│  │ FAISS  │  │Agents│ │SQLite│  │ Gemini │
│ AST │  │Vectors │  │  7x  │ │ DB   │  │  API   │
│Tree │  │  BGE   │  └─────┘  └──────┘  └────────┘
└─┬───┘  └────────┘
  │
  ▼
┌───────────┐
│  Neo4j    │
│   Graph   │
└───────────┘
```

## Core Components

### 1. Indexing Pipeline

**Purpose**: Discover, parse, and catalog code

**Flow**:
1. **File Walker** - Recursively discover source files
2. **AST Parser** - Parse into abstract syntax trees
3. **Chunker** - Split into semantic chunks
4. **Manifest Generator** - Create unified catalog

**Output**: Structured manifest with files, functions, classes, chunks

### 2. Intelligence Layer

**Purpose**: Analyze code quality and health

**Components**:
- **Static Analyzer** - Detect code smells, complexity
- **Import Resolver** - Build dependency graph
- **Health Scanner** - Calculate health scores
- **Code Health DB** - Track metrics over time

**Output**: Health scores, bug hotspots, smell reports

### 3. Graph Systems

**Purpose**: Model code relationships

**Database**: Neo4j

**Nodes**:
- `Function` - name, file, signature, complexity
- `Class` - name, file, methods
- `File` - path, language, size

**Relationships**:
- `CALLS` - Function → Function
- `CONTAINS` - File → Function/Class
- `IMPORTS` - File → File
- `EXTENDS` - Class → Class

**Queries**:
- Find callers/callees
- Trace execution paths
- Analyze dependencies

### 4. Embedding & Vector Store

**Purpose**: Enable semantic code search

**Model**: BGE-M3 (local, 1024 dimensions)

**Process**:
1. Generate embeddings for all chunks
2. Store in FAISS index with metadata
3. Normalize for cosine similarity

**Search**: Query → Embedding → K-NN → Ranked results

### 5. Retrieval System

**Purpose**: Find relevant code for queries

**Strategy**: Hybrid ranking

**Scoring**:
```
score = 0.60 × semantic_similarity
      + 0.25 × graph_relevance
      + 0.10 × code_health
      + 0.05 × recency
```

**Pipeline**:
1. Semantic search (FAISS)
2. Graph expansion (Neo4j)
3. Hybrid ranking
4. Deduplication
5. Context packing

### 6. Memory Systems

**Purpose**: Learn from past interactions

**Storage**: SQLite

**Tracked**:
- Error snapshots
- Resolution attempts
- Debug sessions
- Conversation history

**Benefits**:
- Suggest fixes based on similar errors
- Track recurring bugs
- Maintain context across sessions

### 7. Agent Orchestration

**Purpose**: Coordinate specialized agents

**Agents**:
1. **Query Agent** - Parse user intent
2. **Retrieval Agent** - Find relevant code
3. **Bug Localization Agent** - Pinpoint bugs
4. **Root Cause Agent** - Analyze causes
5. **Reasoning Agent** - Explain code
6. **Patch Agent** - Generate fixes
7. **Refactor Agent** - Suggest improvements

**Workflow**:
```
User Query → Query Agent → Retrieval Agent →
  ↓
Bug Localization → Root Cause → Patch Agent
  ↓
Response to User
```

### 8. Reasoning Engine

**Purpose**: Generate intelligent responses

**LLM**: Google Gemini
- Primary: gemini-2.0-flash-exp
- Fallback: gemini-1.5-pro

**Features**:
- Rate limiting
- Retry logic
- Streaming support
- Token management

**Context Packing**:
- Max tokens: 70K
- Reserved: 3K (system) + 8K (output)
- Available: ~59K for context

## Data Flow

### Indexing Flow
```
Repository → Walker → AST Parser → Chunker → Embeddings → FAISS
                 ↓                                          ↓
              Manifest ← Health Scanner ← Static Analyzer   Graph (Neo4j)
```

### Query Flow
```
User Query → Query Agent → Semantic Search (FAISS)
                       ↓
                Graph Expansion (Neo4j)
                       ↓
                Hybrid Ranking
                       ↓
                Context Packing
                       ↓
                LLM (Gemini)
                       ↓
                Response
```

### Debug Flow
```
Error Input → Bug Localization Agent → Find Similar (Memory DB)
                       ↓
            Retrieve Related Code (Hybrid Search)
                       ↓
            Root Cause Analysis (LLM)
                       ↓
            Patch Generation (Patch Agent)
                       ↓
            Save Resolution (Memory DB)
```

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Testing**: pytest
- **Task Queue**: Celery (optional)

### Databases
- **Graph**: Neo4j
- **Vector**: FAISS
- **Relational**: SQLite
- **Cache**: Redis (optional)

### AI/ML
- **LLM**: Google Gemini
- **Embeddings**: BGE-M3 (sentence-transformers)
- **Parsing**: Tree-sitter

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **State**: Zustand
- **UI**: TailwindCSS
- **Code**: Monaco Editor

## Scalability Considerations

### Performance
- **Indexing**: Batch processing, parallelization
- **Search**: FAISS optimized for large-scale
- **Graph**: Neo4j indexes on key properties
- **Caching**: Embedding cache, LLM response cache

### Storage
- **Embeddings**: ~4KB per chunk
- **Graph**: ~1KB per function node
- **Memory DB**: Grows with errors/sessions

### Limits
- **Max repo size**: ~100K files (with optimization)
- **Max context**: 70K tokens (~280KB code)
- **Max embeddings**: Millions (FAISS scales)

## Security

- **Local-first**: All data stays on your machine
- **API keys**: Stored in `.env`, never committed
- **No telemetry**: No data sent to external services
- **Sandboxing**: (Future) Isolated patch testing

## Extensibility

### Adding New Languages
1. Add Tree-sitter grammar
2. Update `ASTParser` language map
3. Add language-specific patterns

### Custom Agents
1. Implement agent interface
2. Add to `AgentOrchestrator`
3. Define system prompts

### Alternative LLMs
1. Implement `LLMClient` interface
2. Update configuration
3. Test compatibility

## Future Enhancements

- Multi-repository support
- Incremental indexing
- Advanced CFG analysis
- Type inference improvements
- UI/UX polish
- Performance optimization
