# Ergon CLI

This directory contains the command-line interface for Ergon, an Intelligent Tool, Agent, and Workflow Manager.

## Architecture

The CLI has been refactored from a monolithic `main.py` file into a modular structure:

### Core Components

- **`main.py`**: Entry point that imports from the new structure
- **`core.py`**: Core Typer application and command loading logic

### Command Modules

- **`commands/system_commands.py`**: System initialization, UI, status, login commands
- **`commands/agent_commands.py`**: Agent creation, listing, running, and deletion commands
- **`commands/flow_commands.py`**: Flow execution commands
- **`commands/docs_commands.py`**: Documentation management commands

### Utilities

- **`utils/db_helpers.py`**: Database initialization and checking
- **`utils/agent_finder.py`**: Helper for finding agents by name or ID

## Command Structure

The CLI includes the following main commands:

1. **System Management**
   - `ergon init`: Initialize Ergon database and configuration
   - `ergon ui`: Start the Ergon web UI (Streamlit)
   - `ergon status`: Check Ergon status and configuration
   - `ergon login`: Login to Ergon CLI

2. **Agent Management**
   - `ergon create`: Create a new AI agent
   - `ergon list`: List all available agents
   - `ergon run`: Run an AI agent
   - `ergon delete`: Delete an AI agent

3. **Advanced Features**
   - `ergon flow`: Run a flow with multiple agents
   - `ergon nexus`: Chat with a memory-enabled Nexus agent
   - `ergon preload-docs`: Preload documentation sources
   - `ergon setup-mail`: Set up mail provider

4. **Subcommands**
   - `ergon repo`: Repository management commands
   - `ergon docs`: Documentation system commands
   - `ergon tools`: Tool generation commands
   - `ergon db`: Database management commands
   - `ergon system`: System information and management
   - `ergon memory`: Memory management commands
   - `ergon latent`: Latent reasoning commands (if available)

## Usage

For help with any command, use the `--help` flag:

```bash
ergon --help
ergon run --help
```

## Maintainer Notes

When adding new commands:

1. Create a new function in the appropriate module in `commands/`
2. Add the command to the function in `core.py`
3. Keep command implementation in the module, not in `core.py`
4. Use helper functions from `utils/` for common operations

The modular structure makes it easier to add new commands and maintain existing ones without creating a large, monolithic file.