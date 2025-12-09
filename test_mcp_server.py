#!/usr/bin/env python3
"""
Simple MCP server test script
Sends JSON-RPC requests to test the server
"""

import subprocess
import json
import sys


def send_request(proc, method, params=None, request_id=1):
    """Send JSON-RPC request and get response"""
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    if params:
        request["params"] = params

    # Send request
    request_json = json.dumps(request) + "\n"
    proc.stdin.write(request_json)
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline()
    if not response_line:
        raise Exception("No response from server")

    return json.loads(response_line)


def main():
    print("🧪 Testing MCP Server")
    print("=" * 60)

    # Start server
    proc = subprocess.Popen(
        ["./run_mcp_server.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        # Test 1: Initialize
        print("\n[Test 1] Initialize")
        response = send_request(proc, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        print(f"✅ Initialize: {response['result']['serverInfo']['name']}")

        # Test 2: List tools
        print("\n[Test 2] List tools")
        response = send_request(proc, "tools/list", request_id=2)
        tools = response['result']['tools']
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description'][:60]}...")

        # Test 3: Search code
        print("\n[Test 3] Search code for 'JWT authentication'")
        response = send_request(proc, "tools/call", {
            "name": "search_code",
            "arguments": {
                "query": "JWT authentication",
                "limit": 3
            }
        }, request_id=3)

        result_text = response['result']['content'][0]['text']
        result_data = json.loads(result_text)
        print(f"✅ Found {result_data['results_count']} results:")
        for r in result_data['results'][:2]:  # Show first 2
            print(f"   - {r['repo']}/{r['file']}:{r['function']}")

        # Test 4: Get stats
        print("\n[Test 4] Get stats")
        response = send_request(proc, "tools/call", {
            "name": "get_stats",
            "arguments": {}
        }, request_id=4)

        stats_text = response['result']['content'][0]['text']
        stats = json.loads(stats_text)
        print(f"✅ Stats: {stats['total_functions']} functions indexed")

        # Test 5: List resources
        print("\n[Test 5] List resources")
        response = send_request(proc, "resources/list", request_id=5)
        resources = response['result']['resources']
        print(f"✅ Found {len(resources)} resources:")
        for r in resources[:3]:  # Show first 3
            print(f"   - {r['uri']}: {r['name']}")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        # Print server stderr
        stderr = proc.stderr.read()
        if stderr:
            print(f"\nServer stderr:\n{stderr}")
        return 1

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    sys.exit(main())
