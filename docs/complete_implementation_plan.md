# Complete Implementation Plan: MCP Server with RAG for Code Patterns

**Goal:** Build MCP server that provides Claude Code with team's coding patterns via RAG
**Timeline:** 25-32 hours over 3 weekends
**Commitment:** You have 25-35 hours available

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     GOLDEN EXAMPLES                             │
│                    (20-30 Perfect Files)                        │
│                                                                 │
│  patterns/                                                      │
│  ├── handlers/                                                  │
│  │   ├── user_handler.go        (perfect example)              │
│  │   ├── product_handler.go     (perfect example)              │
│  │   └── auth_handler.go        (perfect example)              │
│  ├── services/                                                  │
│  │   ├── user_service.go                                       │
│  │   └── notification_service.go                               │
│  ├── middleware/                                                │
│  │   ├── auth_middleware.go                                    │
│  │   └── logging_middleware.go                                 │
│  └── models/                                                    │
│      ├── user.go                                               │
│      └── product.go                                            │
└────────────────────────────────────────────────────────────────┘
                              ↓ Indexing Phase
┌────────────────────────────────────────────────────────────────┐
│                    YOUR MCP SERVER                              │
│                  (Python Application)                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  1. INDEXER COMPONENT                                     │ │
│  │     ├── File Loader (reads .go, .js, .ts files)          │ │
│  │     ├── AST Parser (tree-sitter)                         │ │
│  │     ├── Chunk Generator (function-level)                 │ │
│  │     └── Metadata Extractor (package, imports, etc)       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  2. RAG COMPONENT                                         │ │
│  │     ├── OpenAI Embeddings API                            │ │
│  │     │   (text-embedding-3-small)                         │ │
│  │     ├── Vector Database (Chroma)                         │ │
│  │     │   - Stores embeddings                              │ │
│  │     │   - Stores metadata                                │ │
│  │     │   - Semantic search                                │ │
│  │     └── Retrieval Logic                                  │ │
│  │         - Query embedding                                │ │
│  │         - Similarity search                              │ │
│  │         - Filtering by metadata                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  3. MCP INTERFACE COMPONENT                               │ │
│  │     ├── MCP Tools (Functions Claude can call)            │ │
│  │     │   - search_patterns()                              │ │
│  │     │   - get_pattern_details()                          │ │
│  │     │   - validate_code()                                │ │
│  │     │   - list_pattern_types()                           │ │
│  │     ├── MCP Server (stdio transport)                     │ │
│  │     └── JSON-RPC Protocol Handler                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Server runs: python mcp_server.py                             │
└────────────────────────────────────────────────────────────────┘
                              ↕ MCP Protocol (STDIO)
┌────────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE                                │
│                  (Official Anthropic CLI)                       │
│                                                                 │
│  Configuration: ~/.config/Claude/claude_desktop_config.json    │
│  {                                                              │
│    "mcpServers": {                                              │
│      "company-patterns": {                                      │
│        "type": "stdio",                                         │
│        "command": "python",                                     │
│        "args": ["/path/to/mcp_server.py"]                      │
│      }                                                          │
│    }                                                            │
│  }                                                              │
│                                                                 │
│  Capabilities:                                                  │
│  - Auto-discovers MCP tools                                    │
│  - Calls tools when needed                                     │
│  - Manages context automatically                               │
└────────────────────────────────────────────────────────────────┘
                              ↓ User Interface
┌────────────────────────────────────────────────────────────────┐
│                        DEVELOPER                                │
│                                                                 │
│  $ claude                                                       │
│  > "Add JWT authentication middleware"                         │
│                                                                 │
│  Claude Code:                                                   │
│  1. Calls: search_patterns("JWT auth", "middleware")           │
│  2. Gets: auth_middleware.go, jwt_handler.go                   │
│  3. Generates code matching those patterns                     │
│  4. Returns: Perfect middleware code ✅                        │
└────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
codebase-patterns-mcp/
├── mcp_server.py              # Main MCP server
├── requirements.txt           # Python dependencies
├── .env                       # API keys (gitignored)
├── README.md                  # Documentation
│
├── src/
│   ├── __init__.py
│   ├── indexer.py            # Loads and indexes patterns
│   ├── rag.py                # RAG retrieval logic
│   ├── parser.py             # AST parsing (tree-sitter)
│   ├── validator.py          # Code validation
│   └── config.py             # Configuration management
│
├── patterns/                  # Your golden examples
│   ├── handlers/
│   │   ├── user_handler.go
│   │   ├── product_handler.go
│   │   └── auth_handler.go
│   ├── services/
│   │   ├── user_service.go
│   │   └── notification_service.go
│   ├── middleware/
│   │   ├── auth_middleware.go
│   │   └── logging_middleware.go
│   └── models/
│       ├── user.go
│       └── product.go
│
├── data/
│   ├── chroma_db/            # Vector database (auto-generated)
│   └── metadata.json         # Pattern metadata cache
│
├── tests/
│   ├── test_indexer.py
│   ├── test_rag.py
│   ├── test_mcp_tools.py
│   └── test_queries.json     # Test queries for evaluation
│
└── scripts/
    ├── setup.sh              # Initial setup script
    ├── index_patterns.py     # Reindex patterns
    └── test_retrieval.py     # Test retrieval quality
```

---

## Phase-by-Phase Implementation

---

## PHASE 1: Foundation & Learning (Weekend 1 - 12 hours)

**Goal:** Understand MCP, build basic server, prove concept works

### **Friday Evening: Setup & Learning (3 hours)**

#### **Task 1.1: Environment Setup (1 hour)**

```bash
# Create project directory
mkdir codebase-patterns-mcp
cd codebase-patterns-mcp

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Create requirements.txt
cat > requirements.txt << EOF
# MCP Server
mcp>=1.0.0

# RAG Components
chromadb>=0.4.0
openai>=1.0.0
sentence-transformers>=2.0.0

# Code Parsing
tree-sitter>=0.20.0
tree-sitter-go>=0.20.0
tree-sitter-javascript>=0.20.0
tree-sitter-typescript>=0.20.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
aiofiles>=23.0.0

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
EOF

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your-key-here
PATTERNS_PATH=./patterns
CHROMA_PATH=./data/chroma_db
LOG_LEVEL=INFO
EOF

# Add to .gitignore
cat > .gitignore << EOF
venv/
.env
*.pyc
__pycache__/
data/chroma_db/
.DS_Store
EOF
```

**Success Criteria:**
- ✅ Virtual environment created
- ✅ All dependencies installed without errors
- ✅ .env file configured with API keys

---

#### **Task 1.2: Learn MCP Basics (1 hour)**

**Read these resources:**
1. Anthropic MCP Documentation: https://docs.anthropic.com/mcp
2. MCP Python SDK: https://github.com/anthropics/mcp-python-sdk
3. Example MCP servers: https://github.com/modelcontextprotocol/servers

**Key concepts to understand:**
- MCP Server structure
- Tool definitions (@mcp.tool decorator)
- STDIO transport
- JSON-RPC protocol (high-level, not deep)

**Hands-on: Run an example MCP server**
```bash
# Try the weather example
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/weather
npm install
node build/index.js

# Observe how it works
```

**Success Criteria:**
- ✅ Understand MCP server structure
- ✅ Know how to define tools
- ✅ Ran example server successfully

---

#### **Task 1.3: Select Golden Examples (1 hour)**

**Choose 5-10 perfect code files for POC:**

**Selection criteria:**
1. **Represents common patterns** (not edge cases)
2. **High quality** (you'd want all code to look like this)
3. **Different pattern types** (handlers, services, middleware)
4. **Consistent style** within each type
5. **Well-documented** (comments, docstrings)

**Recommended initial set:**
```
patterns/
├── handlers/
│   ├── user_handler.go       # RESTful CRUD handler
│   └── auth_handler.go       # Authentication handler
├── services/
│   ├── user_service.go       # Business logic layer
│   └── auth_service.go       # Auth business logic
├── middleware/
│   ├── auth_middleware.go    # JWT validation
│   └── logging_middleware.go # Request logging
└── models/
    ├── user.go               # Data model
    └── response.go           # API response structure
```

**Document why each is "perfect":**
```markdown
# patterns/README.md

## Golden Examples

### handlers/user_handler.go
- **Why perfect:**
  - Named struct types (no anonymous)
  - Consistent error handling
  - Proper separation: handler → service → repository
  - Clear function naming
  - Max 50 lines per function
  
- **Patterns to copy:**
  - HTTP handler signature
  - Error response format
  - Request validation approach
  - Context passing
```

**Success Criteria:**
- ✅ 5-10 files selected and copied to `patterns/`
- ✅ Each tagged by type (handler, service, middleware, etc.)
- ✅ Documentation of why each is perfect

---

### **Saturday Morning: Basic MCP Server (4 hours)**

#### **Task 1.4: Minimal MCP Server (2 hours)**

Create the simplest possible working MCP server:

```python
# mcp_server.py (Version 1 - Minimal)
import asyncio
import os
from mcp.server import Server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create MCP server
server = Server("company-patterns")

@server.tool()
async def search_patterns(query: str, pattern_type: str = None) -> list[TextContent]:
    """
    Search for code patterns matching the query.
    
    Args:
        query: What to search for (e.g., "authentication", "error handling")
        pattern_type: Optional filter (handler, service, middleware, model)
    
    Returns:
        List of matching code patterns
    """
    # For now, just return hardcoded example
    # We'll add real RAG in Phase 2
    
    example_pattern = """
    [File: patterns/handlers/user_handler.go]
    
    func GetUserHandler(w http.ResponseWriter, r *http.Request) {
        // Extract user ID from URL
        userId := chi.URLParam(r, "id")
        
        // Call service layer
        user, err := userService.GetByID(r.Context(), userId)
        if err != nil {
            respondError(w, http.StatusNotFound, "User not found")
            return
        }
        
        // Return success response
        respondJSON(w, http.StatusOK, user)
    }
    """
    
    return [
        TextContent(
            type="text",
            text=f"Found pattern matching '{query}':\n\n{example_pattern}"
        )
    ]

@server.tool()
async def list_pattern_types() -> list[TextContent]:
    """List available pattern types"""
    types = ["handler", "service", "middleware", "model"]
    return [
        TextContent(
            type="text",
            text=f"Available pattern types: {', '.join(types)}"
        )
    ]

async def main():
    """Run the MCP server"""
    print("Starting Company Patterns MCP Server...")
    print(f"Patterns directory: {os.getenv('PATTERNS_PATH', './patterns')}")
    
    # Run server (stdio transport)
    async with server:
        await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Test it works:**
```bash
# Run server directly (should not crash)
python mcp_server.py

# You should see:
# Starting Company Patterns MCP Server...
# Patterns directory: ./patterns
# (then it waits for input - this is correct!)

# Press Ctrl+C to stop
```

**Success Criteria:**
- ✅ Server starts without errors
- ✅ Defines at least one tool
- ✅ Runs and waits for input (STDIO)

---

#### **Task 1.5: Connect to Claude Code (2 hours)**

**Install Claude Code (if not already):**
```bash
npm install -g @anthropic-ai/claude-code

# Verify
claude --version
```

**Configure Claude Code to use your MCP server:**
```bash
# Add your server to Claude Code
claude mcp add-json company-patterns --scope user '{
  "type": "stdio",
  "command": "python",
  "args": ["'$(pwd)'/mcp_server.py"],
  "env": {
    "OPENAI_API_KEY": "'"$OPENAI_API_KEY"'",
    "PATTERNS_PATH": "'"$(pwd)/patterns"'"
  }
}'

# Verify it's added
claude mcp list
```

**Test integration:**
```bash
# Start Claude Code
claude

# Inside Claude Code, check MCP status
> /mcp

# Should show:
# • company-patterns: connected ✅

# Test your tool
> Can you search for handler patterns?

# Claude should call your search_patterns tool!
```

**Troubleshooting if not working:**
```bash
# Check logs
tail -f ~/.claude/logs/mcp.log

# Verify config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Test server directly
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python mcp_server.py
```

**Success Criteria:**
- ✅ Claude Code connects to your MCP server
- ✅ `/mcp` shows "connected"
- ✅ Claude can call your `search_patterns` tool
- ✅ Returns hardcoded example (proves integration works)

---

### **Saturday Afternoon: Basic RAG (5 hours)**

#### **Task 1.6: Implement File Loader (1 hour)**

```python
# src/indexer.py
import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CodeFile:
    """Represents a code file"""
    path: str
    content: str
    language: str
    pattern_type: str  # handler, service, middleware, etc.
    
class PatternLoader:
    """Loads golden pattern files"""
    
    def __init__(self, patterns_dir: str):
        self.patterns_dir = Path(patterns_dir)
        
    def load_all(self) -> List[CodeFile]:
        """Load all pattern files"""
        files = []
        
        # Walk through patterns directory
        for pattern_type_dir in self.patterns_dir.iterdir():
            if not pattern_type_dir.is_dir():
                continue
                
            pattern_type = pattern_type_dir.name  # handlers, services, etc.
            
            # Load all code files in this directory
            for file_path in pattern_type_dir.glob("*"):
                if file_path.suffix not in ['.go', '.js', '.ts', '.py']:
                    continue
                
                try:
                    content = file_path.read_text()
                    language = self._detect_language(file_path.suffix)
                    
                    files.append(CodeFile(
                        path=str(file_path.relative_to(self.patterns_dir)),
                        content=content,
                        language=language,
                        pattern_type=pattern_type
                    ))
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        print(f"Loaded {len(files)} pattern files")
        return files
    
    def _detect_language(self, suffix: str) -> str:
        """Detect language from file extension"""
        mapping = {
            '.go': 'go',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.py': 'python'
        }
        return mapping.get(suffix, 'unknown')

# Test it
if __name__ == "__main__":
    loader = PatternLoader("./patterns")
    files = loader.load_all()
    for f in files:
        print(f"{f.pattern_type}/{f.path} ({f.language}) - {len(f.content)} chars")
```

**Test:**
```bash
python src/indexer.py

# Should output:
# Loaded 8 pattern files
# handlers/user_handler.go (go) - 1234 chars
# handlers/auth_handler.go (go) - 987 chars
# ...
```

**Success Criteria:**
- ✅ Loads all files from patterns directory
- ✅ Correctly detects language
- ✅ Extracts pattern type from directory

---

#### **Task 1.7: Implement Simple Embeddings & Vector DB (2 hours)**

```python
# src/rag.py
import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from src.indexer import CodeFile

class PatternRAG:
    """RAG system for code patterns"""
    
    def __init__(self, chroma_path: str):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize Chroma
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="code_patterns",
            metadata={"description": "Company code patterns"}
        )
        
    def index_patterns(self, files: List[CodeFile]):
        """Index all pattern files"""
        print(f"Indexing {len(files)} patterns...")
        
        # For now, index entire files
        # Phase 2: We'll add function-level chunking
        
        ids = []
        documents = []
        metadatas = []
        
        for i, file in enumerate(files):
            ids.append(f"pattern_{i}")
            documents.append(file.content)
            metadatas.append({
                "path": file.path,
                "language": file.language,
                "pattern_type": file.pattern_type,
                "filename": os.path.basename(file.path)
            })
        
        # Create embeddings and add to collection
        # Chroma will automatically use OpenAI embeddings
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ Indexed {len(files)} patterns")
    
    def search(self, query: str, pattern_type: str = None, top_k: int = 3) -> List[Dict]:
        """Search for matching patterns"""
        
        # Build where clause for filtering
        where = {}
        if pattern_type:
            where["pattern_type"] = pattern_type
        
        # Query collection
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where if where else None
        )
        
        # Format results
        patterns = []
        for i in range(len(results['ids'][0])):
            patterns.append({
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": results['distances'][0][i]
            })
        
        return patterns

# Test it
if __name__ == "__main__":
    from src.indexer import PatternLoader
    
    # Load patterns
    loader = PatternLoader("./patterns")
    files = loader.load_all()
    
    # Index them
    rag = PatternRAG("./data/chroma_db")
    rag.index_patterns(files)
    
    # Test search
    results = rag.search("authentication handler", pattern_type="handlers")
    print(f"\nFound {len(results)} results for 'authentication handler':")
    for r in results:
        print(f"  - {r['metadata']['path']} (score: {r['score']:.3f})")
```

**Test:**
```bash
python src/rag.py

# Should output:
# Loaded 8 pattern files
# Indexing 8 patterns...
# ✅ Indexed 8 patterns
# 
# Found 3 results for 'authentication handler':
#   - handlers/auth_handler.go (score: 0.234)
#   - handlers/user_handler.go (score: 0.456)
#   - middleware/auth_middleware.go (score: 0.567)
```

**Success Criteria:**
- ✅ Creates embeddings using OpenAI
- ✅ Stores in Chroma vector DB
- ✅ Can search and retrieve relevant patterns
- ✅ Filters by pattern_type work

---

#### **Task 1.8: Integrate RAG into MCP Server (2 hours)**

Update `mcp_server.py` to use real RAG:

```python
# mcp_server.py (Version 2 - With RAG)
import asyncio
import os
from mcp.server import Server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

from src.indexer import PatternLoader
from src.rag import PatternRAG

# Load environment
load_dotenv()

# Global RAG instance (initialized on startup)
rag: PatternRAG = None

# Create MCP server
server = Server("company-patterns")

@server.tool()
async def search_patterns(query: str, pattern_type: str = None, limit: int = 3) -> list[TextContent]:
    """
    Search for code patterns matching the query.
    
    Args:
        query: What to search for (e.g., "JWT authentication", "error handling")
        pattern_type: Optional filter (handlers, services, middleware, models)
        limit: Number of results to return (default: 3)
    
    Returns:
        List of matching code patterns with metadata
    """
    # Search using RAG
    results = rag.search(query, pattern_type=pattern_type, top_k=limit)
    
    # Format for Claude
    formatted_results = []
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        content = result['content']
        score = result['score']
        
        formatted = f"""
Result {i} (relevance: {1-score:.2f})
File: {metadata['path']}
Type: {metadata['pattern_type']}
Language: {metadata['language']}

```{metadata['language']}
{content}
```
"""
        formatted_results.append(formatted)
    
    return [
        TextContent(
            type="text",
            text=f"Found {len(results)} patterns matching '{query}':\n\n" + 
                 "\n---\n".join(formatted_results)
        )
    ]

@server.tool()
async def list_pattern_types() -> list[TextContent]:
    """List available pattern types with counts"""
    # Query metadata from Chroma
    all_metadata = rag.collection.get()['metadatas']
    
    types = {}
    for meta in all_metadata:
        ptype = meta.get('pattern_type', 'unknown')
        types[ptype] = types.get(ptype, 0) + 1
    
    formatted = "\n".join([f"- {ptype}: {count} patterns" 
                          for ptype, count in sorted(types.items())])
    
    return [
        TextContent(
            type="text",
            text=f"Available pattern types:\n\n{formatted}"
        )
    ]

async def initialize():
    """Initialize RAG system on startup"""
    global rag
    
    print("Starting Company Patterns MCP Server...")
    
    patterns_path = os.getenv('PATTERNS_PATH', './patterns')
    chroma_path = os.getenv('CHROMA_PATH', './data/chroma_db')
    
    print(f"Patterns directory: {patterns_path}")
    print(f"Vector DB: {chroma_path}")
    
    # Initialize RAG
    rag = PatternRAG(chroma_path)
    
    # Check if we need to index
    if rag.collection.count() == 0:
        print("No patterns indexed. Indexing now...")
        loader = PatternLoader(patterns_path)
        files = loader.load_all()
        rag.index_patterns(files)
    else:
        print(f"Found {rag.collection.count()} indexed patterns")
    
    print("✅ MCP Server ready!")

async def main():
    """Run the MCP server"""
    await initialize()
    
    # Run server
    async with server:
        await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Test:**
```bash
# Restart Claude Code to pick up changes
claude restart

# In Claude Code
> /mcp

# Should show: company-patterns: connected ✅

# Test it
> Search for authentication patterns

# Claude should call your tool and get REAL patterns from your files!
```

**Success Criteria:**
- ✅ MCP server uses RAG for retrieval
- ✅ Returns actual code from your golden examples
- ✅ Claude Code can call tools and get results
- ✅ Filtering by pattern_type works

---

### **Sunday: Testing & Documentation (3 hours)**

#### **Task 1.9: Create Test Suite (1.5 hours)**

```python
# tests/test_queries.json
[
  {
    "id": 1,
    "query": "How do we handle JWT authentication?",
    "pattern_type": "handlers",
    "expected_files": [
      "handlers/auth_handler.go",
      "middleware/auth_middleware.go"
    ]
  },
  {
    "id": 2,
    "query": "Show me user service patterns",
    "pattern_type": "services",
    "expected_files": [
      "services/user_service.go"
    ]
  },
  {
    "id": 3,
    "query": "Error handling in HTTP handlers",
    "pattern_type": "handlers",
    "expected_files": [
      "handlers/user_handler.go",
      "handlers/auth_handler.go"
    ]
  }
]
```

```python
# scripts/test_retrieval.py
import json
from src.rag import PatternRAG

def test_retrieval():
    """Test retrieval quality"""
    rag = PatternRAG("./data/chroma_db")
    
    with open('tests/test_queries.json') as f:
        test_queries = json.load(f)
    
    results = []
    for test in test_queries:
        print(f"\nQuery {test['id']}: {test['query']}")
        
        # Search
        patterns = rag.search(
            test['query'], 
            pattern_type=test.get('pattern_type'),
            top_k=3
        )
        
        # Check if expected files are in results
        retrieved_files = [p['metadata']['path'] for p in patterns]
        expected_files = test['expected_files']
        
        hits = len(set(retrieved_files) & set(expected_files))
        recall = hits / len(expected_files) if expected_files else 0
        
        print(f"  Retrieved: {retrieved_files}")
        print(f"  Expected: {expected_files}")
        print(f"  Recall@3: {recall:.1%}")
        
        results.append({
            "query_id": test['id'],
            "recall": recall,
            "retrieved": retrieved_files
        })
    
    # Overall metrics
    avg_recall = sum(r['recall'] for r in results) / len(results)
    print(f"\n{'='*50}")
    print(f"Average Recall@3: {avg_recall:.1%}")
    print(f"Target: 90%")
    print(f"Status: {'✅ PASS' if avg_recall >= 0.90 else '❌ FAIL'}")

if __name__ == "__main__":
    test_retrieval()
```

**Run tests:**
```bash
python scripts/test_retrieval.py
```

**Success Criteria:**
- ✅ Recall@3 ≥ 70% (acceptable for Phase 1)
- ✅ All test queries return relevant results
- ✅ No crashes or errors

---

#### **Task 1.10: Documentation (1.5 hours)**

```markdown
# README.md

# Company Patterns MCP Server

MCP server that provides Claude Code with access to our company's code patterns via semantic search.

## Quick Start

### Prerequisites
- Python 3.9+
- Claude Code CLI
- OpenAI API key

### Installation

1. Clone and setup:
\`\`\`bash
git clone <your-repo>
cd codebase-patterns-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

2. Configure environment:
\`\`\`bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
\`\`\`

3. Add to Claude Code:
\`\`\`bash
claude mcp add-json company-patterns --scope user '{
  "type": "stdio",
  "command": "python",
  "args": ["'$(pwd)'/mcp_server.py"],
  "env": {
    "OPENAI_API_KEY": "your-key",
    "PATTERNS_PATH": "'$(pwd)/patterns'"
  }
}'
\`\`\`

4. Restart Claude Code:
\`\`\`bash
claude restart
\`\`\`

### Usage

In Claude Code:
\`\`\`
> Search for authentication handler patterns
> Show me middleware examples
> List available pattern types
\`\`\`

Claude will automatically use the MCP tools to find relevant code patterns.

## Adding New Patterns

1. Add perfect example code to `patterns/<type>/`
2. Reindex:
\`\`\`bash
python scripts/index_patterns.py
\`\`\`

## Testing

\`\`\`bash
python scripts/test_retrieval.py
\`\`\`

## Phase 1 Status

✅ Basic MCP server
✅ File loading
✅ Embeddings & vector search
✅ Claude Code integration
✅ Basic testing

📊 Metrics:
- Patterns indexed: 8
- Recall@3: 75%
- Integration: Working

## Next Steps (Phase 2)
- Function-level chunking
- Better metadata
- More patterns (20-30)
- Improved retrieval
```

**Success Criteria:**
- ✅ README documents setup
- ✅ Usage examples provided
- ✅ Current status documented

---

### **Weekend 1 Deliverable:**

At end of Weekend 1, you should have:

✅ **Working MCP Server**
- Connects to Claude Code
- 2 tools: search_patterns, list_pattern_types
- Uses real RAG (embeddings + vector DB)

✅ **Basic RAG System**
- Indexes 5-10 golden examples
- Semantic search working
- Recall@3 ≥ 70%

✅ **Claude Code Integration**
- Configuration complete
- Can call MCP tools
- Gets real code patterns

✅ **Foundation for Phase 2**
- Project structure established
- Core components working
- Ready to enhance

**Checkpoint Questions:**
- Can Claude Code connect to your server? ✅
- Does it retrieve your actual golden examples? ✅
- Can you add a new pattern and search for it? ✅

If YES to all three → **Ready for Phase 2!** 🎉

---

## PHASE 2: Enhancement & Scale (Weekend 2 - 12 hours)

**Goal:** Improve quality, add more patterns, better retrieval

### **Saturday Morning: Better Chunking (4 hours)**

#### **Task 2.1: Implement AST-Based Chunking (3 hours)**

Currently indexing entire files. Now chunk at function level:

```python
# src/parser.py
from tree_sitter import Language, Parser
import tree_sitter_go
from typing import List, Dict

class GoParser:
    """Parse Go code using AST"""
    
    def __init__(self):
        self.parser = Parser()
        self.parser.set_language(Language(tree_sitter_go.language()))
    
    def extract_functions(self, code: str, file_path: str) -> List[Dict]:
        """
        Extract individual functions from Go code
        
        Returns list of function chunks with metadata
        """
        tree = self.parser.parse(bytes(code, "utf8"))
        root = tree.root_node
        
        functions = []
        
        # Find all function declarations
        for node in self._traverse(root):
            if node.type in ["function_declaration", "method_declaration"]:
                func_code = code[node.start_byte:node.end_byte]
                func_name = self._get_function_name(node, code)
                docstring = self._get_docstring(node, code)
                
                functions.append({
                    "code": func_code,
                    "name": func_name,
                    "docstring": docstring,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "file_path": file_path,
                    "lines_of_code": node.end_point[0] - node.start_point[0] + 1
                })
        
        return functions
    
    def _traverse(self, node):
        """Recursively traverse AST"""
        yield node
        for child in node.children:
            yield from self._traverse(child)
    
    def _get_function_name(self, func_node, code: str) -> str:
        """Extract function name"""
        for child in func_node.children:
            if child.type == "identifier":
                return code[child.start_byte:child.end_byte]
        return "anonymous"
    
    def _get_docstring(self, func_node, code: str) -> str:
        """Extract comment above function"""
        # Get previous sibling (comment)
        prev_sibling = func_node.prev_sibling
        if prev_sibling and prev_sibling.type == "comment":
            return code[prev_sibling.start_byte:prev_sibling.end_byte]
        return ""

# Test
if __name__ == "__main__":
    parser = GoParser()
    
    with open("patterns/handlers/user_handler.go") as f:
        code = f.read()
    
    functions = parser.extract_functions(code, "patterns/handlers/user_handler.go")
    
    print(f"Found {len(functions)} functions:")
    for func in functions:
        print(f"  - {func['name']} ({func['lines_of_code']} lines)")
```

**Success Criteria:**
- ✅ Extracts individual functions from Go code
- ✅ Captures function name, docstring, location
- ✅ Works on your golden examples

---

#### **Task 2.2: Update Indexer for Chunking (1 hour)**

```python
# src/indexer.py (Updated)
from src.parser import GoParser

class PatternIndexer:
    """Enhanced indexer with function-level chunking"""
    
    def __init__(self, patterns_dir: str):
        self.patterns_dir = Path(patterns_dir)
        self.go_parser = GoParser()
    
    def load_and_chunk(self) -> List[Dict]:
        """Load files and chunk into functions"""
        chunks = []
        
        for pattern_type_dir in self.patterns_dir.iterdir():
            if not pattern_type_dir.is_dir():
                continue
            
            pattern_type = pattern_type_dir.name
            
            for file_path in pattern_type_dir.glob("*.go"):
                code = file_path.read_text()
                
                # Extract functions
                functions = self.go_parser.extract_functions(
                    code, 
                    str(file_path.relative_to(self.patterns_dir))
                )
                
                # Create chunk for each function
                for func in functions:
                    chunks.append({
                        "id": f"{file_path.stem}_{func['name']}",
                        "content": func['code'],
                        "metadata": {
                            "file_path": func['file_path'],
                            "function_name": func['name'],
                            "pattern_type": pattern_type,
                            "language": "go",
                            "has_docstring": bool(func['docstring']),
                            "loc": func['lines_of_code']
                        }
                    })
        
        print(f"Created {len(chunks)} chunks from functions")
        return chunks
```

**Update RAG to use chunks:**
```python
# src/rag.py (Updated index_patterns method)
def index_patterns(self, chunks: List[Dict]):
    """Index function-level chunks"""
    print(f"Indexing {len(chunks)} chunks...")
    
    ids = [chunk['id'] for chunk in chunks]
    documents = [chunk['content'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    
    # Add to collection
    self.collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"✅ Indexed {len(chunks)} function chunks")
```

**Reindex with new chunking:**
```bash
# Delete old index
rm -rf data/chroma_db

# Reindex with function-level chunks
python scripts/index_patterns.py
```

**Success Criteria:**
- ✅ Chunks at function level instead of file level
- ✅ More granular retrieval (specific functions)
- ✅ Metadata includes function names

---

### **Saturday Afternoon: Expand Patterns (4 hours)**

#### **Task 2.3: Add More Golden Examples (2 hours)**

Expand from 5-10 to 20-30 perfect examples:

**Target distribution:**
```
patterns/
├── handlers/ (8-10 files)
│   ├── user_handler.go
│   ├── product_handler.go
│   ├── auth_handler.go
│   ├── order_handler.go
│   ├── payment_handler.go
│   └── ...
├── services/ (6-8 files)
│   ├── user_service.go
│   ├── auth_service.go
│   ├── notification_service.go
│   ├── email_service.go
│   └── ...
├── middleware/ (4-6 files)
│   ├── auth_middleware.go
│   ├── logging_middleware.go
│   ├── rate_limit_middleware.go
│   ├── cors_middleware.go
│   └── ...
└── models/ (4-6 files)
    ├── user.go
    ├── product.go
    ├── order.go
    └── ...
```

**Selection process:**
1. Review your actual codebase
2. Find files you'd give 9-10/10 rating
3. Copy to patterns directory
4. Document why each is perfect

**Success Criteria:**
- ✅ 20-30 golden examples total
- ✅ Balanced across pattern types
- ✅ Each documented in patterns/README.md

---

#### **Task 2.4: Enhanced Metadata (2 hours)**

Add richer metadata for better filtering:

```python
# src/parser.py (Enhanced)
def extract_functions_with_metadata(self, code: str, file_path: str) -> List[Dict]:
    """Extract functions with enhanced metadata"""
    
    functions = []
    
    for node in self._traverse(root):
        if node.type in ["function_declaration", "method_declaration"]:
            # ... existing extraction ...
            
            # ENHANCED: Extract more metadata
            imports = self._extract_imports(root, code)
            complexity = self._calculate_complexity(node)
            has_error_handling = self._has_error_handling(node, code)
            
            functions.append({
                "code": func_code,
                "name": func_name,
                "docstring": docstring,
                # ... existing metadata ...
                
                # NEW: Enhanced metadata
                "imports": imports,
                "complexity": complexity,
                "has_error_handling": has_error_handling,
                "patterns_used": self._detect_patterns(node, code)
            })
    
    return functions

def _extract_imports(self, root, code: str) -> List[str]:
    """Extract import statements"""
    imports = []
    for node in self._traverse(root):
        if node.type == "import_declaration":
            import_text = code[node.start_byte:node.end_byte]
            imports.append(import_text)
    return imports

def _calculate_complexity(self, node) -> int:
    """Calculate cyclomatic complexity"""
    complexity = 1  # base
    for child in self._traverse(node):
        if child.type in ["if_statement", "for_statement", "case_clause"]:
            complexity += 1
    return complexity

def _has_error_handling(self, node, code: str) -> bool:
    """Check if function has error handling"""
    for child in self._traverse(node):
        if child.type == "if_statement":
            if_code = code[child.start_byte:child.end_byte]
            if "err" in if_code and "!=" in if_code:
                return True
    return False
```

**Success Criteria:**
- ✅ Richer metadata extracted
- ✅ Can filter by complexity, error handling, etc.
- ✅ Better search relevance

---

### **Sunday: Advanced Retrieval (4 hours)**

#### **Task 2.5: Implement Hybrid Search (2 hours)**

Combine semantic search with keyword filtering:

```python
# src/rag.py (Enhanced search)
def search_advanced(
    self,
    query: str,
    pattern_type: str = None,
    max_complexity: int = None,
    must_have_error_handling: bool = False,
    top_k: int = 3
) -> List[Dict]:
    """
    Advanced search with multiple filters
    
    Args:
        query: Semantic search query
        pattern_type: Filter by type (handlers, services, etc.)
        max_complexity: Maximum cyclomatic complexity
        must_have_error_handling: Only return functions with error handling
        top_k: Number of results
    """
    
    # Build where clause for filtering
    where = {}
    if pattern_type:
        where["pattern_type"] = pattern_type
    if must_have_error_handling:
        where["has_error_handling"] = True
    
    # Initial semantic search (get more candidates)
    results = self.collection.query(
        query_texts=[query],
        n_results=top_k * 3,  # Get 3x candidates for filtering
        where=where if where else None
    )
    
    # Post-filter by complexity
    filtered_results = []
    for i in range(len(results['ids'][0])):
        metadata = results['metadatas'][0][i]
        
        # Check complexity filter
        if max_complexity and metadata.get('complexity', 999) > max_complexity:
            continue
        
        filtered_results.append({
            "content": results['documents'][0][i],
            "metadata": metadata,
            "score": results['distances'][0][i]
        })
        
        if len(filtered_results) >= top_k:
            break
    
    return filtered_results
```

**Update MCP tool:**
```python
@server.tool()
async def search_patterns_advanced(
    query: str,
    pattern_type: str = None,
    max_complexity: int = 15,
    require_error_handling: bool = False,
    limit: int = 3
) -> list[TextContent]:
    """
    Advanced pattern search with filters
    
    Args:
        query: What to search for
        pattern_type: Filter by type
        max_complexity: Max cyclomatic complexity (default: 15)
        require_error_handling: Only patterns with error handling
        limit: Number of results
    """
    
    results = rag.search_advanced(
        query,
        pattern_type=pattern_type,
        max_complexity=max_complexity,
        must_have_error_handling=require_error_handling,
        top_k=limit
    )
    
    # Format results...
    return formatted_results
```

**Success Criteria:**
- ✅ Hybrid search (semantic + filters)
- ✅ Can filter by complexity
- ✅ Can filter by error handling presence
- ✅ Better quality results

---

#### **Task 2.6: Add Validation Tool (1 hour)**

```python
@server.tool()
async def validate_code(code: str, pattern_type: str) -> list[TextContent]:
    """
    Validate if code matches team patterns
    
    Args:
        code: Code to validate
        pattern_type: Expected pattern type
    
    Returns:
        Validation results with violations
    """
    
    violations = []
    
    # Check for anonymous structs
    if "struct {" in code and "type" not in code[:code.index("struct {")]:
        violations.append({
            "type": "anonymous_struct",
            "severity": "high",
            "message": "Use named struct types instead of anonymous structs"
        })
    
    # Check cyclomatic complexity
    parser = GoParser()
    # ... parse and check complexity ...
    
    # Check for error handling
    if "err :=" in code and "if err !=" not in code:
        violations.append({
            "type": "missing_error_handling",
            "severity": "high",
            "message": "Error variable declared but not checked"
        })
    
    # Format response
    if violations:
        response = f"Found {len(violations)} violations:\n\n"
        for v in violations:
            response += f"❌ [{v['severity'].upper()}] {v['type']}\n"
            response += f"   {v['message']}\n\n"
    else:
        response = "✅ Code matches team patterns! No violations found."
    
    return [TextContent(type="text", text=response)]
```

**Success Criteria:**
- ✅ Validates code against patterns
- ✅ Detects common violations
- ✅ Provides actionable feedback

---

#### **Task 2.7: Update Tests & Documentation (1 hour)**

```python
# Update test_queries.json with more queries
# Test new features
# Update metrics

# scripts/test_retrieval.py (Enhanced)
def test_advanced_retrieval():
    """Test advanced search features"""
    
    # Test complexity filtering
    results = rag.search_advanced(
        "handler function",
        max_complexity=10
    )
    
    for r in results:
        assert r['metadata']['complexity'] <= 10
    
    # Test error handling filter
    results = rag.search_advanced(
        "service method",
        must_have_error_handling=True
    )
    
    for r in results:
        assert r['metadata']['has_error_handling'] == True
    
    print("✅ Advanced search tests passed")
```

**Update README with new features.**

---

### **Weekend 2 Deliverable:**

At end of Weekend 2, you should have:

✅ **Enhanced RAG**
- Function-level chunking
- 20-30 golden examples indexed
- Rich metadata (complexity, error handling, imports)
- Recall@3 ≥ 85%

✅ **Advanced Features**
- Hybrid search (semantic + filters)
- Complexity filtering
- Error handling detection
- Code validation tool

✅ **Better Integration**
- Multiple MCP tools (search_patterns, search_patterns_advanced, validate_code)
- More useful for developers
- Handles real queries better

**Checkpoint Questions:**
- Is Recall@3 ≥ 85%? ✅
- Can you filter by complexity? ✅
- Does validation tool work? ✅

If YES → **Ready for Phase 3!** 🎉

---

## PHASE 3: Quality & Production (Weekend 3 - 8 hours)

**Goal:** Measure quality, compare to baseline, prepare for team

### **Saturday: Measurement (4 hours)**

#### **Task 3.1: Baseline Measurement (2 hours)**

Test Claude Code WITHOUT your MCP server:

```bash
# Disable your MCP server temporarily
claude mcp remove company-patterns

# Test baseline
claude

> Add JWT authentication middleware

# Save the response
# Rate it on:
# - Pattern Conformance: Does it match your style?
# - Correctness: Does it work?
# - Violations: Any anonymous structs, over-engineering?

# Test 10 different queries
# Document all responses
```

```python
# scripts/measure_baseline.py
test_queries = [
    "Add JWT authentication middleware",
    "Create user service with CRUD operations",
    "Add rate limiting middleware",
    "Implement error handling for API",
    # ... 6 more
]

baseline_results = []

for query in test_queries:
    print(f"\nQuery: {query}")
    print("Please:")
    print("1. Run query in Claude Code (MCP disabled)")
    print("2. Save the generated code")
    print("3. Rate:")
    print("   - Pattern conformance (1-5)")
    print("   - Has anonymous structs? (yes/no)")
    print("   - Cyclomatic complexity (count)")
    print("   - Number of violations")
    
    # Record results
    input("Press Enter when done...")
```

**Success Criteria:**
- ✅ Baseline measured for 10 queries
- ✅ Document current performance
- ✅ Have comparison data

---

#### **Task 3.2: With MCP Measurement (2 hours)**

```bash
# Re-enable MCP server
claude mcp add company-patterns ...

# Test same 10 queries
# Compare results
```

```python
# scripts/compare_results.py
import json

def compare_baseline_vs_mcp():
    """Compare baseline vs MCP results"""
    
    with open('data/baseline_results.json') as f:
        baseline = json.load(f)
    
    with open('data/mcp_results.json') as f:
        mcp = json.load(f)
    
    print("Comparison Results:")
    print("="*60)
    
    metrics = {
        'pattern_conformance': [],
        'anonymous_structs': [],
        'violations': []
    }
    
    for i, (b, m) in enumerate(zip(baseline, mcp)):
        print(f"\nQuery {i+1}: {b['query']}")
        print(f"  Baseline conformance: {b['pattern_conformance']}/5")
        print(f"  MCP conformance: {m['pattern_conformance']}/5")
        print(f"  Improvement: {m['pattern_conformance'] - b['pattern_conformance']:+.1f}")
        
        metrics['pattern_conformance'].append(
            (m['pattern_conformance'] - b['pattern_conformance']) / b['pattern_conformance']
        )
    
    # Overall metrics
    avg_improvement = sum(metrics['pattern_conformance']) / len(metrics['pattern_conformance'])
    
    print(f"\n{'='*60}")
    print(f"Overall Pattern Conformance Improvement: {avg_improvement:.1%}")
    print(f"Target: 80%")
    print(f"Status: {'✅ ACHIEVED' if avg_improvement >= 0.80 else '❌ MISSED'}")
```

**Success Criteria:**
- ✅ MCP shows ≥80% improvement in pattern conformance
- ✅ Reduction in violations (anonymous structs, etc.)
- ✅ Generated code matches team patterns

---

### **Sunday: Team Preparation (4 hours)**

#### **Task 3.3: Create Team Setup Guide (2 hours)**

```markdown
# TEAM_SETUP.md

# Setting Up Company Patterns MCP Server

## For Team Members

### Quick Setup (5 minutes)

1. **Install Claude Code** (if not already installed):
\`\`\`bash
npm install -g @anthropic-ai/claude-code
\`\`\`

2. **Configure MCP Server**:
\`\`\`bash
# Copy this command and run it
claude mcp add-json company-patterns --scope user '{
  "type": "stdio",
  "command": "python",
  "args": ["/shared/path/to/mcp_server.py"],
  "env": {
    "OPENAI_API_KEY": "team-api-key",
    "PATTERNS_PATH": "/shared/path/to/patterns"
  }
}'
\`\`\`

3. **Verify Setup**:
\`\`\`bash
claude restart
claude

> /mcp

# Should show:
# • company-patterns: connected ✅
\`\`\`

4. **Test It**:
\`\`\`bash
> Search for authentication patterns
> Add rate limiting middleware

# Claude should use team patterns automatically!
\`\`\`

### What This Does

- Gives Claude access to our 30 perfect code examples
- Claude automatically finds relevant patterns when you ask for code
- Generated code matches our team's style and standards
- Reduces PR review comments

### Common Issues

**"Server failed to connect"**
- Check MCP server is running: `ps aux | grep mcp_server`
- Check logs: `tail -f ~/.claude/logs/mcp.log`

**"No patterns found"**
- Verify patterns directory exists
- Check environment variables in config

**"Rate limit error"**
- OpenAI API key might need more credits
- Contact [team lead] for access

### Getting Help

- Slack: #claude-code-help
- Email: dev-tools@company.com
- Internal wiki: wiki.company.com/claude-mcp
\`\`\`

**Success Criteria:**
- ✅ Clear setup instructions
- ✅ Troubleshooting guide
- ✅ Contact information

---

#### **Task 3.4: Write RFC (2 hours)**

```markdown
# RFC: Pattern-Aware Code Generation with MCP

## Status: Proposed
## Author: [Your Name]
## Date: 2025-11-22

## Problem Statement

Developers using Claude for code generation receive suggestions that don't match our team's coding patterns and standards. This results in:

- **15-20 PR comments** per PR on average for pattern violations
- **2-3 hours per week** per developer fixing generated code
- Inconsistent code style across the codebase
- Specific issues: anonymous structs, over-engineering, duplicate code

**Business Impact:** 
- Team of 10 developers = 20-30 hours/week spent on corrections
- Slower development velocity
- Inconsistent code quality

## Proposed Solution

Build an MCP (Model Context Protocol) server that provides Claude with access to our "golden example" code patterns via semantic search (RAG).

### Architecture

[Include architecture diagram from above]

### How It Works

1. Team maintains 20-30 "perfect" code examples
2. MCP server indexes these with embeddings
3. When developer asks Claude for code, Claude automatically:
   - Queries MCP server for relevant patterns
   - Receives matching examples
   - Generates code following those patterns

No change to developer workflow - happens automatically!

## Results (POC)

Tested with 10 common code generation requests:

| Metric | Baseline | With MCP | Improvement |
|--------|----------|----------|-------------|
| Pattern Conformance | 2.1/5 | 4.5/5 | +114% |
| Anonymous Structs | 80% had them | 5% had them | -94% |
| PR Comments (avg) | 17 | 3 | -82% |

**Expected Impact:**
- Save 15-20 hours/week team-wide
- Faster PR reviews
- More consistent codebase

## Implementation Plan

### Phase 1: Pilot (Weeks 1-2)
- Deploy to 3 developers
- Gather feedback
- Measure PR comment reduction

### Phase 2: Rollout (Weeks 3-4)
- Deploy to full team
- Training session
- Documentation in wiki

### Phase 3: Maintenance (Ongoing)
- Add new patterns as team evolves
- Update based on feedback
- Monitor metrics

## Costs

- **Development:** Already built (POC complete)
- **Infrastructure:** 
  - OpenAI API: ~$50/month (embeddings)
  - Server: Run on existing dev box (no cost)
- **Maintenance:** 2-4 hours/month updating patterns

**ROI:** Save 60-80 hours/month → Pays for itself 100x over

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Developers bypass tool | Make it default, measure adoption |
| Patterns become outdated | Monthly review process |
| API costs increase | Set spending limits, monitor usage |
| Server downtime | Graceful degradation (Claude works without MCP) |

## Success Metrics

- **Primary:** ≥80% reduction in pattern-related PR comments
- **Secondary:** 
  - Developer satisfaction survey ≥4.5/5
  - 90%+ adoption rate
  - <5 minutes setup time per developer

## Decision

**Recommendation:** Approve and proceed with pilot

**Timeline:**
- Week 1: Pilot with 3 developers
- Week 2: Evaluate results
- Week 3-4: Full team rollout if successful

## Appendix

- [Link to technical documentation]
- [Link to setup guide]
- [Link to POC results spreadsheet]
\`\`\`

**Success Criteria:**
- ✅ Complete RFC with all sections
- ✅ Data-driven decision making
- ✅ Clear next steps

---

### **Weekend 3 Deliverable:**

At end of Weekend 3, you should have:

✅ **Measured Results**
- Baseline vs MCP comparison
- 80%+ improvement in pattern conformance
- Quantified PR comment reduction

✅ **Team Readiness**
- Setup guide for team members
- Troubleshooting documentation
- RFC for leadership approval

✅ **Production Ready**
- Stable MCP server
- Proper error handling
- Logging and monitoring

**Final Checkpoint:**
- Did you achieve ≥80% improvement? ✅
- Is team setup documented? ✅
- Is RFC complete? ✅

If YES → **Ready for team deployment!** 🚀

---

## Summary Timeline & Effort

| Phase | Duration | Key Deliverables | Effort |
|-------|----------|------------------|--------|
| **Phase 1** | Weekend 1 | Working MCP server, basic RAG, Claude integration | 12h |
| **Phase 2** | Weekend 2 | Enhanced chunking, 20-30 patterns, advanced search | 12h |
| **Phase 3** | Weekend 3 | Measurements, team docs, RFC | 8h |
| **TOTAL** | | Production-ready MCP server | **32h** |

## Success Criteria Summary

✅ **Technical:**
- MCP server connects to Claude Code
- Recall@3 ≥ 85%
- Pattern conformance improvement ≥ 80%

✅ **Business:**
- PR comments reduced ≥ 80%
- Team can set up in <5 minutes
- ROI positive (saves time)

✅ **Adoption:**
- Setup guide complete
- RFC approved
- 3+ developers in pilot

---

## Next Steps After Phase 3

1. **Week 1-2:** Pilot with 3 developers
2. **Week 3:** Measure results, gather feedback
3. **Week 4:** Full team rollout if successful
4. **Ongoing:** Maintain and improve patterns

---

**You now have a complete, actionable plan!** Ready to start Weekend 1? 🚀