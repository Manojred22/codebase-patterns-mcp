#!/usr/bin/env python3
"""
Simple MCP server test - Direct import testing
"""

import sys
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.mcp_server import MCPServer

def test_server():
    """Test MCP server directly"""
    print("🧪 Testing MCP Server\n" + "="*60)

    # Initialize server
    print("\n[1] Initializing server...")
    server = MCPServer()
    print("✅ Server initialized")

    # Test 1: Initialize request
    print("\n[2] Testing initialize...")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    response = server.handle_request(request)
    assert response["result"]["serverInfo"]["name"] == "codebase-patterns-mcp"
    print(f"✅ Initialize: {response['result']['serverInfo']['name']} v{response['result']['serverInfo']['version']}")

    # Test 2: List tools
    print("\n[3] Testing tools/list...")
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    response = server.handle_request(request)
    tools = response["result"]["tools"]
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")

    # Test 3: Get stats
    print("\n[4] Testing get_stats tool...")
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_stats",
            "arguments": {}
        }
    }
    response = server.handle_request(request)
    stats_text = response["result"]["content"][0]["text"]
    stats = json.loads(stats_text)
    print(f"✅ Stats: {stats['total_functions']} functions indexed")
    print(f"   - Repos: {len(stats['repos'])}")
    print(f"   - Types: {len(stats['types'])}")

    # Test 4: Search code
    print("\n[5] Testing search_code tool...")
    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "search_code",
            "arguments": {
                "query": "JWT authentication",
                "limit": 3
            }
        }
    }
    response = server.handle_request(request)
    result_text = response["result"]["content"][0]["text"]
    result_data = json.loads(result_text)
    print(f"✅ Search: Found {result_data['results_count']} results for 'JWT authentication'")
    for i, r in enumerate(result_data['results'][:2], 1):
        print(f"   {i}. {r['repo']}/{r['file']}:{r['function']}")
        print(f"      Type: {r['code_type']}, Lines: {r['lines_of_code']}")

    # Test 5: Search with type filter
    print("\n[6] Testing search with type filter...")
    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "search_code",
            "arguments": {
                "query": "HTTP request middleware",
                "limit": 3,
                "code_type": "middleware"
            }
        }
    }
    response = server.handle_request(request)
    result_text = response["result"]["content"][0]["text"]
    result_data = json.loads(result_text)
    print(f"✅ Filtered search: Found {result_data['results_count']} middleware results")
    for i, r in enumerate(result_data['results'], 1):
        print(f"   {i}. {r['function']} (type: {r['code_type']})")

    # Test 6: List resources
    print("\n[7] Testing resources/list...")
    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "resources/list",
        "params": {}
    }
    response = server.handle_request(request)
    resources = response["result"]["resources"]
    print(f"✅ Found {len(resources)} resources:")
    for r in resources[:4]:
        print(f"   - {r['uri']}: {r['name']}")

    # Test 7: Read resource
    print("\n[8] Testing resources/read...")
    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "resources/read",
        "params": {
            "uri": "codebase://stats"
        }
    }
    response = server.handle_request(request)
    content = response["result"]["contents"][0]
    stats = json.loads(content["text"])
    print(f"✅ Read resource: codebase://stats")
    print(f"   Total functions: {stats['total_functions']}")

    # Test 8: Error handling
    print("\n[9] Testing error handling...")
    request = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "invalid_method",
        "params": {}
    }
    response = server.handle_request(request)
    assert "error" in response
    print(f"✅ Error handling: {response['error']['message']}")

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("\n📊 Test Summary:")
    print("   - Server initialization: ✅")
    print("   - Tools listing: ✅")
    print("   - Code search: ✅")
    print("   - Type filtering: ✅")
    print("   - Statistics: ✅")
    print("   - Resources: ✅")
    print("   - Error handling: ✅")
    print("\n🎉 MCP Server is working correctly!")

if __name__ == "__main__":
    try:
        test_server()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
