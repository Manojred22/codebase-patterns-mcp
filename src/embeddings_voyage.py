"""
Voyage AI embeddings — code-specialized embedding model.

Uses voyage-code-3 which is purpose-built for code search.
"""

import os
from typing import List

import voyageai
from tqdm import tqdm


class VoyageEmbeddingGenerator:
    """Generate embeddings using Voyage AI API.

    Compatible with EmbeddingGenerator interface used by VectorStore.
    Single-text calls (len=1) use input_type="query" for better search quality.
    Batch calls use input_type="document" for indexing.
    """

    def __init__(self, api_key: str = None, model: str = "voyage-code-3"):
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Voyage API key not provided and VOYAGE_API_KEY env var not set")

        self.client = voyageai.Client(api_key=self.api_key)
        self.model = model

    def generate_embeddings(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Uses input_type="query" for single texts (search queries),
        input_type="document" for batches (indexing).
        """
        # Single text = search query
        input_type = "query" if len(texts) == 1 else "document"

        all_embeddings = []

        if len(texts) > 1:
            print(f"\n🔮 Generating Voyage embeddings ({len(texts)} texts, model={self.model})...")

        for i in tqdm(
            range(0, len(texts), batch_size),
            desc="Voyage batches",
            disable=(len(texts) <= batch_size),
        ):
            batch = texts[i:i + batch_size]

            try:
                result = self.client.embed(
                    batch,
                    model=self.model,
                    input_type=input_type,
                )
                all_embeddings.extend(result.embeddings)
            except Exception as e:
                print(f"\n❌ Error generating Voyage embeddings for batch {i // batch_size}: {e}")
                all_embeddings.extend([None] * len(batch))

        if len(texts) > 1:
            print(f"✅ Generated {len([e for e in all_embeddings if e is not None])} embeddings")

        return all_embeddings

    def get_embedding_dimension(self) -> int:
        if self.model == "voyage-code-3":
            return 1024
        return 1024  # Default for voyage models
