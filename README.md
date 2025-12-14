# Codebase Patterns MCP Server

MCP server providing Claude Code with semantic access to your codebase patterns through intelligent code search.

## What is This?

This MCP (Model Context Protocol) server enables Claude Code to semantically search your codebase. Instead of manually finding and passing relevant code examples, Claude can automatically discover existing patterns, conventions, and implementations from your repositories.

## Key Features

- **Semantic Code Search**: Find relevant code by meaning, not just keywords
- **Function-Level Indexing**: Indexes individual functions with metadata (type, purpose, etc.)
- **Fast Vector Search**: Powered by ChromaDB for efficient similarity search
- **OpenAI Embeddings**: Uses `text-embedding-3-small` for high-quality semantic understanding
- **Claude Code Integration**: Seamlessly works with Claude Code via MCP protocol

## Quick Start

```bash
# 1. Clone and setup
git clone <your-repo>
cd codebase-patterns-mcp
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.template .env
# Edit .env and add your OpenAI API key

# 3. Add your repositories
# Place your repos in the ./repos directory

# 4. Index your code
python index_repos.py

# 5. Test the search
python search_cli.py "authentication handler"

# 6. Set up MCP server for Claude Code
cp .mcp.json.template .mcp.json
# Edit .mcp.json with your absolute paths
# Then configure in Claude Code settings
```

## Architecture

```
Your Repos → Indexer (tree-sitter) → Embeddings (OpenAI) → Vector DB (Chroma) → MCP Server → Claude Code
```

## Use Cases

- **Pattern Discovery**: "Show me how we handle authentication"
- **Convention Learning**: Find naming conventions, directory structures
- **Code Reuse**: Discover existing implementations before building new ones
- **Onboarding**: Help new developers learn the codebase quickly

## Requirements

- Python 3.9+
- OpenAI API key
- Go repositories (currently supports Go, extensible to other languages)

## Documentation

- `CONTEXT.md` - Project overview and motivation
- `docs/setup-guide.md` - Detailed setup instructions
- `docs/mcp-server-usage.md` - MCP server configuration
- `docs/phase1-architecture.md` - Technical architecture details

## Project Status

✅ Phase 1: Semantic search with function-level indexing
✅ Phase 2: MCP server implementation
🔄 Phase 3: Testing and refinement

## Cost

Indexing cost depends on codebase size:
- ~2,000 functions: ~$0.04 (using `text-embedding-3-small`)
- Reindexing only needed when code changes significantly


## Contributing

Raise a PR
Please add a doc explaining what you are trying to do.
