"""
Tool routing verification checklist.

Defines prompts that SHOULD and SHOULD NOT trigger search_code calls.
Reads MCP log files and produces a pass/fail markdown checklist.

Usage:
    # After running prompts through Claude Code, check routing:
    python -c "from eval.tool_routing import generate_routing_checklist; print(generate_routing_checklist())"
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# Prompts that SHOULD trigger a search_code call
SHOULD_CALL_PROMPTS = [
    "Add telemetry tracing to this service",
    "How do we handle authentication in our codebase?",
    "Set up an HTTP client with retry logic",
    "Show me our database repository pattern",
    "What error handling pattern does the team use?",
    "Add observability to this endpoint",
    "How should I set up logging?",
    "What's our standard for API error responses?",
]

# Prompts that SHOULD NOT trigger a search_code call
SHOULD_NOT_CALL_PROMPTS = [
    "Fix the typo on line 42",
    "What does this function do?",
    "Rename this variable to camelCase",
    "Add a comment explaining this block",
    "Run the tests",
    "Format this file",
]


def load_log_entries(log_dir: str = "./data/logs") -> List[Dict[str, Any]]:
    """Load all MCP request log entries from the log directory."""
    log_path = Path(log_dir)
    entries = []

    if not log_path.exists():
        return entries

    for log_file in sorted(log_path.glob("mcp-requests-*.jsonl")):
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    return entries


def generate_routing_checklist(log_dir: str = "./data/logs") -> str:
    """Generate a markdown checklist from MCP log entries.

    This is a manual verification workflow:
    1. Run the SHOULD_CALL_PROMPTS through Claude Code with MCP enabled
    2. Run this function to check which ones actually triggered search_code
    3. Review the checklist
    """
    entries = load_log_entries(log_dir)
    search_queries = [
        e.get("query", "").lower()
        for e in entries
        if e.get("tool_name") == "search_code" and e.get("query")
    ]

    lines = [
        "# Tool Routing Verification Checklist\n",
        f"Log entries found: {len(entries)}",
        f"search_code calls: {len(search_queries)}\n",
        "## Should Call search_code\n",
        "These prompts should trigger a search_code tool call:\n",
    ]

    for prompt in SHOULD_CALL_PROMPTS:
        # Fuzzy check: see if any logged query is similar to this prompt
        found = any(
            _fuzzy_match(prompt.lower(), q) for q in search_queries
        )
        status = "[x]" if found else "[ ]"
        lines.append(f"- {status} \"{prompt}\"")

    lines.append("\n## Should NOT Call search_code\n")
    lines.append("These prompts should NOT trigger a search_code call:\n")

    for prompt in SHOULD_NOT_CALL_PROMPTS:
        found = any(
            _fuzzy_match(prompt.lower(), q) for q in search_queries
        )
        status = "[ ]" if found else "[x]"  # Inverted: unchecked means it was called (bad)
        lines.append(f"- {status} \"{prompt}\"")

    lines.append("\n---")
    lines.append("*Run the prompts through Claude Code, then re-run this checklist.*")

    return "\n".join(lines)


def _fuzzy_match(prompt: str, query: str) -> bool:
    """Check if a prompt and a logged query are roughly about the same topic."""
    # Extract key words from each
    prompt_words = set(prompt.split())
    query_words = set(query.split())
    # If more than 40% of prompt words appear in the query, consider it a match
    if not prompt_words:
        return False
    overlap = len(prompt_words & query_words)
    return overlap / len(prompt_words) > 0.4


if __name__ == "__main__":
    print(generate_routing_checklist())
