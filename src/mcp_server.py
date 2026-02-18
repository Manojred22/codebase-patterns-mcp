#!/usr/bin/env python3
"""
MCP Server for Company Patterns - Semantic Code Search

Implements Model Context Protocol (MCP) over STDIO using JSON-RPC 2.0
Compatible with Python 3.9+ (no MCP SDK required)
"""

import sys
import json
import os
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from .vector_store import VectorStore
from .embeddings import EmbeddingGenerator
from .request_logger import RequestLogger

# Load environment
load_dotenv()


class MCPServer:
    """Lightweight MCP server implementing JSON-RPC protocol."""

    def __init__(self):
        """Initialize MCP server with vector store."""
        chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")
        self.repos_path = os.getenv("REPOS_PATH", "./repos")

        # Create embedding generator for search queries
        embedding_generator = EmbeddingGenerator()

        self.vector_store = VectorStore(
            persist_directory=chroma_path,
            embedding_generator=embedding_generator,
        )

        self.request_logger = RequestLogger()

        self.log("Company Patterns MCP Server initialized")
        self.log(f"Vector DB: {chroma_path}")
        self.log(f"Indexed functions: {self.vector_store.collection.count()}")

    def log(self, message: str):
        """Log to stderr (stdout is for JSON-RPC protocol)."""
        print(f"[MCP Server] {message}", file=sys.stderr, flush=True)

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming JSON-RPC request. Returns None for notifications."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # Notifications have no id — silently acknowledge
        if request_id is None and method != "initialize":
            self.log(f"Notification received: {method} (ignored)")
            return None

        self.log(f"Received request: {method}")

        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_tools_list()
            elif method == "tools/call":
                result = self.handle_tools_call(params)
            elif method == "resources/list":
                result = self.handle_resources_list()
            elif method == "resources/read":
                result = self.handle_resources_read(params)
            else:
                return self.error_response(request_id, -32601, f"Method not found: {method}")

            return self.success_response(request_id, result)

        except Exception as e:
            self.log(f"Error handling {method}: {str(e)}")
            return self.error_response(request_id, -32603, str(e))

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
            },
            "serverInfo": {
                "name": "codebase-patterns-mcp",
                "version": "0.2.0",
            },
        }

    def handle_tools_list(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "search_code",
                    "description": (
                        "Search the team's shared codebase library for reusable implementations and patterns. "
                        "This searches ACROSS MULTIPLE REPOSITORIES (not the current project) using semantic similarity. "
                        "Returns full source code of matching functions with design pattern and framework annotations.\n\n"
                        "WHEN TO USE:\n"
                        "1. BEFORE writing new code for common concerns — authentication, telemetry/observability, "
                        "logging, database access, error handling, API clients, middleware, configuration, caching, "
                        "retry logic, circuit breakers, rate limiting, validation. The team likely has existing "
                        "implementations and preferred libraries. Search first, then generate code that follows "
                        "the team's established patterns.\n"
                        "2. When the user asks conceptual questions like 'how do we handle X', 'show me examples of Y', "
                        "'what patterns do we use for Z'.\n"
                        "3. When you're about to recommend a third-party library — check if the team already has "
                        "an internal wrapper or preferred alternative.\n\n"
                        "WHEN NOT TO USE:\n"
                        "- Finding specific symbols, files, or definitions in the CURRENT project (use Grep/Glob/Read).\n"
                        "- Exact function name lookups like 'findUserById' (use Grep).\n"
                        "- Reading or modifying files in the current working directory."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "A conceptual or natural language query describing what kind of code you're looking for. "
                                    "Good: 'JWT token validation', 'retry logic with exponential backoff', 'REST API error handling', "
                                    "'OpenTelemetry instrumentation', 'HTTP client with retry'. "
                                    "Bad: 'findUserById' (use Grep for exact symbol names)."
                                ),
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5,
                            },
                            "code_type": {
                                "type": "string",
                                "description": "Filter by architectural role of the code",
                                "enum": ["handler", "middleware", "service", "repository", "model", "utility", "client", "other"],
                            },
                            "language": {
                                "type": "string",
                                "description": "Filter by programming language",
                                "enum": ["go", "java", "python", "javascript", "typescript"],
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Filter by design pattern: factory, singleton, builder, strategy, decorator, observer, repository",
                            },
                            "framework": {
                                "type": "string",
                                "description": "Filter by framework: spring_boot, spring_mvc, jpa, flask, django, fastapi, express, react, nextjs, nestjs, angular",
                            },
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "get_stats",
                    "description": (
                        "Get a summary of what's in the team's shared codebase library — "
                        "how many functions are indexed, which repositories, languages, "
                        "design patterns, and frameworks are represented. "
                        "Use this to understand what's available before searching, "
                        "or when the user asks about the team's tech stack or codebase composition."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                },
            ]
        }

    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with timing and structured logging."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        start = time.monotonic()
        error_msg = None
        result_count = None
        try:
            if tool_name == "search_code":
                result = self.tool_search_code(arguments)
                # Parse result_count from search response
                try:
                    text = result["content"][0]["text"]
                    result_count = json.loads(text).get("results_count")
                except (KeyError, IndexError, json.JSONDecodeError):
                    pass
                return result
            elif tool_name == "get_stats":
                return self.tool_get_stats()
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            error_msg = str(e)
            raise
        finally:
            latency_ms = (time.monotonic() - start) * 1000
            self.request_logger.log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                result_count=result_count,
                latency_ms=latency_ms,
                error=error_msg,
            )

    def tool_search_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search code tool implementation with multi-filter support."""
        query = args.get("query")
        limit = args.get("limit", 5)
        code_type = args.get("code_type")
        language = args.get("language")
        pattern = args.get("pattern")
        framework = args.get("framework")

        if not query:
            raise ValueError("query parameter is required")

        # Build composite metadata filter
        filters = []
        if code_type:
            filters.append({"code_type": code_type})
        if language:
            filters.append({"language": language})
        if pattern:
            filters.append({"patterns": {"$contains": pattern}})
        if framework:
            filters.append({"frameworks": {"$contains": framework}})

        filter_metadata = None
        if len(filters) == 1:
            filter_metadata = filters[0]
        elif len(filters) > 1:
            filter_metadata = {"$and": filters}

        results = self.vector_store.search(query, n_results=limit, filter_metadata=filter_metadata)

        formatted_results = []
        for r in results:
            meta = r["metadata"]
            formatted_results.append({
                "id": r["id"],
                "repo": meta.get("repo", ""),
                "file": meta.get("file", ""),
                "function": meta.get("function", ""),
                "language": meta.get("language", ""),
                "start_line": meta.get("start_line", 0),
                "end_line": meta.get("end_line", 0),
                "lines_of_code": meta.get("lines_of_code", 0),
                "code_type": meta.get("code_type", ""),
                "construct_type": meta.get("construct_type", ""),
                "class_name": meta.get("class_name", ""),
                "patterns": meta.get("patterns", ""),
                "frameworks": meta.get("frameworks", ""),
                "has_docstring": meta.get("has_docstring", False),
                "is_method": meta.get("is_method", False),
                "receiver": meta.get("receiver", ""),
                "source_code": r["content"],  # Full source code from documents field
                "relevance_score": 1.0 - r.get("distance", 0.0) if r.get("distance") is not None else None,
            })

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "query": query,
                        "results_count": len(formatted_results),
                        "results": formatted_results,
                    }, indent=2),
                }
            ]
        }

    def tool_get_stats(self) -> Dict[str, Any]:
        """Get codebase statistics with full breakdowns."""
        stats = self.vector_store.get_stats()

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(stats, indent=2),
                }
            ]
        }

    def handle_resources_list(self) -> Dict[str, Any]:
        """List available resources."""
        stats = self.vector_store.get_stats()

        resources = [
            {
                "uri": "codebase://stats",
                "name": "Codebase Statistics",
                "description": f"Statistics about indexed codebase ({stats['total_functions']} functions)",
                "mimeType": "application/json",
            }
        ]

        for repo_name in stats.get("repos", {}).keys():
            resources.append({
                "uri": f"codebase://{repo_name}",
                "name": f"Repository: {repo_name}",
                "description": f"Functions from {repo_name} repository",
                "mimeType": "application/json",
            })

        return {"resources": resources}

    def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource."""
        uri = params.get("uri")

        if uri == "codebase://stats":
            stats = self.vector_store.get_stats()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(stats, indent=2),
                    }
                ]
            }

        if uri and uri.startswith("codebase://"):
            repo_name = uri.replace("codebase://", "")
            stats = self.vector_store.get_stats()

            if repo_name in stats.get("repos", {}):
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps({
                                "repo": repo_name,
                                "function_count": stats["repos"][repo_name],
                                "note": "Use search_code tool to find specific functions",
                            }, indent=2),
                        }
                    ]
                }

        raise ValueError(f"Resource not found: {uri}")

    def success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    def error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }

    def run(self):
        """Main server loop - read from stdin, write to stdout."""
        self.log("Server started, waiting for requests...")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    # Skip sending response for notifications
                    if response is not None:
                        print(json.dumps(response), flush=True)
                except json.JSONDecodeError as e:
                    self.log(f"Invalid JSON: {e}")
                    error = self.error_response(None, -32700, "Parse error")
                    print(json.dumps(error), flush=True)

        except KeyboardInterrupt:
            self.log("Server stopped")
        except Exception as e:
            self.log(f"Fatal error: {e}")
            raise


def main():
    """Entry point."""
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
