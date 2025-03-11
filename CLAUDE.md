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

# Create a Mail agent
agenteer create -n "MailAgent" -d "Description" -t mail

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
   
   # For LangGraph projects
   agenteer preload-docs --source langgraph --max-pages 300
   
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

## Latest Development Updates (March 11, 2025)

### Key Accomplishments

1. **Mail Agent Configuration**
   - Fixed configuration by adding `config_path` attribute to Settings class
   - Added proper directory validation and creation
   - Set up foundation for Gmail and Outlook OAuth

2. **Agent Management**
   - Added `delete` command to CLI with interactive confirmation
   - Implemented cascading deletion of associated data (tools, files, executions)
   - Added delete button to UI with confirmation dialog

3. **Human-Friendly Agent Interface**
   - Enhanced CLI to work with agent names instead of just IDs
   - Added fuzzy matching for partial name matches
   - Implemented intelligent lookup fallbacks (ID → exact name → partial match)
   - Added comprehensive agent name logging for traceability

4. **Timeout Functionality**
   - Added timeout capability to agent runner with three actions:
     - `log`: Record timeout and return gentle message (default)
     - `alarm`: Record timeout and return prominent warning
     - `kill`: Terminate execution and return error message
   - Added performance metrics in logs (execution time, completion status)

### Mail Agent Status

As of the latest development cycle, we have:

1. **Feature Branch**: Currently implementing Phase 2 features
   - ✅ Added Microsoft Outlook/Microsoft 365 provider support
   - ✅ Implemented HTML email composition for both Gmail and Outlook
   - 🔄 Developing attachment handling capability
   - 🔄 Working on email threading and conversation view

2. **Merge Plan**:
   - Complete testing of Phase 1 functionality on main branch
   - Test current feature branch development (Outlook + HTML email)  
   - Complete and test remaining Phase 2 features
   - Merge feature branch to main

3. **Key File Structure**:
   - `agenteer/core/agents/mail/tools.py`: Tool definitions for agents
   - `agenteer/core/agents/mail/service.py`: Mail service abstraction
   - `agenteer/core/agents/mail/providers.py`: Provider implementations (Gmail, Outlook)
   - `agenteer/core/agents/generators/mail_generator.py`: Mail agent generation

4. **Known Issues**:
   - Gmail requires specific content type handling for HTML emails
   - Outlook authentication requires manual code entry (needs improved UX)
   - Need to implement more robust error handling for timeouts
   - Need better handling of message attachments

### UI Integration

The Mail Agent will have dedicated UI components for better user experience:

1. **Mail Agent Creation Page**
   - Form to create a new Mail Agent with options for:
     - Provider selection (Gmail, Outlook)
     - Custom name and description
     - Access level configuration
     - Template selection

2. **Mail Agent UI Components**
   - Inbox view with sorting/filtering
   - Message detail view with HTML rendering
   - Compose email interface with rich text editor
   - Settings panel for provider configuration

3. **Implementation Plan**
   ```python
   # UI route for Mail Agent in streamlit_app.py
   elif page == "Mail":
       st.title("Mail Agent")
       
       # Check if authenticated
       if not mail_service.is_authenticated():
           st.warning("Please authenticate with your email provider")
           provider = st.selectbox("Select Provider", ["Gmail", "Outlook"])
           if st.button("Authenticate"):
               auth_url = mail_service.get_auth_url(provider.lower())
               st.markdown(f"[Click here to authenticate]({auth_url})")
       else:
           # Show inbox
           tab1, tab2, tab3 = st.tabs(["Inbox", "Compose", "Settings"])
           
           with tab1:
               messages = mail_service.get_inbox_messages()
               display_inbox(messages)
               
           with tab2:
               compose_email_form()
               
           with tab3:
               mail_settings()
   ```

4. **Agent Interaction Flows**
   - **Basic Mail Reading Flow**:
     1. User asks "Show me my recent emails"
     2. Agent uses get_inbox tool
     3. Agent formats and displays email summary
     4. User can click to view full email or reply
     
   - **Email Composition Flow**:
     1. User asks "Send an email to person@example.com"
     2. Agent prompts for subject and body
     3. Agent confirms before sending
     4. Agent sends email and confirms delivery

## Testing Plan

### Mail Agent Testing Progress

We've successfully implemented and tested the following components:

#### Phase 1 Testing (Main Branch) - March 10, 2025
1. **Unit Tests Created and Passing:**
   - `test_mail_tools.py` - Verifying mail tool definitions, registration, and basic functionality
   - `test_mail_service.py` - Testing the mail service initialization and configuration
   - `test_gmail_integration.py` - Testing Gmail provider functionality (authentication, reading inbox, sending messages)
   - `test_html_emails.py` - Testing HTML email formatting capabilities
   - `test_mail_generator.py` - Testing mail agent generation

2. **Agent Creation Successful:**
   - Created "TestMailAgent" with mail agent type
   - Ready for OAuth authentication testing

3. **Next Steps:**
   - Set up proper Gmail API credentials for OAuth testing
   - Test the complete OAuth authentication flow
   - Verify inbox reading functionality with real Gmail account
   - Test sending and replying to emails

#### Phase 2 Testing (Feature Branch)
1. **Outlook/Microsoft 365 Tests**
   - OAuth authentication flow for Microsoft
   - Reading Outlook inbox
   - Sending emails via Outlook
   - Replying to messages
   - Searching Outlook emails

2. **HTML Email Tests**
   - Sending emails with HTML formatting
   - Testing content type handling
   - Verifying HTML rendering in received emails
   - Testing HTML in replies

3. **Pending Feature Tests** (To be implemented)
   - Attachment handling
   - Email threading/conversation view
   - Draft management
   - Move/delete operations
   - Enhanced folder management

#### Test Implementation Plan

We need to create the following test files in the `tests/agents/mail/` directory:

```
tests/
  agents/
    mail/
      __init__.py
      test_gmail_integration.py    # Tests for Gmail provider
      test_outlook_integration.py  # Tests for Outlook provider
      test_html_emails.py          # Tests for HTML email functionality
      test_mail_tools.py           # Tests for mail tool definitions and registration
      test_mail_service.py         # Tests for MailService abstraction layer
      conftest.py                  # Shared fixtures for mail tests
```

The test files should use pytest fixtures to mock the email providers and avoid making actual API calls during testing. For manual testing with real APIs, we'll need to create separate integration test scripts.

#### Test Environment Setup
```bash
# Clone the repository
git clone https://github.com/username/Agenteer.git
cd Agenteer

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Create test directory structure if it doesn't exist
mkdir -p tests/agents/mail

# Run tests once implemented
python -m pytest tests/agents/mail/test_mail_tools.py -v
python -m pytest tests/agents/mail/test_mail_service.py -v
python -m pytest tests/agents/mail/test_gmail_integration.py -v
python -m pytest tests/agents/mail/test_outlook_integration.py -v
python -m pytest tests/agents/mail/test_html_emails.py -v
```

#### Mock Testing vs. Real API Testing

For CI/CD pipelines, we'll use mock testing to avoid dependencies on external services. For development, we'll need to test with real email accounts:

1. **Mock Testing** (CI/CD-friendly)
   ```python
   # Example mock test for Gmail authentication
   def test_gmail_auth_flow(mocker):
       # Mock Gmail OAuth flow
       mock_flow = mocker.patch('google_auth_oauthlib.flow.InstalledAppFlow')
       mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_credentials
       
       # Test authentication
       provider = GmailProvider(credentials_file="test_creds.json")
       result = asyncio.run(provider.authenticate())
       
       assert result is True
       assert provider.credentials is not None
   ```

2. **Real API Testing** (Manual Development Testing)
   - Requires real Gmail/Outlook test accounts
   - Should be run manually, not in CI pipelines
   - Will need proper OAuth credentials configuration
   - Should clean up after tests (delete test emails, etc.)

## Development Roadmap

### Mail Agent Development Plan

We are implementing the mail agent in three phases:

#### Phase 1 (Completed)
- Basic Gmail integration with OAuth authentication
- Core mail operations (read, send, reply, search)
- Mail service abstraction layer
- Agent tools for LLM integration

#### Phase 2 (In Progress)
- ✅ Outlook/Microsoft 365 support
- ✅ HTML email composition
- Attachment handling (download/view)
- Email threading/conversation view
- Draft management (save/edit/send)
- Move/delete emails
- Better folder management

#### Phase 3 (Planned)
- Email templates
- Email analytics (response times, frequency)
- Auto-categorization
- Smart follow-up reminders
- Contact management integration
- Calendar integration for scheduling

### Pending Tests

#### Mail Agent Testing
- Gmail OAuth authentication flow
- Reading inbox messages
- Sending test emails
- Replying to messages
- Testing HTML email rendering
- Testing Outlook authentication
- Testing attachment handling (when implemented)

#### LangGraph Documentation
- Verify LangGraph documentation crawling
- Test LangGraph document retrieval
- Validate search accuracy for LangGraph content

### Commit Message Format

Always use this format for commit messages:
```
feat: Descriptive title for the changes

Design & Engineering Guidance:
- Bullet point describing key implementation details
- Another bullet point with important design decisions
- Additional context about the implementation

🤖 Generated with [Claude Code](https://claude.ai/code)
Designed & Engineering Guidance by Casey Koons <cskoons@gmail.com>
Co-Authored-By: Casey Koons <cskoons@gmail.com> & Claude <noreply@anthropic.com>
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