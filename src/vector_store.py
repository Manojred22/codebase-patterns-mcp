"""
Vector store module - manages Chroma vector database.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from dataclasses import asdict

from .indexer import IndexedFunction
from .embeddings import EmbeddingGenerator


class VectorStore:
    """Manages Chroma vector database for code search"""

    def __init__(self, persist_directory: str = "./data/chroma_db", collection_name: str = "production_code"):
        """
        Initialize vector store

        Args:
            persist_directory: Where to store the database
            collection_name: Name of the collection
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize embedding generator for queries
        self.embedding_generator = EmbeddingGenerator()

        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Production Go code functions"}
        )

        print(f"📦 Vector store initialized: {collection_name}")
        print(f"   Location: {self.persist_directory}")
        print(f"   Existing documents: {self.collection.count()}")

    def add_functions(self, functions: List[IndexedFunction], embeddings: List[List[float]]):
        """
        Add functions with their embeddings to the vector store

        Args:
            functions: List of IndexedFunction objects
            embeddings: Corresponding embedding vectors
        """
        if len(functions) != len(embeddings):
            raise ValueError(f"Mismatch: {len(functions)} functions but {len(embeddings)} embeddings")

        # Filter out any None embeddings (failed API calls)
        valid_items = [(f, e) for f, e in zip(functions, embeddings) if e is not None]

        if not valid_items:
            print("❌ No valid embeddings to add")
            return

        functions_valid, embeddings_valid = zip(*valid_items)

        # Convert tuples to lists explicitly for Chroma compatibility
        functions_valid = list(functions_valid)
        embeddings_valid = list(embeddings_valid)

        print(f"\n💾 Adding {len(functions_valid)} functions to vector store...")

        # Prepare data for Chroma
        ids = [f.id for f in functions_valid]
        documents = [f.content for f in functions_valid]
        metadatas = [f.metadata for f in functions_valid]

        # Ensure all embeddings are lists (convert from any format)
        embeddings_list = [list(e) for e in embeddings_valid]

        # Add to collection in batch
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings_list,
            metadatas=metadatas
        )

        print(f"✅ Added {len(functions_valid)} functions")
        print(f"   Total in store: {self.collection.count()}")

    def search(self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar code functions

        Args:
            query: Search query (natural language or code)
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"code_type": "handler"})

        Returns:
            List of search results with content and metadata
        """
        # Generate query embedding using OpenAI (same model as indexing)
        query_embedding = self.embedding_generator.generate_embeddings([query])[0]

        if query_embedding is None:
            raise ValueError("Failed to generate query embedding")

        # Query the collection with embedding vector
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata if filter_metadata else None
        )

        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })

        return formatted_results

    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        count = self.collection.count()

        # Get all metadata to compute stats
        if count > 0:
            sample = self.collection.get(limit=count)
            metadatas = sample['metadatas']

            repos = {}
            types = {}

            for meta in metadatas:
                repo = meta.get('repo', 'unknown')
                code_type = meta.get('code_type', 'unknown')

                repos[repo] = repos.get(repo, 0) + 1
                types[code_type] = types.get(code_type, 0) + 1

            return {
                "total_functions": count,
                "repos": repos,
                "types": types
            }
        else:
            return {"total_functions": 0, "repos": {}, "types": {}}

    def reset(self):
        """Delete all data in the collection (use with caution!)"""
        print(f"⚠️  Resetting collection...")
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"description": "Production Go code functions"}
        )
        print("✅ Collection reset")


if __name__ == "__main__":
    # Test vector store
    from dotenv import load_dotenv
    load_dotenv()

    store = VectorStore()
    stats = store.get_stats()

    print(f"\n📊 Vector Store Stats:")
    print(f"   Total functions: {stats['total_functions']}")

    if stats['repos']:
        print(f"\n   By repo:")
        for repo, count in sorted(stats['repos'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {repo:30s}: {count:4d}")

    if stats['types']:
        print(f"\n   By type:")
        for code_type, count in sorted(stats['types'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {code_type:15s}: {count:4d}")
