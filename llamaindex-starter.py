"""
LlamaIndex RAG for Go Codebase - Complete Starter Implementation
Weekend POC - Focus on Go repositories

Setup Instructions:
1. Create virtual environment: python3 -m venv venv
2. Activate: source venv/bin/activate (or venv\Scripts\activate on Windows)
3. Install: pip install -r requirements.txt (see requirements below)
4. Set environment variables:
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
5. Run: python rag_system.py
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

# LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
    Document
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# For Go AST parsing
try:
    from tree_sitter import Language, Parser
    import tree_sitter_go
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    print("Warning: tree-sitter not available. Using simple chunking.")

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """Configuration for RAG system"""
    
    # Paths
    repos_path: str = "./go-repos"  # Where your Go repos are
    persist_dir: str = "./chroma_db"  # Where to store vector DB
    
    # File patterns
    file_extensions: List[str] = None
    exclude_patterns: List[str] = None
    
    # Chunking
    chunk_size: int = 512  # tokens per chunk
    chunk_overlap: int = 50  # overlap between chunks
    
    # Retrieval
    top_k: int = 5  # Number of chunks to retrieve
    similarity_threshold: float = 0.7
    
    # Models
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "claude-sonnet-4-20250514"
    
    def __post_init__(self):
        if self.file_extensions is None:
            self.file_extensions = [".go", ".js", ".ts", ".py", ".php"]
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "vendor/", 
                "node_modules/", 
                ".git/",
                "test/",
                "_test.go"  # Exclude test files
            ]

# ============================================================================
# GO CODE PARSER
# ============================================================================

class GoCodeParser:
    """Parse Go code using tree-sitter for function-level chunking"""
    
    def __init__(self):
        if not HAS_TREE_SITTER:
            raise ImportError(
                "tree-sitter not installed. Run: pip install tree-sitter tree-sitter-go"
            )
        
        self.parser = Parser()
        self.parser.set_language(Language(tree_sitter_go.language()))
    
    def extract_functions(self, code: str, file_path: str) -> List[Dict]:
        """
        Extract function definitions from Go code
        Returns list of {content, metadata} dicts
        """
        tree = self.parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node
        
        chunks = []
        
        # Find package name
        package_name = self._extract_package_name(root_node, code)
        
        # Find all function declarations
        for node in self._traverse_tree(root_node):
            if node.type in ["function_declaration", "method_declaration"]:
                func_text = code[node.start_byte:node.end_byte]
                func_name = self._extract_function_name(node, code)
                
                # Get docstring if exists
                docstring = self._extract_docstring(node, code)
                
                chunks.append({
                    "content": func_text,
                    "metadata": {
                        "file_path": file_path,
                        "language": "go",
                        "package": package_name,
                        "function_name": func_name,
                        "has_docstring": docstring is not None,
                        "docstring": docstring,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                    }
                })
        
        return chunks
    
    def _traverse_tree(self, node):
        """Recursively traverse syntax tree"""
        yield node
        for child in node.children:
            yield from self._traverse_tree(child)
    
    def _extract_package_name(self, root_node, code: str) -> str:
        """Extract package name from Go file"""
        for node in root_node.children:
            if node.type == "package_clause":
                # Get package identifier
                for child in node.children:
                    if child.type == "package_identifier":
                        return code[child.start_byte:child.end_byte]
        return "unknown"
    
    def _extract_function_name(self, func_node, code: str) -> str:
        """Extract function name from function declaration node"""
        for child in func_node.children:
            if child.type == "identifier":
                return code[child.start_byte:child.end_byte]
        return "anonymous"
    
    def _extract_docstring(self, func_node, code: str) -> Optional[str]:
        """Extract docstring/comment above function"""
        # Go uses comments directly above function
        # This is simplified - real implementation would look for comment nodes
        lines = code[:func_node.start_byte].split('\n')
        if len(lines) >= 2 and lines[-2].strip().startswith('//'):
            return lines[-2].strip()
        return None

# ============================================================================
# CODE LOADER WITH METADATA
# ============================================================================

class CodebaseLoader:
    """Load codebase with proper metadata and chunking"""
    
    def __init__(self, config: Config):
        self.config = config
        self.go_parser = GoCodeParser() if HAS_TREE_SITTER else None
    
    def load_documents(self) -> List[Document]:
        """Load all code files with metadata"""
        
        print(f"Loading documents from {self.config.repos_path}...")
        
        # Use LlamaIndex's SimpleDirectoryReader
        reader = SimpleDirectoryReader(
            input_dir=self.config.repos_path,
            required_exts=self.config.file_extensions,
            recursive=True,
            exclude=self.config.exclude_patterns
        )
        
        documents = reader.load_data()
        print(f"Loaded {len(documents)} files")
        
        # Enhance with Go-specific chunking
        if self.go_parser:
            enhanced_docs = self._chunk_go_files(documents)
        else:
            enhanced_docs = documents
        
        # Add repository-level metadata
        for doc in enhanced_docs:
            self._enrich_metadata(doc)
        
        print(f"Created {len(enhanced_docs)} chunks")
        return enhanced_docs
    
    def _chunk_go_files(self, documents: List[Document]) -> List[Document]:
        """Chunk Go files by function"""
        enhanced = []
        
        for doc in documents:
            file_path = doc.metadata.get('file_path', '')
            
            if file_path.endswith('.go'):
                # Parse Go file into functions
                try:
                    chunks = self.go_parser.extract_functions(
                        doc.text, 
                        file_path
                    )
                    
                    # Create Document for each function
                    for chunk in chunks:
                        func_doc = Document(
                            text=chunk['content'],
                            metadata=chunk['metadata']
                        )
                        enhanced.append(func_doc)
                
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
                    # Fall back to original document
                    enhanced.append(doc)
            else:
                # Non-Go files: keep as-is
                enhanced.append(doc)
        
        return enhanced
    
    def _enrich_metadata(self, doc: Document):
        """Add additional metadata to document"""
        file_path = doc.metadata.get('file_path', '')
        
        # Extract repo name from path
        path_parts = Path(file_path).parts
        if len(path_parts) > 0:
            doc.metadata['repo_name'] = path_parts[0]
        
        # Detect language if not set
        if 'language' not in doc.metadata:
            ext = Path(file_path).suffix
            lang_map = {
                '.go': 'go',
                '.js': 'javascript', 
                '.ts': 'typescript',
                '.py': 'python',
                '.php': 'php'
            }
            doc.metadata['language'] = lang_map.get(ext, 'unknown')
        
        # File size
        doc.metadata['content_length'] = len(doc.text)

# ============================================================================
# RAG SYSTEM
# ============================================================================

class CodebaseRAG:
    """Complete RAG system for codebase"""
    
    def __init__(self, config: Config):
        self.config = config
        self.index = None
        self.query_engine = None
        
        # Configure global settings
        Settings.embed_model = OpenAIEmbedding(
            model=config.embedding_model
        )
        Settings.llm = Anthropic(
            model=config.llm_model,
            temperature=0.1
        )
        Settings.chunk_size = config.chunk_size
        Settings.chunk_overlap = config.chunk_overlap
    
    def build_index(self, force_rebuild: bool = False):
        """Build or load vector index"""
        
        # Check if index exists
        if os.path.exists(self.config.persist_dir) and not force_rebuild:
            print(f"Loading existing index from {self.config.persist_dir}...")
            self._load_index()
        else:
            print("Building new index...")
            self._create_index()
        
        # Create query engine
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=self.config.top_k
        )
        
        print("✓ RAG system ready!")
    
    def _create_index(self):
        """Create new index from codebase"""
        
        # Load documents
        loader = CodebaseLoader(self.config)
        documents = loader.load_documents()
        
        # Create Chroma vector store
        chroma_client = chromadb.PersistentClient(
            path=self.config.persist_dir
        )
        chroma_collection = chroma_client.get_or_create_collection("codebase")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        # Build index
        print("Creating embeddings and building index...")
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        print(f"✓ Index created and persisted to {self.config.persist_dir}")
    
    def _load_index(self):
        """Load existing index"""
        chroma_client = chromadb.PersistentClient(
            path=self.config.persist_dir
        )
        chroma_collection = chroma_client.get_or_create_collection("codebase")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store
        )
    
    def query(self, question: str, return_sources: bool = True) -> Dict:
        """
        Query the codebase
        
        Returns:
            {
                'answer': str,
                'sources': List[Dict],  # Retrieved chunks
                'metadata': Dict
            }
        """
        if not self.query_engine:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        print(f"\n🔍 Query: {question}")
        
        # Query
        response = self.query_engine.query(question)
        
        # Extract sources
        sources = []
        if return_sources and hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                sources.append({
                    'content': node.text,
                    'score': node.score,
                    'metadata': node.metadata
                })
        
        result = {
            'answer': str(response),
            'sources': sources,
            'metadata': {
                'num_sources': len(sources),
                'top_score': sources[0]['score'] if sources else None
            }
        }
        
        return result
    
    def retrieve_only(self, query: str, k: int = None) -> List[Dict]:
        """
        Retrieve relevant chunks without LLM generation
        Useful for evaluation
        """
        k = k or self.config.top_k
        
        retriever = self.index.as_retriever(similarity_top_k=k)
        nodes = retriever.retrieve(query)
        
        return [
            {
                'content': node.text,
                'score': node.score,
                'metadata': node.metadata
            }
            for node in nodes
        ]

# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    """Main entry point"""
    
    # Configuration
    config = Config(
        repos_path="./go-repos",  # UPDATE THIS to your repos path
        persist_dir="./chroma_db",
        top_k=5
    )
    
    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        return
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
    
    # Initialize RAG system
    rag = CodebaseRAG(config)
    
    # Build index (set force_rebuild=True to rebuild)
    rag.build_index(force_rebuild=False)
    
    # Interactive query loop
    print("\n" + "="*80)
    print("RAG System Ready! Type 'quit' to exit, 'rebuild' to rebuild index")
    print("="*80 + "\n")
    
    while True:
        question = input("\n💬 Your question: ").strip()
        
        if not question:
            continue
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if question.lower() == 'rebuild':
            print("Rebuilding index...")
            rag.build_index(force_rebuild=True)
            continue
        
        # Query
        result = rag.query(question)
        
        # Display results
        print(f"\n💡 Answer:\n{result['answer']}")
        
        print(f"\n📚 Sources ({len(result['sources'])} retrieved):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n--- Source {i} (score: {source['score']:.3f}) ---")
            print(f"File: {source['metadata'].get('file_path', 'unknown')}")
            if 'function_name' in source['metadata']:
                print(f"Function: {source['metadata']['function_name']}")
            print(f"Preview: {source['content'][:200]}...")

# ============================================================================
# REQUIREMENTS.TXT
# ============================================================================

REQUIREMENTS = """
# Core LlamaIndex
llama-index
llama-index-embeddings-openai
llama-index-llms-anthropic
llama-index-vector-stores-chroma

# Vector DB
chromadb

# Code parsing
tree-sitter
tree-sitter-go

# Utilities
python-dotenv
"""

if __name__ == "__main__":
    # Save requirements.txt
    with open("requirements.txt", "w") as f:
        f.write(REQUIREMENTS.strip())
    print("✓ requirements.txt created")
    
    # Run main
    main()
