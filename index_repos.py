#!/usr/bin/env python3
"""
Main indexing script - indexes repos, generates embeddings, stores in Chroma.
Run this to build/update the vector database.
"""

import os
import sys
from dotenv import load_dotenv

from src.indexer import CodeIndexer
from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore


def main():
    load_dotenv(override=True)

    repos_path = os.getenv("REPOS_PATH", "./repos")
    chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")

    print("=" * 60)
    print("🚀 Code Indexing Pipeline")
    print("=" * 60)
    print(f"   Repos: {repos_path}")
    print(f"   Vector DB: {chroma_path}")
    print("=" * 60)

    # Step 1: Index all repos (multi-language)
    print("\n[1/3] Indexing repositories...")
    indexer = CodeIndexer(repos_path)
    functions = indexer.index_all_repos()

    if not functions:
        print("❌ No functions found. Exiting.")
        return 1

    # Step 2: Generate embeddings
    print(f"\n[2/3] Generating embeddings...")
    generator = EmbeddingGenerator()

    texts = [f.content for f in functions]
    embeddings = generator.generate_embeddings(texts, batch_size=100)

    failed_count = sum(1 for e in embeddings if e is None)
    if failed_count > 0:
        print(f"⚠️  Warning: {failed_count} embeddings failed")

    # Step 3: Store in vector database (upsert)
    print(f"\n[3/3] Storing in vector database...")
    store = VectorStore(persist_directory=chroma_path)

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("⚠️  Resetting vector store (clearing existing data)...")
        store.reset()

    store.add_functions(functions, embeddings)

    # Show stats
    print("\n" + "=" * 60)
    print("✅ Indexing complete!")
    print("=" * 60)

    stats = store.get_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Total functions: {stats['total_functions']}")

    if stats.get('languages'):
        print(f"\n   By language:")
        for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {lang:15s}: {count:4d} functions")

    if stats.get('repos'):
        print(f"\n   By repo:")
        for repo, count in sorted(stats['repos'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {repo:30s}: {count:4d} functions")

    if stats.get('types'):
        print(f"\n   By type:")
        for code_type, count in sorted(stats['types'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {code_type:15s}: {count:4d} functions")

    if stats.get('patterns'):
        print(f"\n   By pattern:")
        for pattern, count in sorted(stats['patterns'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {pattern:15s}: {count:4d} functions")

    if stats.get('frameworks'):
        print(f"\n   By framework:")
        for fw, count in sorted(stats['frameworks'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {fw:15s}: {count:4d} functions")

    print("\n" + "=" * 60)
    print('🎉 Ready to search! Try: python search_cli.py "JWT authentication"')
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
