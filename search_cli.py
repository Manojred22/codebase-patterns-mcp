#!/usr/bin/env python3
"""
Search CLI - search for code functions using natural language queries.
"""

import sys
import os
from dotenv import load_dotenv

from src.vector_store import VectorStore


def format_result(result: dict, index: int) -> str:
    """Format a search result for display"""
    meta = result['metadata']

    lines = [
        f"\n{'='*70}",
        f"[{index}] {result['id']}",
        f"{'='*70}",
        f"📁 Repo: {meta['repo']}",
        f"📄 File: {meta['file']}:{meta['start_line']}-{meta['end_line']}",
        f"🏷️  Type: {meta['code_type']}",
    ]

    if meta.get('is_method'):
        lines.append(f"🔧 Method: {meta['receiver']}")

    if meta.get('has_docstring'):
        lines.append(f"📝 Has documentation: ✓")

    lines.extend([
        f"📏 Lines: {meta['lines_of_code']}",
        f"\n{'-'*70}",
        f"Code Preview:",
        f"{'-'*70}",
        result['content'][:300] + "..." if len(result['content']) > 300 else result['content'],
        f"{'='*70}",
    ])

    return "\n".join(lines)


def main():
    load_dotenv(override=True)

    if len(sys.argv) < 2:
        print("Usage: python search_cli.py <query> [--limit N] [--type TYPE]")
        print("\nExamples:")
        print("  python search_cli.py \"JWT authentication\"")
        print("  python search_cli.py \"database transaction\" --limit 10")
        print("  python search_cli.py \"error handling\" --type handler")
        return 1

    # Parse arguments
    query = sys.argv[1]
    limit = 5
    filter_type = None

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])

    if "--type" in sys.argv:
        idx = sys.argv.index("--type")
        filter_type = sys.argv[idx + 1]

    # Initialize vector store
    chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")
    store = VectorStore(persist_directory=chroma_path)

    # Check if database has data
    stats = store.get_stats()
    if stats['total_functions'] == 0:
        print("❌ Vector database is empty. Run 'python index_repos.py' first.")
        return 1

    print(f"\n🔍 Searching for: \"{query}\"")
    if filter_type:
        print(f"   Filtering by type: {filter_type}")
    print(f"   Limit: {limit}")
    print(f"   Database: {stats['total_functions']} functions\n")

    # Build filter
    metadata_filter = {"code_type": filter_type} if filter_type else None

    # Search
    results = store.search(query, n_results=limit, filter_metadata=metadata_filter)

    if not results:
        print("❌ No results found.")
        return 0

    print(f"✅ Found {len(results)} results:\n")

    # Display results
    for i, result in enumerate(results, 1):
        print(format_result(result, i))

    print(f"\n💡 Tip: Use --type to filter by code type:")
    print(f"   Available types: {', '.join(stats['types'].keys())}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
