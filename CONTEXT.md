# Company Patterns MCP Server - Project Context

## What We're Building
MCP server providing Claude Code with **codebase awareness** via semantic search (RAG).

## The Real Problem
**Claude lacks context about existing codebase:**
- ❌ Invents new solutions instead of reusing existing components
- ❌ Doesn't know what already exists in large codebases
- ❌ Developer spends time on "context archaeology" - manually finding and passing relevant files
- ❌ If relevant files are missed → Claude hallucinates/invents
- ❌ Wasting tokens passing large contexts repeatedly
- ❌ Hard to know: "Does this exist? Should this be in a library?"

**Result:** Developer cognitive load on context retrieval, not code review

## Solution: Codebase Awareness via MCP
MCP server with semantic code search:
- Indexes existing codebase (functions, not just files)
- **"Does this already exist?"** - search before generating
- **"What's relevant here?"** - auto-discover related code
- **"Should this be a library?"** - detect duplication across repos
- Claude queries MCP automatically → gets YOUR code as context → reuses instead of inventing

## MVP Scope
**Sample repos** (good examples to index - NOT including example-api-project)
- `example-api-project` = **bad example** (showing problem, not indexed)
- Other repos = good repos following standard patterns (to be indexed)
- Start small, validate approach
- Local vector DB (Chroma)
- Periodic indexing (after major changes)
- Budget: Minimal for embeddings (OpenAI API usage)

## Stack
- **Indexing**: Python + tree-sitter (Go parser) + OpenAI embeddings
- **Storage**: Chroma (local, persistent)
- **MCP Server**: Python + MCP SDK (STDIO transport)
- **Client**: Claude Code CLI

## Implementation Status
- Planning: Complete ✅
- Phase 1 (Semantic Search): Complete ✅
- Phase 2 (MCP Server): Complete ✅
- Phase 3 (Integration Testing): Ready to start

## Current Status
Ready for integration and testing with your own repositories

## Problem Example
**See:** `docs/concrete-problem-examples.md`

The `example/example-api-project` repo demonstrates the problem:
- ❌ **Bad example** - built with Claude WITHOUT codebase context
- **Multiple review iteration cycles** due to missing context
- **Significant dead code** generated and deleted
- Wrong naming conventions
- Reinvented existing patterns
- Didn't follow established guidelines
- Used inconsistent test patterns
- **Significant time wasted on rework**

**With MCP:** Claude would search existing repos, find patterns, and follow them from the start.

**Note:** `example-api-project` will NOT be indexed - it's the "before" example showing what goes wrong.

## Success Metrics
- **Search Quality**: Recall@5 ≥ 90% ("finds what I'd manually look for")
- **Time Saved**: Reduce manual context passing by 50%+
- **Reuse Rate**: Claude reuses existing code 70%+ of the time
- **Latency**: Search results < 5 seconds
- **Rework Reduction**: Fewer review cycles needed

## Repository Structure
```
codebase-patterns-mcp/
├── example/
│   └── example-api-project/   # ❌ Bad example (NOT indexed)
│
└── repos/                     # ✅ Your repos to index
    ├── your-repo-1/           # Add your repositories here
    ├── your-repo-2/
    └── ...
```

## Key Commands
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (copy template and edit)
cp .env.template .env
# Edit .env with your OpenAI API key

# Index your repos
python index_repos.py

# Test search (CLI)
python search_cli.py "your search query"

# Run MCP server
./run_mcp_server.sh

# Connect to Claude Code
# Copy .mcp.json.template to .mcp.json and configure paths
```

## Getting Started

1. Clone the repository
2. Set up Python environment (see Key Commands above)
3. Configure your OpenAI API key in `.env`
4. Add your repositories to the `repos/` directory
5. Run indexing: `python index_repos.py`
6. Test search: `python search_cli.py "your query"`
7. Configure and run MCP server for Claude Code integration

**See documentation in `docs/` for detailed guides**
