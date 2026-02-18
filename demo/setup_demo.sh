#!/usr/bin/env bash
set -euo pipefail

# Demo Setup Script
# One command to go from clone to working demo:
#   bash demo/setup_demo.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "========================================"
echo "  Codebase Patterns MCP — Demo Setup"
echo "========================================"
echo ""

# Step 1: Copy sample repos to repos/
echo "Step 1: Copying sample repos to repos/..."
mkdir -p repos
for repo_dir in sample-repos/*/; do
    repo_name=$(basename "$repo_dir")
    if [ -d "repos/$repo_name" ]; then
        echo "  Removing existing repos/$repo_name..."
        rm -rf "repos/$repo_name"
    fi
    echo "  Copying $repo_name..."
    cp -r "$repo_dir" "repos/$repo_name"
done
echo "  Done. Repos:"
ls -1 repos/
echo ""

# Step 2: Index repos
echo "Step 2: Indexing repositories..."
python index_repos.py --reset
echo ""

# Step 3: Run evaluation
echo "Step 3: Running search quality evaluation..."
python eval/run_eval.py
echo ""

# Step 4: Run demo
echo "Step 4: Running before/after demo..."
python eval/demo.py
echo ""

echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Results:"
echo "  Eval results: data/eval/results.json"
echo "  Eval report:  data/eval/report.md"
echo "  MCP logs:     data/logs/mcp-requests-*.jsonl"
echo ""
echo "Next steps:"
echo "  1. Review data/eval/report.md for search quality metrics"
echo "  2. Start the MCP server: python -m src.mcp_server"
echo "  3. Run prompts through Claude Code and check tool routing:"
echo "     python -c \"from eval.tool_routing import generate_routing_checklist; print(generate_routing_checklist())\""
