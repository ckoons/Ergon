# Ergon

<div align="center">
  <img src="images/icon.jpeg" alt="Ergon Logo" width="800"/>
  <h3>The Intelligent Agent Builder</h3>
</div>

Ergon is a streamlined AI agent platform with a powerful memory-enabled chat interface called **Nexus**. It enables the rapid creation, management, and usage of AI agents with intelligent recommendations and minimal configuration. Ergon combines PydanticAI, LangChain, LangGraph, Anthropic, OpenAI and other LLM modules into an intuitive, conversation-driven experience.

## Key Features

- **Nexus Interface**: Memory-enabled AI assistant that helps you find and use agents
- **Intelligent Agent Recommendations**: Suggests the right agent based on your needs
- **Comprehensive Documentation System**: Index, search, and manage documentation
- **Zero-Config Setup**: Get started with minimal setup requirements
- **Unified Interface**: Consistent experience across CLI and web UI
- **Memory Capabilities**: Agents that remember past interactions
- **GitHub Integration**: Create GitHub-specific agents with repository access
- **Mail Integration**: Create email agents that can read and send email via Gmail and Outlook
- **Agent Management**: Intuitive tools for creating, organizing, and using agents

## Installation

### Local Installation

```bash
# Clone the repository
git clone https://github.com/ckoons/Ergon.git
cd Ergon

# Run the setup script
./setup.sh

# Activate the virtual environment
source venv/bin/activate

# Start the Nexus UI
agenteer ui

# Or use the wrapper script for cleaner output
./run_chatbot

# Or use the CLI
ergon create -n "my_agent" -d "A weather agent that fetches forecast data"
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build --platform linux/arm64 -t ergon .  # For Apple Silicon Macs
docker build --platform linux/amd64 -t ergon .  # For Intel/AMD systems
docker run -p 8501:8501 -p 8000:8000 ergon
```

> **Note for Apple Silicon Mac users**: Be sure to include the `--platform linux/arm64` flag when building and running Docker images to ensure compatibility.

### Documentation Preloading

Ergon offers built-in documentation preloading to enhance agent capabilities. There are several ways to preload documentation:

1. **Via the UI (Recommended)**: 
   Navigate to the Documentation or Web Search pages in the UI. If no documentation is found, you'll see a "Preload Essential Documentation" button that will automatically crawl and index documentation from Pydantic, LangChain, LangGraph, and Anthropic.

2. **Using the CLI**:
   ```bash
   # Preload all documentation sources
   ergon preload-docs

   # Preload a specific source
   ergon preload-docs --source pydantic
   ergon preload-docs --source langchain
   ergon preload-docs --source langgraph
   ergon preload-docs --source anthropic

   # Customize crawling settings
   ergon preload-docs --max-pages 500 --max-depth 4 --timeout 300
   ```

3. **With Docker**:
   ```bash
   # Preload all documentation sources
   docker run --platform linux/arm64 ergon preload-docs  # For Apple Silicon Macs
   docker run --platform linux/amd64 ergon preload-docs  # For Intel/AMD systems

   # Preload a specific source
   docker run --platform linux/arm64 ergon preload-docs --source langchain  # For Apple Silicon
   docker run --platform linux/arm64 ergon preload-docs --source langgraph  # For Apple Silicon
   ```

The preloaded documentation enables agents to leverage knowledge from these frameworks when responding to queries, making them more effective for framework-specific tasks.

Ergon automatically caches documentation for faster preloading in future sessions. Cached documentation is stored in the `vector_store/doc_cache` directory and is valid for 7 days, after which it will be refreshed automatically. This ensures your documentation stays current while minimizing network usage.

## Requirements

- Python 3.10+
- No external services required (uses SQLite by default)
- LLM API key (supports Claude, OpenAI, or local models via Ollama)

## UI Overview

The Ergon UI is designed to be intuitive and streamlined:

- **Nexus**: Memory-enabled AI assistant for finding and using agents
- **My Agents**: Browse, organize, and manage your created agents
- **Create Agent**: Form to create new agents with different capabilities
- **Documentation**: Preload, search, and manage documentation resources

## Architecture

Ergon consists of several core components:

1. **Core Engine**: Agent generation and execution logic
2. **Local Database**: SQLite-based storage for agents and sessions
3. **Vector Store**: FAISS-based document embedding and retrieval
4. **UI**: Streamlit-based web interface 
5. **CLI**: Command-line interface for automation and scripting
6. **API**: REST API for integration with other tools
7. **Documentation Crawler**: Tools for indexing documentation

## Configuration

Ergon uses a hierarchical configuration system with environment variables loaded from multiple files in the following priority order:

1. `.env.owner`: Highest priority, personal settings not checked into version control
2. `.env.local`: Middle priority, machine-specific settings not checked into version control 
3. `.env`: Lowest priority, base configuration shared by all users

Values in earlier files override those in later files. All files are loaded, creating a cascading configuration system.

### Authentication Configuration

Ergon includes a configurable authentication system controlled via the `ERGON_AUTHENTICATION` environment variable:

- `ERGON_AUTHENTICATION=true` (default): User authentication is required
- `ERGON_AUTHENTICATION=false`: Authentication is bypassed (useful for testing)

You can set this variable in any of the environment files or on the command line:

```bash
# Run with authentication disabled
ERGON_AUTHENTICATION=false ergon ui

# Run tests without authentication prompts
ERGON_AUTHENTICATION=false pytest tests/
```

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

# Authentication settings
ERGON_AUTHENTICATION=true  # Set to false to disable authentication

# Application settings
LOG_LEVEL="INFO"
DEBUG=false
```

## Working with Agents

Ergon provides a unified interface for creating, running, and managing AI agents through both the CLI and web UI.

### Creating Agents

```bash
# Create a standard agent
ergon create -n "MyAgent" -d "Description of the agent" -t standard

# Create a GitHub agent
ergon create -n "GitHubAgent" -d "GitHub repository manager" -t github

# Create a Mail agent
ergon create -n "MailAgent" -d "Email management assistant" -t mail
```

### Running Agents

There are several ways to run your agents:

```bash
# List available agents
ergon list

# Run an agent by ID
ergon run 3 -i "Your input here"

# Run an agent by name (more human-friendly)
ergon run "MyAgent" -i "Your input here"

# Run an agent in interactive mode (conversation)
ergon run "MyAgent" --interactive

# Run an agent with a timeout (30 seconds)
ergon run "GitHubAgent" -i "Your input here" --timeout 30

# Set timeout action (log, alarm, or kill)
ergon run "MailAgent" -i "Your input here" --timeout 30 --timeout-action alarm
```

### Agent Timeout Management

Ergon provides built-in timeout functionality to monitor and control agent executions:

#### Timeout Options

- `--timeout <seconds>`: Set a maximum execution time in seconds
- `--timeout-action <action>`: Specify what happens when timeout occurs:
  - `log`: Record timeout in logs and return a gentle message (default)
  - `alarm`: Record timeout and return a more prominent warning message
  - `kill`: Terminate the agent execution and return an error message

#### Use Cases

- **Resource Management**: Prevent runaway agents from consuming excessive resources
- **Performance Monitoring**: Track how long agents take to complete tasks
- **Workflow Orchestration**: Ensure batch operations complete within time constraints
- **Production Reliability**: Implement circuit breakers for mission-critical agent tasks

#### Examples

```bash
# Set a 30-second timeout with default "log" action
ergon run "ResearchAgent" -i "Research quantum computing" --timeout 30

# Use "alarm" action to get a more noticeable timeout warning
ergon run "DataAgent" -i "Analyze this dataset" --timeout 60 --timeout-action alarm

# Use "kill" action to forcibly terminate long-running operations
ergon run "ComplexAgent" -i "Complex task" --timeout 120 --timeout-action kill
```

### Managing Agents

You can manage your agents with the following commands:

```bash
# List all agents
ergon list

# Delete an agent by ID (with confirmation prompt)
ergon delete 3

# Delete an agent by name (with confirmation prompt)
ergon delete "TestAgent"

# Force delete an agent without confirmation
ergon delete "MyAgent" --force
```

### Using the Nexus Interface

You can launch the Nexus interface to interact with your agents in an intuitive, conversation-driven experience:

```bash
# Start the UI (using the convenience script for cleaner output)
./run_chatbot

# Or use the standard command
ergon ui
```

The Nexus interface provides several ways to work with agents:

#### Conversational Agent Usage

1. Simply ask Nexus about your task or what you need help with
2. Nexus will recommend appropriate agents based on your request
3. Select the recommended agent from the sidebar
4. Continue your conversation with the selected agent

#### Memory-Enabled Experience

Ergon's Nexus features enhanced memory capabilities through integration with Engram (formerly ClaudeMemoryBridge):

```bash
# Create a new memory-enabled Nexus agent
ergon create -n "MemoryAgent" -d "Agent with enhanced memory capabilities" -t nexus

# Chat with the memory agent in interactive mode
ergon nexus "MemoryAgent" --interactive

# Single request with memory
ergon nexus "MemoryAgent" -i "Hello, do you remember me?"

# Disable memory for a specific interaction
ergon nexus "MemoryAgent" -i "This is a private question" --no-memory
```

The Nexus memory system offers:

- **Persistent Memory**: Information is remembered across different sessions
- **Category Organization**: Memories are organized by category (personal, projects, facts, etc.)
- **Importance Ranking**: 1-5 scoring system prioritizes critical information
- **Auto-categorization**: Content is automatically analyzed to determine category and importance
- **Rich Storage & Retrieval**: Optimized memory storage with tagging and metadata

The system works automatically when Engram is installed, but gracefully falls back to local file-based storage when unavailable. If you're migrating from ClaudeMemoryBridge to Engram, see our [migration guide](MIGRATION.md).

#### Special Commands

Nexus supports special commands to enhance your experience:

- **!rate**: Open the feature importance rating interface to provide feedback
- **!plan**: Generate and review implementation plans for features

#### Agent Management

The UI provides comprehensive agent management tools:

- **Creating Agents**: 
  - Use the "Create Agent" page for standard agent creation
  - Create specialized Nexus agents directly from the chat interface

- **Managing Agents**: The "My Agents" page provides:
  - Organized view of agents by type
  - One-click usage in Nexus
  - Agent deletion with confirmation

#### Documentation System

The documentation interface allows you to:

- Preload documentation from key frameworks (Pydantic, LangChain, LangGraph, Anthropic)
- Search indexed documentation using semantic search
- Add custom documentation from URLs or direct input
- Track documentation status and statistics

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
