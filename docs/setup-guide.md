# Setup Guide

## Prerequisites

- Python 3.9+
- An [OpenAI API key](https://platform.openai.com/api-keys) (for embeddings)
- Your team's repositories (Go, Java, Python, JavaScript, or TypeScript)

## Step 1: Install

```bash
git clone https://github.com/Manojred22/codebase-patterns-mcp.git
cd codebase-patterns-mcp
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure

```bash
cp .env.template .env
```

Edit `.env` and set your OpenAI API key:

```
OPENAI_API_KEY=sk-...
```

Optional settings (defaults are fine for most cases):

```
CHROMA_PATH=./data/chroma_db    # Where the vector database is stored
REPOS_PATH=./repos              # Where your repositories live
```

## Step 3: Add Your Repositories

Place your team's repositories in the `repos/` directory:

```bash
mkdir -p repos

# Option A: Clone repos
git clone https://github.com/your-org/auth-service repos/auth-service
git clone https://github.com/your-org/api-gateway repos/api-gateway

# Option B: Copy existing repos
cp -r ~/projects/auth-service repos/
cp -r ~/projects/api-gateway repos/
```

The indexer automatically skips test files, vendor directories, node_modules, build artifacts, and generated code.

Supported file types:
- `.go` — Go
- `.java` — Java
- `.py` — Python
- `.js`, `.jsx` — JavaScript
- `.ts`, `.tsx` — TypeScript

## Step 4: Index Your Code

```bash
python index_repos.py
```

First run takes 1-5 minutes depending on codebase size. You'll see:

```
[1/3] Parsing repositories...
  Repo: auth-service — 47 functions
  Repo: api-gateway — 83 functions
[2/3] Generating embeddings...
[3/3] Storing in vector database...
Total functions: 130
```

To re-index from scratch (clears existing data):

```bash
python index_repos.py --reset
```

## Step 5: Test the Search

```bash
python search_cli.py "authentication middleware"
```

You should see relevant functions from your repos with source code, patterns detected, and relevance scores.

## Step 6: Connect to Claude Code

Create `.mcp.json` in your project root (or wherever you use Claude Code):

```json
{
  "mcpServers": {
    "codebase-patterns": {
      "command": "/absolute/path/to/codebase-patterns-mcp/venv/bin/python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/absolute/path/to/codebase-patterns-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

Replace the paths with your actual absolute paths. Then restart Claude Code — it will pick up the MCP server automatically.

## Step 7: Make Claude Search Proactively (Optional)

By default, Claude only calls `search_code` when you explicitly ask about patterns. To make it search automatically before writing code:

```bash
cp CLAUDE.md.template CLAUDE.md
```

Edit `CLAUDE.md` to match your project. This tells Claude to always check the team's codebase library before writing code for common concerns (telemetry, auth, database access, etc.).

## Step 8: Verify It Works

Ask Claude Code something like:

> "Add authentication middleware to this service"

Claude should call `search_code`, find your team's auth patterns, and generate code that uses your internal libraries and conventions.

Check the MCP request log to confirm:

```bash
cat data/logs/mcp-requests-*.jsonl
```

You should see a structured log entry for the `search_code` call.

## Troubleshooting

### "ModuleNotFoundError"

Make sure the virtual environment is activated:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "No results found"

Check that repos are indexed:

```bash
python search_cli.py --stats
```

If count is 0, run `python index_repos.py` again.

### MCP server not connecting in Claude Code

- Verify the paths in `.mcp.json` are absolute paths
- Check that the Python path points to the venv Python, not system Python
- Look at Claude Code's MCP server logs for errors

### FutureWarning from tree-sitter

```
FutureWarning: Language(path, name) is deprecated...
```

This is a harmless warning from the `tree_sitter_languages` package. It doesn't affect functionality.
