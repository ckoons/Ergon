"""
Agenteer Streamlit UI Application
"""

import streamlit as st
import os
from datetime import datetime

# Import agenteer modules
from agenteer.utils.config.settings import settings
from agenteer.core.database.engine import init_db, get_db_session
from agenteer.core.database.models import Agent, AgentExecution, AgentMessage
from agenteer.core.agents.generator import AgentGenerator
from agenteer.core.agents.runner import AgentRunner

# Initialize the app
st.set_page_config(
    page_title="Agenteer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database if needed
if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
    with st.spinner("Initializing database..."):
        init_db()
    st.success("Database initialized successfully\!")

# Define sidebar
st.sidebar.title("Agenteer")
st.sidebar.markdown("AI Agent Builder")

# Navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Home", "Create Agent", "My Agents", "Settings"]
)

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

# Home page
if page == "Home":
    st.title("Welcome to Agenteer")
    
    st.markdown("""
    Agenteer is a streamlined AI agent builder with minimal configuration.
    
    ### Get Started
    
    - **Create Agent**: Create a new AI agent from scratch
    - **My Agents**: View and interact with your existing agents
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
            st.metric("Agents", agent_count)
    
    with col2:
        st.subheader("Models")
        available_models = settings.available_models
        
        if available_models:
            st.success(f"{len(available_models)} model(s) available")
            st.json(available_models)
        else:
            st.warning("No models available. Please configure API keys.")

# Create Agent page
elif page == "Create Agent":
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
        
        # Agent type (simple placeholder for now)
        agent_type = st.selectbox(
            "Agent Type",
            ["Basic (Q&A)", "Tool-Using", "Web Browser", "Custom"]
        )
        
        submit = st.form_submit_button("Create Agent")
        
        if submit:
            if not name:
                st.error("Please provide a name for your agent.")
            elif not model:
                st.error("Please select a model for your agent.")
            else:
                with st.spinner("Creating agent..."):
                    # Initialize agent generator
                    generator = AgentGenerator(model=model)
                    
                    # Generate agent
                    agent_data = generator.generate(
                        name=name,
                        description=description or f"An AI assistant named {name}"
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
                
                st.success(f"Agent '{name}' created successfully with ID {agent.id}\!")
                st.markdown("Go to **My Agents** to start using your new agent.")

# My Agents page
elif page == "My Agents":
    st.title("My Agents")
    
    # Get agents from database
    with get_db_session() as db:
        agents = db.query(Agent).all()
    
    if not agents:
        st.info("No agents found. Create one in the **Create Agent** page.")
    else:
        # Display agents
        for agent in agents:
            with st.expander(f"{agent.name} (ID: {agent.id})"):
                st.markdown(f"**Description**: {agent.description}")
                st.markdown(f"**Model**: {agent.model_name}")
                st.markdown(f"**Created**: {agent.created_at.strftime('%Y-%m-%d %H:%M') if agent.created_at else 'Unknown'}")
                
                # Display system prompt
                with st.expander("System Prompt"):
                    st.code(agent.system_prompt)
                
                # Agent interaction
                st.markdown("### Chat with Agent")
                
                # Initialize chat history in session state
                if f"chat_history_{agent.id}" not in st.session_state:
                    st.session_state[f"chat_history_{agent.id}"] = []
                
                # Display chat history
                for message in st.session_state[f"chat_history_{agent.id}"]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                
                # Chat input
                if prompt := st.chat_input(f"Message {agent.name}..."):
                    # Add user message to chat history
                    st.session_state[f"chat_history_{agent.id}"].append({"role": "user", "content": prompt})
                    
                    # Display user message
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    # Create agent runner
                    runner = AgentRunner(agent=agent)
                    
                    # Run agent
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            response = runner.run(prompt)
                        st.markdown(response)
                    
                    # Add assistant message to chat history
                    st.session_state[f"chat_history_{agent.id}"].append({"role": "assistant", "content": response})

# Settings page
elif page == "Settings":
    st.title("Settings")
    
    # API Keys section
    st.header("API Keys")
    
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
            # TODO: Implement actual settings saving
            # This is a placeholder implementation
            st.success("Settings saved\! (Note: This is a placeholder, settings aren't actually saved yet)")
    
    # Database settings
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
    
    if st.button("Reset Database (Danger\!)"):
        # Add a confirmation step
        st.warning("This will delete all agents and data. Are you sure?")
        if st.button("Yes, I'm sure"):
            # TODO: Implement database reset
            st.error("Database reset not implemented yet.")
