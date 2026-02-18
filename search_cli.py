#!/usr/bin/env python3
"""
Search CLI - search for code functions using natural language queries.
Supports filtering by language, pattern, framework, and code type.
"""

import sys
import os
from dotenv import load_dotenv

from src.vector_store import VectorStore
from src.embeddings import EmbeddingGenerator


def format_result(result: dict, index: int) -> str:
    """Format a search result for display."""
    meta = result['metadata']

    lines = [
        f"\n{'='*70}",
        f"[{index}] {result['id']}",
        f"{'='*70}",
        f"📁 Repo: {meta.get('repo', '')}",
        f"📄 File: {meta.get('file', '')}:{meta.get('start_line', '')}-{meta.get('end_line', '')}",
        f"🌐 Language: {meta.get('language', '')}",
        f"🏷️  Type: {meta.get('code_type', '')}",
    ]

    if meta.get('class_name'):
        lines.append(f"📦 Class: {meta['class_name']}")

    if meta.get('is_method'):
        receiver = meta.get('receiver', '')
        if receiver:
            lines.append(f"🔧 Method receiver: {receiver}")

    if meta.get('has_docstring'):
        lines.append("📝 Has documentation: ✓")

    if meta.get('patterns'):
        lines.append(f"🧩 Patterns: {meta['patterns']}")

    if meta.get('frameworks'):
        lines.append(f"⚡ Frameworks: {meta['frameworks']}")

    lines.extend([
        f"📏 Lines: {meta.get('lines_of_code', '')}",
        f"\n{'-'*70}",
        "Source Code:",
        f"{'-'*70}",
        result['content'],
        f"{'='*70}",
    ])

    return "\n".join(lines)


def main():
    load_dotenv(override=True)

    if len(sys.argv) < 2:
        print("Usage: python search_cli.py <query> [options]")
        print("\nOptions:")
        print("  --limit N          Maximum results (default: 5)")
        print("  --type TYPE        Filter by code type (handler, service, ...)")
        print("  --language LANG    Filter by language (go, java, python, javascript)")
        print("  --pattern PAT      Filter by design pattern (factory, singleton, ...)")
        print("  --framework FW     Filter by framework (spring_boot, flask, react, ...)")
        print("\nExamples:")
        print('  python search_cli.py "JWT authentication"')
        print('  python search_cli.py "database transaction" --language java')
        print('  python search_cli.py "API endpoint" --framework spring_boot')
        print('  python search_cli.py "create user" --pattern factory')
        return 1

    # Parse arguments
    query = sys.argv[1]
    limit = 5
    filter_type = None
    language = None
    pattern = None
    framework = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif args[i] == "--type" and i + 1 < len(args):
            filter_type = args[i + 1]
            i += 2
        elif args[i] == "--language" and i + 1 < len(args):
            language = args[i + 1]
            i += 2
        elif args[i] == "--pattern" and i + 1 < len(args):
            pattern = args[i + 1]
            i += 2
        elif args[i] == "--framework" and i + 1 < len(args):
            framework = args[i + 1]
            i += 2
        else:
            i += 1

    # Initialize vector store with embedding generator for search
    chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")
    embedding_gen = EmbeddingGenerator()
    store = VectorStore(persist_directory=chroma_path, embedding_generator=embedding_gen)

    # Check if database has data
    stats = store.get_stats()
    if stats['total_functions'] == 0:
        print("❌ Vector database is empty. Run 'python index_repos.py' first.")
        return 1

    print(f"\n🔍 Searching for: \"{query}\"")
    if filter_type:
        print(f"   Type: {filter_type}")
    if language:
        print(f"   Language: {language}")
    if pattern:
        print(f"   Pattern: {pattern}")
    if framework:
        print(f"   Framework: {framework}")
    print(f"   Limit: {limit}")
    print(f"   Database: {stats['total_functions']} functions\n")

    # Build composite filter
    filters = []
    if filter_type:
        filters.append({"code_type": filter_type})
    if language:
        filters.append({"language": language})
    if pattern:
        filters.append({"patterns": {"$contains": pattern}})
    if framework:
        filters.append({"frameworks": {"$contains": framework}})

    metadata_filter = None
    if len(filters) == 1:
        metadata_filter = filters[0]
    elif len(filters) > 1:
        metadata_filter = {"$and": filters}

    # Search
    results = store.search(query, n_results=limit, filter_metadata=metadata_filter)

    if not results:
        print("❌ No results found.")
        return 0

    print(f"✅ Found {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(format_result(result, i))

    print(f"\n💡 Tip: Use --language, --pattern, --framework to filter results")
    if stats.get('languages'):
        print(f"   Languages: {', '.join(stats['languages'].keys())}")
    if stats.get('types'):
        print(f"   Types: {', '.join(stats['types'].keys())}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
