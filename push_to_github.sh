#!/bin/bash
# Script to initialize git and push to GitHub

cd /Users/manoj.reddy/codebase-patterns-mcp

echo "Initializing git repository..."
git init

echo "Adding files..."
git add .

echo "Creating initial commit..."
git commit -m "Initial commit - Codebase Patterns MCP Server

- Semantic code search with function-level indexing
- MCP server implementation for Claude Code integration
- Support for Go repositories (extensible to other languages)
- Vector search powered by ChromaDB and OpenAI embeddings
- Sanitized for open source release

🤖 Generated with Claude Code"

echo "Adding remote origin..."
git remote add origin https://github.com/Manojred22/codebase-patterns-mcp.git

echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo "✅ Successfully pushed to GitHub!"
