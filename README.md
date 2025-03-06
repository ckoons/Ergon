# Agenteer

Agenteer is a streamlined AI agent builder focused on simplicity, performance, and usability. It enables the rapid creation, testing, and deployment of Pydantic AI agents with minimal configuration.

## Key Features

- **Zero-Config Setup**: Get started with minimal setup requirements
- **Unified Interface**: CLI and web UI in a single package
- **Local First**: Runs entirely on local resources when needed
- **Extensible**: Plugin architecture for custom agent capabilities
- **Performance**: Optimized for speed with local caching

## Getting Started

```bash
# Install Agenteer
pip install agenteer

# Start the UI
agenteer ui

# Or use the CLI
agenteer create --name "my_agent" --description "A weather agent that fetches forecast data"
```

## Requirements

- Python 3.10+
- No external services required (uses SQLite by default)
- LLM API key (supports Claude, OpenAI, or local models via Ollama)

## Architecture

Agenteer consists of several core components:

1. **Core Engine**: Agent generation and execution logic
2. **Local Database**: SQLite-based storage for agents and sessions
3. **Vector Store**: FAISS-based document embedding and retrieval
4. **UI**: Streamlit-based web interface 
5. **CLI**: Command-line interface for automation and scripting
6. **API**: REST API for integration with other tools

## Use Cases

- Rapid prototyping of AI agents
- Creating specialized agents for specific domains
- Building agent-powered workflows
- Teaching and learning about LLM agent design patterns

## License

MIT
