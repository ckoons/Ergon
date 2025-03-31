# Tekton Suite Launcher

A unified launcher for the Tekton ecosystem that orchestrates the startup of all Tekton components in the correct dependency order.

## File Structure

The Tekton launcher has been refactored into a modular structure for better organization:

- `__init__.py`: Package initialization and re-exports
- `main.py`: Main entry point and signal handling
- `cli.py`: Command-line interface and argument parsing
- `components.py`: Component definitions and metadata
- `startup.py`: Functions for starting components
- `shutdown.py`: Functions for stopping components
- `status.py`: Functions for checking component status

## Usage

The launcher can be invoked through the original script for backward compatibility:

```bash
python tekton.py [command] [options]
```

Or directly through the module:

```bash
python -m tekton.main [command] [options]
```

## Commands

- `start`: Start Tekton components
  - Options:
    - List of component IDs to start (default: all core components)
    - `--all`: Include optional components
    - `--ollama-model`: Specify Ollama model (default: llama3)
    - `--claude-model`: Specify Claude model (default: claude-3-sonnet-20240229)
    - `--openai-model`: Specify OpenAI model (default: gpt-4o-mini)

- `stop`: Stop Tekton components
  - Options:
    - List of component IDs to stop (default: all running components)

- `status`: Show Tekton component status

- `list`: List available Tekton components

## Available Components

- `database`: Core SQLite and vector databases
- `engram`: Centralized memory and embedding service
- `ergon`: Agent and tool management framework
- `ollama`: Local LLM integration through Ollama (optional)
- `claude`: Anthropic Claude API integration (optional)
- `openai`: OpenAI API integration (optional)

## Examples

```bash
# Start all core components
python tekton.py start

# Start all components (including optional ones)
python tekton.py start --all

# Start specific components
python tekton.py start ergon claude

# Start Claude with a specific model
python tekton.py start claude --claude-model claude-3-opus-20240229

# Stop all components
python tekton.py stop

# Stop specific components
python tekton.py stop claude openai

# Show component status
python tekton.py status

# List available components
python tekton.py list
```