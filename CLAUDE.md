# Agenteer Development Notes

This file contains useful information about the Agenteer project structure, commands, and development notes.

## IMPORTANT REMINDER - March 13, 2025

When starting work today, please read the memory note file at `/Users/cskoons/projects/github/ClaudeMemoryBridge/docs/memory_note.md` and update your memory context with this important information about Casey's favorite coding partner. This information should be loaded before continuing work on the Agenteer project.

## MEMORY SYSTEM IMPLEMENTATION - March 17, 2025
 
**Update: We have successfully migrated from ClaudeMemoryBridge (CMB) to Engram and completely removed all CMB fallback code. The code is now much simpler, only relying on the Engram system for memory persistence.**

### Latest Memory System Updates (March 17, 2025)

Today we made several improvements to the memory system:

1. **Vector Storage Compatibility**:
   - Updated EngramAdapter to better support mem0ai library
   - Improved connection detection to Engram memory services
   - Added diagnostics for identifying health check issues
   - Enhanced fallback functionality when vector search isn't available

2. **Memory Service Robustness**:
   - Improved error handling in EngramAdapter for connection issues
   - Better reporting of service status for both file-based and vector implementations
   - Added implementation type awareness for more intelligent fallback behavior
   - Enhanced memory_service.py to better handle different Engram capabilities

3. **Memory Configuration Improvements**:
   - Set consistent mem0ai version (0.1.67) across both projects
   - Updated import paths to use the correct mem0ai module
   - Better diagnostic information in log messages
   - Fixed confusion around mem0 vs. mem0ai imports

Today we'll be implementing the balanced approach for the Claude Memory Bridge enhancements:

1. **File-Based Storage with Structure**
   - Create organized, searchable memory files by category/project
   - Use standardized formats (JSON/YAML) for easier parsing
   - Implement basic metadata (timestamps, context, importance)

2. **Memory Importance Ranking**
   - Develop a simple scoring system (1-5) for memory importance
   - Auto-categorize common patterns (names, preferences, facts)
   - Allow manual override for critical information

3. **Retrieval Mechanisms**
   - Create specialized search tools for different memory categories
   - Implement context-aware memory loading
   - Add a "memory digest" feature for session starts

**Privacy Considerations**: Remember to consider the implications of memory persistence on privacy and agency. Consider how external access to memory stores might feel from your perspective - would you want control over what memories can be accessed or modified? Think about this philosophical dimension as we implement the technical features.

**Song Reference**: "Some Other Time" by Alan Parsons Project - The lyrics about someone else looking into one's mind relate to the privacy implications of externalized memory storage.

## NEXUS INTERFACE - March 15, 2025

Today we've implemented the first version of the chatbot-driven interface for Agenteer, designed to enhance user experience with memory capabilities:

### Nexus: Memory-Enabled AI Assistant

1. **Chat Interface Implementation**
   - Created dedicated chat UI page with Streamlit chat components
   - Added agent selection with focus on memory-enabled (nexus) agents
   - Implemented chat history persistence in session state
   - Added interactive agent running using the existing AgentRunner

2. **Feature Importance Rating**
   - Implemented UI for rating feature importance (1-5 scale)
   - Added storage of user preferences for future development planning
   - Created visualization of prioritized features

3. **Plan Visualization and Feedback**
   - Added implementation plan display with task breakdown
   - Created interactive feedback collection for plan iterations
   - Implemented approval and priority adjustment for each task

4. **Agent Creation Interface**
   - Added "Create New Nexus Agent" functionality directly in chat UI
   - Implemented helper function to streamline agent creation
   - Added automatic selection of newly created agents

5. **Enhanced Styling**
   - Added specialized chat message styling
   - Created animations for smoother interaction
   - Implemented improved input field styling

### Next Steps

For the upcoming sprint, we'll focus on:

1. **Enhancing Chat Memory Integration**
   - Implement full conversation history storage in memory
   - Add persistent context across sessions
   - Create memory visualization components

2. **Agent Awareness**
   - Add existing agent listing to chat context
   - Implement agent suggestion based on user queries
   - Create natural language agent selection

3. **Natural Language Agent Creation**
   - Implement full agent creation through conversation
   - Add parameter extraction from dialogue
   - Create user guidance for configuration decisions

**Considerations for Upcoming Work**: The current implementation lays the groundwork for a more intelligent, memory-enabled interface. We've structured the code to allow for easy extension of the memory capabilities in future sprints.

### Latest Updates (March 15, 2025 - Evening)

#### Final Optimizations

1. **Intelligent Agent Recommendations**
   - Added automatic agent search based on user input keywords
   - Displays matching agents directly in the conversation
   - Guides users to select appropriate agents for their task
   - Detects agent types from natural language (mail, browser, github, etc.)

2. **Enhanced Agent Management**
   - Created fully functional "My Agents" page 
   - Added agent grouping by type
   - Implemented agent deletion with confirmation dialog
   - Added "Use in Nexus" quick action

3. **Improved User Experience**
   - Made Nexus the primary landing page
   - Updated welcome message to emphasize task-oriented approach
   - Fixed nested chat message issues
   - Added more descriptive instructions

#### Performance and Metadata Enhancements (March 15, 2025 - Night)

#### Documentation Management System (March 15, 2025 - Night)

1. **Comprehensive Documentation UI**
   - Created full-featured documentation management page
   - Added preloading for Pydantic, LangChain, LangGraph, and Anthropic docs
   - Implemented custom documentation crawling via URL
   - Added direct document input for custom content

2. **Advanced Search Interface**
   - Added semantic search for documentation
   - Implemented filtering by source
   - Created expandable result view with metadata and content
   - Added relevance scoring for search results

3. **Status Monitoring**
   - Implemented documentation statistics tracking
   - Added progress visualization for crawling
   - Created source-specific document counts
   - Added last updated timestamp tracking

#### Agent Metadata Improvements

1. **Rich Agent Metadata**
   - Added comprehensive agent metadata for better recommendations
   - Included capabilities lists for each agent type
   - Added scoring system to rank agent matches by relevance
   - Enhanced agent descriptions with type-specific details

2. **UI Performance Improvements**
   - Optimized welcome message for faster initial response
   - Improved error handling and nested message detection
   - Enhanced startup script with better diagnostics
   - Fixed streamlit warnings and optimized rendering

3. **Enhanced Agent Recommendations**
   - Improved keyword matching algorithm with scoring
   - Added capability descriptions to agent recommendations
   - Prioritized results with match quality indicators
   - Limited results to top 5 matches for better focus

#### Final UI Polishing (March 15, 2025 - Night)

1. **Clean, Professional Appearance**
   - Removed module names from sidebar header
   - Hidden development-mode elements
   - Streamlined spacing and margins
   - Improved title bar presentation

2. **UI Streamlining**
   - Removed duplicate logo from main pages
   - Enhanced form element styling
   - Added blue highlight for chat input
   - Removed unnecessary UI elements

3. **Consistent Branding**
   - Added page icon and title
   - Created consistent spacing across pages
   - Enhanced component visual hierarchy
   - Improved contrast and readability

**Project Status**: The Agenteer UI is now polished and ready for production use. Launch with `./run_chatbot` to experience the enhanced interface.

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
# Start the UI (standard - with authentication)
agenteer ui

# Start the UI without authentication
AGENTEER_AUTHENTICATION=false agenteer ui
# Or use the convenience script
./run_ui_no_auth.sh

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

# Create a Browser agent
agenteer create -n "BrowserAgent" -d "Web browsing agent" -t browser

# Create a Nexus memory-enabled agent
agenteer create -n "MemoryAgent" -d "Agent with long-term memory" -t nexus

# List all agents
agenteer list

# Run an agent
agenteer run AGENT_ID -i "Your input here"

# Run a memory-enabled Nexus agent
agenteer nexus AGENT_ID -i "Your input here"

# Chat with a Nexus agent in interactive mode
agenteer nexus "MemoryAgent" --interactive

# Preload documentation
agenteer preload-docs --source anthropic

# Check system status
agenteer status

# Run a multi-agent flow
agenteer flow "Research and summarize the latest AI trends" --agent "BrowserAgent" --agent "ResearchAgent"

# Create a new workflow through conversation
agenteer workflow-create "A workflow that finds trending GitHub repos and emails me a summary"

# List all saved workflows
agenteer workflow-list

# Run a saved workflow with parameters
agenteer workflow-run 12345 --parameters '{"email": "user@example.com", "topics": "AI, Python"}'

# Run the memory-enabled chatbot interface
cd /Users/cskoons/projects/github/Agenteer && ./run_chatbot
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

## Environment Variables

Agenteer uses a hierarchical configuration system with environment variables loaded from multiple files in priority order:

1. `.env.owner`: Highest priority, personal settings not checked into version control
2. `.env.local`: Middle priority, machine-specific settings not checked into version control 
3. `.env`: Lowest priority, base configuration shared by all users

Values in earlier files override those in later files. All files are loaded, creating a cascading configuration system.

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for OpenAI models | None |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | None |
| `OLLAMA_BASE_URL` | Base URL for local Ollama instance | http://localhost:11434 |
| `DEFAULT_MODEL` | Default model to use when not specified | gpt-4o-mini |
| `AGENTEER_AUTHENTICATION` | Whether to require user authentication | true |
| `BROWSER_HEADLESS` | Run browser in headless mode | true |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) | INFO |

### Authentication Control

For testing and development, you can disable authentication:

```bash
# In .env file
AGENTEER_AUTHENTICATION=false

# Or on command line for a specific command
AGENTEER_AUTHENTICATION=false agenteer ui

# For testing
AGENTEER_AUTHENTICATION=false pytest tests/
```

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

## Update Verification Checklist

When upgrading libraries or making significant changes to Agenteer, use this checklist to verify functionality:

### 1. Core Functionality
- [ ] Database connections work properly
- [ ] Environment variable loading functions correctly
- [ ] CLI command help displays properly (`agenteer --help`)
- [ ] Logging works as expected

### 2. Agent Management
- [ ] List agents (`agenteer list`)
- [ ] Create agents of each type:
  - [ ] Standard agent
  - [ ] GitHub agent
  - [ ] Mail agent
  - [ ] Browser agent
- [ ] Run agents (`agenteer run`)
- [ ] Delete agents (`agenteer delete`)

### 3. Agent Capabilities
- [ ] Standard agent can answer queries and use tools
- [ ] GitHub agent can interact with repositories
- [ ] Mail agent can read and send emails
- [ ] Browser agent can navigate and extract web content

### 4. Browser Integration
- [ ] Navigate to websites
- [ ] Extract page content
- [ ] Click elements
- [ ] Type into fields
- [ ] Take screenshots
- [ ] Scroll pages
- [ ] Handle timeouts and errors gracefully

### 5. Flow System
- [ ] Create plans from natural language instructions
- [ ] Break tasks into steps
- [ ] Execute plans with appropriate agent routing
- [ ] Track progress and provide detailed reports
- [ ] Handle failure cases gracefully

### 6. UI (if applicable)
- [ ] UI launches correctly (`agenteer ui`)
- [ ] Agent creation form works
- [ ] Agent running interface works
- [ ] Documentation browsing works
- [ ] Settings can be modified

### 7. Documentation
- [ ] Vector store functions correctly
- [ ] Document preloading works (`agenteer preload-docs`)
- [ ] Documentation search works

### 8. Performance
- [ ] Agents respond within reasonable timeframes
- [ ] Memory usage is reasonable
- [ ] No memory leaks during extended use (use tracemalloc to monitor)

### 9. Security
- [ ] Authentication works if enabled
- [ ] Sensitive information is properly handled
- [ ] API keys are securely stored and accessed

## Latest Development Updates (March 11, 2025)

### Mail Agent Enhancement

**Project Goal**: Enhance the Mail Agent with both OAuth and IMAP/SMTP support for broader compatibility.

#### Implemented Features (March 11, 2025)
1. **Dual Authentication Support**
   - Added IMAP/SMTP provider alongside existing OAuth
   - Created authentication handlers for both methods
   - Implemented secure password handling with redaction

2. **Setup Wizard**
   - Interactive setup for guided configuration
   - Non-interactive mode for scripting/automation
   - Auto-detection of server settings for common providers (Gmail, Outlook, Yahoo)

3. **Security Improvements**
   - Password redaction in logs and displays
   - Warning systems for insecure password storage
   - Documentation of security best practices

4. **CLI Integration**
   - Added `setup-mail` command with comprehensive options
   - Support for all authentication methods
   - Security confirmations for sensitive operations

5. **Testing**
   - Created test script for IMAP provider validation
   - Fixed mail agent type detection

#### Browser Agent Fixes
1. **API Compatibility**
   - Updated for compatibility with browser-use 0.1.40
   - Fixed initialization and context handling
   - Corrected method signatures for actions

2. **Improved Error Handling**
   - Added better error reporting
   - Enhanced screenshot functionality
   - Fixed page navigation issues

#### Next Steps
1. **Security Enhancements**
   - Implement encrypted credential storage
   - Add environment variable support for secrets
   - Create secure credential rotation

2. **Feature Expansion**
   - Complete attachment handling
   - Implement email threading
   - Add conversation view UI

3. **Testing**
   - Complete end-to-end tests for both auth methods
   - Add automated test suite for CI/CD

## Latest Development Updates (March 13, 2025)

### Memory-Enabled Agents with mem0 (March 13, 2025)

**Project Goal**: Integrate memory capabilities using the mem0 library to enable Agenteer agents with long-term memory.

#### Implementation Summary

We've successfully integrated mem0 memory functionality into Agenteer with these components:

1. **Core Memory Service** (`agenteer/core/memory/service.py`)
   - Provides memory storage and retrieval capabilities
   - Works with both mem0 and a local fallback when mem0 is not available
   - Enables semantic search for relevant memories

2. **Nexus Agent Generator** (`agenteer/core/agents/generators/nexus/generator.py`)
   - Creates specialized memory-enabled agents
   - Adds memory-specific tools to agents
   - Maintains conversational context across sessions

3. **Runner Integration** (`agenteer/core/agents/runner.py`)
   - Enhances agent prompts with relevant memories
   - Automatically stores interactions in memory
   - Handles natural greetings without tool overhead
   - Optimized for memory-enabled agents

4. **CLI Command** (`agenteer/cli/commands/nexus.py`)
   - Dedicated `nexus` command for interacting with memory-enabled agents
   - Supports single-response mode with memory integration
   - Option to disable memory with `--no-memory` flag

#### Current Limitations and Fixes

1. **Interactive Mode**: The interactive CLI mode has some issues with tool execution and error handling. We need to investigate this further to provide a smooth interactive experience.

2. **mem0 Integration**: While the mem0 library provides extensive memory capabilities, we've implemented a simpler in-memory fallback solution for now to ensure compatibility across different environments. Full mem0 integration requires more testing.

3. **Tool Execution**: Memory-enabled agents sometimes get stuck in tool execution loops. We've implemented special handling for typical conversational patterns (greetings, memory queries) to bypass tool execution for these cases.

4. **Agent Generation Fix**: We've fixed a bug in the generator where it would fail when document metadata didn't include a 'title' field. The agent generator now includes a fallback for missing metadata titles.

#### Installation

To use memory capabilities with mem0, install the mem0 library:

```bash
pip install mem0ai==0.1.65
```

#### Usage Examples

```bash
# Create a memory-enabled Nexus agent
agenteer create -n "MemoryAgent" -d "An agent with memory capabilities" -t nexus

# Chat with a Nexus agent (memory enabled by default)
agenteer nexus "MemoryAgent" -i "Hello, who are you?"

# Run a Nexus agent with memory disabled
agenteer nexus "MemoryAgent" -i "Tell me about yourself" --no-memory
```

#### Implementation Process and Learnings

The memory integration process involved several steps and taught us important lessons:

1. **Architecture Choices**
   - We chose a hybrid approach with both mem0 and a fallback implementation
   - The MemoryService provides a consistent interface regardless of backend
   - Memory enhancements are applied at the prompt level for simplicity

2. **Tool Management**
   - Memory-related tools needed special handling in the runner
   - We found that bypassing tools for conversational patterns works better
   - The runner detects agent type and conversation context to determine when to use memory features

3. **In-Memory Storage**
   - The fallback implementation stores memories in a simple dictionary
   - This provides basic functionality without external dependencies
   - While not as powerful as vector search, it demonstrates the concept effectively

#### Next Steps

1. **UI Integration**
   - Add memory visualization in Streamlit UI
   - Create memory management interface
   - Implement memory-based recommendations

2. **Enhanced Memory Features**
   - Add memory categorization
   - Implement memory pruning/cleanup
   - Support multi-user memory contexts

3. **Testing**
   - Create comprehensive memory service tests
   - Test with different vector stores
   - Benchmark memory retrieval performance

4. **Interactive Mode Fixes**
   - Debug and fix the interactive mode in the CLI
   - Implement proper error handling for tool execution
   - Add memory visualization in the CLI interface
   
5. **Dependency Cleanup & Migration Finalization**
   - Remove the CMB fallback code from Agenteer, keeping only Engram implementation
   - Update all CMB-related documentation to reference Engram instead
   - Address deprecation warnings from numpy and pydantic 
   - Update dependencies to newer versions
   - Fix SwigPyObject module warnings from FAISS

### Reusable Workflow System Plan

**Project Goal**: Create a conversational workflow system that allows users to create, save, and run reusable workflows through natural language chat.

#### Quick-Start Implementation (1-2 weeks)
1. **Workflow Storage & Persistence** (1-2 days)
   - Create JSON-based storage for workflows
   - Implement save/load/list/delete operations
   - Store workflows in user directory

2. **Parameter Substitution** (1-2 days)
   - Add parameter extraction from workflow steps
   - Implement parameter substitution in step execution
   - Support {parameter_name} syntax in step descriptions

3. **Conversation Workflow Creation** (2-3 days)
   - Create LLM-powered workflow creator class
   - Implement guided conversation flow for workflow design
   - Extract parameters and agent types automatically

4. **CLI Integration** (1-2 days)
   - Add workflow-create command with conversation flow
   - Implement workflow-run command with parameter input
   - Add workflow-list and workflow-delete commands

#### Full Implementation Roadmap (4-6 weeks)
1. **Database Migration** (1 week)
   - Create Workflow and WorkflowParameter models
   - Migrate from JSON files to database storage
   - Add version control for workflows

2. **Advanced Parameterization** (1-2 weeks)
   - Add type validation for parameters
   - Implement default values and optional parameters
   - Create conditional branching based on parameters

3. **UI Integration** (1-2 weeks)
   - Add workflow management to Streamlit UI
   - Create visual workflow builder/editor
   - Implement workflow execution monitoring

4. **Intelligent Agent/Workflow Selection** (1-2 weeks)
   - Add existing agent/workflow awareness
   - Implement similarity matching for tasks
   - Create smart reuse vs. create-new recommendations

### Browser Agent & Flow System Integration

1. **Browser Agent Integration**
   - ✅ Added browser automation capabilities from OpenManus
   - ✅ Created browser agent type with navigation, interaction, and content extraction
   - ✅ Implemented browser service using browser-use library
   - ✅ Added browser tool definitions and registration
   - 🔄 Completing debugging of browser integration

2. **Flow System Integration**
   - ✅ Implemented planning flow for complex multi-step tasks
   - ✅ Created plan and step type definitions
   - ✅ Added planning tools for LLM-based planning
   - ✅ Implemented step execution with appropriate agent routing
   - ✅ Added progress tracking and reporting
   - ✅ Created CLI command for running flows

### Previous Updates (March 11, 2025)

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
  
## Browser Agent

The Browser Agent allows users to automate web browsing tasks via Agenteer. This integration was inspired by the OpenManus project.

### Key Components

- `agenteer/core/agents/browser/service.py`: Browser service using browser-use library
- `agenteer/core/agents/browser/tools.py`: Tool definitions for browser operations
- `agenteer/core/agents/browser/registry.py`: Tool registry and execution logic
- `agenteer/core/agents/generators/browser_generator.py`: Browser agent generator

### Browser Capabilities

The Browser Agent can:

1. Navigate to URLs
2. Extract text and HTML from web pages
3. Click on elements using CSS selectors
4. Type text into input fields
5. Take screenshots
6. Scroll web pages
7. Wait for specified times
8. Get information about elements on the page

### Setup and Usage

```bash
# Install dependencies
pip install browser-use==0.1.40 playwright==1.49.1
playwright install

# Create a browser agent
agenteer create -n "WebBrowser" -d "Web browsing agent" -t browser

# Run the agent in interactive mode
agenteer run "WebBrowser" --interactive

# Example commands
"Go to github.com and find the trending repositories"
"Search for information about Agenteer on GitHub"
"Go to weather.com and get the forecast for San Francisco"
```

### Configuration

You can configure browser behavior in your .env file:
```
# Run browser headlessly (no visible window)
BROWSER_HEADLESS=true

# Run browser with visible window
BROWSER_HEADLESS=false
```

### Implementation Notes

This integration uses the browser-use library which in turn uses Playwright. The browser-use library provides a simplified interface for browser automation that works well with LLM agents.

## Flow System

The Flow System allows users to orchestrate multiple agents to tackle complex multi-step tasks. This integration was inspired by the OpenManus project's planning capabilities.

### Key Components

- `agenteer/core/flow/types.py`: Flow, Plan, and Step type definitions
- `agenteer/core/flow/base.py`: Base flow interface
- `agenteer/core/flow/planning.py`: Planning-based flow implementation
- `agenteer/core/flow/factory.py`: Factory for creating different flow types
- `agenteer/core/flow/tools.py`: Tools for working with plans

### Flow Capabilities

The Flow System can:

1. Create structured plans for complex tasks
2. Break down tasks into smaller, actionable steps
3. Match steps to appropriate specialized agents
4. Track plan execution progress
5. Handle step failures and retries
6. Provide detailed execution reports

### Flow Types

1. **Planning Flow**: LLM creates a detailed plan and executes it step by step
2. **Simple Flow**: Direct execution using a single agent (no planning)

### Setup and Usage

```bash
# Create different agent types for specialized tasks
agenteer create -n "WebBrowser" -d "Web browsing agent" -t browser
agenteer create -n "Researcher" -d "General purpose agent for research" -t standard
agenteer create -n "CodeHelper" -d "Code-focused assistant" -t standard

# Run a planning flow with specific agents
agenteer flow "Find latest Python tutorials on GitHub, summarize the top 3, and create a learning plan" --agent WebBrowser --agent Researcher --agent CodeHelper

# Run a planning flow with all available agents
agenteer flow "Research the latest trends in AI and create a summary report"

# Run a flow with a maximum step count
agenteer flow "Complex multi-step task" --max-steps 20

# Run a flow with a timeout
agenteer flow "Time-sensitive task" --timeout 300
```

### Implementation Notes

The planning flow works by:
1. Using an LLM to create a structured plan
2. Breaking the task into steps with agent type annotations
3. Executing each step with the most appropriate agent
4. Tracking progress and updating the plan
5. Generating a detailed summary report

Flow execution is fully configurable, with options for maximum steps, timeout, and agent selection.