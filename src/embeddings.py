"""
Embeddings module - creates vector embeddings using OpenAI API.
"""

import os
from typing import List
from openai import OpenAI
from tqdm import tqdm


class EmbeddingGenerator:
    """Generate embeddings using OpenAI API"""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        """
        Initialize embedding generator

        Args:
            api_key: OpenAI API key (or from env)
            model: Embedding model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def generate_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to embed per API call

        Returns:
            List of embedding vectors (each is list of floats)
        """
        all_embeddings = []

        print(f"\n🔮 Generating embeddings ({len(texts)} texts, batches of {batch_size})...")

        # Process in batches
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
            batch = texts[i:i + batch_size]

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

            except Exception as e:
                print(f"\n❌ Error generating embeddings for batch {i//batch_size}: {e}")
                # Return None for failed embeddings
                all_embeddings.extend([None] * len(batch))

        print(f"✅ Generated {len([e for e in all_embeddings if e is not None])} embeddings")

        return all_embeddings

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        # text-embedding-3-small: 1536 dimensions
        # text-embedding-3-large: 3072 dimensions
        if "small" in self.model:
            return 1536
        elif "large" in self.model:
            return 3072
        else:
            return 1536  # Default


if __name__ == "__main__":
    # Test embeddings
    from dotenv import load_dotenv
    load_dotenv()

    generator = EmbeddingGenerator()

    # Test with sample texts
    texts = [
        "func AuthMiddleware() Handler { return func(w, r) { ... } }",
        "func CreateAccount(req Request) (*Account, error) { ... }",
        "func ValidateToken(token string) bool { ... }"
    ]

    embeddings = generator.generate_embeddings(texts)

    print(f"\n✅ Test successful!")
    print(f"   Embeddings generated: {len(embeddings)}")
    print(f"   Dimensions: {len(embeddings[0]) if embeddings[0] else 'N/A'}")
    print(f"   Sample (first 5 values): {embeddings[0][:5] if embeddings[0] else 'N/A'}")
