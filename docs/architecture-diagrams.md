# Architecture Diagrams: RAG vs MCP

## 1. Traditional RAG Architecture (What We Discussed First)

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR CODEBASE (large codebase)                 │
│              Go, JavaScript, TypeScript, Python, PHP         │
└─────────────────────────────────────────────────────────────┘
                            ↓ (Indexing Phase)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   INDEXING PIPELINE                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Code Loader │→│ AST Parser   │→│ Chunk Generator │   │
│  │ (Python)    │  │ (tree-sitter)│  │ (functions)     │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        OpenAI Embeddings API                        │   │
│  │        (text-embedding-3-small)                     │   │
│  │        Converts code → vectors (1536 dimensions)    │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        Vector Database (Chroma)                     │   │
│  │        Stores: embeddings + metadata + code chunks  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

                    (Query Phase - Runtime)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      DEVELOPER                               │
│   Types: "Add JWT authentication middleware"                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   YOUR RAG APPLICATION                       │
│                     (Python Script)                          │
│                                                              │
│  1. Embed query → [0.234, -0.891, ...]                     │
│  2. Search vector DB → Top 5 similar chunks                 │
│  3. Format context:                                         │
│     "Here are relevant patterns:                            │
│      [auth_middleware.go code]                              │
│      [jwt_validator.go code]                                │
│      Now generate middleware matching these."               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              ANTHROPIC CLAUDE API                            │
│              (You call via HTTP/SDK)                         │
│                                                              │
│  POST https://api.anthropic.com/v1/messages                 │
│  {                                                           │
│    "model": "claude-sonnet-4-20250514",                     │
│    "messages": [{"role": "user", "content": "..."}]         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   CLAUDE RESPONSE                            │
│         Generated code matching your patterns                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      DEVELOPER                               │
│              Reviews and uses generated code                 │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- You build the entire pipeline (Python scripts)
- You manually call Claude API with context
- Developer interacts with YOUR tool (CLI, web UI, etc.)
- This is a "DIY" solution

---

## 2. MCP Architecture (The Better Approach)

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR CODEBASE (large codebase)                 │
│              Go, JavaScript, TypeScript, Python, PHP         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   YOUR MCP SERVER                            │
│                   (Python/Node.js)                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Code Indexer                                      │    │
│  │  - Loads golden examples                           │    │
│  │  - Parses with AST                                 │    │
│  │  - Creates embeddings                              │    │
│  │  - Stores in vector DB (Chroma/Pinecone)          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MCP Tools (Claude can call these)                 │    │
│  │                                                     │    │
│  │  @mcp.tool()                                       │    │
│  │  def search_patterns(query: str, type: str):      │    │
│  │      """Search for code patterns"""                │    │
│  │      # Semantic search                             │    │
│  │      return relevant_patterns                      │    │
│  │                                                     │    │
│  │  @mcp.tool()                                       │    │
│  │  def get_pattern_details(file_path: str):         │    │
│  │      """Get full pattern code"""                   │    │
│  │      return full_code                              │    │
│  │                                                     │    │
│  │  @mcp.tool()                                       │    │
│  │  def validate_against_patterns(code: str):        │    │
│  │      """Check if code matches patterns"""          │    │
│  │      return violations                             │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Listens on: stdio, HTTP, or SSE                           │
└─────────────────────────────────────────────────────────────┘
                            ↕ MCP Protocol (JSON-RPC)
┌─────────────────────────────────────────────────────────────┐
│              CLAUDE (Multiple Access Points)                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Claude.ai    │  │ Claude       │  │ VS Code      │     │
│  │ (Web)        │  │ Desktop App  │  │ (Cline/etc)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  Claude automatically:                                       │
│  1. Discovers available MCP tools                          │
│  2. Decides when to call them                              │
│  3. Formats tool queries                                   │
│  4. Receives tool responses                                │
│  5. Uses context to generate code                          │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      DEVELOPER                               │
│                                                              │
│  Option 1: Claude Desktop App                               │
│  - Configures MCP server in settings                        │
│  - Types: "Add JWT auth middleware"                         │
│  - Claude automatically queries MCP server                   │
│  - Gets patterns, generates matching code                    │
│                                                              │
│  Option 2: VS Code (with Cline extension)                   │
│  - MCP server configured                                     │
│  - Works in editor directly                                  │
│  - Claude has access to patterns automatically               │
│                                                              │
│  Option 3: Custom CLI Tool                                   │
│  - You build wrapper around Claude API                       │
│  - Connects to your MCP server                               │
│  - Team uses via command line                                │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- MCP server runs as separate process
- Claude NATIVELY supports MCP protocol
- Developer uses Claude's official interfaces
- No manual context building needed

---

## 3. Detailed MCP Flow (Step-by-Step)

```
STEP 1: Developer asks question
┌──────────────────────────────────┐
│  Developer (in Claude Desktop):  │
│  "Add rate limiting middleware"  │
└──────────────────────────────────┘
            ↓
            
STEP 2: Claude analyzes request
┌──────────────────────────────────────────────────────┐
│  Claude thinks:                                      │
│  "I need examples of middleware patterns.            │
│   I have access to MCP tool 'search_patterns'."     │
└──────────────────────────────────────────────────────┘
            ↓
            
STEP 3: Claude calls your MCP server
┌──────────────────────────────────────────────────────┐
│  MCP Request (JSON-RPC):                             │
│  {                                                   │
│    "method": "tools/call",                          │
│    "params": {                                      │
│      "name": "search_patterns",                    │
│      "arguments": {                                │
│        "query": "middleware rate limiting",        │
│        "type": "middleware",                       │
│        "limit": 3                                  │
│      }                                             │
│    }                                               │
│  }                                                 │
└──────────────────────────────────────────────────────┘
            ↓
            
STEP 4: Your MCP server processes
┌──────────────────────────────────────────────────────┐
│  Your MCP Server:                                    │
│  1. Embeds query: "middleware rate limiting"        │
│  2. Searches vector DB                              │
│  3. Filters by type="middleware"                    │
│  4. Returns top 3 matches:                          │
│     - auth_middleware.go (score: 0.89)              │
│     - logging_middleware.go (score: 0.85)           │
│     - cors_middleware.go (score: 0.82)              │
└──────────────────────────────────────────────────────┘
            ↓
            
STEP 5: MCP server returns results
┌──────────────────────────────────────────────────────┐
│  MCP Response:                                       │
│  {                                                   │
│    "content": [                                      │
│      {                                               │
│        "type": "text",                               │
│        "text": "[File: auth_middleware.go]\n        │
│                 func AuthMiddleware() gin.Handler { │
│                   return func(c *gin.Context) {     │
│                     // pattern code...               │
│                   }                                  │
│                 }                                    │
│                 \n\n[File: logging_middleware.go]..." │
│      }                                               │
│    ]                                                 │
│  }                                                   │
└──────────────────────────────────────────────────────┘
            ↓
            
STEP 6: Claude uses context to generate
┌──────────────────────────────────────────────────────┐
│  Claude generates:                                   │
│                                                      │
│  func RateLimitMiddleware(limit int) gin.Handler {  │
│    return func(c *gin.Context) {                    │
│      // Matches auth_middleware pattern             │
│      // Same error handling style                   │
│      // Same return pattern                         │
│    }                                                 │
│  }                                                   │
│                                                      │
│  Explanation: "I created rate limiting middleware   │
│  matching your team's patterns from auth and        │
│  logging middlewares."                              │
└──────────────────────────────────────────────────────┘
            ↓
            
STEP 7: Developer sees result
┌──────────────────────────────────────────────────────┐
│  Developer:                                          │
│  ✅ Code matches team patterns                      │
│  ✅ No anonymous structs                            │
│  ✅ Consistent error handling                       │
│  ✅ Simple, not over-engineered                     │
│                                                      │
│  Action: Copy code, commit, PR                      │
│  Result: Fewer PR comments! 🎉                      │
└──────────────────────────────────────────────────────┘
```

---

## 4. How Developers Actually Use This

### **Option A: Claude Desktop App** ⭐ Easiest

```
┌─────────────────────────────────────────────┐
│        Claude Desktop App                   │
│  (Mac/Windows application from Anthropic)   │
│                                             │
│  Settings → Model Context Protocol          │
│  Add Server:                                │
│    Name: "Company Code Patterns"            │
│    Command: python /path/to/mcp_server.py   │
│                                             │
│  [Start Chatting]                           │
│  Developer: "Add auth to API endpoint"      │
│  Claude: [auto-uses your MCP server]        │
└─────────────────────────────────────────────┘
```

**Configuration file** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "code-patterns": {
      "command": "python",
      "args": ["/path/to/your/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "PATTERNS_PATH": "/path/to/golden/examples"
      }
    }
  }
}
```

**Developer workflow:**
1. Opens Claude Desktop
2. Types question normally
3. Claude automatically queries your MCP server
4. Gets generated code matching patterns
5. Copy/paste into their project

**No command line needed!**

---

### **Option B: VS Code with Extensions** ⭐ For IDE users

```
┌─────────────────────────────────────────────┐
│              VS Code                        │
│                                             │
│  Extension: Cline (or similar MCP client)   │
│                                             │
│  Settings:                                  │
│    MCP Servers:                             │
│      - code-patterns: python mcp_server.py  │
│                                             │
│  Usage:                                     │
│  1. Highlight code selection                │
│  2. Cmd+I: Ask Claude                       │
│  3. "Refactor this to match our patterns"   │
│  4. Claude uses MCP, generates code         │
│  5. Code appears inline                     │
└─────────────────────────────────────────────┘
```

**Extensions that support MCP:**
- **Cline** (formerly Claude Dev) - Popular, free
- **Continue** - Open source AI coding assistant
- **Cursor** - Full IDE with MCP support

---

### **Option C: Custom CLI Tool** ⭐ For your specific workflow

```bash
# You build this wrapper
$ codegen "add rate limiting"

# Behind the scenes:
# 1. Connects to your MCP server
# 2. Calls Claude API with MCP context
# 3. Returns generated code

Output:
✅ Retrieved 3 matching patterns
✅ Generated RateLimitMiddleware
✅ Pattern conformance: 95%
✅ Code saved to: middleware/rate_limit.go
```

**Your custom tool** (Python/Go):
```python
# codegen.py
import anthropic

def generate_code(request):
    # Connect to your MCP server
    mcp = connect_to_mcp_server()
    
    # Get patterns
    patterns = mcp.search_patterns(request)
    
    # Call Claude with context
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{
            "role": "user",
            "content": f"Context: {patterns}\n\nTask: {request}"
        }]
    )
    
    return response.content
```

---

### **Option D: Claude API Direct** ⭐ Programmatic

For automation/CI/CD:
```python
# In your build scripts
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    # MCP tools automatically available if configured
    messages=[{"role": "user", "content": "Generate API endpoint"}]
)
```

---

## 5. Claude's Plugin/Integration Ecosystem

### **Does Claude have "plugins"?**

**Not exactly. Here's what Claude offers:**

### **A. Model Context Protocol (MCP)** ⭐ What you're building
- **Purpose:** Connect Claude to external data/tools
- **You build:** MCP servers
- **Claude uses:** Your servers automatically
- **Standardized:** Works across Claude Desktop, API, extensions

### **B. Projects & Artifacts** (claude.ai feature)
- **Purpose:** Reusable context in web interface
- **How:** Upload docs/code to "Project"
- **Limit:** Not programmable, manual upload
- **Use case:** One-time context, not pattern matching

### **C. API Integrations** (via SDKs)
- Python SDK: `pip install anthropic`
- Node.js SDK: `npm install @anthropic-ai/sdk`
- Direct HTTP API calls

### **D. Third-Party Extensions**
- Cline (VS Code)
- Continue (VS Code)
- Cursor (full IDE)
- Browser extensions
- Alfred workflows
- Raycast extensions

---

## 6. Architecture Comparison: RAG vs MCP

| Aspect | RAG (DIY) | MCP (Anthropic Native) |
|--------|-----------|------------------------|
| **Claude Integration** | You manually call API | Claude natively supports |
| **Context Building** | You format prompts | Claude formats automatically |
| **Tool Discovery** | N/A | Claude discovers tools |
| **Developer UX** | Use YOUR tool | Use Claude's tools |
| **Maintenance** | You maintain everything | MCP protocol maintained by Anthropic |
| **Extensibility** | Custom code | Standard protocol |
| **Adoption** | Team learns your tool | Team uses familiar Claude |
| **Setup Complexity** | Medium | Higher initially |
| **Long-term Value** | Limited | High (future-proof) |

---

## 7. What You're Actually Building

### **Your MCP Server** (Python/Node.js)
```
your-mcp-server/
├── server.py              # MCP server main
├── indexer.py            # Index golden examples
├── retrieval.py          # Semantic search
├── patterns/             # Your 20-30 golden files
│   ├── handlers/
│   ├── services/
│   └── middleware/
├── chroma_db/           # Vector database
└── mcp_config.json      # Configuration
```

**Size:** ~500-1000 lines of Python

**What it does:**
1. Indexes your golden examples on startup
2. Exposes MCP tools (search_patterns, etc.)
3. Responds to Claude's queries
4. Returns relevant patterns

---

### **Developer Usage Flow:**

```
Day 1: Setup (One-time)
Developer installs:
  - Claude Desktop App (or VS Code extension)
  - Your MCP server (runs in background)
  - Configuration file pointing to server

Day 2+: Daily Use
Developer:
  1. Opens Claude Desktop
  2. Types: "Add pagination to user API"
  3. Claude automatically:
     - Queries your MCP server
     - Gets pagination patterns
     - Generates matching code
  4. Developer: Copy, paste, commit
  5. PR review: Fewer comments! 🎉
```

**No manual steps beyond typing the request!**

---

## 8. Recommended Architecture for Your Team

```
┌────────────────────────────────────────────────────────┐
│                   CLOUD / CENTRAL SERVER               │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │        Your MCP Server (Always Running)      │    │
│  │                                              │    │
│  │  - Indexes 20-30 golden examples             │    │
│  │  - Provides MCP tools                        │    │
│  │  - Accessible via HTTP/SSE                   │    │
│  │  - Team-wide patterns in one place           │    │
│  └──────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
                        ↕ MCP Protocol
┌────────────────────────────────────────────────────────┐
│                    DEVELOPER MACHINES                   │
│                                                        │
│  Developer 1          Developer 2          Developer 3 │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐ │
│  │ Claude   │        │ Claude   │        │ VS Code  │ │
│  │ Desktop  │        │ Desktop  │        │ + Cline  │ │
│  └──────────┘        └──────────┘        └──────────┘ │
│       ↓                   ↓                   ↓        │
│  Points to central MCP server (shared config)         │
└────────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ One MCP server for entire team
- ✅ Patterns updated centrally
- ✅ Consistent across all developers
- ✅ Easy to maintain

---

## 9. Summary: Where Does Claude Fit?

**Claude is the CONSUMER of your MCP server:**

1. **You build:** MCP server with pattern library
2. **Claude uses:** Your MCP server (via native protocol)
3. **Claude provides:** Code generation using your patterns
4. **Developer uses:** Claude's interface (Desktop/VS Code/API)

**Analogy:**
- Your MCP server = Database of patterns
- Claude = Smart query engine + code generator
- MCP Protocol = SQL (standardized query language)
- Developer = End user of the system

**You're not building a plugin FOR Claude.**
**You're building a knowledge source THAT Claude consumes.**

---

## Next Question to Answer:

Given 25-35 hours commitment, which architecture do you prefer?

**Option A: Start with RAG (8-10 hours)**
- Faster initial result
- Learn basics
- Migrate to MCP later

**Option B: Go directly to MCP (25-35 hours)**
- Proper architecture from start
- Steeper learning curve
- Better long-term solution

What's your preference?