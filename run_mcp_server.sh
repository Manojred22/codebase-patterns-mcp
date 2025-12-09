#!/bin/bash
#
# MCP Server Launcher
# Usage: ./run_mcp_server.sh
#

# Exit on error
set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Run MCP server
python -m src.mcp_server
