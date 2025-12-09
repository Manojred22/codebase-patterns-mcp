# MCP Server - Usage Guide

## Overview

The Company Patterns MCP Server provides semantic code search capabilities to Claude Code through the Model Context Protocol (MCP).

**Built with:** Python 3.9+ (no MCP SDK - manual JSON-RPC implementation)

## Features

### Tools
1. **`search_code`** - Semantic code search across indexed codebase
   - Natural language queries ("JWT authentication", "database transactions")
   - Filter by code type (handler, middleware, service, etc.)
   - Returns relevant functions with metadata and code previews

2. **`get_stats`** - Get statistics about indexed codebase
   - Total functions indexed
   - Breakdown by repository
   - Breakdown by code type

### Resources
- **`codebase://stats`** - Codebase statistics (JSON)
- **`codebase://{repo_name}`** - Repository-specific information

## Setup

### 1. Prerequisites
```bash
# Ensure database is indexed
python index_repos.py

# Verify indexed functions
python search_cli.py "test query" --limit 1
```

### 2. Configure Claude Code

Add to your Claude Code MCP settings (`~/.claude/mcp_settings.json` or similar):

```json
{
  "mcpServers": {
    "company-patterns": {
      "command": "/absolute/path/to/your/codebase-patterns-mcp/run_mcp_server.sh",
      "env": {
        "OPENAI_API_KEY": "your-key-here",
        "CHROMA_PATH": "./data/chroma_db",
        "REPOS_PATH": "./repos"
      }
    }
  }
}
```

**Important:** Update the `command` path to your actual project location.

### 3. Test MCP Server

**Manual test (JSON-RPC):**
```bash
# Start server
./run_mcp_server.sh

# In another terminal, send JSON-RPC request
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | ./run_mcp_server.sh
```

**With Claude Code:**
1. Open Claude Code CLI
2. The `company-patterns` MCP server should auto-connect
3. Use natural language: *"Search for JWT authentication code in our repos"*
4. Claude will automatically call `search_code` tool

## Usage Examples

### Example 1: Search for Authentication Code
**User:** *"Show me how we handle JWT authentication in our codebase"*

**Claude will:**
1. Call `search_code` tool with query "JWT authentication"
2. Get top 5 relevant functions
3. Show you the code with file locations

**Expected results:**
- `go-auth/.../middleware.go:Middleware`
- `pf-partner-gateway/.../auth.go:AuthMiddleware`
- Related JWT handler functions

### Example 2: Find Database Transaction Patterns
**User:** *"How do we handle database transactions and error handling?"*

**Claude will:**
1. Search for "database transaction error handling"
2. Return relevant repository functions
3. Explain the patterns found

### Example 3: Filter by Code Type
**User:** *"Show me all HTTP middleware functions"*

**Claude will:**
1. Call `search_code` with `code_type: "middleware"`
2. Return only middleware functions
3. Summarize common patterns

## Tool API Reference

### `search_code`

**Input Schema:**
```typescript
{
  query: string        // Required: search query
  limit?: number       // Optional: max results (default: 5)
  code_type?: string   // Optional: filter by type
}
```

**Code Types:**
- `handler` - HTTP/API handlers
- `middleware` - Request/response middleware
- `service` - Business logic services
- `repository` - Data access layer
- `model` - Data models/entities
- `utility` - Helper/utility functions
- `client` - External API clients
- `other` - Other functions

**Example Response:**
```json
{
  "query": "JWT authentication",
  "results_count": 3,
  "results": [
    {
      "id": "go-auth/internal/api/middleware/authenticate/middleware.go:Middleware",
      "repo": "go-auth",
      "file": "internal/api/middleware/authenticate/middleware.go",
      "function": "Middleware",
      "start_line": 18,
      "end_line": 35,
      "code_type": "middleware",
      "code_preview": "func Middleware(a authenticator) func(next http.Handler) http.Handler {...",
      "relevance_score": 0.92
    }
  ]
}
```

### `get_stats`

**Input:** None

**Example Response:**
```json
{
  "total_functions": 2139,
  "repos": {
    "pf-go-roi": 564,
    "go-auth": 440,
    "pf-partner-gateway": 409,
    ...
  },
  "types": {
    "other": 1250,
    "client": 172,
    "handler": 160,
    ...
  }
}
```

## Architecture

```
┌─────────────┐
│ Claude Code │
└──────┬──────┘
       │ JSON-RPC over STDIO
       │
┌──────▼──────────────┐
│  MCP Server         │
│  (src/mcp_server.py)│
├─────────────────────┤
│ Tools:              │
│ - search_code       │
│ - get_stats         │
├─────────────────────┤
│ Resources:          │
│ - codebase://stats  │
│ - codebase://{repo} │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│  Vector Store       │
│  (Chroma + OpenAI)  │
│  2,139 functions    │
└─────────────────────┘
```

## Debugging

### Check Server Logs
Server logs go to **stderr** (stdout is for JSON-RPC):
```bash
./run_mcp_server.sh 2>&1 | grep "\[MCP Server\]"
```

### Common Issues

**1. "Vector database is empty"**
- Solution: Run `python index_repos.py` first

**2. "Failed to generate query embedding"**
- Check `OPENAI_API_KEY` is set
- Verify key is valid: `echo $OPENAI_API_KEY`

**3. "Module not found: src.mcp_server"**
- Ensure running from project root
- Check virtual environment is activated

**4. "Connection refused" in Claude Code**
- Verify `command` path in MCP settings is absolute
- Check server can start: `./run_mcp_server.sh` (should wait for input)

## Performance

**Typical latencies:**
- Initialize: <100ms
- List tools/resources: <10ms
- Search (query embedding + vector search): ~500ms-1s
- Get stats: <10ms

**Cost:**
- Search query embedding: ~$0.0001 per query (OpenAI text-embedding-3-small)
- No cost for stats or resource access

## Next Steps

1. ✅ **Phase 1 Complete:** Semantic search working
2. ✅ **Phase 2 Complete:** MCP server implemented
3. ⏳ **Phase 3:** Test integration with Claude Code
4. ⏳ **Phase 4:** Monitor search quality and iterate

## Support

**Issues?** Check:
1. Database indexed: `python search_cli.py "test" --limit 1`
2. Server starts: `./run_mcp_server.sh` (should wait)
3. Environment variables set in `.env`
4. MCP settings path is absolute

**Need help?** Review phase1-architecture.md for system design details.
