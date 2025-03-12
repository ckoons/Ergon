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
        st.session_state.page = "Login"  # Start with login page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
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
    if "show_detail_for_execution" not in st.session_state:
        st.session_state.show_detail_for_execution = None

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
    
    # Add custom CSS for better form field visibility and styling
    st.markdown("""
    <style>
    /* Global text color - make everything bright white by default */
    body, p, span, div, h1, h2, h3, h4, h5, h6, label, button, input, textarea, select {
        color: #FFFFFF !important;
    }
    
    /* All Streamlit text elements to be white */
    .stTextInput, .stTextArea, .stSelectbox, .stSlider, .stCheckbox, 
    .stRadio, .stNumber, .stText, .stMarkdown, .stTitle, .stHeader, 
    .stSubheader, .stSuccess, .stInfo, .stWarning, .stError, .stTabs,
    .stDataFrame, .stTable {
        color: #FFFFFF !important;
    }
    
    /* Larger, bolder form labels across the app */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label, .stSlider > label {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;  /* Bright white for maximum visibility */
    }
    
    /* Improved contrast for info boxes */
    .stAlert > div {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    
    /* Better visibility for Streamlit text and markdown */
    .css-183lzff {  /* General text */
        color: #FFFFFF !important;
    }
    
    /* Make text in widgets more visible */
    .stSelectbox label, .stSlider label, .stText, .stMarkdown, 
    .stMarkdown p, .stMarkdown span, .stMarkdown div {
        color: #FFFFFF !important;
    }
    
    /* Make help text more visible */
    .stMarkdown a, small, .stSelectbox div small, .stTextInput div small, 
    .stNumberInput div small, .stTextArea div small {
        color: #FFFFFF !important;  /* White text for everything */
        opacity: 1 !important;
    }
    
    /* Bright sidebar text */
    .css-1544g2n {  /* Sidebar */
        color: white !important;
    }
    
    /* All sidebar content should be bright white */
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] .stMarkdown div,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stButton,
    [data-testid="stSidebar"] div {
        color: white !important;
    }
    
    /* Larger tab labels/buttons */
    .stTabs button[role="tab"] {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
    }
    
    /* Make the tab text more visible */
    .stTabs button[role="tab"] p {
        color: #FFFFFF !important;
    }
    
    /* Highlight the active tab more clearly - with blue to match buttons */
    .stTabs button[role="tab"][aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-bottom-color: #2196F3 !important; /* Blue to match buttons */
        border-bottom-width: 3px !important;
    }
    
    /* Better form field styling */
    .stTextInput > div[data-baseweb="input"] > div,
    .stTextArea > div[data-baseweb="textarea"] > div {
        border-width: 2px !important;
        color: #FFFFFF !important;
    }
    
    /* Input field text */
    input, textarea, .stTextInput input, .stTextArea textarea {
        color: #FFFFFF !important;
    }
    
    /* Focus styling for form fields */
    .stTextInput > div[data-baseweb="input"]:focus-within > div,
    .stTextArea > div[data-baseweb="textarea"]:focus-within > div {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 0 1px #ff4b4b !important;
    }
    
    /* Highlight active field */
    .streamlit-expanderHeader:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Make sure headers are especially visible */
    h1, h2, h3, .stTitle, .stHeader, .stSubheader {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    
    /* Improve button responsiveness */
    button[kind="primary"], button[kind="secondary"] {
        transition: all 0.2s ease !important;
    }
    
    /* Button hover effects to make them more responsive */
    button[kind="primary"]:hover {
        background-color: #F4511E !important; /* Darker orange on hover */
        transform: scale(1.03) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: #BF360C !important; /* Even darker orange on hover */
        transform: scale(1.03) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Make buttons stand out more - using light red/orange color scheme */
    button[kind="primary"] {
        background-color: #FF7043 !important; /* Light red/orange */
        color: white !important;
        font-weight: 600 !important;
    }
    
    button[kind="secondary"] {
        background-color: #E64A19 !important; /* Darker orange */
        color: white !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)
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

# Define sidebar - Remove header and use only the subtitle with bright white text
st.sidebar.markdown("<div style='font-size: 2em; font-weight: bold; margin-bottom: 20px; color: #FFFFFF;'>AI Agent Builder</div>", unsafe_allow_html=True)

# Add custom CSS for sidebar expander styling with different colors for each
st.sidebar.markdown("""
<style>
/* Style for all expander headers in the sidebar */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    margin-bottom: 0.5rem;
}

/* Base style for all expander headers */
[data-testid="stSidebar"] [data-testid="stExpander"] > div:first-child {
    border-radius: 4px !important;
    transition: background-color 0.3s ease !important;
    padding: 0.5rem !important;
}

/* Make expander label text white and bold */
[data-testid="stSidebar"] [data-testid="stExpander"] p {
    color: #FFFFFF !important;
    font-weight: bold !important;
    font-size: 1.1em !important;
}

/* Default style for buttons in sidebar */
[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #FF7043 !important; /* Light red/orange */
}

/* Button hover effects for sidebar */
[data-testid="stSidebar"] button[kind="primary"]:hover {
    background-color: #F4511E !important; /* Darker orange on hover */
}
</style>
""", unsafe_allow_html=True)

# Add logged in user info and logout button if authenticated
if st.session_state.authenticated:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.username = None
        credential_manager.logout()
        navigate_to("Login")
        st.rerun()

# Get counts for UI elements but don't show navigation control
with get_db_session() as db:
    agent_count = db.query(Agent).count()
    doc_count = db.query(DocumentationPage).count()

# Style for Navigation expander - Light Orange
st.markdown("""
<style>
/* Navigation expander - Light Orange */
[data-testid="stSidebar"] [data-testid="stExpander"]:nth-of-type(1) > div:first-child {
    background-color: #FF9800 !important; /* Light Orange */
}

/* Navigation expander hover - Brighter Orange */
[data-testid="stSidebar"] [data-testid="stExpander"]:nth-of-type(1) > div:first-child:hover {
    background-color: #FFA726 !important; /* Brighter Orange */
}
</style>
""", unsafe_allow_html=True)

# Only show navigation if authenticated
if st.session_state.authenticated:
    # Navigation dropdown in sidebar with clickable links and descriptions
    with st.sidebar.expander("Navigation"):
        # Agenteer Main page section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.button("▶", key="home_btn", help="Go to Main Page", type="primary")  # Blue button
        with col2:
            st.markdown("**Agenteer**")
            st.markdown("<span style='color:#FFFFFF; font-size:0.9em; font-weight:500;'>Main Page</span>", unsafe_allow_html=True)
        if st.session_state.get("home_btn"):
            navigate_to("Home")
    
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        # Create Agent section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.button("▶", key="create_agent_btn", help="Go to Create Agent", type="primary")  # Blue button
        with col2:
            st.markdown("**Create Agent**")
            st.markdown("<span style='color:#FFFFFF; font-size:0.9em; font-weight:500;'>Create a new AI agent from scratch</span>", unsafe_allow_html=True)
        if st.session_state.get("create_agent_btn"):
            navigate_to("Create Agent")
    
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        # My Agents section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.button("▶", key="my_agents_btn", help="Go to My Agents", type="primary")  # Blue button
        with col2:
            st.markdown("**Existing Agents**")
            st.markdown("<span style='color:#FFFFFF; font-size:0.9em; font-weight:500;'>View and interact with your existing agents</span>", unsafe_allow_html=True)
        if st.session_state.get("my_agents_btn"):
            navigate_to("My Agents")
        
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        # Documentation section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.button("▶", key="documentation_btn", help="Go to Documentation", type="primary")  # Blue button
        with col2:
            st.markdown("**Documentation**")
            st.markdown("<span style='color:#FFFFFF; font-size:0.9em; font-weight:500;'>Manage documentation for agent creation</span>", unsafe_allow_html=True)
        if st.session_state.get("documentation_btn"):
            navigate_to("Documentation")
    
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        # Web Search section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.button("▶", key="web_search_btn", help="Go to Web Search", type="primary")  # Blue button
        with col2:
            st.markdown("**Web Search**")
            st.markdown("<span style='color:#FFFFFF; font-size:0.9em; font-weight:500;'>Crawl and index web documentation</span>", unsafe_allow_html=True)
        if st.session_state.get("web_search_btn"):
            navigate_to("Web Search")
        
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
    
        # Settings section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.button("▶", key="settings_btn", help="Go to Settings", type="primary")  # Blue button
        with col2:
            st.markdown("**Settings**")
            st.markdown("<span style='color:#FFFFFF; font-size:0.9em; font-weight:500;'>Configure Agenteer settings</span>", unsafe_allow_html=True)
        if st.session_state.get("settings_btn"):
            navigate_to("Settings")

st.sidebar.markdown("---")
st.sidebar.markdown("### System Status")

# Style for Database expander - Light Blue
st.markdown("""
<style>
/* Database expander - Light Blue */
[data-testid="stSidebar"] [data-testid="stExpander"]:nth-of-type(2) > div:first-child {
    background-color: #2196F3 !important; /* Light Blue */
}

/* Database expander hover - Brighter Blue */
[data-testid="stSidebar"] [data-testid="stExpander"]:nth-of-type(2) > div:first-child:hover {
    background-color: #42A5F5 !important; /* Brighter Blue */
}
</style>
""", unsafe_allow_html=True)

# Database info
with st.sidebar.expander("Database"):
    st.info(f"Location: {settings.database_url}")
    st.metric("Agents", agent_count)
    st.metric("Documentation Pages", doc_count)

# Style for Models expander - Light Blue
st.markdown("""
<style>
/* Models expander - Light Blue */
[data-testid="stSidebar"] [data-testid="stExpander"]:nth-of-type(3) > div:first-child {
    background-color: #2196F3 !important; /* Light Blue */
}

/* Models expander hover - Brighter Blue */
[data-testid="stSidebar"] [data-testid="stExpander"]:nth-of-type(3) > div:first-child:hover {
    background-color: #42A5F5 !important; /* Brighter Blue */
}
</style>
""", unsafe_allow_html=True)

# Model info
with st.sidebar.expander("Models"):
    available_models = settings.available_models
    if available_models:
        st.success(f"{len(available_models)} model(s) available")
        st.selectbox("Available models:", available_models, key="sidebar_model_select")
    else:
        st.warning("No models available. Please configure API keys.")

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

# Import credential manager
try:
    from agenteer.utils.config.credentials import credential_manager
    debug("Imported credential manager")
except Exception as e:
    debug(f"Error importing credential manager: {str(e)}")
    debug(traceback.format_exc())

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

# Check if authentication is required via environment variable
if settings.require_authentication:
    # Authentication check - redirect to login if not authenticated
    if not st.session_state.authenticated and st.session_state.page != "Login":
        debug("User not authenticated, redirecting to login")
        st.session_state.page = "Login"
        st.rerun()
else:
    # Skip authentication if not required
    if not st.session_state.authenticated:
        debug("Authentication disabled via environment variable, auto-authenticating")
        st.session_state.authenticated = True
        st.session_state.username = "admin@example.com"
        if st.session_state.page == "Login":
            st.session_state.page = "Home"
            st.rerun()

# Login page
if st.session_state.page == "Login":
    st.title("Login to Agenteer")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if email and password:
                    # Authenticate user
                    if credential_manager.authenticate(email, password):
                        st.session_state.authenticated = True
                        st.session_state.username = email
                        st.session_state.page = "Home"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Please enter both email and password")
    
    with col2:
        with st.form("register_form"):
            st.subheader("Register")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if not new_email:
                    st.error("Please enter an email address")
                elif not new_password:
                    st.error("Password cannot be empty")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    # Register new user
                    if credential_manager.register(new_email, new_password):
                        st.success("Registration successful! You can now log in.")
                        st.session_state.page = "Login"
                        st.rerun()
                    else:
                        st.error("User already exists or registration failed")

# Home page
elif st.session_state.page == "Home":
    # Larger title without subtitle
    st.markdown("""
    <div style='margin-bottom: 25px;'>
        <h1 style='margin: 0; padding: 0; color: #FFFFFF; font-size: 3.5rem; font-weight: bold; text-align: center;'>Agenteer</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick actions directly under title with colored buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Create New Agent", 
                    use_container_width=True, 
                    key="home_create_btn",
                    type="primary"):  # Blue primary button
            navigate_to("Create Agent")
    
    with col2:
        if st.button("Existing Agents", 
                    use_container_width=True, 
                    key="home_browse_btn",
                    type="primary"):  # Changed to primary blue
            navigate_to("My Agents")
    
    with col3:
        if st.button("Documentation", 
                    use_container_width=True, 
                    key="home_docs_btn",
                    type="primary"):  # Changed to primary blue 
            navigate_to("Documentation")
            
    with col4:
        if st.button("Web Search", 
                    use_container_width=True, 
                    key="home_crawl_btn",
                    type="primary"):  # Blue primary button
            navigate_to("Web Search")
    
    # Styling for Recent Activity expander - Green
    st.markdown("""
    <style>
    /* Style for Recent Activity expander in main content */
    [data-testid="stExpander"] {
        margin-bottom: 1rem;
    }
    
    /* Recent Activity expander - Green */
    div:not([data-testid="stSidebar"]) [data-testid="stExpander"] > div:first-child {
        background-color: #4CAF50 !important; /* Green */
        border-radius: 4px !important;
        transition: background-color 0.3s ease !important;
        padding: 0.5rem !important;
    }
    
    /* Recent Activity expander hover - Brighter Green */
    div:not([data-testid="stSidebar"]) [data-testid="stExpander"] > div:first-child:hover {
        background-color: #66BB6A !important; /* Brighter Green */
    }
    
    /* Make expander label text white and bold */
    div:not([data-testid="stSidebar"]) [data-testid="stExpander"] p {
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 1.1em !important;
    }
    
    /* Keep all buttons inside main content orange */
    div:not([data-testid="stSidebar"]) button[kind="primary"] {
        background-color: #FF7043 !important; /* Light red/orange */
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Orange button hover effects */
    div:not([data-testid="stSidebar"]) button[kind="primary"]:hover {
        background-color: #F4511E !important; /* Darker orange on hover */
        transform: scale(1.03) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Recent activity section (closed by default, green with white title)
    with st.expander("Recent Activity", expanded=False):
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
                # Initialize session state for detailed view
                if "show_detail_for_execution" not in st.session_state:
                    st.session_state.show_detail_for_execution = None
                    
                # Check if a dialog is currently open, if not show the list
                if st.session_state.show_detail_for_execution is None:
                    for execution in recent_executions:
                        agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
                        
                        if agent:
                            # Create row for each execution with button and text
                            col1, col2 = st.columns([1, 5])
                            
                            with col1:
                                # Button to open detail dialog
                                btn_key = f"open_detail_{execution.id}"
                                if st.button("📋", key=btn_key, help="View Details"):
                                    st.session_state.show_detail_for_execution = execution.id
                                    st.rerun()
                            
                            with col2:
                                # Just show the title/date
                                st.markdown(f"**{agent.name}** - {execution.started_at.strftime('%Y-%m-%d %H:%M')}")
                            
                            # Add a divider
                            st.markdown("<hr style='margin: 5px 0px; border-width: 1px;'>", unsafe_allow_html=True)
                
                # If a detail dialog is open, show it as a "modal"
                else:
                    execution_id = st.session_state.show_detail_for_execution
                    execution = db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
                    
                    if execution:
                        agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
                        
                        if agent:
                            # Create a container that looks like a modal dialog
                            with st.container():
                                # Dialog header with title and close button
                                col1, col2 = st.columns([5, 1])
                                
                                with col1:
                                    st.markdown(f"## {agent.name} - {execution.started_at.strftime('%Y-%m-%d %H:%M')}")
                                
                                with col2:
                                    # Close button
                                    if st.button("❌ Close", type="primary"):
                                        st.session_state.show_detail_for_execution = None
                                        st.rerun()
                                
                                # Dialog content - all messages
                                messages = (
                                    db.query(AgentMessage)
                                    .filter(AgentMessage.execution_id == execution_id)
                                    .order_by(AgentMessage.timestamp)
                                    .all()
                                )
                                
                                st.markdown("### Conversation")
                                for message in messages:
                                    if message.role == "user":
                                        st.markdown(f"**User**: {message.content}")
                                    elif message.role == "assistant":
                                        st.markdown(f"**{agent.name}**: {message.content}")
                                    elif message.role == "tool":
                                        st.markdown(f"**Tool ({message.tool_name})**: {message.tool_output}")
                                
                                # Return button at bottom
                                st.button("Return to Activities", on_click=lambda: setattr(st.session_state, "show_detail_for_execution", None))

# Create Agent page
elif st.session_state.page == "Create Agent":
    st.title("Create Agent")
    
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

# My Agents page (renamed to Existing Agents for consistency)
elif st.session_state.page == "My Agents":
    st.title("Existing Agents")
    
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
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"## {agent.name}")
                    st.markdown(f"*{agent.description}*")
                
                with col2:
                    st.markdown(f"**Model**: {agent.model_name}")
                    st.markdown(f"**Created**: {agent.created_at.strftime('%Y-%m-%d %H:%M') if agent.created_at else 'Unknown'}")
                
                with col3:
                    # Delete agent button with confirmation
                    if st.button("🗑️ Delete Agent", key=f"delete_agent_{agent.id}", 
                                type="secondary", help="Delete this agent and all associated data"):
                        # Create confirmation dialog
                        confirm_delete = st.warning(f"Are you sure you want to delete '{agent.name}'? This cannot be undone.")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("Yes, Delete", key=f"confirm_delete_{agent.id}", type="primary"):
                                # Delete agent and associated data
                                try:
                                    # First delete messages (due to foreign key constraints)
                                    execution_ids = [row[0] for row in db.query(AgentExecution.id).filter(AgentExecution.agent_id == agent.id).all()]
                                    if execution_ids:
                                        db.query(AgentMessage).filter(AgentMessage.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                                    
                                    # Then delete executions
                                    db.query(AgentExecution).filter(AgentExecution.agent_id == agent.id).delete(synchronize_session=False)
                                    
                                    # Delete tools and files
                                    db.query(AgentTool).filter(AgentTool.agent_id == agent.id).delete(synchronize_session=False)
                                    db.query(AgentFile).filter(AgentFile.agent_id == agent.id).delete(synchronize_session=False)
                                    
                                    # Get agent name for success message
                                    agent_name = agent.name
                                    
                                    # Finally delete the agent
                                    db.query(Agent).filter(Agent.id == agent.id).delete(synchronize_session=False)
                                    
                                    # Commit changes
                                    db.commit()
                                    
                                    # Clear selected agent
                                    st.session_state.selected_agent_id = None
                                    
                                    # Show success message and refresh
                                    st.success(f"Agent '{agent_name}' successfully deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting agent: {str(e)}")
                        with col_no:
                            if st.button("Cancel", key=f"cancel_delete_{agent.id}", type="secondary"):
                                # Just refresh to hide the confirmation
                                st.rerun()
                
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
    st.title("Documentation")
    
    # Tabs for different documentation views
    tabs = st.tabs(["Search", "Crawl", "Browse"])
    
    # Search tab
    with tabs[0]:
        st.subheader("Search Documentation")
        
        # Check if we have any documentation
        with get_db_session() as db:
            total_docs = db.query(DocumentationPage).count()
        
        if total_docs == 0:
            st.warning("No documentation found in the database.")
            st.info("Go to the **Crawl** tab to preload documentation before searching.")
            
            # Add quick action button to preload docs
            if st.button("Preload Essential Documentation", 
                        type="primary",
                        help="Preload Pydantic, LangChain, and Anthropic documentation"):
                with st.spinner("Preloading documentation from Pydantic, LangChain, and Anthropic..."):
                    try:
                        # Run documentation preloading with longer timeout
                        pydantic_pages = asyncio.run(crawl_pydantic_ai_docs(
                            max_pages=300, max_depth=3, timeout=600  # 10 minute timeout
                        ))
                        st.success(f"Indexed {pydantic_pages} Pydantic documentation pages")
                        
                        langchain_pages = asyncio.run(crawl_langchain_docs(
                            max_pages=300, max_depth=3, timeout=600  # 10 minute timeout
                        ))
                        st.success(f"Indexed {langchain_pages} LangChain documentation pages")
                        
                        anthropic_pages = asyncio.run(crawl_anthropic_docs(
                            max_pages=300, max_depth=3, timeout=600  # 10 minute timeout
                        ))
                        st.success(f"Indexed {anthropic_pages} Anthropic documentation pages")
                        
                        total_pages = pydantic_pages + langchain_pages + anthropic_pages
                        st.success(f"Documentation preloading complete! Indexed {total_pages} pages.")
                        
                        # Set a flag to refresh this panel
                        st.session_state.navigation_action = "refresh_after_crawl"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error preloading documentation: {str(e)}")
        else:
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
            # Count total documentation
            total_docs = db.query(DocumentationPage).count()
            
            if total_docs == 0:
                st.warning("No documentation found in the database.")
                st.info("Go to the **Crawl** tab to preload documentation before browsing.")
                
                # Add quick action button to preload docs
                if st.button("Preload Essential Documentation", 
                            type="primary",
                            key="browse_preload_button",
                            help="Preload Pydantic, LangChain, and Anthropic documentation"):
                    with st.spinner("Preloading documentation from Pydantic, LangChain, and Anthropic..."):
                        try:
                            # Run documentation preloading with longer timeout
                            pydantic_pages = asyncio.run(crawl_pydantic_ai_docs(
                                max_pages=300, max_depth=3, timeout=600  # 10 minute timeout
                            ))
                            st.success(f"Indexed {pydantic_pages} Pydantic documentation pages")
                            
                            langchain_pages = asyncio.run(crawl_langchain_docs(
                                max_pages=300, max_depth=3, timeout=600  # 10 minute timeout
                            ))
                            st.success(f"Indexed {langchain_pages} LangChain documentation pages")
                            
                            anthropic_pages = asyncio.run(crawl_anthropic_docs(
                                max_pages=300, max_depth=3, timeout=600  # 10 minute timeout
                            ))
                            st.success(f"Indexed {anthropic_pages} Anthropic documentation pages")
                            
                            total_pages = pydantic_pages + langchain_pages + anthropic_pages
                            st.success(f"Documentation preloading complete! Indexed {total_pages} pages.")
                            
                            # Set a flag to refresh this panel
                            st.session_state.navigation_action = "refresh_after_crawl"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error preloading documentation: {str(e)}")
            else:
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
                    st.info("No documentation found for the selected source. Try selecting another source.")
                else:
                    for doc in docs:
                        with st.expander(doc.title or "Untitled"):
                            st.markdown(f"**Source**: {doc.source}")
                            st.markdown(f"**URL**: [{doc.url}]({doc.url})")
                            st.markdown("**Content**:")
                            st.markdown(doc.content[:500] + "..." if len(doc.content) > 500 else doc.content)

# Web Search page
elif st.session_state.page == "Web Search":
    st.title("Web Search")
    
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
                                 max_value=20,  # Increased from 5 to 20
                                 value=3, 
                                 step=1,
                                 help="Maximum link depth to crawl")
                                 
            timeout = st.slider("Time Out (seconds)", 
                               min_value=0, 
                               max_value=120, 
                               value=10, 
                               step=5,
                               help="Maximum time to wait for a page to load before timing out")
        
        with col2:
            file_types = st.multiselect("File Types",
                                       ["html", "md", "pdf", "txt"],
                                       default=["html", "md"],
                                       help="Types of files to crawl and index")
            
            follow_links = st.checkbox("Follow External Links", 
                                      value=False,
                                      help="If enabled, the crawler will follow links to external domains")
    
    # Start crawling button with prominent color
    if st.button("Start Crawling", 
                type="primary",  # Ensure it has primary blue color
                use_container_width=False):  # Not full width for emphasis
        with st.spinner(f"Crawling {crawl_source} documentation..."):
            try:
                if crawl_source == "All Sources":
                    pages_crawled = asyncio.run(crawl_all_docs(
                        max_pages=max_pages, 
                        max_depth=max_depth, 
                        timeout=timeout
                    ))
                elif crawl_source == "Pydantic AI":
                    pages_crawled = asyncio.run(crawl_pydantic_ai_docs(
                        max_pages=max_pages, 
                        max_depth=max_depth, 
                        timeout=timeout
                    ))
                elif crawl_source == "LangChain":
                    pages_crawled = asyncio.run(crawl_langchain_docs(
                        max_pages=max_pages, 
                        max_depth=max_depth, 
                        timeout=timeout
                    ))
                elif crawl_source == "Anthropic":
                    pages_crawled = asyncio.run(crawl_anthropic_docs(
                        max_pages=max_pages, 
                        max_depth=max_depth, 
                        timeout=timeout
                    ))
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
            elif total_docs == 0:
                st.warning("No documentation found in the database.")
                
                # Show preload button for easy onboarding
                if st.button("Preload Essential Documentation", 
                           type="primary",
                           help="Preload Pydantic, LangChain, and Anthropic documentation"):
                    try:
                        # Setup progress tracking
                        progress_text = "Starting documentation preloading..."
                        progress_bar = st.progress(0, text=progress_text)
                        status_area = st.empty()
                        
                        # Function to update progress
                        def update_progress(stage, count, total_stages=3):
                            stage_progress = (stage - 1) / total_stages
                            page_progress = count / 300  # Assuming 300 pages max per source
                            combined_progress = stage_progress + (page_progress / total_stages)
                            progress_bar.progress(combined_progress, text=progress_text)
                        
                        # Run documentation preloading with longer timeout
                        progress_text = "Preloading Pydantic documentation (Stage 1/3)..."
                        status_area.info("Crawling Pydantic documentation...")
                        
                        # Create a custom crawler with progress callback
                        class ProgressTracker:
                            def __init__(self, stage):
                                self.count = 0
                                self.stage = stage
                            
                            def increment(self):
                                self.count += 1
                                update_progress(self.stage, self.count)
                                return self.count
                        
                        # Pydantic docs
                        pydantic_tracker = ProgressTracker(1)
                        pydantic_pages = asyncio.run(crawl_pydantic_ai_docs(
                            max_pages=300, max_depth=3, timeout=600,  # 10 minute timeout
                            progress_callback=lambda: pydantic_tracker.increment()
                        ))
                        status_area.success(f"Indexed {pydantic_pages} Pydantic documentation pages")
                        
                        # LangChain docs
                        progress_text = "Preloading LangChain documentation (Stage 2/3)..."
                        status_area.info("Crawling LangChain documentation...")
                        langchain_tracker = ProgressTracker(2)
                        langchain_pages = asyncio.run(crawl_langchain_docs(
                            max_pages=300, max_depth=3, timeout=600,  # 10 minute timeout
                            progress_callback=lambda: langchain_tracker.increment()
                        ))
                        status_area.success(f"Indexed {langchain_pages} LangChain documentation pages")
                        
                        # Anthropic docs
                        progress_text = "Preloading Anthropic documentation (Stage 3/3)..."
                        status_area.info("Crawling Anthropic documentation...")
                        anthropic_tracker = ProgressTracker(3)
                        anthropic_pages = asyncio.run(crawl_anthropic_docs(
                            max_pages=300, max_depth=3, timeout=600,  # 10 minute timeout
                            progress_callback=lambda: anthropic_tracker.increment()
                        ))
                        status_area.success(f"Indexed {anthropic_pages} Anthropic documentation pages")
                        
                        # Complete
                        total_pages = pydantic_pages + langchain_pages + anthropic_pages
                        progress_bar.progress(1.0, text="Documentation preloading complete!")
                        st.success(f"Documentation preloading complete! Indexed {total_pages} pages.")
                        
                        # Set a flag to refresh this panel
                        st.session_state.navigation_action = "refresh_after_crawl"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error preloading documentation: {str(e)}")
        
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
