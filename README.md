# Codebase Patterns MCP Server

MCP server that gives Claude Code semantic access to your team's codebase patterns — so generated code follows your internal standards from day one.

## The Problem

When you ask Claude to "add telemetry tracing", it generates generic code pointing to `localhost` with no compliance fields. Your team already has an internal telemetry library with specific endpoints, required fields, and conventions. Claude doesn't know about it.

## The Solution

This MCP server indexes your repositories and exposes a `search_code` tool. When Claude needs to write code for common concerns (auth, telemetry, database, HTTP clients), it searches your codebase first and generates code that follows your team's actual patterns.

**Same prompt, completely different output:**

| Without MCP | With MCP |
|-------------|----------|
| `jaeger.New(jaeger.WithEndpoint("localhost:14268"))` | `telemetry.NewTracer(AcmeTracerConfig{TeamLabel: "platform", CostCenter: "CC-1234"})` |
| Generic Jaeger exporter | Team's OTLP exporter to `telemetry.internal.acme.com` |
| No compliance fields | `TeamLabel` + `CostCenter` required for billing |

## Search Quality

Evaluated against 8 ground-truth queries across telemetry, auth, HTTP clients, database repos, and error handling:

| Metric | Score | Target |
|--------|-------|--------|
| Recall@5 | **100%** | 80% |
| Precision@3 | **95.8%** | 80% |
| MRR | **100%** | 85% |
| Recall@3 | **82.7%** | 90% |

Every query finds a relevant result at rank 1. All expected results appear within the top 5.

## Key Features

- **Semantic Code Search** — find code by meaning, not keywords
- **Multi-Language Support** — Go, Java, Python, JavaScript, TypeScript
- **Pattern Detection** — factory, singleton, builder, strategy, decorator, observer, repository
- **Framework Detection** — Spring Boot, Flask, Express, NestJS, Django, FastAPI, and more
- **Function-Level Indexing** — each function indexed with rich metadata
- **Request Logging** — structured JSONL logs for every MCP tool call
- **Eval Framework** — ground truth queries, metrics, and automated reporting

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/Manojred22/codebase-patterns-mcp.git
cd codebase-patterns-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.template .env
# Edit .env and add your OPENAI_API_KEY

# 3. Add your repositories to ./repos/

# 4. Index your code
python index_repos.py

# 5. Test the search
python search_cli.py "authentication handler"

# 6. Configure MCP server for Claude Code
cp .mcp.json.template .mcp.json
# Edit .mcp.json with your absolute paths
```

For detailed step-by-step instructions, see [docs/setup-guide.md](docs/setup-guide.md).

## Try the Demo

Run the full demo with the included sample repos (Acme-branded code across 5 languages):

```bash
bash demo/setup_demo.sh
```

This copies sample repos, indexes them, runs the eval, and shows the before/after demo. You'll see:

1. **Scene 1** — Claude's generic output (Jaeger, localhost, no compliance)
2. **Scene 2** — Live MCP search results with actual source code
3. **Scene 3** — Claude's output using team patterns (internal endpoints, compliance fields)

To run individual steps:

```bash
# Just the eval (after indexing)
python eval/run_eval.py

# Just the demo
python eval/demo.py

# Check tool routing after running prompts through Claude Code
python -c "from eval.tool_routing import generate_routing_checklist; print(generate_routing_checklist())"
```

Results are saved to `data/eval/report.md` and `data/eval/results.json`.

## Architecture

```
Your Repos → Indexer (tree-sitter) → Embeddings (OpenAI) → Vector DB (Chroma) → MCP Server → Claude Code
```

## Make Claude Use Your Patterns Proactively

By default, Claude only searches when you explicitly ask. To make it **automatically check internal code before generating new code**:

1. Copy `CLAUDE.md.template` to your project root as `CLAUDE.md`
2. Customize it with your project-specific rules

This tells Claude to search the team's codebase library before writing code for common concerns — so it uses your internal libraries instead of generic alternatives.

## Measuring Efficiency on Your Own Codebase

Once you're using the MCP server on a real project, here's how to measure whether it's actually helping.

### What Gets Logged

Every `search_code` call is logged to `data/logs/mcp-requests-YYYY-MM-DD.jsonl`. Each entry records:

```json
{
  "timestamp": "2026-02-18T15:01:22Z",
  "tool_name": "search_code",
  "query": "authentication middleware",
  "filters": {"language": "go"},
  "limit": 5,
  "result_count": 5,
  "latency_ms": 142.3,
  "error": null
}
```

This gives you a full audit trail of what Claude searched for and what it found.

### Run the Eval on Your Code

Write your own ground truth queries in `eval/ground_truth.py` — queries that matter for your team, with the function IDs you expect to find. Then run:

```bash
python eval/run_eval.py
```

This produces `data/eval/report.md` with Recall@K, Precision@K, and MRR scores, plus a per-query breakdown showing exactly which results were found and which were missed.

### Check Code Quality

After Claude generates code using MCP results, check if it followed your patterns:

```python
from eval.code_quality import check_code_quality

result = check_code_quality(generated_code, "telemetry")
print(result)
# {'score': 1.0, 'acme_markers_found': ['AcmeTracerConfig', 'TeamLabel'], 'generic_markers_found': [], 'verdict': 'conformant'}
```

Edit the marker lists in `eval/code_quality.py` to match your team's identifiers instead of the Acme defaults.

### Verify Tool Routing

Check whether Claude is calling `search_code` when it should (and not calling it when it shouldn't):

```bash
python -c "from eval.tool_routing import generate_routing_checklist; print(generate_routing_checklist())"
```

This reads the JSONL logs and produces a pass/fail checklist. Edit the prompt lists in `eval/tool_routing.py` to match your team's common tasks.

### What to Track Over Time

| Question | Where to look |
|----------|---------------|
| Is Claude calling search_code? | `data/logs/mcp-requests-*.jsonl` — check `result_count > 0` |
| Are search results relevant? | `python eval/run_eval.py` — Recall@5 and MRR |
| Is generated code using our patterns? | `eval.code_quality.check_code_quality()` — conformance score |
| How fast are searches? | JSONL logs — `latency_ms` field (should be <500ms) |
| What queries are developers asking? | JSONL logs — `query` field, look for gaps in your indexed repos |

### Adding Your Own Ground Truth

Replace the sample queries in `eval/ground_truth.py` with queries relevant to your codebase:

```python
TestQuery(
    id="your-auth",
    query="JWT token validation middleware",
    category="auth",
    expected_ids=[
        "your-repo/src/auth/middleware.go:ValidateJWT",
        "your-repo/src/auth/token.go:ParseToken",
    ],
    expected_id_patterns=[
        r"your-repo.*auth.*:ValidateJWT",
        r"your-repo.*auth.*:ParseToken",
    ],
)
```

Run `python eval/run_eval.py` after indexing to see the actual function IDs, then update `expected_ids` to match.

## Project Structure

```
src/                     # Core server and indexing
  mcp_server.py          # MCP JSON-RPC server (search_code + get_stats tools)
  request_logger.py      # Structured JSONL request logging
  indexer.py             # Multi-language code indexer
  embeddings.py          # OpenAI embedding generator
  vector_store.py        # ChromaDB vector store
  parsers/               # Tree-sitter parsers (Go, Java, Python, JS, TS)
  detectors/             # Pattern and framework detection

eval/                    # Evaluation framework
  ground_truth.py        # 8 test queries with expected results
  search_quality.py      # Recall@K, Precision@K, MRR metrics
  run_eval.py            # Main eval runner
  report.py              # Markdown report generator
  demo.py                # Before/after demo for presentations
  tool_routing.py        # Tool routing verification checklist
  code_quality.py        # Pattern conformance checker

sample-repos/            # Acme-branded sample code (5 languages, 27 files)
demo/setup_demo.sh       # One-command demo setup
```

## Requirements

- Python 3.9+
- OpenAI API key
- Supported languages: Go, Java, Python, JavaScript, TypeScript

## Cost

Indexing cost depends on codebase size:
- ~2,000 functions: ~$0.04 (using `text-embedding-3-small`)
- Reindexing only needed when code changes significantly

## Contributing

Raise a PR with a doc explaining what you're trying to do.
