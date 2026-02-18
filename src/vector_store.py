"""
Vector store module - manages Chroma vector database.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

from .models import IndexedFunction


class VectorStore:
    """Manages Chroma vector database for code search."""

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "production_code",
        embedding_generator=None,
    ):
        """
        Initialize vector store.

        Args:
            persist_directory: Where to store the database.
            collection_name: Name of the collection.
            embedding_generator: Optional EmbeddingGenerator instance (required for search).
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.embedding_generator = embedding_generator

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Production code functions"},
        )

        print(f"📦 Vector store initialized: {collection_name}")
        print(f"   Location: {self.persist_directory}")
        print(f"   Existing documents: {self.collection.count()}")

    def add_functions(self, functions: List[IndexedFunction], embeddings: List[List[float]]):
        """Add functions with their embeddings to the vector store (upsert)."""
        if len(functions) != len(embeddings):
            raise ValueError(f"Mismatch: {len(functions)} functions but {len(embeddings)} embeddings")

        valid_items = [(f, e) for f, e in zip(functions, embeddings) if e is not None]
        if not valid_items:
            print("❌ No valid embeddings to add")
            return

        functions_valid, embeddings_valid = zip(*valid_items)
        functions_valid = list(functions_valid)
        embeddings_valid = list(embeddings_valid)

        print(f"\n💾 Upserting {len(functions_valid)} functions to vector store...")

        ids = [f.id for f in functions_valid]
        documents = [f.full_code for f in functions_valid]
        metadatas = [f.metadata for f in functions_valid]
        embeddings_list = [list(e) for e in embeddings_valid]

        # Upsert in batches (Chroma limit)
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=ids[i:end],
                documents=documents[i:end],
                embeddings=embeddings_list[i:end],
                metadatas=metadatas[i:end],
            )

        print(f"✅ Upserted {len(functions_valid)} functions")
        print(f"   Total in store: {self.collection.count()}")

    def search(self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar code functions.

        Requires embedding_generator to be set.
        """
        if self.embedding_generator is None:
            raise RuntimeError("Cannot search: no embedding_generator provided to VectorStore")

        query_embedding = self.embedding_generator.generate_embeddings([query])[0]
        if query_embedding is None:
            raise ValueError("Failed to generate query embedding")

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata if filter_metadata else None,
        )

        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None,
                })

        return formatted_results

    def get_stats(self) -> Dict:
        """Get statistics about the vector store (metadata only, no doc loading)."""
        count = self.collection.count()

        if count == 0:
            return {"total_functions": 0, "repos": {}, "types": {}, "languages": {}, "patterns": {}, "frameworks": {}}

        sample = self.collection.get(limit=count, include=["metadatas"])
        metadatas = sample["metadatas"]

        repos: Dict[str, int] = {}
        types: Dict[str, int] = {}
        languages: Dict[str, int] = {}
        patterns: Dict[str, int] = {}
        frameworks: Dict[str, int] = {}

        for meta in metadatas:
            repo = meta.get("repo", "unknown")
            repos[repo] = repos.get(repo, 0) + 1

            code_type = meta.get("code_type", "unknown")
            types[code_type] = types.get(code_type, 0) + 1

            lang = meta.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1

            for p in meta.get("patterns", "").split(","):
                p = p.strip()
                if p:
                    patterns[p] = patterns.get(p, 0) + 1

            for f in meta.get("frameworks", "").split(","):
                f = f.strip()
                if f:
                    frameworks[f] = frameworks.get(f, 0) + 1

        return {
            "total_functions": count,
            "repos": repos,
            "types": types,
            "languages": languages,
            "patterns": patterns,
            "frameworks": frameworks,
        }

    def reset(self):
        """Delete all data in the collection."""
        print("⚠️  Resetting collection...")
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"description": "Production code functions"},
        )
        print("✅ Collection reset")
