# Quick Setup Guide - Get Running in 30 Minutes

## Step 1: Environment Setup (10 minutes)

### Create Project Directory
```bash
mkdir codebase-rag
cd codebase-rag
```

### Create Python Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Install Dependencies
The starter code automatically creates `requirements.txt` when you run it, or create manually:

```bash
# Save this as requirements.txt
cat > requirements.txt << EOF
llama-index
llama-index-embeddings-openai
llama-index-llms-anthropic
llama-index-vector-stores-chroma
chromadb
tree-sitter
tree-sitter-go
python-dotenv
EOF

# Install
pip install -r requirements.txt
```

### Set API Keys
```bash
# Option 1: Environment variables
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 2: .env file (better)
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EOF
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

---

## Step 2: Prepare Your Go Repos (10 minutes)

### Create Repo Directory
```bash
mkdir go-repos
cd go-repos
```

### Option A: Clone Repos
```bash
# Clone your 5-10 selected repos
git clone <repo1-url>
git clone <repo2-url>
# ... etc
```

### Option B: Copy Existing Repos
```bash
# Copy from your workspace
cp -r ~/projects/auth-service ./
cp -r ~/projects/api-gateway ./
# ... etc
```

### Recommended Structure
```
go-repos/
├── auth-service/
│   ├── main.go
│   ├── auth/
│   │   ├── jwt.go
│   │   └── middleware.go
│   └── ...
├── api-gateway/
│   ├── main.go
│   └── ...
└── database-utils/
    └── ...
```

**Important:** Remove unnecessary files to speed up indexing:
```bash
cd go-repos

# Remove git histories
find . -name ".git" -type d -exec rm -rf {} +

# Remove dependencies
find . -name "vendor" -type d -exec rm -rf {} +
find . -name "node_modules" -type d -exec rm -rf {} +

# Remove test files (optional, but reduces noise)
find . -name "*_test.go" -delete
```

---

## Step 3: First Run (5 minutes)

### Copy Starter Code
Save the "LlamaIndex RAG Implementation" artifact as `rag_system.py` in your project root.

### Directory Structure Should Be:
```
codebase-rag/
├── venv/
├── go-repos/
│   ├── auth-service/
│   ├── api-gateway/
│   └── ...
├── rag_system.py
├── requirements.txt
└── .env
```

### Run It!
```bash
python rag_system.py
```

**What will happen:**
1. Creates `chroma_db/` directory
2. Loads all Go files from `go-repos/`
3. Parses Go code into functions
4. Creates embeddings (takes 1-5 minutes depending on size)
5. Stores in Chroma vector database
6. Opens interactive query prompt

### First Test Query
```
💬 Your question: How do we validate JWT tokens?
```

You should see:
- Claude's answer based on your code
- 5 retrieved source chunks
- File paths and relevance scores

---

## Step 4: Verify It's Working (5 minutes)

### Test Different Query Types

**1. Specific function:**
```
Where is the database connection pool configured?
```

**2. Pattern/practice:**
```
Show me error handling patterns in the API
```

**3. Cross-file question:**
```
How do authentication and authorization work together?
```

### Check Retrieval Quality
Look at the sources. Ask yourself:
- Are the retrieved files actually relevant?
- Is the top source the most relevant?
- Are important files missing?

**If retrieval looks bad:**
- Chunk size might be wrong
- Need better metadata
- Will tune tomorrow (Saturday)

---

## Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'llama_index'"
**Fix:** Make sure venv is activated
```bash
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "tree-sitter not available"
**Fix:** Install tree-sitter separately
```bash
pip install tree-sitter tree-sitter-go
```

**Fallback:** The code will work without tree-sitter, just with simpler chunking.

### Issue: "No documents loaded"
**Fix:** Check your `repos_path` in the config
```python
config = Config(
    repos_path="./go-repos",  # Make sure this path is correct
)
```

### Issue: Indexing takes forever (>10 minutes)
**Fix:** You might have too many files. Check:
```bash
find go-repos -type f | wc -l
```

If >1000 files, start with fewer repos (2-3) for tonight.

### Issue: "Rate limit exceeded" from OpenAI
**Fix:** You're embedding too much too fast. 
```python
# Add to config
chunk_size: int = 1000  # Larger chunks = fewer API calls
```

Or wait a few minutes and try again.

---

## Success Checklist ✓

After setup, you should have:
- [ ] Python environment working
- [ ] API keys configured
- [ ] 5-10 Go repos in `go-repos/` directory
- [ ] `rag_system.py` running without errors
- [ ] Vector index built (`chroma_db/` exists)
- [ ] Able to query and get responses
- [ ] Responses reference your actual code

**Time check:** If you finished in 30 mins, great! If not, no worries - getting it working is what matters.

---

## What's Next?

### Tonight (if you have time):
1. **Create test queries list**
   - 15-20 questions about your codebase
   - Save to `test_queries.json`
   - Manually identify relevant files for each

2. **Try a few queries**
   - Get a feel for retrieval quality
   - Note what works well, what doesn't

### Tomorrow Morning (Saturday):
- Improve chunking based on what you learned
- Add metadata filtering
- Tune retrieval parameters
- Start building evaluation framework

---

## Quick Reference

### Rebuild Index
```python
# In interactive mode, type:
rebuild
```

Or restart with:
```bash
rm -rf chroma_db/
python rag_system.py
```

### Check What's Indexed
```python
from chromadb import PersistentClient

client = PersistentClient(path="./chroma_db")
collection = client.get_collection("codebase")
print(f"Total chunks: {collection.count()}")
```

### Query Programmatically
```python
from rag_system import CodebaseRAG, Config

config = Config(repos_path="./go-repos")
rag = CodebaseRAG(config)
rag.build_index()

result = rag.query("How do we handle errors?")
print(result['answer'])
```

---

## Need Help?

**Debug mode:** Add this at the top of `rag_system.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test without full system:**
```python
# Just test loading
loader = CodebaseLoader(config)
docs = loader.load_documents()
print(f"Loaded {len(docs)} documents")
for doc in docs[:3]:
    print(doc.metadata)
```

---

You're ready! 🚀 Let's build this thing.