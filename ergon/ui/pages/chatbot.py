"""
Chatbot interface for Ergon with memory and agent awareness.
"""

import streamlit as st
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import Ergon components
from ergon.core.agents.runner import AgentRunner
from ergon.core.database.engine import get_db_session
from ergon.core.database.models import Agent, AgentExecution, AgentMessage
from ergon.core.memory.service import MemoryService
from sqlalchemy import func

async def run_agent_async(
    agent_obj: Agent, 
    user_input: str, 
    execution_id: int,
    disable_memory: bool = False
) -> str:
    """Run the agent with the given input and return the response."""
    # Create runner
    runner = AgentRunner(
        agent=agent_obj,
        execution_id=execution_id
    )
    
    # Run agent
    if disable_memory:
        # Run in simple mode without memory tools
        response = await runner._run_simple(user_input)
    else:
        # Run normal mode with memory
        response = await runner.run(user_input)
    
    return response

def run_agent(
    agent_obj: Agent, 
    user_input: str, 
    execution_id: int,
    disable_memory: bool = False
) -> str:
    """Synchronous wrapper for running an agent."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        response = loop.run_until_complete(
            run_agent_async(agent_obj, user_input, execution_id, disable_memory)
        )
    finally:
        loop.close()
    
    return response

def get_agent_list() -> List[Dict[str, Any]]:
    """Get a list of all agents in the system."""
    with get_db_session() as db:
        agents = db.query(Agent).all()
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "type": agent.type or "standard"
            }
            for agent in agents
        ]

def find_matching_agents(query: str) -> List[Dict[str, Any]]:
    """Find agents matching a search query in name, description or type."""
    agents = get_agent_list()
    query = query.lower()
    
    # Agent metadata for better recommendations
    agent_metadata = {
        # Mail agent capabilities
        "mail": {
            "keywords": ["mail", "email", "gmail", "outlook", "message", "send", "inbox", "imap", "smtp"],
            "capabilities": ["send emails", "read emails", "search inbox", "manage drafts", "handle attachments"],
            "desc": "Email management agent that can read, send, and organize emails"
        },
        # Browser agent capabilities
        "browser": {
            "keywords": ["browser", "web", "chrome", "firefox", "internet", "website", "browse", "surf"],
            "capabilities": ["navigate websites", "extract content", "fill forms", "click buttons", "take screenshots"],
            "desc": "Web browsing agent that can navigate and interact with websites"
        },
        # GitHub agent capabilities
        "github": {
            "keywords": ["github", "git", "repo", "repository", "code", "pull", "commit", "issue", "branch"],
            "capabilities": ["manage repositories", "create issues", "handle pull requests", "view code"],
            "desc": "GitHub integration agent for repository and issue management"
        },
        # Nexus agent capabilities
        "nexus": {
            "keywords": ["nexus", "memory", "remember", "context", "conversation", "recall"],
            "capabilities": ["remember conversations", "maintain context", "recall previous interactions"],
            "desc": "Memory-enabled agent that maintains context across conversations"
        },
        # Standard agent capabilities
        "standard": {
            "keywords": ["standard", "basic", "default", "general", "assistant"],
            "capabilities": ["answer questions", "provide information", "general assistance"],
            "desc": "General-purpose agent for basic tasks and assistance"
        }
    }
    
    # Score all agents based on query relevance
    scored_agents = []
    
    for agent in agents:
        score = 0
        agent_type = agent.get("type") or "standard"
        agent_name = agent.get("name", "").lower()
        agent_desc = agent.get("description", "").lower()
        
        # Get metadata for this agent type
        metadata = agent_metadata.get(agent_type, agent_metadata["standard"])
        
        # 1. Check keyword matches (primary criterion)
        for keyword in metadata["keywords"]:
            if keyword in query:
                score += 10  # Strong relevance for keyword matches
        
        # 2. Check name matches
        if query in agent_name:
            score += 8
        elif any(word in agent_name for word in query.split()):
            score += 5
            
        # 3. Check description matches
        if agent_desc and query in agent_desc:
            score += 6
        elif agent_desc and any(word in agent_desc for word in query.split()):
            score += 3
            
        # 4. Add metadata to agent for better descriptions
        agent_with_metadata = agent.copy()
        agent_with_metadata["capabilities"] = metadata["capabilities"]
        agent_with_metadata["type_description"] = metadata["desc"]
        agent_with_metadata["score"] = score
        
        if score > 0:
            scored_agents.append(agent_with_metadata)
    
    # Sort by score (highest first)
    scored_agents.sort(key=lambda a: a["score"], reverse=True)
    
    # Return top matches or all if few
    return scored_agents[:5] if len(scored_agents) > 5 else scored_agents

def find_agent_by_name_or_id(agent_identifier: str) -> Optional[Agent]:
    """Find an agent by ID or name."""
    try:
        agent_id = int(agent_identifier)
        id_lookup = True
    except ValueError:
        id_lookup = False
    
    with get_db_session() as db:
        if id_lookup:
            # Find by ID
            return db.query(Agent).filter(Agent.id == agent_id).first()
        else:
            # Find by exact name match first
            agent = db.query(Agent).filter(func.lower(Agent.name) == agent_identifier.lower()).first()
            
            # Try partial match if no exact match
            if agent is None:
                agent = db.query(Agent).filter(func.lower(Agent.name).contains(agent_identifier.lower())).first()
            
            return agent

def rate_feature_importance():
    """Display feature importance rating interface."""
    st.subheader("Rate Feature Importance")
    
    # Define features to rate
    features = [
        "Long-term Memory",
        "Agent Awareness",
        "Workflow Creation",
        "Plan Visualization",
        "Agent Creation via Chat",
        "Feedback Collection"
    ]
    
    # Display rating interface
    ratings = {}
    
    st.write("Please rate the importance of these features (1 = least important, 5 = most important):")
    
    cols = st.columns(2)
    
    for i, feature in enumerate(features):
        col_idx = i % 2
        with cols[col_idx]:
            ratings[feature] = st.slider(
                feature, 
                min_value=1, 
                max_value=5, 
                value=3,
                key=f"rating_{feature}"
            )
    
    # Submit button
    if st.button("Submit Ratings"):
        # Store in session state
        st.session_state.feature_ratings = ratings
        
        # Sort by importance
        sorted_features = sorted(
            ratings.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        st.success("Thank you for your feedback! Your priorities are:")
        
        for feature, rating in sorted_features:
            st.write(f"- {feature}: {rating}/5")
        
        # Store in memory if a nexus agent is selected
        if "selected_agent" in st.session_state and st.session_state.selected_agent:
            if st.session_state.selected_agent.get("type") == "nexus":
                # Store in future version
                st.info("Feature priorities stored in agent memory!")

def display_plan_review(plan):
    """Display a plan for review with feedback options."""
    st.subheader("Implementation Plan Review")
    
    st.write("Please review this implementation plan and provide feedback:")
    
    # Display each phase of the plan
    for i, phase in enumerate(plan):
        with st.expander(f"Phase {i+1}: {phase['name']}", expanded=True):
            st.write(phase['description'])
            
            # Display tasks
            for j, task in enumerate(phase['tasks']):
                task_key = f"task_{i}_{j}"
                
                # Store original approval state if not in session
                if f"{task_key}_approved" not in st.session_state:
                    st.session_state[f"{task_key}_approved"] = None
                
                cols = st.columns([1, 8, 3])
                
                # Task approval
                with cols[0]:
                    approved = st.checkbox("✓", key=f"{task_key}_checkbox", value=st.session_state[f"{task_key}_approved"])
                    st.session_state[f"{task_key}_approved"] = approved
                
                # Task description
                with cols[1]:
                    st.write(f"{j+1}. {task['description']}")
                
                # Priority
                with cols[2]:
                    priority = st.selectbox(
                        "Priority", 
                        ["High", "Medium", "Low"],
                        index=["High", "Medium", "Low"].index(task.get("priority", "Medium")),
                        key=f"{task_key}_priority"
                    )
                    
                    # Update task priority in the plan
                    plan[i]['tasks'][j]['priority'] = priority
            
            # Phase feedback
            st.text_area(
                "Feedback for this phase:", 
                key=f"phase_{i}_feedback"
            )
    
    # Overall feedback
    st.text_area(
        "Overall feedback on the plan:",
        key="overall_plan_feedback"
    )
    
    # Submit button
    if st.button("Submit Plan Feedback"):
        st.success("Thank you for your feedback! The plan will be updated accordingly.")
        
        # Collect all feedback
        feedback = {
            "overall": st.session_state.overall_plan_feedback,
            "phases": [
                {
                    "phase": i,
                    "feedback": st.session_state.get(f"phase_{i}_feedback", ""),
                    "tasks": [
                        {
                            "task": j,
                            "approved": st.session_state.get(f"task_{i}_{j}_approved", False),
                            "priority": st.session_state.get(f"task_{i}_{j}_priority", "Medium")
                        }
                        for j in range(len(phase['tasks']))
                    ]
                }
                for i, phase in enumerate(plan)
            ]
        }
        
        # Store feedback in session state
        st.session_state.plan_feedback = feedback
        
        # Update session state plan with the feedback
        st.session_state.current_plan = plan
        
        return feedback
    
    return None

def chatbot_interface():
    """Main function for the Nexus chatbot interface."""
    st.title("Ergon Nexus")
    st.markdown("*Your AI-powered assistant with memory capabilities*")
    
    # Remove extra spacing
    st.markdown("""
    <style>
    /* Reduce top spacing */
    .stApp > header {
        height: 0px;
    }
    
    /* Make chat more prominent */
    [data-testid="stChatInput"] > div {
        border-color: #2196F3 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        # Add default welcome message for faster startup
        welcome_message = """
        👋 Welcome to Nexus! I'm your AI assistant for working with memory-enabled agents.
        
        You can start immediately by:
        - Just ask me about any task (e.g., "I need a mail agent" or "Help me browse the web")
        - I'll help you find the right agent for your task
        - Create a new Nexus agent using the sidebar if needed
        - Use special commands like `!rate` and `!plan` to provide feedback
        
        What would you like help with today?
        """
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": welcome_message
        })
        
        # Mark welcome as shown
        st.session_state.welcome_shown = True
    
    if "execution_id" not in st.session_state:
        st.session_state.execution_id = None
    
    if "plan_mode" not in st.session_state:
        st.session_state.plan_mode = False
    
    if "feature_rating_mode" not in st.session_state:
        st.session_state.feature_rating_mode = False
    
    if "plan_review_mode" not in st.session_state:
        st.session_state.plan_review_mode = False
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Help section for commands
        with st.expander("Command Help"):
            st.markdown("""
            ### Chat Commands
            
            - **!rate** - Open feature importance rating tool
            - **!plan** - Generate and review implementation plan
            
            Type these commands in the chat input for additional functionality.
            """)
        
        # Get available memory-enabled agents
        agents = get_agent_list()
        
        # Filter to nexus agents if possible
        nexus_agents = [a for a in agents if a["type"] == "nexus"]
        
        # If no nexus agents, use all agents
        display_agents = nexus_agents if nexus_agents else agents
        
        # Agent selection
        agent_options = [f"{a['name']} (ID: {a['id']})" for a in display_agents]
        agent_options.insert(0, "Select an agent")
        
        selected_agent_str = st.selectbox(
            "Select Agent", 
            agent_options,
            index=0
        )
        
        # Create new nexus agent button
        if st.button("Create New Nexus Agent"):
            st.session_state.show_create_nexus = True
        
        # Create Nexus agent dialog
        if "show_create_nexus" in st.session_state and st.session_state.show_create_nexus:
            with st.expander("Create New Nexus Agent", expanded=True):
                from ..utils.agent_helpers import create_nexus_agent
                
                new_agent_name = st.text_input("Agent Name", value="MemoryAgent")
                new_agent_desc = st.text_area(
                    "Agent Description", 
                    value="A memory-enabled agent for Ergon chatbot"
                )
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("Create Agent"):
                        if new_agent_name and new_agent_desc:
                            with st.spinner("Creating agent..."):
                                result = create_nexus_agent(new_agent_name, new_agent_desc)
                                
                                if result.get("success", False):
                                    st.success(f"Agent '{new_agent_name}' created successfully!")
                                    
                                    # Refresh agent list
                                    agents = get_agent_list()
                                    nexus_agents = [a for a in agents if a["type"] == "nexus"]
                                    display_agents = nexus_agents if nexus_agents else agents
                                    agent_options = [f"{a['name']} (ID: {a['id']})" for a in display_agents]
                                    agent_options.insert(0, "Select an agent")
                                    
                                    # Select the newly created agent
                                    new_agent_id = result.get("id")
                                    new_agent_option = next(
                                        (opt for opt in agent_options if f"(ID: {new_agent_id})" in opt),
                                        None
                                    )
                                    
                                    if new_agent_option:
                                        st.session_state.selected_agent = result
                                    
                                    st.session_state.show_create_nexus = False
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Error creating agent: {result.get('error', 'Unknown error')}")
                        else:
                            st.warning("Please provide both name and description")
                
                with col2:
                    if st.button("Cancel"):
                        st.session_state.show_create_nexus = False
                        st.experimental_rerun()
        
        # Memory toggle
        disable_memory = st.checkbox("Disable Memory", value=False)
        
        # Display warning if not a nexus agent
        if selected_agent_str != "Select an agent":
            agent_id = int(selected_agent_str.split("(ID: ")[1].split(")")[0])
            selected_agent = next((a for a in agents if a["id"] == agent_id), None)
            
            if selected_agent:
                st.session_state.selected_agent = selected_agent
                
                if selected_agent["type"] != "nexus":
                    st.warning("This is not a memory-enabled agent. Memory features will be limited.")
        
        # Feedback & Planning tools
        st.subheader("Feedback Tools")
        
        if st.button("Rate Feature Importance"):
            st.session_state.feature_rating_mode = True
            st.session_state.plan_review_mode = False
            st.session_state.plan_mode = False
        
        if "current_plan" in st.session_state and st.button("Review Implementation Plan"):
            st.session_state.plan_review_mode = True
            st.session_state.feature_rating_mode = False
            st.session_state.plan_mode = False
    
    # Special modes handling
    if st.session_state.feature_rating_mode:
        rate_feature_importance()
        
        if st.button("Return to Chat"):
            st.session_state.feature_rating_mode = False
        
        return
    
    if st.session_state.plan_review_mode and "current_plan" in st.session_state:
        feedback = display_plan_review(st.session_state.current_plan)
        
        if st.button("Return to Chat"):
            st.session_state.plan_review_mode = False
        
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # Display pending response if any
    if "pending_response" in st.session_state:
        with st.chat_message("assistant"):
            st.markdown(st.session_state.pending_response)
        # Clear pending response after displaying
        st.session_state.pending_response = None
    
    # Input area - always allow input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
            # Process agent command
            if user_input.startswith("!plan"):
                # Switch to plan mode
                st.session_state.plan_mode = True
                
                # Sample implementation plan (this would be generated by the agent)
                sample_plan = [
                    {
                        "name": "Memory-Enhanced Chat Interface",
                        "description": "Implement the basic memory-enabled chat interface",
                        "tasks": [
                            {
                                "description": "Create chatbot UI page",
                                "priority": "High"
                            },
                            {
                                "description": "Connect to memory service",
                                "priority": "High"
                            },
                            {
                                "description": "Implement persistent conversation history",
                                "priority": "Medium"
                            },
                            {
                                "description": "Add agent awareness features",
                                "priority": "Medium"
                            }
                        ]
                    },
                    {
                        "name": "Agent Management via Chat",
                        "description": "Allow creating and running agents through conversation",
                        "tasks": [
                            {
                                "description": "Implement natural language agent creation",
                                "priority": "High"
                            },
                            {
                                "description": "Extract parameters from dialogue",
                                "priority": "Medium"
                            },
                            {
                                "description": "Add agent utilization capabilities",
                                "priority": "High"
                            },
                            {
                                "description": "Implement conversation context maintenance",
                                "priority": "Low"
                            }
                        ]
                    }
                ]
                
                # Store the plan in session state
                st.session_state.current_plan = sample_plan
                
                # Store the response
                response = "I've created an implementation plan. You can review it using the 'Review Implementation Plan' button in the sidebar."
                
                # Add assistant message to chat
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })
                
                # Set pending response to display after current block
                st.session_state.pending_response = response
                
                st.session_state.plan_review_mode = True
                st.experimental_rerun()
            
            elif user_input.startswith("!rate"):
                # Switch to feature rating mode
                st.session_state.feature_rating_mode = True
                
                # Store the response
                response = "Let's rate the importance of different features. I've opened the rating interface in the main area."
                
                # Add assistant message to chat
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })
                
                # Set pending response to display after current block
                st.session_state.pending_response = response
                
                st.experimental_rerun()
            
            else:
                # Check if an agent is selected
                if "selected_agent" not in st.session_state or not st.session_state.selected_agent:
                    # Try to find a relevant agent based on the user's message
                    matching_agents = find_matching_agents(user_input)
                    
                    # Build a helpful response
                    if matching_agents:
                        response = f"I found {len(matching_agents)} agent(s) that might help with your request:\n\n"
                        
                        for i, agent in enumerate(matching_agents, 1):
                            agent_type = agent["type"] or "standard"
                            agent_score = agent.get("score", 0)
                            
                            # Start with the agent name and type
                            response += f"{i}. **{agent['name']}** (Type: {agent_type}"
                            
                            # Add match score for transparency
                            if agent_score > 20:
                                response += ", Excellent match)"
                            elif agent_score > 10:
                                response += ", Good match)"
                            else:
                                response += ")"
                            
                            response += "\n"
                            
                            # Add the agent's description if available
                            if agent["description"]:
                                response += f"   {agent['description']}\n"
                            else:
                                # Use the type description if no specific description
                                response += f"   {agent.get('type_description', '')}\n"
                            
                            # Add capabilities
                            if "capabilities" in agent:
                                response += "   **Capabilities**: " + ", ".join(agent["capabilities"]) + "\n"
                            
                            response += "\n"
                        
                        response += "Please select one of these agents from the sidebar dropdown to continue our conversation."
                    else:
                        response = "I don't see any agents that match your request. You can select any agent from the sidebar to continue our conversation, or create a new Nexus agent using the 'Create New Nexus Agent' button."
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response
                    })
                    
                    # We'll display this message at the end, outside of current chat block
                    st.session_state.pending_response = response
                    return
                
                # Find agent
                agent = find_agent_by_name_or_id(str(st.session_state.selected_agent["id"]))
                
                if not agent:
                    # Store response outside of any existing chat_message blocks
                    response = "Error: Agent not found. Please select a different agent or create a new one."
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response
                    })
                    
                    # We'll display this message at the end, outside of current chat block
                    st.session_state.pending_response = response
                    return
                
                # Create or reuse execution_id
                if not st.session_state.execution_id:
                    with get_db_session() as db:
                        execution = AgentExecution(
                            agent_id=agent.id,
                            started_at=datetime.now()
                        )
                        db.add(execution)
                        db.commit()
                        st.session_state.execution_id = execution.id
                
                # Show thinking indicator
                with st.chat_message("assistant"):
                    thinking_placeholder = st.empty()
                    thinking_placeholder.markdown("Thinking...")
                    
                    try:
                        # Run the agent
                        response = run_agent(
                            agent, 
                            user_input, 
                            st.session_state.execution_id,
                            disable_memory
                        )
                        
                        # Add to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                        # Set pending response to display after the current block
                        st.session_state.pending_response = response
                        
                        # Remove the thinking placeholder
                        thinking_placeholder.empty()
                        
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        
                        # Add error to chat history
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                        # Set pending response to display after the current block
                        st.session_state.pending_response = error_msg
                        
                        # Remove the thinking placeholder
                        thinking_placeholder.empty()
                        
                        # Reset execution_id on error
                        st.session_state.execution_id = None
    # We now add the welcome message at initialization, so we don't need this block anymore