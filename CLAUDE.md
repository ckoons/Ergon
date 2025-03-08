# Agenteer Development Notes

This file contains useful information about the Agenteer project structure, commands, and development notes.

## UI Styling

The Agenteer UI has been styled with the following color scheme:

- Main action buttons: Light Red/Orange (`#FF7043`) with darker hover effect (`#F4511E`)
- Navigation in sidebar: Specific colors for different expanders
- Recent Activity section: Collapsible expander with detail view

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
# Start the UI (standard)
agenteer ui

# Start the UI with suppressed PyTorch warnings
./run_ui.sh

# Run the CLI
agenteer --help

# Create a new agent
agenteer create -n "AgentName" -d "Description" -t standard

# Create a GitHub agent
agenteer create -n "GitHubAgent" -d "Description" -t github

# List all agents
agenteer list

# Run an agent
agenteer run AGENT_ID -i "Your input here"

# Preload documentation
agenteer preload-docs --source anthropic

# Check system status
agenteer status
```

## Docker and Platform Compatibility

### Docker Commands

```bash
# Build Docker image for Apple Silicon (ARM64)
docker build --platform linux/arm64 -t agenteer .

# Build Docker image for Intel/AMD (AMD64)
docker build --platform linux/amd64 -t agenteer .

# Run UI in Docker
docker run --platform linux/arm64 -p 8501:8501 agenteer ui

# Run CLI commands in Docker
docker run --platform linux/arm64 agenteer preload-docs
docker run --platform linux/arm64 agenteer status

# Run with persistent data volume
docker volume create agenteer-data
docker run --platform linux/arm64 -v agenteer-data:/data -p 8501:8501 agenteer ui
```

### Platform-Specific Notes

#### macOS (Apple Silicon)
- Always use `--platform linux/arm64` for Docker commands
- Install Xcode Command Line Tools: `xcode-select --install`
- Use `./run_ui.sh` script to suppress PyTorch warnings

#### macOS (Intel)
- Use `--platform linux/amd64` for Docker commands 
- Install Xcode Command Line Tools: `xcode-select --install`
- Use `./run_ui.sh` script to suppress PyTorch warnings

#### Windows
- Use WSL2 for best compatibility
- Install Docker Desktop for Windows
- Running UI: `python -m agenteer.cli.main ui`

#### Linux
- Install Python 3.10+ and venv
- Follow standard installation process
- No special considerations needed

## Documentation Management

### Preloading Documentation

#### Common Patterns:

1. **Initial Setup**: When setting up a new Agenteer instance:
   ```bash
   # Preload all essential documentation
   agenteer preload-docs --timeout 300
   ```

2. **Focused Documentation**: When working with specific frameworks:
   ```bash
   # For Pydantic work
   agenteer preload-docs --source pydantic --max-pages 300
   
   # For LangChain projects
   agenteer preload-docs --source langchain --max-pages 300
   
   # For Anthropic API development
   agenteer preload-docs --source anthropic --max-pages 300
   ```

3. **Docker Deployment**:
   ```bash
   # Preload in Docker container
   docker run --platform linux/arm64 agenteer preload-docs --timeout 600  # For Apple Silicon
   docker run --platform linux/amd64 agenteer preload-docs --timeout 600  # For Intel/AMD
   ```

4. **Checking Status**:
   ```bash
   # Verify documentation is loaded
   agenteer status
   ```

#### Best Practices:

- Set reasonable `max-pages` limits (100-300) to avoid excessive crawling
- Use longer timeouts (300-600 seconds) for complete documentation
- Preload only documentation relevant to your current project
- Run preloading during off-hours for large documentation sets
- Verify loaded documentation by checking status

## Troubleshooting

### Common Issues

#### PyTorch Warnings
If you see warnings like `RuntimeError: Tried to instantiate class '__path__._path'...`:
- This is a known issue with PyTorch and Streamlit's file watcher
- Use the `./run_ui.sh` script which suppresses these warnings
- Install watchdog: `pip install watchdog`

#### Documentation Crawling Errors
If you see `Error processing URL...` messages:
- These are normal when crawling documentation sites
- Some pages may be unavailable or have moved
- The crawler will continue with available pages
- Check network connectivity if all URLs fail

#### Docker "Exec Format Error"
If you see `exec format error` when running Docker:
- Make sure to specify the correct platform flag
- For Apple Silicon: `--platform linux/arm64`
- For Intel/AMD: `--platform linux/amd64`

#### Port Already In Use
If you see `Bind for 0.0.0.0:8501 failed: port is already allocated`:
- Another instance of the UI is already running
- Run `docker ps` to find and stop the container
- Or use a different port: `-p 8502:8501`

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