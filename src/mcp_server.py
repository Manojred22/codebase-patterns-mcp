#!/usr/bin/env python3
"""
MCP Server for Company Patterns - Semantic Code Search

Implements Model Context Protocol (MCP) over STDIO using JSON-RPC 2.0
Compatible with Python 3.9+ (no MCP SDK required)
"""

import sys
import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from .vector_store import VectorStore
from .indexer import CodeIndexer

# Load environment
load_dotenv()


class MCPServer:
    """Lightweight MCP server implementing JSON-RPC protocol"""

    def __init__(self):
        """Initialize MCP server with vector store"""
        chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")
        repos_path = os.getenv("REPOS_PATH", "./repos")

        self.vector_store = VectorStore(persist_directory=chroma_path)
        self.repos_path = repos_path

        # Log to stderr (stdout is for JSON-RPC)
        self.log("Company Patterns MCP Server initialized")
        self.log(f"Vector DB: {chroma_path}")
        self.log(f"Indexed functions: {self.vector_store.collection.count()}")

    def log(self, message: str):
        """Log to stderr (stdout is for JSON-RPC protocol)"""
        print(f"[MCP Server] {message}", file=sys.stderr, flush=True)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

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
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "codebase-patterns-mcp",
                "version": "0.1.0"
            }
        }

    def handle_tools_list(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": "search_code",
                    "description": "Search for code functions using semantic search. Returns relevant functions from the indexed codebase.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language or code search query (e.g., 'JWT authentication', 'database transaction handling')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5
                            },
                            "code_type": {
                                "type": "string",
                                "description": "Filter by code type: handler, middleware, service, repository, model, utility, client, other",
                                "enum": ["handler", "middleware", "service", "repository", "model", "utility", "client", "other"]
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_stats",
                    "description": "Get statistics about the indexed codebase (total functions, repositories, code types)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }

    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "search_code":
            return self.tool_search_code(arguments)
        elif tool_name == "get_stats":
            return self.tool_get_stats()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def tool_search_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search code tool implementation"""
        query = args.get("query")
        limit = args.get("limit", 5)
        code_type = args.get("code_type")

        if not query:
            raise ValueError("query parameter is required")

        # Build metadata filter
        filter_metadata = {"code_type": code_type} if code_type else None

        # Search
        results = self.vector_store.search(query, n_results=limit, filter_metadata=filter_metadata)

        # Format for MCP
        formatted_results = []
        for r in results:
            meta = r["metadata"]
            formatted_results.append({
                "id": r["id"],
                "repo": meta["repo"],
                "file": meta["file"],
                "function": meta["function"],
                "start_line": meta["start_line"],
                "end_line": meta["end_line"],
                "lines_of_code": meta["lines_of_code"],
                "code_type": meta["code_type"],
                "has_docstring": meta["has_docstring"],
                "is_method": meta["is_method"],
                "receiver": meta.get("receiver", ""),
                "code_preview": r["content"][:500],  # First 500 chars
                "relevance_score": 1.0 - r.get("distance", 0.0) if r.get("distance") else None
            })

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "query": query,
                        "results_count": len(formatted_results),
                        "results": formatted_results
                    }, indent=2)
                }
            ]
        }

    def tool_get_stats(self) -> Dict[str, Any]:
        """Get codebase statistics"""
        stats = self.vector_store.get_stats()

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(stats, indent=2)
                }
            ]
        }

    def handle_resources_list(self) -> Dict[str, Any]:
        """List available resources"""
        stats = self.vector_store.get_stats()

        resources = [
            {
                "uri": "codebase://stats",
                "name": "Codebase Statistics",
                "description": f"Statistics about indexed codebase ({stats['total_functions']} functions)",
                "mimeType": "application/json"
            }
        ]

        # Add resource for each repository
        for repo_name in stats.get("repos", {}).keys():
            resources.append({
                "uri": f"codebase://{repo_name}",
                "name": f"Repository: {repo_name}",
                "description": f"Functions from {repo_name} repository",
                "mimeType": "application/json"
            })

        return {"resources": resources}

    def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource"""
        uri = params.get("uri")

        if uri == "codebase://stats":
            stats = self.vector_store.get_stats()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(stats, indent=2)
                    }
                ]
            }

        # Handle repo-specific resources
        if uri.startswith("codebase://"):
            repo_name = uri.replace("codebase://", "")
            # Get all functions from this repo
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
                                "note": "Use search_code tool to find specific functions"
                            }, indent=2)
                        }
                    ]
                }

        raise ValueError(f"Resource not found: {uri}")

    def success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """Create success response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    def run(self):
        """Main server loop - read from stdin, write to stdout"""
        self.log("Server started, waiting for requests...")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
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
    """Entry point"""
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
