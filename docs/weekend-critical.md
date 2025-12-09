# Weekend Critical Path: RAG for Codebase

**Goal:** Working RAG POC + RFC 
**Scope:** 5-10 representative repos  
**Focus:** Quality & Accuracy over Speed

---

## POC Success Metrics (Define These First!)

### 1. Retrieval Accuracy
**What:** Does the system find the *right* code?

**Metric: Recall@K**
```
Recall@K = (# of relevant docs in top K) / (total # of relevant docs)
```

**How to Measure:**
1. Create 15-20 test queries like:
   - "How do we handle JWT authentication?"
   - "Where is the database connection pool configured?"
   - "Show me error handling patterns for API calls"

2. For EACH query, manually create ground truth:
   ```json
   {
     "query": "How do we validate JWT tokens?",
     "relevant_files": [
       "src/auth/jwt.go",
       "src/middleware/auth.js",
       "src/utils/token-validator.py"
     ]
   }
   ```

3. Run your RAG retrieval, get top K=5 results

4. Calculate:
   ```python
   relevant_found = len(set(retrieved) & set(ground_truth))
   recall = relevant_found / len(ground_truth)
   ```

**Example:**
```
Retrieved: [jwt.go, config.json, auth.js, routes.go, crypto.py]
Ground truth: [jwt.go, auth.js, token-validator.py]
Matched: jwt.go, auth.js
Recall@5 = 2/3 = 66.7%
```

**Target: ≥80% Recall@5** (at least 80% of relevant files in top 5 results)

### 2. Context Relevance
**What:** Is the retrieved code actually useful?

**Metric: Manual Relevance Rating**

**Rating Scale:**
```
5 = Directly answers query, highly relevant
4 = Relevant, provides useful context  
3 = Somewhat relevant, tangentially related
2 = Marginally relevant, minor connection
1 = Not relevant, irrelevant
```

**How to Measure:**
For each query, rate each retrieved chunk:

**Example:**
```
Query: "How do we handle rate limiting?"

Chunk 1: RateLimitMiddleware implementation
Rating: 5/5 (exactly what we need)

Chunk 2: API throttling configuration
Rating: 4/5 (related config, useful)

Chunk 3: API logging function
Rating: 2/5 (API-related but not rate limiting)

Chunk 4: Database connection code
Rating: 1/5 (irrelevant)

Chunk 5: Rate limit error messages
Rating: 4/5 (part of the system)

Mean Relevance = (5+4+2+1+4)/5 = 3.2/5
```

**Process:**
1. Retrieve top 5 chunks for each query
2. Manually rate each 1-5
3. Calculate average across all chunks, all queries
4. **Target: ≥4.0/5.0** average relevance

### 3. End-to-End Quality (The Real Test)
**What:** Does Claude Code give better answers?

**Setup: Create 10 test questions:**
```json
{
  "test_questions": [
    {
      "id": 1,
      "question": "How do we handle authentication in the API?",
      "evaluation_criteria": {
        "accuracy": "Does it reference our actual JWT implementation?",
        "completeness": "Covers validation, middleware, error handling?",
        "specificity": "Uses our actual code, not generic examples?"
      }
    },
    {
      "id": 2,
      "question": "Where is error logging implemented?",
      "evaluation_criteria": {
        "accuracy": "Correct logger package and configuration?",
        "completeness": "Shows log levels, formatting, destinations?",
        "specificity": "Our custom error wrapper functions?"
      }
    }
    // ... 8 more questions
  ]
}
```

**Baseline Test (WITHOUT RAG):**
```
For each question:
1. Ask Claude Code directly (no context from your codebase)
2. Rate the response:
   - Accuracy (1-5): Factually correct for YOUR codebase?
   - Completeness (1-5): Covers all important aspects?
   - Specificity (1-5): References YOUR actual code vs generic?
3. Note time to get useful answer
```

**Example Baseline:**
```
Q: "How do we handle authentication?"
Claude (no context): 
"Typically you'd use JWT tokens, store in Authorization header,
validate signature, check expiration..."

Ratings:
- Accuracy: 3/5 (generic JWT info, might not match our setup)
- Completeness: 2/5 (missing our specific middleware chain)  
- Specificity: 1/5 (no reference to our actual code)
Average: 2.0/5
```

**With RAG Test:**
```
For same questions:
1. Your RAG retrieves relevant code chunks
2. Pass chunks as context to Claude
3. Rate same criteria
```

**Example With RAG:**
```
Q: "How do we handle authentication?"
Your RAG finds:
- src/auth/jwt.go:ValidateToken()
- src/middleware/auth_middleware.js
- config/auth.yaml

Claude (with context):
"Your authentication flow uses JWT validation in jwt.go:ValidateToken(), 
which checks signature and expiration. The auth_middleware.js wraps this,
extracting tokens from Authorization header and setting user context..."

Ratings:
- Accuracy: 5/5 (references our actual implementation)
- Completeness: 4/5 (covers main flow, might miss edge cases)
- Specificity: 5/5 (cites exact files and functions)
Average: 4.7/5
```

**Calculate Improvement:**
```python
baseline_score = 2.0
rag_score = 4.7
improvement = (rag_score - baseline_score) / baseline_score
# = (4.7 - 2.0) / 2.0 = 135% improvement ✓✓
```

**Target: ≥30% improvement** in average score across all questions

### 4. Performance Baseline
- Query latency (acceptable: <3 seconds)
- Index build time (for scaling estimate)

---

## Weekend Timeline (Aggressive but Doable)

### Friday Evening (3-4 hours): Theory + Setup
- **Theory blitz** (see below)
- Choose framework (LangChain vs LlamaIndex)
- Set up environment
- Select 5-10 representative repos
- Create test queries with ground truth

### Saturday (8-10 hours): Build
- Ingest codebase into vector DB
- Implement basic RAG pipeline
- Test retrieval quality
- Iterate on chunking strategy

### Sunday (6-8 hours): Benchmark + RFC
- Run all POC metrics
- Compare with/without RAG
- Document findings
- Write RFC with architecture + scaling plan
- Prepare demo

---

## Critical Theory (Just Enough to Build Smart)

### 1. Embeddings (30 mins)

**What they are:**
Text → Dense vector (array of numbers, typically 384-1536 dimensions)

**Why they work:**
- Semantic meaning encoded in vector space
- Similar meanings = similar vectors (measured by cosine similarity)
- Example: `"login"` and `"authentication"` close in vector space, but far from `"database"`

**Key Insight for Code:**
- Code embeddings capture *semantic* relationships, not just keywords
- Function names, comments, structure all contribute
- `getUserById()` and `fetchUserData()` will be close even with different names

**Models to Use:**
- **`text-embedding-3-small`** (OpenAI) - 1536 dims, great for code
- **`all-MiniLM-L6-v2`** (open source) - 384 dims, free, decent
- **Specialized:** `codebert-base` for code-specific understanding

**Analogy:** Like a GPS coordinate system for meaning - instead of latitude/longitude, you have 1536 dimensions representing semantic concepts.

---

### 2. Vector Databases (20 mins)

**What they do:**
Store embeddings + enable fast similarity search

**Core Concept: Approximate Nearest Neighbor (ANN)**
- Finding exact nearest vectors in high dimensions = slow (brute force)
- ANN algorithms trade small accuracy loss for massive speed gain
- Think: Google Maps doesn't check every possible route, uses heuristics

**Options for POC:**
1. **Chroma** - Easiest, embedded, perfect for POC
2. **Pinecone** - Managed, scales easily, free tier
3. **Weaviate** - Open source, GraphQL, good for hybrid search
4. **FAISS** - Facebook's library, fastest, requires more setup

**Recommendation:** Start with **Chroma** - one API call, works locally, zero config.

**Key Operations:**
```python
# Conceptually:
db.add(chunks)  # Store embeddings
results = db.query(query_text, top_k=5)  # Find similar
```

---

### 3. RAG Architecture (40 mins)

**What is RAG:** Retrieval-Augmented Generation
1. Retrieve relevant context from your knowledge base
2. Augment the LLM prompt with that context
3. Generate response based on augmented context

**Why it works:**
- LLMs have limited context windows
- Can't train LLM on your private codebase (expensive/impractical)
- RAG lets you "teach" LLM your codebase at query time

**Critical Design Decisions:**

#### A. Chunking Strategy (Most Important!)

**Problem:** Can't embed entire files (too big, loses granularity)

**Options:**
1. **Fixed size** (e.g., 500 tokens) - Simple but breaks logical boundaries
2. **AST-based** (functions, classes) - Respects code structure ✓ Best for code
3. **Sliding window** - Overlapping chunks (good for context preservation)

**For Code, Use AST Chunking:**
- Each function = one chunk
- Each class = one chunk (or split if huge)
- Preserves logical boundaries
- Metadata: file path, repo, language, imports

**Implementation:**
```python
from tree_sitter import Parser  # For AST parsing
# Parse code → extract functions/classes → each is a chunk
```

#### B. Metadata Enrichment

**Beyond just code text, store:**
- File path + repo name (for source tracking)
- Language (for syntax-specific handling)
- Imports/dependencies (for relationship understanding)
- File-level docstrings/README context
- Last modified date (for recency)

**Why:** Enables hybrid search and filtering

#### C. Retrieval Strategy

**Basic:** Pure semantic search (query → top K chunks)

**Better (for POC):** Hybrid approach
1. Vector similarity (semantic search)
2. Keyword filtering (language, repo, file path)
3. Reranking (optional but powerful)

**Example Query Flow:**
```
User: "How do we handle errors in API calls?"

1. Embed query → vector
2. Vector search → 20 candidates
3. Filter: language="javascript", path contains "api/"
4. Rerank by relevance → top 5
5. Send to Claude Code with context
```

#### D. Context Window Management

**Problem:** LLMs have token limits (Claude: 200K tokens, but expensive)

**Strategy:**
- Retrieve top K chunks (K=5-10)
- Each chunk: ~200-500 tokens
- Total context budget: ~2000-5000 tokens
- Leave room for conversation history

**Format for Claude:**
```
Here is relevant code from your codebase:

[File: src/auth/jwt.go]
```go
func ValidateToken(token string) (*Claims, error) {
    // ... code ...
}
```

[File: src/api/middleware.js]
```javascript
async function authMiddleware(req, res, next) {
    // ... code ...
}
```

Now answer the question: [User's question]
```

---

### 4. Quick Implementation Path

**Stack Recommendation:**
- **Framework:** LangChain (more flexible) or LlamaIndex (faster setup)
- **Vector DB:** Chroma (for POC)
- **Embeddings:** OpenAI `text-embedding-3-small`
- **LLM:** Claude via API

**Code Outline (LangChain):**

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader

# 1. Load code
loader = DirectoryLoader('./repos/', glob="**/*.{js,go,py}")
docs = loader.load()

# 2. Chunk (use AST splitter for better results)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(docs)

# 3. Create embeddings + store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. Query
def query_codebase(question):
    results = vectorstore.similarity_search(question, k=5)
    context = "\n\n".join([f"[{r.metadata['source']}]\n{r.page_content}" 
                           for r in results])
    
    # 5. Send to Claude
    prompt = f"Context from codebase:\n{context}\n\nQuestion: {question}"
    # Call Claude API...
    return response
```

**Better Chunking (AST-based):**
Use `tree-sitter` to parse code and extract functions:
```python
import tree_sitter_go  # Language-specific
# Parse → extract function definitions → each = chunk
```

---

## Implementation Checklist

### Setup (Friday)
- [ ] Install dependencies (`langchain`, `chromadb`, `openai`, `tree-sitter`)
- [ ] Set up API keys (OpenAI, Anthropic)
- [ ] Clone/access 5-10 representative repos
- [ ] Create `test_queries.json` with 15-20 queries + ground truth

### Build (Saturday)
- [ ] Implement code loader (filter by extension)
- [ ] Implement AST-based chunking for each language
- [ ] Add metadata (file path, repo, language)
- [ ] Build vector index
- [ ] Implement query function
- [ ] Test retrieval quality manually
- [ ] Iterate on chunk size/overlap

### Benchmark (Sunday Morning)
- [ ] Run Recall@K on test queries
- [ ] Calculate relevance scores
- [ ] Baseline: Ask Claude Code 10 questions WITHOUT context
- [ ] With RAG: Same 10 questions WITH context
- [ ] Compare results
- [ ] Measure query latency

### RFC (Sunday Afternoon)
- [ ] Document architecture
- [ ] Document metrics and results
- [ ] Scaling plan for large codebase
- [ ] Cost analysis (embedding API calls, storage)
- [ ] Next iteration improvements

---

## Potential Pitfalls (What to Watch Out For)

### 1. Chunking Too Large/Small
- **Too large:** Dilutes semantic meaning, poor retrieval
- **Too small:** Loses context, fragmented results
- **Sweet spot for code:** Function-level (50-500 lines typically)

### 2. Ignoring Metadata
- Don't just embed raw code
- Include file paths, comments, docstrings in chunk text
- Store repo/language as filterable metadata

### 3. Not Testing Retrieval Quality First
- **Trap:** Building full pipeline then discovering retrieval sucks
- **Fix:** Test retrieval BEFORE integrating with Claude

### 4. Over-Engineering Weekend POC
- Don't build distributed system for 10 repos
- Don't implement graph DB yet
- Don't fine-tune embeddings
- **Just:** Load → Chunk → Embed → Query → Benchmark

---

## What We're Skipping (See Deep Dive Doc)

This weekend path skips:
- How embeddings actually work (transformer architecture)
- Fine-tuning embedding models
- Advanced retrieval (re-ranking, hypothetical document embeddings)
- Graph relationships between code
- Production concerns (monitoring, updates, scaling)
- Cost optimization strategies
- Alternative architectures

You're learning *just enough* to build smart. The Deep Dive doc covers the fundamentals you're trading off for speed.

---

## Monday Deliverable: RFC Outline

```markdown
# RAG-Enhanced Codebase Assistant: POC Results

## Executive Summary
- Problem statement
- Solution approach
- POC results (metrics)
- Recommendation

## Architecture
- System diagram
- Component breakdown
- Technology choices

## POC Results
- Retrieval accuracy (Recall@K)
- Context relevance scores
- Claude Code comparison (with/without RAG)
- Performance metrics

## Scaling Plan (10 → large codebase)
- Infrastructure needs
- Cost estimates
- Timeline
- Risks

## Next Steps
- Iteration 1: Improve chunking
- Iteration 2: Add graph relationships
- Iteration 3: Production hardening
```

---

**Ready to start?** Pick your repos, define your test queries, and let's build!
