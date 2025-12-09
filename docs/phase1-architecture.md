# Phase 1: Semantic Code Search Architecture

**Status:** COMPLETE ✓
**Date:** November 23, 2025

## Overview

Phase 1 implements a semantic code search system for Go repositories using RAG (Retrieval-Augmented Generation). The system indexes production Go code, generates embeddings, and stores them in a local vector database for semantic search.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT: GO REPOSITORIES                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  repo-1  │  │  repo-2  │  │  repo-3  │  │  repo-4  │  +  more  │
│  │          │  │          │  │          │  │          │           │
│  │ (564 fn) │  │ (440 fn) │  │  (298 fn) │  │ (295 fn) │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                    ~1,700+ production .go files                      │
│                    (tests, vendor, mocks excluded)                   │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│               COMPONENT 1: CODE INDEXER (indexer.py)                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  • Crawls repositories recursively                             │ │
│  │  • Filters production code (excludes tests/vendor/generated)   │ │
│  │  • Delegates to parser for each .go file                       │ │
│  │  • Creates IndexedFunction objects with metadata               │ │
│  │  • Detects code_type (handler, service, repository, etc.)      │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│               COMPONENT 2: GO PARSER (parser.py)                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  • Uses tree-sitter for AST parsing                            │ │
│  │  • Extracts function declarations & method declarations        │ │
│  │  • Captures: name, signature, body, docstring, receiver        │ │
│  │  • Returns GoFunction dataclass with line numbers              │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  OUTPUT: 2,139 INDEXED FUNCTIONS                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  IndexedFunction {                                             │ │
│  │    id: "repo/file.go:FunctionName"                             │ │
│  │    content: "docstring + signature + body (500 chars)"         │ │
│  │    metadata: {                                                 │ │
│  │      repo, file, function, start_line, end_line,               │ │
│  │      has_docstring, is_method, receiver, code_type             │ │
│  │    }                                                           │ │
│  │  }                                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│          COMPONENT 3: EMBEDDING GENERATOR (embeddings.py)            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  • OpenAI API: text-embedding-3-small                          │ │
│  │  • Batch processing: 100 texts per API call                    │ │
│  │  • Vector dimension: 1536 floats                               │ │
│  │  • Cost: ~$0.04 for 2,139 functions                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│               OUTPUT: 2,139 EMBEDDING VECTORS                        │
│              [0.0169, 0.0101, 0.0599, -0.0190, ...]                 │
│                     1536 dimensions each                             │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│            COMPONENT 4: VECTOR STORE (vector_store.py)               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  • Chroma DB (local persistent storage)                        │ │
│  │  • Collection: "production_code"                               │ │
│  │  • Stores: IDs + Documents + Embeddings + Metadata             │ │
│  │  • Semantic search with metadata filters                       │ │
│  │                                                                 │ │
│  │  FIXES APPLIED:                                                │ │
│  │  ✓ Convert tuple embeddings → list format                      │ │
│  │  ✓ Convert None metadata values → empty strings                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  CHROMA VECTOR DATABASE                              │
│              Location: ./data/chroma_db/                             │
│                                                                       │
│  Collection: production_code                                         │
│  ├── 2,139 function embeddings                                      │
│  ├── Full function content                                          │
│  └── Rich metadata for filtering                                    │
│                                                                       │
│  Enables:                                                            │
│  • Semantic similarity search                                       │
│  • Metadata filtering (by repo, type, etc.)                         │
│  • Fast vector operations                                           │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│            COMPONENT 5: SEARCH CLI (search_cli.py)                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Usage: python search_cli.py "query" [--limit N] [--type TYPE] │ │
│  │                                                                 │ │
│  │  Features:                                                      │ │
│  │  • Natural language queries                                    │ │
│  │  • Adjustable result count                                     │ │
│  │  • Metadata filtering                                          │ │
│  │  • Formatted output with code preview                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components Implemented

### 1. **Code Parser** (`src/parser.py`)

**Purpose:** Extract function definitions from Go source code using AST parsing.

**Technology:** tree-sitter (Go grammar)

**Output:**
```python
@dataclass
class GoFunction:
    name: str              # Function name
    signature: str         # Full signature
    body: str             # Function body
    docstring: Optional[str]  # Documentation
    receiver: Optional[str]   # For methods (e.g., "*Service")
    start_line: int
    end_line: int
```

**Key Features:**
- Extracts both functions and methods
- Captures docstrings
- Line-accurate positioning
- Handles Go-specific syntax (receivers)

---

### 2. **Repository Indexer** (`src/indexer.py`)

**Purpose:** Crawl repositories, filter production code, and prepare for embedding.

**Filtering Logic:**
- **INCLUDES:** Regular `.go` source files
- **EXCLUDES:**
  - Test files (`*_test.go`)
  - Vendor code (`/vendor/`, `/mocks/`, `/testdata/`)
  - Generated files (`.pb.go`, `.gen.go`, `generated`)
  - Config files (YAML, JSON, etc.)

**Output:**
```python
@dataclass
class IndexedFunction:
    id: str               # "repo/file.go:FunctionName"
    content: str          # Docstring + signature + body (truncated)
    metadata: Dict        # Rich metadata for filtering
```

**Metadata Fields:**
- `repo`: Repository name
- `file`: Relative file path
- `function`: Function name
- `start_line`, `end_line`: Line numbers
- `lines_of_code`: Function size
- `has_docstring`: Documentation flag
- `is_method`: Method vs function
- `receiver`: Method receiver (if applicable)
- `code_type`: Heuristic classification (handler, service, repository, etc.)

---

### 3. **Embedding Generator** (`src/embeddings.py`)

**Purpose:** Generate vector embeddings for semantic search.

**Technology:** OpenAI `text-embedding-3-small`

**Specifications:**
- Vector dimension: 1536
- Batch size: 100 texts per API call
- Cost: ~$0.02 per 1M tokens
- Error handling: None values for failed embeddings

**Performance:**
- 2,139 functions processed in ~40 seconds
- Cost: ~$0.04 per full index

---

### 4. **Vector Store** (`src/vector_store.py`)

**Purpose:** Manage Chroma vector database for semantic search.

**Features:**
- Persistent local storage
- Batch insertion
- Semantic similarity search
- Metadata filtering
- Statistics and analytics

**API:**
```python
store = VectorStore(persist_directory="./data/chroma_db")

# Add functions
store.add_functions(functions, embeddings)

# Search
results = store.search(
    query="JWT authentication",
    n_results=5,
    filter_metadata={"code_type": "handler"}
)

# Statistics
stats = store.get_stats()
```

**Critical Fixes Applied:**
1. **Embeddings Format:** Convert tuples to lists for Chroma compatibility
2. **Metadata None Values:** Convert None to empty strings

---

### 5. **Search CLI** (`search_cli.py`)

**Purpose:** Command-line interface for testing semantic search.

**Usage:**
```bash
# Basic search
python search_cli.py "JWT authentication"

# With options
python search_cli.py "database transaction" --limit 10 --type service
```

**Output Format:**
```
[1] go-auth/middleware/jwt.go:ValidateToken
====================================================================
📁 Repo: go-auth
📄 File: middleware/jwt.go:45-78
🏷️  Type: middleware
📏 Lines: 33
----------------------------------------------------------------------
Code Preview:
----------------------------------------------------------------------
func ValidateToken(token string) (Claims, error) {
    // Parse and validate JWT token
    ...
}
====================================================================
```

---

## Data Flow

```
.go files → Parser → Functions → Indexer → IndexedFunctions
                                              ↓
                                     Embedding Generator
                                              ↓
                                         Embeddings
                                              ↓
                                       Vector Store
                                              ↓
                                         Chroma DB
                                              ↓
                                        Search CLI
                                              ↓
                                      Semantic Results
```

---

## Project Structure

```
project/
├── src/
│   ├── parser.py         # tree-sitter Go AST parser
│   ├── indexer.py        # Repository crawler & filter
│   ├── embeddings.py     # OpenAI embedding generator
│   └── vector_store.py   # Chroma DB wrapper
│
├── index_repos.py        # Main indexing pipeline
├── search_cli.py         # Search interface
├── requirements.txt      # Python dependencies
├── .env                  # API keys (gitignored)
│
├── repos/                # Source repositories (gitignored)
├── data/                 # Vector database (gitignored)
│   └── chroma_db/
│
└── docs/
    ├── CONTEXT.md
    ├── concrete-problem-examples.md
    └── phase1-architecture.md (this file)
```

---

## Key Metrics

| Metric | Value |
|--------|-------|
| **Repositories** | 9 total (7 production + 1 example + 1 empty) |
| **Total .go files found** | 2,427 |
| **Test files skipped** | 573 |
| **Vendor/mocks skipped** | 78 |
| **Generated files skipped** | 4 |
| **Production files indexed** | 1,772 |
| **Functions extracted** | 2,139 |
| **Embedding cost** | ~$0.12 (includes debugging runs) |
| **Vector database size** | ~79 MB (includes model cache) |
| **Average indexing time** | ~40 seconds (parsing + embeddings) |

---

## Repository Breakdown

| Repository | Functions | Notes |
|------------|-----------|-------|
| repo-1 | 564 | Largest codebase |
| repo-2 | 440 | Authentication services |
| repo-3 | 409 | API gateway |
| repo-4 | 298 | Core API |
| repo-5 | 295 | Service engine |
| repo-6 | 97 | Utilities |
| repo-7 | 28 | Event handling |
| repo-8 | 8 | Integration service |
| repo-9 | 0 | No production code |

---

## Function Type Distribution

| Type | Count | Description |
|------|-------|-------------|
| other | 1,250 | Uncategorized (default) |
| client | 172 | API clients |
| handler | 160 | HTTP/gRPC handlers |
| service | 147 | Business logic services |
| model | 137 | Data models |
| utility | 107 | Helper functions |
| repository | 107 | Data access layer |
| middleware | 59 | Request middleware |

---

## Technical Challenges & Solutions

### Challenge 1: tree-sitter Version Compatibility

**Problem:** API breaking change between tree-sitter 0.21.3 and 0.23.2

**Error:**
```python
TypeError: __init__() takes exactly 1 argument (2 given)
```

**Solution:**
- Pinned to tree-sitter 0.21.3
- Changed from `Parser(language)` to `Parser().set_language(language)`

**Files:** `requirements.txt`, `src/parser.py`

---

### Challenge 2: Chroma Embeddings Format

**Problem:** Chroma rejects tuple format for embeddings

**Error:**
```
ValueError: Expected embeddings to be a list of floats or ints,
a list of lists, a numpy array, or a list of numpy arrays, got ([...
```

**Root Cause:**
```python
# This creates tuples, not lists
functions_valid, embeddings_valid = zip(*valid_items)
```

**Solution:**
```python
# Explicit conversion to list format (vector_store.py:76)
embeddings_list = [list(e) if not isinstance(e, list) else e
                   for e in embeddings_valid]
```

---

### Challenge 3: None Metadata Values

**Problem:** Chroma rejects None values in metadata

**Error:**
```
TypeError: 'NoneType' object cannot be converted to 'PyString'
```

**Root Cause:**
```python
# receiver is None for regular functions (not methods)
"receiver": func.receiver  # Can be None!
```

**Solution:**
```python
# Convert None to empty string (indexer.py:176)
"receiver": func.receiver if func.receiver else ""
```

---

## Dependencies

### Python Packages

```
chromadb>=0.4.0          # Vector database
openai>=1.0.0            # Embeddings API
tree-sitter==0.21.3      # AST parser (pinned version)
tree-sitter-languages==1.10.2  # Language grammars
python-dotenv>=1.0.0     # Environment variables
pydantic>=2.0.0          # Data validation
tqdm>=4.65.0             # Progress bars
click>=8.1.0             # CLI framework
pytest>=7.0.0            # Testing
```

### External Services

- **OpenAI API:** Embedding generation
- **Chroma:** Local vector database (no cloud dependency)

---

## Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-proj-...     # Required for embeddings
REPOS_PATH=./repos              # Input repositories path
CHROMA_PATH=./data/chroma_db    # Vector database path
LOG_LEVEL=INFO                  # Logging level
```

---

## Usage

### Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Copy repositories to index
cp -r /path/to/repos ./repos/
```

### Indexing

```bash
# Index all repositories
python index_repos.py

# Reset and reindex
python index_repos.py --reset
```

### Searching

```bash
# Basic search
python search_cli.py "JWT authentication"

# Advanced search
python search_cli.py "database transaction" --limit 10 --type service
```

### Testing Individual Components

```bash
# Test parser
python src/parser.py

# Test indexer
python src/indexer.py

# Test embeddings
python src/embeddings.py

# Test vector store
python src/vector_store.py
```

---

## Future Improvements (Phase 2)

1. **MCP Server Integration**
   - Build MCP server wrapping search functionality
   - Implement tools for semantic search
   - Add repository management tools

2. **Enhanced Search**
   - Multi-repo filtering
   - Code similarity scoring
   - Full file context retrieval

3. **Incremental Updates**
   - Git hook integration
   - Delta indexing (only changed files)
   - Automatic reindexing

4. **Performance Optimization**
   - Caching layer
   - Parallel processing
   - Streaming results

5. **Claude Code Integration** (Phase 3)
   - Configure Claude Code MCP
   - Context enrichment in prompts
   - Pattern suggestion workflow

---

## Lessons Learned

1. **Version Pinning:** Always pin critical dependencies (tree-sitter)
2. **Type Validation:** Explicit type conversion prevents runtime errors
3. **Error Handling:** Graceful degradation for failed embeddings
4. **Filtering Logic:** Production code filtering is crucial for signal/noise
5. **Cost Management:** Batch processing reduces API costs significantly
6. **Metadata Design:** Rich metadata enables powerful filtering

---

## Success Criteria - MET ✓

- [x] Index 2,000+ production Go functions
- [x] Generate embeddings for all functions
- [x] Store in local vector database
- [x] Build search CLI
- [x] Cost under $1 for MVP
- [x] Sub-1 minute indexing time
- [x] Semantic search working

---

## Next Phase

**Phase 2: MCP Server Development**

Build Model Context Protocol server to expose semantic search to Claude Code.

See: `docs/phase2-mcp-server.md` (to be created)
