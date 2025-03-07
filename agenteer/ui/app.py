"""
Agenteer Streamlit UI Application
"""

import streamlit as st
import os
import json
import asyncio
from datetime import datetime
import time
from typing import Dict, List, Any, Optional
import uuid
import sys
import traceback
from sqlalchemy.sql.expression import func

# Add debug mode for easier troubleshooting
DEBUG = True

def debug(msg):
    """Print debug messages to stderr"""
    if DEBUG:
        print(f"DEBUG: {msg}", file=sys.stderr)

debug("Starting Agenteer UI application")

# Initialize session state with proper defaults
def initialize_session_state():
    """Initialize all required session state variables with defaults"""
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    if "selected_agent_id" not in st.session_state:
        st.session_state.selected_agent_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if "created_agent_id" not in st.session_state:
        st.session_state.created_agent_id = None
    if "navigation_action" not in st.session_state:
        st.session_state.navigation_action = None
    if "clear_activity" not in st.session_state:
        st.session_state.clear_activity = False
    if "last_crawl_time" not in st.session_state:
        st.session_state.last_crawl_time = None

# Call the initialization function
initialize_session_state()
debug(f"Current page: {st.session_state.page}")

# Functions for cleaner navigation
def navigate_to(page, **kwargs):
    """Navigate to a specific page with optional parameters"""
    st.session_state.page = page
    debug(f"Navigating to: {page}")
    
    # Store any additional parameters in session state
    for key, value in kwargs.items():
        st.session_state[key] = value
        debug(f"Setting session state {key}={value}")

# Import agenteer modules
debug("Importing modules...")
try:
    from agenteer.utils.config.settings import settings
    debug("Imported settings")
    from agenteer.core.database.engine import init_db, get_db_session
    debug("Imported database engine")
    from agenteer.core.database.models import Agent, AgentExecution, AgentMessage, AgentTool, AgentFile, DocumentationPage
    debug("Imported database models")
    from agenteer.core.agents.generator import AgentGenerator, generate_agent
    debug("Imported agent generator")
    from agenteer.core.agents.runner import AgentRunner
    debug("Imported agent runner")
    from agenteer.core.docs.crawler import crawl_pydantic_ai_docs, crawl_langchain_docs, crawl_anthropic_docs, crawl_all_docs
    debug("Imported document crawler")
    from agenteer.core.vector_store.faiss_store import FAISSDocumentStore
    debug("Imported vector store")
    from agenteer.core.llm.client import LLMClient
    debug("Imported LLM client")
except Exception as e:
    debug(f"Error importing modules: {str(e)}")
    debug(traceback.format_exc())

# Initialize the app
debug("Setting up Streamlit page config")
try:
    st.set_page_config(
        page_title="Agenteer",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    debug("Streamlit page config set successfully")
except Exception as e:
    debug(f"Error setting page config: {str(e)}")
    debug(traceback.format_exc())

# Initialize database if needed
debug("Checking if database exists")
try:
    db_path = settings.database_url.replace("sqlite:///", "")
    debug(f"Database path: {db_path}")
    if not os.path.exists(db_path):
        debug("Database does not exist, initializing...")
        with st.spinner("Initializing database..."):
            init_db()
        debug("Database initialized successfully")
        st.success("Database initialized successfully!")
    else:
        debug("Database already exists")
except Exception as e:
    debug(f"Error initializing database: {str(e)}")
    debug(traceback.format_exc())
    st.error(f"Error initializing database: {str(e)}")

# Define sidebar
st.sidebar.title("Agenteer")
st.sidebar.markdown("AI Agent Builder")

# Navigation
page_options = ["Home", "Create Agent", "My Agents", "Documentation", "Crawl", "Settings"]
current_page_index = page_options.index(st.session_state.page) if st.session_state.page in page_options else 0

selected_page = st.sidebar.selectbox(
    "Navigation",
    page_options,
    index=current_page_index,
    key="sidebar_nav"
)

# Handle navigation from sidebar
if selected_page != st.session_state.page:
    navigate_to(selected_page)
    # Don't use experimental_rerun here, let Streamlit handle the rerun naturally

st.sidebar.markdown("---")
st.sidebar.markdown("### LLM Status")

if settings.has_openai:
    st.sidebar.success("OpenAI API: Connected")
else:
    st.sidebar.warning("OpenAI API: Not configured")

if settings.has_anthropic:
    st.sidebar.success("Anthropic API: Connected")
else:
    st.sidebar.warning("Anthropic API: Not configured")

if settings.has_ollama:
    st.sidebar.success("Ollama: Connected")
else:
    st.sidebar.warning("Ollama: Not available")

# Render the appropriate page content based on session state
debug(f"Rendering page: {st.session_state.page}")

# Check if there's a pending navigation action
if st.session_state.navigation_action:
    debug(f"Executing navigation action: {st.session_state.navigation_action}")
    action = st.session_state.navigation_action
    st.session_state.navigation_action = None
    
    if action == "go_to_my_agents_after_create" and st.session_state.created_agent_id:
        navigate_to("My Agents", selected_agent_id=st.session_state.created_agent_id)
    elif action == "refresh_after_crawl":
        # Just clear the action, no need to navigate
        debug("Refreshing after document crawl")
    elif action == "db_reset_complete":
        st.success("Database was reset successfully. Starting with a fresh environment.")
    elif action == "cancel_db_reset":
        debug("Database reset canceled")

# Home page
if st.session_state.page == "Home":
    st.title("Welcome to Agenteer")
    
    st.markdown("""
    Agenteer is a streamlined AI agent builder with minimal configuration.
    
    ### Get Started
    
    - **Create Agent**: Create a new AI agent from scratch
    - **My Agents**: View and interact with your existing agents
    - **Documentation**: Manage documentation for agent creation
    - **Settings**: Configure Agenteer settings
    
    ### System Status
    """)
    
    # Display status information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Database")
        st.info(f"Location: {settings.database_url}")
        
        with get_db_session() as db:
            agent_count = db.query(Agent).count()
            doc_count = db.query(DocumentationPage).count()
            st.metric("Agents", agent_count)
            st.metric("Documentation Pages", doc_count)
    
    with col2:
        st.subheader("Models")
        available_models = settings.available_models
        
        if available_models:
            st.success(f"{len(available_models)} model(s) available")
            st.selectbox("Available models:", available_models, key="home_model_select")
        else:
            st.warning("No models available. Please configure API keys.")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Create New Agent", use_container_width=True, key="home_create_btn"):
            navigate_to("Create Agent")
    
    with col2:
        if st.button("Browse Agents", use_container_width=True, key="home_browse_btn"):
            navigate_to("My Agents")
    
    with col3:
        if st.button("Manage Documentation", use_container_width=True, key="home_docs_btn"):
            navigate_to("Documentation")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Add a Clear button for recent activity
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Clear Activity", key="clear_activity_btn"):
            # We don't actually delete from the database, just clear the UI display
            st.session_state.clear_activity = True
            
    # Check if we should show activity
    if not hasattr(st.session_state, "clear_activity") or not st.session_state.clear_activity:
        with get_db_session() as db:
            recent_executions = (
                db.query(AgentExecution)
                .order_by(AgentExecution.started_at.desc())
                .limit(5)
                .all()
        )
        
        if not recent_executions:
            st.info("No recent activity. Create an agent and start interacting with it!")
        else:
            for execution in recent_executions:
                agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
                
                if agent:
                    with st.expander(f"{agent.name} - {execution.started_at.strftime('%Y-%m-%d %H:%M')}"):
                        messages = (
                            db.query(AgentMessage)
                            .filter(AgentMessage.execution_id == execution.id)
                            .order_by(AgentMessage.timestamp)
                            .all()
                        )
                        
                        for message in messages:
                            if message.role == "user":
                                st.markdown(f"**User**: {message.content}")
                            elif message.role == "assistant":
                                st.markdown(f"**{agent.name}**: {message.content}")
                            elif message.role == "tool":
                                st.markdown(f"**Tool ({message.tool_name})**: {message.tool_output}")
    else:
        st.info("Activity log cleared. Create a new agent or run an existing one to see new activity.")
        # Add button to restore activity
        if st.button("Restore Activity"):
            st.session_state.clear_activity = False

# Create Agent page
elif st.session_state.page == "Create Agent":
    st.title("Create New Agent")
    
    with st.form("create_agent_form"):
        name = st.text_input("Agent Name", placeholder="my_weather_agent")
        description = st.text_area("Description", placeholder="A weather forecasting agent...")
        
        # Model selection
        available_models = settings.available_models
        if not available_models:
            st.error("No models available. Please configure API keys in Settings.")
            model = ""
        else:
            model = st.selectbox("Model", available_models)
        
        # Temperature
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1,
                              help="Higher values make the output more random, lower values more deterministic")
        
        # Advanced options
        with st.expander("Advanced Options"):
            # Agent type selection
            agent_type = st.selectbox(
                "Agent Type",
                ["Basic (Q&A)", "Tool-Using", "Web Browser", "Custom"]
            )
            
            # Tools section (conditionally shown)
            tools_list = []
            if agent_type != "Basic (Q&A)":
                st.subheader("Tools")
                
                # Built-in tool templates
                tool_templates = {
                    "web_search": {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    "calculator": {
                        "name": "calculator",
                        "description": "Perform a calculation",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "expression": {
                                    "type": "string",
                                    "description": "The mathematical expression to evaluate"
                                }
                            },
                            "required": ["expression"]
                        }
                    },
                    "weather": {
                        "name": "get_weather",
                        "description": "Get weather information for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The location to get weather for"
                                },
                                "units": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                    "description": "Temperature units"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                }
                
                # Add built-in tools
                st.subheader("Built-in Tools")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.checkbox("Web Search"):
                        tools_list.append(tool_templates["web_search"])
                
                with col2:
                    if st.checkbox("Calculator"):
                        tools_list.append(tool_templates["calculator"])
                
                with col3:
                    if st.checkbox("Weather"):
                        tools_list.append(tool_templates["weather"])
                
                # Custom tools
                st.subheader("Custom Tools")
                custom_tool_count = st.number_input("Number of custom tools", min_value=0, max_value=5, value=0)
                
                for i in range(custom_tool_count):
                    with st.container():
                        st.markdown(f"Tool {i+1}")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            tool_name = st.text_input(f"Tool {i+1} Name", key=f"tool_name_{i}")
                        
                        with col2:
                            tool_desc = st.text_input(f"Tool {i+1} Description", key=f"tool_desc_{i}")
                        
                        param_count = st.number_input(f"Number of parameters for Tool {i+1}", min_value=1, max_value=5, value=1, key=f"param_count_{i}")
                        
                        properties = {}
                        required = []
                        
                        for j in range(param_count):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                param_name = st.text_input(f"Parameter {j+1} Name", key=f"param_name_{i}_{j}")
                            
                            with col2:
                                param_type = st.selectbox(f"Parameter {j+1} Type", ["string", "number", "boolean"], key=f"param_type_{i}_{j}")
                            
                            with col3:
                                param_required = st.checkbox(f"Required?", value=True, key=f"param_required_{i}_{j}")
                            
                            param_desc = st.text_input(f"Parameter {j+1} Description", key=f"param_desc_{i}_{j}")
                            
                            if param_name:
                                properties[param_name] = {
                                    "type": param_type,
                                    "description": param_desc
                                }
                                
                                if param_required:
                                    required.append(param_name)
                        
                        if tool_name and properties:
                            tools_list.append({
                                "name": tool_name,
                                "description": tool_desc,
                                "parameters": {
                                    "type": "object",
                                    "properties": properties,
                                    "required": required
                                }
                            })
        
        submit = st.form_submit_button("Create Agent")
        
        if submit:
            if not name:
                st.error("Please provide a name for your agent.")
            elif not model:
                st.error("Please select a model for your agent.")
            else:
                with st.spinner("Creating agent..."):
                    try:
                        # Generate agent
                        agent_data = generate_agent(
                            name=name,
                            description=description or f"An AI assistant named {name}",
                            model_name=model,
                            temperature=temperature,
                            tools=tools_list if tools_list else None
                        )
                        
                        # Save agent to database
                        with get_db_session() as db:
                            agent = Agent(
                                name=agent_data["name"],
                                description=agent_data["description"],
                                model_name=model,
                                system_prompt=agent_data["system_prompt"]
                            )
                            db.add(agent)
                            db.commit()
                            db.refresh(agent)
                            
                            # Save agent files
                            for file_data in agent_data["files"]:
                                file = AgentFile(
                                    agent_id=agent.id,
                                    filename=file_data["filename"],
                                    file_type=file_data["file_type"],
                                    content=file_data["content"]
                                )
                                db.add(file)
                            
                            # Save agent tools
                            for tool_data in tools_list:
                                tool = AgentTool(
                                    agent_id=agent.id,
                                    name=tool_data["name"],
                                    description=tool_data.get("description", ""),
                                    function_def=json.dumps(tool_data)
                                )
                                db.add(tool)
                            
                            db.commit()
                        
                        st.success(f"Agent '{name}' created successfully with ID {agent.id}!")
                        
                        # Display agent details and next steps
                        st.markdown("## Agent Created Successfully")
                        st.markdown(f"### {name}")
                        st.markdown(f"*{description}*")
                        
                        with st.expander("System Prompt"):
                            st.code(agent_data["system_prompt"])
                        
                        if tools_list:
                            with st.expander("Tools"):
                                for tool in tools_list:
                                    st.markdown(f"**{tool['name']}**: {tool.get('description', '')}")
                        
                        st.markdown("### Next Steps")
                        st.markdown("1. Go to **My Agents** to chat with your new agent")
                        st.markdown("2. Review the generated files")
                        st.markdown("3. Test your agent with different queries")
                        
                        if st.button("Go to My Agents"):
                            # Store the agent ID and set up navigation to execute on next render
                            st.session_state.created_agent_id = agent.id
                            st.session_state.navigation_action = "go_to_my_agents_after_create"
                            navigate_to("My Agents", selected_agent_id=agent.id)
                            debug(f"Preparing navigation to My Agents with selected agent {agent.id}")
                            
                    except Exception as e:
                        st.error(f"Error creating agent: {str(e)}")

# My Agents page
elif st.session_state.page == "My Agents":
    st.title("My Agents")
    
    # Get agents from database
    with get_db_session() as db:
        agents = db.query(Agent).all()
    
    if not agents:
        st.info("No agents found. Create one in the **Create Agent** page.")
        
        if st.button("Create New Agent"):
            navigate_to("Create Agent")
    else:
        # Agent selection
        agent_options = {f"{agent.name} (ID: {agent.id})": agent.id for agent in agents}
        
        # Ensure the selected agent ID is valid and exists
        if not st.session_state.selected_agent_id or st.session_state.selected_agent_id not in agent_options.values():
            # Default to the first agent if the selected ID is invalid
            st.session_state.selected_agent_id = list(agent_options.values())[0]
        
        # Find the display name for the selected agent ID
        selected_agent_display = next(
            (name for name, agent_id in agent_options.items() 
             if agent_id == st.session_state.selected_agent_id),
            list(agent_options.keys())[0]
        )
        
        selected_agent_name = st.selectbox(
            "Select Agent",
            options=list(agent_options.keys()),
            index=list(agent_options.keys()).index(selected_agent_display),
            key="agent_selector"
        )
        
        # Update selected agent ID in session state
        selected_agent_id = agent_options[selected_agent_name]
        if selected_agent_id != st.session_state.selected_agent_id:
            st.session_state.selected_agent_id = selected_agent_id
            debug(f"Updated selected agent to: {selected_agent_id}")
        
        # Get selected agent
        with get_db_session() as db:
            agent = db.query(Agent).filter(Agent.id == selected_agent_id).first()
            
            if agent:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"## {agent.name}")
                    st.markdown(f"*{agent.description}*")
                
                with col2:
                    st.markdown(f"**Model**: {agent.model_name}")
                    st.markdown(f"**Created**: {agent.created_at.strftime('%Y-%m-%d %H:%M') if agent.created_at else 'Unknown'}")
                
                # Tabs for different agent views
                tabs = st.tabs(["Chat", "Files", "Tools", "Executions"])
                
                # Chat tab
                with tabs[0]:
                    # Initialize chat history in centralized session state
                    if agent.id not in st.session_state.chat_history:
                        st.session_state.chat_history[agent.id] = []
                    
                    # Display chat history
                    for message in st.session_state.chat_history[agent.id]:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])
                    
                    # Reset chat button
                    col1, col2 = st.columns([4, 1])
                    with col2:
                        if st.button("Reset Chat", key=f"reset_chat_{agent.id}"):
                            st.session_state.chat_history[agent.id] = []
                    
                    # Chat input
                    if prompt := st.chat_input(f"Message {agent.name}..."):
                        # Add user message to chat history
                        st.session_state.chat_history[agent.id].append({"role": "user", "content": prompt})
                        
                        # Display user message
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        
                        # Create execution record
                        execution = AgentExecution(agent_id=agent.id)
                        db.add(execution)
                        db.commit()
                        db.refresh(execution)
                        
                        # Record user message
                        user_message = AgentMessage(
                            execution_id=execution.id,
                            role="user",
                            content=prompt
                        )
                        db.add(user_message)
                        db.commit()
                        
                        # Create agent runner
                        runner = AgentRunner(agent=agent, execution_id=execution.id)
                        
                        # Run agent
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                response = runner.run(prompt)
                            st.markdown(response)
                        
                        # Add assistant message to chat history
                        st.session_state.chat_history[agent.id].append({"role": "assistant", "content": response})
                        
                        # Record assistant message
                        assistant_message = AgentMessage(
                            execution_id=execution.id,
                            role="assistant",
                            content=response
                        )
                        db.add(assistant_message)
                        
                        # Mark execution as completed
                        execution.completed_at = datetime.now()
                        execution.success = True
                        db.commit()
                
                # Files tab
                with tabs[1]:
                    files = db.query(AgentFile).filter(AgentFile.agent_id == agent.id).all()
                    
                    if not files:
                        st.info("No files found for this agent.")
                    else:
                        # Group files by type
                        file_groups = {}
                        for file in files:
                            if file.file_type not in file_groups:
                                file_groups[file.file_type] = []
                            file_groups[file.file_type].append(file)
                        
                        # Display files grouped by type
                        for file_type, file_list in file_groups.items():
                            st.subheader(f"{file_type.capitalize()} Files")
                            
                            for file in file_list:
                                with st.expander(file.filename):
                                    st.code(file.content, language=file_type if file_type in ["python", "markdown"] else None)
                
                # Tools tab
                with tabs[2]:
                    tools = db.query(AgentTool).filter(AgentTool.agent_id == agent.id).all()
                    
                    if not tools:
                        st.info("No tools found for this agent.")
                    else:
                        for tool in tools:
                            with st.expander(f"{tool.name}"):
                                st.markdown(f"**Description**: {tool.description}")
                                
                                try:
                                    tool_def = json.loads(tool.function_def)
                                    st.markdown("**Parameters**:")
                                    
                                    if "parameters" in tool_def and "properties" in tool_def["parameters"]:
                                        for param_name, param_def in tool_def["parameters"]["properties"].items():
                                            required = "Required" if "required" in tool_def["parameters"] and param_name in tool_def["parameters"]["required"] else "Optional"
                                            st.markdown(f"- `{param_name}` ({param_def.get('type', 'unknown')}): {param_def.get('description', '')} *{required}*")
                                    
                                    st.code(json.dumps(tool_def, indent=2), language="json")
                                except json.JSONDecodeError:
                                    st.error("Invalid tool definition JSON")
                
                # Executions tab
                with tabs[3]:
                    executions = (
                        db.query(AgentExecution)
                        .filter(AgentExecution.agent_id == agent.id)
                        .order_by(AgentExecution.started_at.desc())
                        .limit(10)
                        .all()
                    )
                    
                    if not executions:
                        st.info("No executions found for this agent.")
                    else:
                        for execution in executions:
                            status = "Completed" if execution.completed_at else "In Progress"
                            success = "Success" if execution.success else "Failed" if execution.success is not None else "Unknown"
                            
                            with st.expander(f"{execution.started_at.strftime('%Y-%m-%d %H:%M')} - {status} ({success})"):
                                messages = (
                                    db.query(AgentMessage)
                                    .filter(AgentMessage.execution_id == execution.id)
                                    .order_by(AgentMessage.timestamp)
                                    .all()
                                )
                                
                                if not messages:
                                    st.info("No messages found for this execution.")
                                else:
                                    for message in messages:
                                        if message.role == "user":
                                            st.markdown(f"**User**: {message.content}")
                                        elif message.role == "assistant":
                                            st.markdown(f"**{agent.name}**: {message.content}")
                                        elif message.role == "tool":
                                            st.markdown(f"**Tool ({message.tool_name})**:")
                                            st.markdown(f"Input: `{message.tool_input}`")
                                            st.markdown(f"Output: {message.tool_output}")

# Documentation page
elif st.session_state.page == "Documentation":
    st.title("Documentation Management")
    
    # Tabs for different documentation views
    tabs = st.tabs(["Search", "Crawl", "Browse"])
    
    # Search tab
    with tabs[0]:
        st.subheader("Search Documentation")
        
        search_query = st.text_input("Search Query")
        
        if search_query:
            with st.spinner("Searching..."):
                vector_store = FAISSDocumentStore()
                results = vector_store.search(search_query, top_k=5)
                
                if not results:
                    st.info("No results found. Try crawling some documentation first.")
                else:
                    for i, result in enumerate(results):
                        with st.expander(f"{i+1}. {result['metadata'].get('title', 'Untitled')} (Score: {result['score']:.2f})"):
                            st.markdown(f"**Source**: {result['metadata'].get('source', 'Unknown')}")
                            st.markdown(f"**URL**: {result['metadata'].get('url', 'Unknown')}")
                            st.markdown("**Content**:")
                            st.markdown(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
    
    # Crawl tab
    with tabs[1]:
        st.subheader("Crawl Documentation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            crawl_source = st.selectbox(
                "Documentation Source",
                ["All Sources", "Pydantic AI", "LangChain", "Anthropic"]
            )
            
            max_pages = st.slider("Maximum Pages", min_value=10, max_value=500, value=100, step=10)
        
        with col2:
            st.markdown("This will crawl documentation from the selected source and index it for use in agent generation.")
            st.markdown("**Note**: This process can take several minutes depending on the number of pages.")
            
            crawl_button = st.button("Start Crawling")
        
        if crawl_button:
            with st.spinner(f"Crawling {crawl_source} documentation..."):
                try:
                    if crawl_source == "All Sources":
                        pages_crawled = asyncio.run(crawl_all_docs())
                    elif crawl_source == "Pydantic AI":
                        pages_crawled = asyncio.run(crawl_pydantic_ai_docs())
                    elif crawl_source == "LangChain":
                        pages_crawled = asyncio.run(crawl_langchain_docs())
                    elif crawl_source == "Anthropic":
                        pages_crawled = asyncio.run(crawl_anthropic_docs())
                    
                    st.success(f"Successfully crawled {pages_crawled} pages from {crawl_source}!")
                    
                    # Set a flag to refresh this panel
                    st.session_state.navigation_action = "refresh_after_crawl"
                except Exception as e:
                    st.error(f"Error crawling documentation: {str(e)}")
        
        # Display documentation statistics
        with get_db_session() as db:
            total_docs = db.query(DocumentationPage).count()
            
            sources = (
                db.query(DocumentationPage.source, func.count(DocumentationPage.id))
                .group_by(DocumentationPage.source)
                .all()
            )
            
            st.markdown(f"**Total Documentation Pages**: {total_docs}")
            
            if sources:
                st.markdown("**Pages by Source**:")
                for source, count in sources:
                    st.markdown(f"- {source}: {count} pages")
    
    # Browse tab
    with tabs[2]:
        st.subheader("Browse Documentation")
        
        with get_db_session() as db:
            # Source filter
            sources = [
                r[0] for r in 
                db.query(DocumentationPage.source)
                .distinct()
                .all()
            ]
            
            selected_source = st.selectbox("Filter by Source", ["All Sources"] + sources)
            
            # Query for documents
            if selected_source == "All Sources":
                docs = (
                    db.query(DocumentationPage)
                    .order_by(DocumentationPage.title)
                    .limit(100)
                    .all()
                )
            else:
                docs = (
                    db.query(DocumentationPage)
                    .filter(DocumentationPage.source == selected_source)
                    .order_by(DocumentationPage.title)
                    .limit(100)
                    .all()
                )
            
            if not docs:
                st.info("No documentation found. Try crawling some documentation first.")
            else:
                for doc in docs:
                    with st.expander(doc.title or "Untitled"):
                        st.markdown(f"**Source**: {doc.source}")
                        st.markdown(f"**URL**: [{doc.url}]({doc.url})")
                        st.markdown("**Content**:")
                        st.markdown(doc.content[:500] + "..." if len(doc.content) > 500 else doc.content)

# Crawl page
elif st.session_state.page == "Crawl":
    st.title("Document Crawler")
    
    st.markdown("""
    The Document Crawler helps you gather and index external documentation to enhance your agents.
    Crawled documents are stored in the vector database and can be used for retrieval and context augmentation.
    """)
    
    # Crawl source selection
    crawl_source = st.selectbox(
        "Documentation Source",
        ["All Sources", "Pydantic AI", "LangChain", "Anthropic", "Custom URL"]
    )
    
    if crawl_source == "Custom URL":
        custom_url = st.text_input("Enter URL to crawl", placeholder="https://example.com/docs")
        st.info("Note: For custom URLs, you may need to specify additional crawl parameters.")
        
        base_url = st.text_input(
            "Base URL (optional)", 
            placeholder="https://example.com",
            help="The base URL to limit crawling scope. Leave empty to use the provided URL as base."
        )
    else:
        custom_url = None
        base_url = None
    
    # Crawl settings
    with st.expander("Crawl Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            max_pages = st.slider("Maximum Pages", 
                                 min_value=10, 
                                 max_value=500, 
                                 value=100, 
                                 step=10,
                                 help="Maximum number of pages to crawl")
            
            max_depth = st.slider("Maximum Depth", 
                                 min_value=1, 
                                 max_value=5, 
                                 value=3, 
                                 step=1,
                                 help="Maximum link depth to crawl")
        
        with col2:
            file_types = st.multiselect("File Types",
                                       ["html", "md", "pdf", "txt"],
                                       default=["html", "md"],
                                       help="Types of files to crawl and index")
            
            follow_links = st.checkbox("Follow External Links", 
                                      value=False,
                                      help="If enabled, the crawler will follow links to external domains")
    
    # Start crawling button
    if st.button("Start Crawling", type="primary"):
        with st.spinner(f"Crawling {crawl_source} documentation..."):
            try:
                if crawl_source == "All Sources":
                    pages_crawled = asyncio.run(crawl_all_docs(max_pages=max_pages))
                elif crawl_source == "Pydantic AI":
                    pages_crawled = asyncio.run(crawl_pydantic_ai_docs(max_pages=max_pages))
                elif crawl_source == "LangChain":
                    pages_crawled = asyncio.run(crawl_langchain_docs(max_pages=max_pages))
                elif crawl_source == "Anthropic":
                    pages_crawled = asyncio.run(crawl_anthropic_docs(max_pages=max_pages))
                elif crawl_source == "Custom URL" and custom_url:
                    # Custom URL crawling would need to be implemented
                    st.warning("Custom URL crawling is not yet implemented")
                    pages_crawled = 0
                else:
                    st.error("Please select a valid documentation source")
                    pages_crawled = 0
                
                if pages_crawled > 0:
                    st.success(f"Successfully crawled {pages_crawled} pages from {crawl_source}!")
                
                # Set a flag to refresh this panel
                st.session_state.navigation_action = "refresh_after_crawl"
            except Exception as e:
                st.error(f"Error crawling documentation: {str(e)}")
    
    # Display documentation statistics
    st.subheader("Document Statistics")
    with get_db_session() as db:
        total_docs = db.query(DocumentationPage).count()
        
        sources = (
            db.query(DocumentationPage.source, func.count(DocumentationPage.id))
            .group_by(DocumentationPage.source)
            .all()
        )
        
        st.markdown(f"**Total Documentation Pages**: {total_docs}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if sources:
                st.markdown("**Pages by Source**:")
                for source, count in sources:
                    st.markdown(f"- {source}: {count} pages")
        
        with col2:
            # Last crawl time would be stored in settings or database
            st.markdown("**Last Crawl**:")
            st.markdown("No recent crawl activity")

# Settings page
elif st.session_state.page == "Settings":
    st.title("Settings")
    
    # Tabs for different settings
    tabs = st.tabs(["API Keys", "Database", "Models", "Interface"])
    
    # API Keys tab
    with tabs[0]:
        st.header("API Keys")
        
        st.warning("⚠️ API keys are not saved in the database for security reasons. They are loaded from environment variables or `.env` files.")
        
        with st.form("api_keys_form"):
            openai_key = st.text_input(
                "OpenAI API Key",
                value=settings.openai_api_key or "",
                type="password",
                help="Your OpenAI API key for GPT models"
            )
            
            anthropic_key = st.text_input(
                "Anthropic API Key",
                value=settings.anthropic_api_key or "",
                type="password",
                help="Your Anthropic API key for Claude models"
            )
            
            ollama_url = st.text_input(
                "Ollama Base URL",
                value=settings.ollama_base_url,
                help="URL for your Ollama instance (local or remote)"
            )
            
            submit = st.form_submit_button("Save API Keys")
            
            if submit:
                st.info("To save API keys permanently, add them to your `.env` or `.env.owner` file.")
                
                # Show example .env content
                st.code(f"""# Add to .env or .env.owner file
OPENAI_API_KEY={openai_key}
ANTHROPIC_API_KEY={anthropic_key}
OLLAMA_BASE_URL={ollama_url}
""")
    
    # Database tab
    with tabs[1]:
        st.header("Database Settings")
        
        db_location = st.text_input(
            "Database Location",
            value=settings.database_url,
            disabled=True,
            help="Location of the SQLite database (read-only)"
        )
        
        vector_db_location = st.text_input(
            "Vector Database Location",
            value=settings.vector_db_path,
            disabled=True,
            help="Location of the vector database (read-only)"
        )
        
        # Database statistics
        with get_db_session() as db:
            agent_count = db.query(Agent).count()
            doc_count = db.query(DocumentationPage).count()
            execution_count = db.query(AgentExecution).count()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Agents", agent_count)
            
            with col2:
                st.metric("Documentation Pages", doc_count)
            
            with col3:
                st.metric("Agent Executions", execution_count)
        
        # Reset option
        with st.expander("Reset Database"):
            st.warning("⚠️ This will delete all agents, documentation, and execution history.")
            
            if st.button("Reset Database"):
                # Add a confirmation step
                st.error("Are you sure? This cannot be undone.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Yes, I'm sure"):
                        # Reset database
                        try:
                            # Remove database file
                            db_path = settings.database_url.replace("sqlite:///", "")
                            if os.path.exists(db_path):
                                os.remove(db_path)
                            
                            # Clear vector store
                            vector_store = FAISSDocumentStore()
                            vector_store.clear()
                            
                            # Reinitialize database
                            init_db()
                            
                            # Reset session state
                            st.session_state.chat_history = {}
                            st.session_state.selected_agent_id = None
                            st.session_state.created_agent_id = None
                            
                            # Set navigation action to return to Home
                            st.session_state.navigation_action = "db_reset_complete"
                            
                            st.success("Database reset successfully!")
                            navigate_to("Home")
                        except Exception as e:
                            st.error(f"Error resetting database: {str(e)}")
                
                with col2:
                    if st.button("No, cancel"):
                        # Clear the confirmation UI without using experimental_rerun
                        st.session_state.navigation_action = "cancel_db_reset"
                        navigate_to("Settings")
    
    # Models tab
    with tabs[2]:
        st.header("Model Settings")
        
        # Current model
        st.subheader("Default Model")
        current_model = settings.default_model
        st.markdown(f"**Current Default Model**: `{current_model}`")
        
        # Available models
        st.subheader("Available Models")
        available_models = settings.available_models
        
        if not available_models:
            st.warning("No models available. Please configure API keys.")
        else:
            for model in available_models:
                provider = "OpenAI" if "gpt" in model.lower() else "Anthropic" if "claude" in model.lower() else "Ollama"
                st.markdown(f"- `{model}` ({provider})")
        
        # Model settings in .env file
        st.subheader("Model Configuration")
        st.markdown("To change the default model, edit your `.env` or `.env.owner` file:")
        st.code("""# Add to .env or .env.owner file
DEFAULT_MODEL=claude-3-7-sonnet-20250219
USE_LOCAL_MODELS=false
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
""")
    
    # Interface tab
    with tabs[3]:
        st.header("Interface Settings")
        
        # Debug mode
        debug_mode = st.checkbox("Debug Mode", value=settings.debug)
        
        # Log level
        log_level = st.selectbox(
            "Log Level",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(settings.log_level.value)
        )
        
        if st.button("Save Interface Settings"):
            st.info("To save interface settings permanently, add them to your `.env` or `.env.owner` file:")
            
            st.code(f"""# Add to .env or .env.owner file
DEBUG={str(debug_mode).lower()}
LOG_LEVEL={log_level}
""")
