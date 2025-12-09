# Transition Guide: Moving to Claude Code

## Quick Setup (10 minutes)

### Step 1: Save All Context (5 minutes)

Create your project directory and save all documents:

```bash
# Create project directory
mkdir -p ~/codebase-patterns-mcp
cd ~/codebase-patterns-mcp

# Create docs directory for all our planning documents
mkdir -p docs

# You'll save each artifact as a separate file:
# - docs/01-collaboration-journey.md
# - docs/02-solution-alternatives.md
# - docs/03-mcp-metrics-benchmarks.md
# - docs/04-architecture-diagrams.md
# - docs/05-detailed-implementation-plan.md
# - docs/06-evaluation-framework.py
# - docs/07-deep-dive-foundation.md

# Create a quick reference
cat > docs/README.md << 'EOF'
# Documentation Index

## Planning Documents (Read First)
1. **detailed-implementation-plan.md** ⭐ START HERE
   - Complete 32-hour implementation plan
   - Phase-by-phase tasks with code examples
   - Your main guide for building

2. **architecture-diagrams.md**
   - Visual architecture (RAG vs MCP)
   - Component breakdown
   - Data flow

3. **solution-alternatives.md**
   - Why we chose MCP
   - All 6 options evaluated
   - Decision matrix

## Reference Documents
4. **mcp-metrics-benchmarks.md**
   - Success metrics defined
   - Industry benchmarks
   - How to measure success

5. **collaboration-journey.md**
   - Complete conversation history
   - Decisions made
   - Current status

## Code & Tools
6. **evaluation-framework.py**
   - Metrics calculation code
   - Testing utilities
   - Ready to use

7. **deep-dive-foundation.md**
   - AI/ML learning resource
   - For deeper understanding
   - Reference as needed

## Quick Start
1. Read: detailed-implementation-plan.md
2. Start: Phase 1, Task 1.1 (Environment Setup)
3. Reference: architecture-diagrams.md as needed
EOF
```

**Save each artifact:**
- Go to claude.ai (this conversation)
- Click on each artifact on the right side
- Copy the content
- Save as the filename shown above

---

### Step 2: Create Project Context File (3 minutes)

This is the key file Claude Code will use:

```bash
cat > CONTEXT.md << 'EOF'
# Company Patterns MCP Server - Project Context

## What We're Building
MCP server that provides Claude Code with semantic search access to our team's "golden example" code patterns via RAG (Retrieval-Augmented Generation).

## The Problem We're Solving
- Developers using Claude get code that doesn't match team patterns
- Results in 15-20 PR comments per PR
- Specific issues: anonymous structs, over-engineering, duplicate code
- Team wastes 20-30 hours/week fixing generated code

## Our Solution
MCP server with RAG that:
1. Indexes 20-30 "perfect" example code files
2. Uses semantic search (embeddings + vector DB)
3. Claude Code automatically queries it when generating code
4. Returns code matching team's patterns

## Architecture Decision
- **Chosen:** MCP server with RAG inside
- **Stack:** Python + MCP SDK + Chroma + OpenAI embeddings + tree-sitter
- **Transport:** STDIO (local development)
- **Why:** Native Claude Code integration, future-proof, standard protocol

## Success Metrics
- Pattern conformance improvement: ≥80%
- Recall@3: ≥85%
- PR comment reduction: ≥80%
- Team adoption: ≥90%

## Implementation Status
- **Planning:** 100% complete ✅
- **Current:** Starting Phase 1 implementation
- **Timeline:** 32 hours over 3 weekends
- **Starting:** Phase 1, Task 1.1 (Environment Setup)

## Phase 1 Goals (Weekend 1 - 12 hours)
1. Basic MCP server running
2. Simple RAG (load 5-10 files, basic search)
3. Claude Code integration working
4. Can retrieve actual patterns

## Key Files to Reference
- `/docs/detailed-implementation-plan.md` - Main implementation guide
- `/docs/architecture-diagrams.md` - System architecture
- `/docs/mcp-metrics-benchmarks.md` - Success metrics

## Current Task
**Phase 1, Task 1.1: Environment Setup**
- Create virtual environment
- Install dependencies
- Configure API keys
- Verify setup

## Important Notes
- Using Python for MCP server (even though patterns are Go)
- Starting with 5-10 patterns, expanding to 20-30 in Phase 2
- Claude Code has native MCP support (no wrapper needed!)
- OpenAI API for embeddings, Anthropic API for Claude

## API Keys Needed
- OPENAI_API_KEY (for embeddings)
- ANTHROPIC_API_KEY (for Claude Code - if not already configured)

## Commands to Remember
```bash
# Activate environment
source venv/bin/activate

# Run MCP server
python mcp_server.py

# Add to Claude Code
claude mcp add-json company-patterns --scope user '...'

# Check MCP status
claude
> /mcp
```

## Next Steps
1. Run environment setup commands
2. Install dependencies
3. Create initial project structure
4. Start coding mcp_server.py
EOF
```

---

### Step 3: Set Up Claude Code (2 minutes)

```bash
# Make sure Claude Code is installed
claude --version

# If not installed:
npm install -g @anthropic-ai/claude-code

# Verify
which claude
```

---

### Step 4: Start Claude Code with Context

```bash
# Make sure you're in your project directory
cd ~/codebase-patterns-mcp

# Start Claude Code
claude

# In Claude Code, give it context:
> I'm starting implementation of a company patterns MCP server. 
> Read CONTEXT.md for the full project context.
> Then read docs/detailed-implementation-plan.md for the implementation plan.
> I want to start with Phase 1, Task 1.1 (Environment Setup).
> Can you help me set up the Python virtual environment and install dependencies?
```

---

## How to Use Claude Code for This Project

### Initial Context Loading

```bash
claude

> Here's what we're building:
> - Read CONTEXT.md (project overview)
> - Read docs/detailed-implementation-plan.md (complete plan)
> - I'm starting Phase 1, Task 1.1
> 
> Let's begin with environment setup. Create the virtual environment
> and requirements.txt as specified in the plan.
```

### Iterative Development

For each task:

```bash
> I'm now on Phase 1, Task 1.4: Minimal MCP Server
> 
> Reference: docs/detailed-implementation-plan.md, section "Task 1.4"
> 
> Create mcp_server.py following the example in the plan.
> Make sure it:
> 1. Uses MCP SDK
> 2. Defines search_patterns tool
> 3. Returns hardcoded example for now
> 
> Show me the code first, then I'll review before you write the file.
```

### When You Need Clarification

```bash
> I'm looking at Phase 1, Task 1.7 (Implement Simple Embeddings & Vector DB).
> 
> I see the example code in docs/detailed-implementation-plan.md
> but I'm not sure about the Chroma configuration.
> 
> Can you explain the ChromaDB setup and help me implement it?
```

### Testing As You Go

```bash
> I've completed Task 1.6 (File Loader).
> 
> Now I want to test it before moving on.
> Based on the plan's testing section, create a test script
> that verifies the loader works correctly.
> 
> Then run it and show me the output.
```

---

## Conversation Patterns with Claude Code

### ✅ Good Prompts

**Specific and contextual:**
```
> Phase 1, Task 1.4: Create mcp_server.py
> Reference the example in docs/detailed-implementation-plan.md
> Use the search_patterns tool signature shown there
> Start with hardcoded return value as specified
```

**Request review before writing:**
```
> Show me the code for src/indexer.py first
> I want to review it before you write the file
```

**Test incrementally:**
```
> I've finished Task 1.6. Let's test it works before moving to 1.7
> Create a test script that loads patterns and prints summary
```

### ❌ Avoid

**Too vague:**
```
> Create the MCP server
(Which task? What features? Following which spec?)
```

**Skipping ahead:**
```
> Build the complete RAG system
(Start with Phase 1 basics first!)
```

---

## Workflow Recommendations

### Session Structure

**Start of session:**
```bash
claude

> Current status: Completed Tasks 1.1-1.3
> Now starting Task 1.4: Minimal MCP Server
> Context in CONTEXT.md and docs/detailed-implementation-plan.md
```

**During development:**
```
> Task 1.4 complete. Tested manually, works!
> Moving to Task 1.5: Connect to Claude Code
> Show me the configuration command first
```

**End of session:**
```
> Summary of today's progress:
> ✅ Tasks 1.1-1.5 complete
> ✅ MCP server runs
> ✅ Connected to Claude Code
> 
> Next session: Start Task 1.6 (File Loader)
> 
> Save this session summary to docs/progress.md
```

### Git Commits

After each completed task:
```bash
git add .
git commit -m "Phase 1, Task 1.4: Minimal MCP server

- Created mcp_server.py with basic structure
- Defined search_patterns tool
- Returns hardcoded example
- Successfully runs without errors

Next: Task 1.5 (Connect to Claude Code)"
```

---

## Managing Long Context

Claude Code has limits on context length. Here's how to manage:

### Core Context (Always Include)
- `CONTEXT.md` (project overview)
- Current task from implementation plan
- Files you're actively working on

### Reference When Needed
- Full implementation plan (when planning)
- Architecture diagrams (when designing)
- Metrics document (when testing)

### Example Context Management

```bash
> For this task, I need:
> 1. CONTEXT.md (project overview)
> 2. docs/detailed-implementation-plan.md, Phase 1, Task 1.7 section
> 3. The existing src/indexer.py file
> 
> I don't need the full architecture doc right now.
> Let's focus on implementing the RAG component.
```

---

## Checkpoint Files

Create checkpoint files after major milestones:

```bash
# After completing Phase 1
cat > docs/phase1-complete.md << 'EOF'
# Phase 1 Completion Checkpoint

## Date: 2025-11-23

## Completed Tasks
- ✅ Task 1.1: Environment Setup
- ✅ Task 1.2: Learn MCP Basics
- ✅ Task 1.3: Select Golden Examples (8 files)
- ✅ Task 1.4: Minimal MCP Server
- ✅ Task 1.5: Connect to Claude Code
- ✅ Task 1.6: File Loader
- ✅ Task 1.7: Embeddings & Vector DB
- ✅ Task 1.8: Integrate RAG into MCP
- ✅ Task 1.9: Test Suite
- ✅ Task 1.10: Documentation

## Metrics Achieved
- Patterns indexed: 8
- Recall@3: 75%
- Claude Code integration: Working ✅

## What Works
- MCP server starts and runs
- Claude Code connects successfully
- search_patterns tool retrieves actual patterns
- Basic RAG retrieval functional

## Known Issues
- Recall@3 below target (75% vs 90%)
- Only file-level chunking (not function-level yet)
- Limited to 8 patterns (need 20-30)

## Ready for Phase 2
✅ Foundation is solid
✅ Core components working
✅ Can proceed to enhancement

## Next Session
Start Phase 2, Task 2.1: AST-Based Chunking
EOF
```

---

## Quick Reference Commands

### Project Setup
```bash
cd ~/codebase-patterns-mcp
source venv/bin/activate
```

### Claude Code
```bash
# Start
claude

# Check MCP servers
> /mcp

# Restart Claude Code
claude restart
```

### Testing
```bash
# Test MCP server directly
python mcp_server.py

# Test retrieval
python scripts/test_retrieval.py

# Test with Claude Code
claude
> Search for handler patterns
```

### Development
```bash
# Run server
python mcp_server.py

# Reindex patterns
python scripts/index_patterns.py

# Check logs
tail -f ~/.claude/logs/mcp.log
```

---

## Success Indicators

After setup, you should be able to:

✅ **Run this command successfully:**
```bash
source venv/bin/activate
python -c "import mcp; print('MCP SDK installed')"
python -c "import chromadb; print('Chroma installed')"
```

✅ **See this in Claude Code:**
```bash
claude
> /mcp
# Output shows: company-patterns: connected ✅
```

✅ **Get actual patterns:**
```bash
> Search for authentication patterns
# Claude calls your tool and returns your golden examples
```

---

## Troubleshooting

### Can't import MCP
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall
pip install mcp
```

### Claude Code can't connect
```bash
# Check config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Check server runs
python mcp_server.py
# Should not crash immediately

# Check logs
tail -f ~/.claude/logs/mcp.log
```

### MCP server crashes
```bash
# Run with verbose output
python -v mcp_server.py

# Check Python version
python --version  # Should be 3.9+
```

---

## Ready to Start!

### Your Action Items Right Now:

1. **Save all documents** (5 min)
   ```bash
   mkdir -p ~/codebase-patterns-mcp/docs
   # Save each artifact as shown above
   ```

2. **Create CONTEXT.md** (2 min)
   ```bash
   cd ~/codebase-patterns-mcp
   # Create CONTEXT.md with content above
   ```

3. **Start Claude Code** (1 min)
   ```bash
   claude
   > Read CONTEXT.md and docs/detailed-implementation-plan.md
   > Let's start Phase 1, Task 1.1: Environment Setup
   ```

4. **Begin coding!** 🚀

---

**You're all set!** Claude Code will have all the context it needs, and you can reference the detailed plan as you go.

**Pro tip:** Keep this browser tab open with claude.ai so you can reference artifacts easily if needed.

**Ready to code?** Start Claude Code and begin with Task 1.1! 💪