# Tekton Scripts

This directory contains scripts for managing the Tekton ecosystem of AI components and tools.

## Core Scripts

### tekton.py - Unified Tekton Suite Launcher

The `tekton.py` script orchestrates the startup of all Tekton components in the correct dependency order.

**Usage:**

```bash
# Start the core Tekton components (database and Engram)
tekton start

# Start all Tekton components, including optional ones
tekton start --all

# Start specific components
tekton start ergon ollama

# Start Ollama with a specific model
tekton start ollama --ollama-model llama3

# Stop all running Tekton components
tekton stop

# Stop specific components
tekton stop ollama

# Show status of all Tekton components
tekton status

# List available components
tekton list
```

### tekton_client.py - Individual AI Client Launcher

The `tekton_client.py` script manages individual AI model clients with Tekton integration.

**Usage:**

```bash
# Launch Ollama with Tekton integration
tekton_client ollama --model llama3

# Launch Claude with Tekton integration
tekton_client claude --model claude-3-sonnet-20240229

# Launch OpenAI with Tekton integration
tekton_client openai --model gpt-4o-mini

# Launch Claude Code with Tekton integration
tekton_client claudecode

# List all registered clients
tekton_client list

# Show status
tekton_client status

# Get detailed help
tekton_client help
```

### setup_symlinks.sh - Create Symlinks in ~/utils

This script creates symlinks for Tekton scripts in the ~/utils directory for easy access.

**Usage:**

```bash
./setup_symlinks.sh
```

After running this script, you can use `tekton` and `tekton_client` commands directly from anywhere on your system (assuming ~/utils is in your PATH).

## Component Dependencies

Components are started in the following dependency order:

1. **database** - Core SQLite and vector databases
2. **engram** - Centralized memory and embedding service
3. **ergon** - Agent and tool management framework
4. **ollama**, **claude**, **openai** (optional) - Model integrations

## Client Registration

The Tekton system uses a client registration system to manage the lifecycle of different AI model clients. When any component starts, it registers with Engram and can be centrally managed.

## Configuration

Tekton components use a shared configuration in ~/.tekton directory. This includes:

- SQLite database for relational data
- Vector databases for embeddings
- Configuration files

Environment variables can be set in a .env file in the Ergon directory.