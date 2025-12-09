#!/usr/bin/env python3
"""Test embedding format"""

from dotenv import load_dotenv
load_dotenv(override=True)

from src.embeddings import EmbeddingGenerator
from src.indexer import IndexedFunction

# Generate test embeddings
generator = EmbeddingGenerator()

texts = [
    "func TestOne() { }",
    "func TestTwo() { }",
    "func TestThree() { }"
]

print("Generating embeddings...")
embeddings = generator.generate_embeddings(texts)

print(f"\n📊 Embedding Analysis:")
print(f"   Type of embeddings: {type(embeddings)}")
print(f"   Number of embeddings: {len(embeddings)}")
print(f"   Type of first embedding: {type(embeddings[0])}")
print(f"   Length of first embedding: {len(embeddings[0]) if embeddings[0] else 'None'}")
print(f"   Sample: {embeddings[0][:5] if embeddings[0] else 'None'}")

# Now test with vector store
print("\n\nTesting with VectorStore...")
from src.vector_store import VectorStore

functions = [
    IndexedFunction(
        id=f"test-{i}",
        content=texts[i],
        metadata={"repo": "test", "file": "test.go", "function": f"Test{i}"}
    )
    for i in range(len(texts))
]

store = VectorStore(persist_directory="./data/test_chroma")
store.reset()  # Clear any existing data

try:
    store.add_functions(functions, embeddings)
    print("\n✅ SUCCESS! Embeddings added without error")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
