# Agenteer

![Agenteer UI](images/icon.jpeg)


Agenteer is a streamlined AI agent builder focused on simplicity, performance, and usability. It enables the rapid creation, testing, and deployment of AI agents with minimal configuration. Agenteer produces functional agents using PydanticAI, LangChain, LangGraph, Anthropic MCP, OpenAI and other LLM modules.

## Key Features

- **Zero-Config Setup**: Get started with minimal setup requirements
- **Unified Interface**: CLI and web UI in a single package
- **Local First**: Runs entirely on local resources when needed
- **Extensible**: Plugin architecture for custom agent capabilities
- **Performance**: Optimized for speed with local caching
- **Documentation Crawler**: Automatically index documentation with progress tracking and caching
- **GitHub Integration**: Create GitHub-specific agents with repository access
- **Mail Integration**: Create email agents that can read and send email via Gmail and Outlook

## Installation

### Local Installation

```bash
# Clone the repository
git clone https://github.com/ckoons/Agenteer.git
cd Agenteer

# Run the setup script
./setup.sh

# Activate the virtual environment
source venv/bin/activate

# Start the UI
agenteer ui

# Or use the wrapper script for cleaner output
./run_ui.sh

# Or use the CLI
agenteer create -n "my_agent" -d "A weather agent that fetches forecast data"
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build --platform linux/arm64 -t agenteer .  # For Apple Silicon Macs
docker build --platform linux/amd64 -t agenteer .  # For Intel/AMD systems
docker run -p 8501:8501 -p 8000:8000 agenteer
```

> **Note for Apple Silicon Mac users**: Be sure to include the `--platform linux/arm64` flag when building and running Docker images to ensure compatibility.

### Documentation Preloading

Agenteer offers built-in documentation preloading to enhance agent capabilities. There are several ways to preload documentation:

1. **Via the UI (Recommended)**: 
   Navigate to the Documentation or Web Search pages in the UI. If no documentation is found, you'll see a "Preload Essential Documentation" button that will automatically crawl and index documentation from Pydantic, LangChain, LangGraph, and Anthropic.

2. **Using the CLI**:
   ```bash
   # Preload all documentation sources
   agenteer preload-docs

   # Preload a specific source
   agenteer preload-docs --source pydantic
   agenteer preload-docs --source langchain
   agenteer preload-docs --source langgraph
   agenteer preload-docs --source anthropic

   # Customize crawling settings
   agenteer preload-docs --max-pages 500 --max-depth 4 --timeout 300
   ```

3. **With Docker**:
   ```bash
   # Preload all documentation sources
   docker run --platform linux/arm64 agenteer preload-docs  # For Apple Silicon Macs
   docker run --platform linux/amd64 agenteer preload-docs  # For Intel/AMD systems

   # Preload a specific source
   docker run --platform linux/arm64 agenteer preload-docs --source langchain  # For Apple Silicon
   docker run --platform linux/arm64 agenteer preload-docs --source langgraph  # For Apple Silicon
   ```

The preloaded documentation enables agents to leverage knowledge from these frameworks when responding to queries, making them more effective for framework-specific tasks.

Agenteer automatically caches documentation for faster preloading in future sessions. Cached documentation is stored in the `vector_store/doc_cache` directory and is valid for 7 days, after which it will be refreshed automatically. This ensures your documentation stays current while minimizing network usage.

## Requirements

- Python 3.10+
- No external services required (uses SQLite by default)
- LLM API key (supports Claude, OpenAI, or local models via Ollama)

## UI Overview

The Agenteer UI is designed to be intuitive and streamlined:

- **Home**: Dashboard with quick actions and recent activity
- **Create Agent**: Form to create new agents with different capabilities
- **Existing Agents**: Browse and interact with your created agents
- **Documentation**: Search, crawl, and browse documentation
- **Web Search**: Crawl and index external documentation
- **Settings**: Configure API keys, database, and models

## Architecture

Agenteer consists of several core components:

1. **Core Engine**: Agent generation and execution logic
2. **Local Database**: SQLite-based storage for agents and sessions
3. **Vector Store**: FAISS-based document embedding and retrieval
4. **UI**: Streamlit-based web interface 
5. **CLI**: Command-line interface for automation and scripting
6. **API**: REST API for integration with other tools
7. **Documentation Crawler**: Tools for indexing documentation

## Configuration

Agenteer uses a hierarchical configuration system:

- `.env`: Base configuration shared by all users
- `.env.owner`: Personal settings (API keys, model preferences)
- `.env.local`: Local development settings

Example configuration:

```bash
# API Keys
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"
OLLAMA_BASE_URL="http://localhost:11434"

# Model settings
DEFAULT_MODEL="claude-3-7-sonnet-20250219"
USE_LOCAL_MODELS=false
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"

# Application settings
LOG_LEVEL="INFO"
DEBUG=false
```

## Working with Agents

Agenteer provides a unified interface for creating, running, and managing AI agents through both the CLI and web UI.

### Creating Agents

```bash
# Create a standard agent
agenteer create -n "MyAgent" -d "Description of the agent" -t standard

# Create a GitHub agent
agenteer create -n "GitHubAgent" -d "GitHub repository manager" -t github

# Create a Mail agent
agenteer create -n "MailAgent" -d "Email management assistant" -t mail
```

### Running Agents

There are several ways to run your agents:

```bash
# List available agents to get their IDs
agenteer list

# Run an agent with a specific input
agenteer run AGENT_ID -i "Your input here"

# Run an agent in interactive mode (conversation)
agenteer run AGENT_ID --interactive
```

### Managing Agents

You can manage your agents with the following commands:

```bash
# List all agents
agenteer list

# Delete an agent (with confirmation prompt)
agenteer delete AGENT_ID

# Force delete an agent without confirmation
agenteer delete AGENT_ID --force
```

### Using the Web UI

You can launch the web UI to interact with your agents in a more user-friendly interface:

```bash
agenteer ui
```

The web UI provides several ways to work with agents:

#### Running Agents in the UI

1. Navigate to the "My Agents" page from the sidebar
2. Select an agent from the dropdown menu at the top
3. Use the Chat tab to interact with your agent:
   - Type messages in the chat input at the bottom
   - View the conversation history in the chat window
   - Use the "Reset Chat" button to clear the conversation history

#### Agent Management in the UI

The UI provides several features for managing your agents:

- **Creating Agents**: Use the "Create Agent" page to set up new agents with different capabilities
- **Viewing Agent Details**: The "My Agents" page shows details for each agent, including:
  - Files tab: View the agent's system prompt and other configuration files
  - Tools tab: See the tools available to the agent
  - Executions tab: Review past agent executions and their results
- **Deleting Agents**: Click the "Delete Agent" button on the agent details page to remove an agent

#### Other UI Features

- **Documentation**: Search and browse the documentation loaded into the system
- **Web Search**: Crawl and index external documentation
- **Settings**: Configure API keys, database connections, and other system settings

### Agent Types

#### Standard Agents
General-purpose agents for various tasks, including code assistance, knowledge retrieval, and more.

#### GitHub Agents
Specialized agents for GitHub integration. These agents can:

- List your GitHub repositories
- Get repository details
- Create and manage repositories
- View issues and pull requests
- Create, edit and delete files in repositories

You can use GitHub agents in three ways:

1. **Through the UI**:
   - Create a GitHub agent in the "Create Agent" page by selecting the GitHub agent type
   - Run the agent from the "My Agents" page and interact with it via chat

2. **Through the CLI**:
   - Create a GitHub agent: `agenteer create -n "GitHubAgent" -d "Description" -t github`
   - Run the agent: `agenteer run AGENT_ID --interactive`

3. **Using the standalone script**:
   ```bash
   # Using the standalone GitHub agent
   python github_agent.py --list                # List repositories
   python github_agent.py --get REPO_NAME       # Get repository details
   python github_agent.py --create NEW_REPO     # Create a new repository

   # Using natural language
   python github_agent.py "list repositories"
   ```

#### Mail Agents
Email integration agents that can read, send, and manage emails. These agents can:

- Connect to Gmail or Outlook/Microsoft 365 accounts
- Read messages from your inbox
- Send new emails with HTML formatting
- Reply to existing conversations 
- Search for specific emails
- View email folders/labels

You can use Mail agents in two ways:

1. **Through the UI**:
   - Create a Mail agent in the "Create Agent" page by selecting the Mail agent type
   - Run the agent from the "My Agents" page and interact with it via chat
   - Use natural language to request email operations

2. **Through the CLI**:
   - Create a Mail agent: `agenteer create -n "MailAgent" -d "Description" -t mail`
   - Run the agent: `agenteer run AGENT_ID --interactive`

When you first run a Mail agent, it will guide you through the authentication process:
1. Use the `setup_mail` command with your provider of choice (gmail or outlook)
2. Complete the OAuth authentication flow in your web browser
3. Once authenticated, you can use commands like:
   - get_inbox - View your recent emails
   - send_message - Compose and send new emails
   - reply_to_message - Reply to existing conversations
   - search_messages - Find specific emails

##### Mail Agent Setup

###### Gmail Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Gmail API:
   - From the dashboard, go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop application" as the application type
   - Name your OAuth client
5. Download the credentials:
   - After creation, download the JSON file
   - Rename it to `gmail_credentials.json`
   - Place it in the `~/.agenteer/mail` directory (will be created automatically if it doesn't exist)

###### Outlook/Microsoft 365 Setup

1. Go to the [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
   - Name your application
   - Select "Accounts in any organizational directory and personal Microsoft accounts"
   - Set the redirect URI to `http://localhost:8000/auth/callback`
4. After registration, note your Application (client) ID
5. Add API permissions:
   - Go to "API permissions" > "Add a permission"
   - Select "Microsoft Graph" > "Delegated permissions"
   - Add the following permissions:
     - Mail.Read
     - Mail.Send
     - Mail.ReadWrite
6. Configure authentication:
   - Go to "Authentication"
   - Ensure the redirect URI is set correctly
   - Under "Advanced settings", enable "Allow public client flows"
7. Create a client secret (optional):
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Provide a description and choose expiration
   - Copy the secret value immediately (it won't be shown again)
8. Add the client ID to your `.env` file:
   ```
   OUTLOOK_CLIENT_ID=your-client-id-here
   ```

## Use Cases

- Rapid prototyping of AI agents
- Creating specialized agents for specific domains
- Building agent-powered workflows
- Teaching and learning about LLM agent design patterns
- Documentation searching and knowledge management
- GitHub repository management and automation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
