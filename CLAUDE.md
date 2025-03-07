# Agenteer Development Notes

This file contains useful information about the Agenteer project structure, commands, and development notes.

## GitHub Integration

The GitHub integration allows Agenteer to create agents that can interact with GitHub repositories.

### Key Components

- `agenteer/core/agents/generators/github_generator.py`: Defines GitHub tool functions and agent generation
- `agenteer/utils/config/settings.py`: Contains GitHub API configuration settings
- `github_agent.py`: Standalone GitHub agent with CLI interface
- `github_demo.py`: Simple demo script for GitHub API interactions

### GitHub Usage Examples

```bash
# Using the standalone GitHub agent
python github_agent.py --list                # List repositories
python github_agent.py --get REPO_NAME       # Get repository details
python github_agent.py --create NEW_REPO     # Create a new repository
python github_agent.py --delete REPO_NAME    # Delete a repository

# Using natural language
python github_agent.py "list repositories"
python github_agent.py "get repository details for Agenteer"
```

### GitHub Demo Usage

```bash
# Demo basic GitHub API functionality
python github_demo.py repos    # List repositories
python github_demo.py info     # Show user information
python github_demo.py events   # Show recent events
python github_demo.py stars    # List starred repositories
python github_demo.py orgs     # List organizations
```

## UI Structure

The Agenteer UI is built with Streamlit and organized into several pages:

- **Home**: Dashboard with quick actions and recent activity
- **Create Agent**: Form for creating new agents
- **My Agents**: Browse and interact with existing agents
- **Documentation**: Search, crawl, and browse documentation
- **Web Search**: Crawl and index external documentation
- **Settings**: Configure API keys, database, and other settings

## Common Commands

```bash
# Start the UI
streamlit run agenteer/ui/app.py

# Run the CLI
python -m agenteer.cli.main --help

# Create a new agent
python -m agenteer.cli.main create -n "AgentName" -d "Description" -t standard

# Create a GitHub agent
python -m agenteer.cli.main create -n "GitHubAgent" -d "Description" -t github

# List all agents
python -m agenteer.cli.main list

# Run an agent
python -m agenteer.cli.main run AGENT_ID -i "Your input here"
```

## Project Organization

- `agenteer/`: Main package
  - `api/`: API server functionality
  - `cli/`: Command-line interface
  - `core/`: Core functionality
    - `agents/`: Agent creation and execution
    - `database/`: Database models and operations
    - `docs/`: Documentation crawling
    - `llm/`: LLM client integration
    - `models/`: Data models
    - `vector_store/`: Vector database functionality
  - `ui/`: Streamlit UI application
  - `utils/`: Utility functions and configuration