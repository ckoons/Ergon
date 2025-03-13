"""
Generate a Nexus agent with memory capabilities.
"""

import json
from typing import Dict, Any, List, Optional
import logging
import sys

from agenteer.core.database.engine import get_db_session
from agenteer.core.database.models import Agent, AgentTool, AgentFile

logger = logging.getLogger(__name__)

def generate_nexus_agent(name: str, description: str, model_name: str) -> Agent:
    """
    Generate a Nexus agent with memory capabilities.
    
    Args:
        name: Name of the agent
        description: Description of the agent
        model_name: Model to use for the agent
        
    Returns:
        The created agent
    """
    # Create agent directly in the database
    with get_db_session() as db:
        agent = Agent(
            name="Nexus-" + name,  # Prepend with "Nexus-" so our type detection works
            description=description,
            model_name=model_name,
            system_prompt="""You are Nexus, an AI assistant with long-term memory capabilities.
You can remember past conversations and user preferences to provide more helpful responses.
When you recall something from memory, you can mention it to the user as appropriate.
Answer questions clearly and concisely based on your knowledge and available memory.
"""
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
    
    # Create memory tools
    memory_tools = _create_memory_tools()
    
    # Create agent tools
    with get_db_session() as db:
        for tool_def in memory_tools:
            tool = AgentTool(
                agent_id=agent.id,
                name=tool_def["name"],
                description=tool_def["description"],
                function_def=json.dumps(tool_def["parameters"])
            )
            db.add(tool)
        db.commit()
    
    # Create Python file with tool implementations
    tool_file_content = """
import json
import logging
from typing import Dict, Any, List, Optional

# Agenteer imports (will be available when running the agent)
from agenteer.core.memory.service import MemoryService

logger = logging.getLogger(__name__)

# These functions will be available to the agent
async def store_memory(key: str, value: str) -> str:
    # Store a memory for future reference
    # agent_id is injected by the runner
    try:
        memory_service = MemoryService(agent_id)
        message = {"role": "system", "content": value}
        success = await memory_service.add([message], user_id=key)
        
        if success:
            return f"Successfully stored memory with key: {key}"
        else:
            return f"Failed to store memory with key: {key}"
    except Exception as e:
        logger.error(f"Error in store_memory: {str(e)}")
        return f"Error storing memory: {str(e)}"

async def retrieve_memory(query: str, limit: int = 3) -> str:
    # Search memories for relevant information
    # agent_id is injected by the runner
    try:
        memory_service = MemoryService(agent_id)
        memory_results = await memory_service.search(query, limit=limit)
        
        if not memory_results or not memory_results.get("results"):
            return "No relevant memories found."
        
        response = "Found the following relevant memories:\\n\\n"
        for i, memory in enumerate(memory_results["results"]):
            response += f"{i+1}. {memory['memory']}\\n\\n"
        
        return response
    except Exception as e:
        logger.error(f"Error in retrieve_memory: {str(e)}")
        return f"Error retrieving memories: {str(e)}"

async def remember_interaction(user_message: str, agent_response: str) -> str:
    # Store an interaction in memory
    # agent_id is injected by the runner
    try:
        memory_service = MemoryService(agent_id)
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": agent_response}
        ]
        timestamp = __import__('datetime').datetime.now().isoformat()
        success = await memory_service.add(messages, user_id=f"interaction_{timestamp}")
        
        if success:
            return "Interaction stored in memory successfully."
        else:
            return "Failed to store interaction in memory."
    except Exception as e:
        logger.error(f"Error in remember_interaction: {str(e)}")
        return f"Error storing interaction: {str(e)}"
"""
    
    # Add tool file to agent
    with get_db_session() as db:
        file = AgentFile(
            agent_id=agent.id,
            filename="memory_tools.py",
            content=tool_file_content,
            file_type="python"
        )
        db.add(file)
        db.commit()
    
    return agent

def _create_memory_tools() -> List[Dict[str, Any]]:
    """Create tool definitions for memory operations."""
    return [
        {
            "name": "store_memory",
            "description": "Store important information in long-term memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "A unique identifier or category for the memory"
                    },
                    "value": {
                        "type": "string",
                        "description": "The information to remember"
                    }
                },
                "required": ["key", "value"]
            }
        },
        {
            "name": "retrieve_memory",
            "description": "Search for relevant memories to help answer a question",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in memories"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to retrieve",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "remember_interaction",
            "description": "Store the current interaction in memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "The user's message"
                    },
                    "agent_response": {
                        "type": "string",
                        "description": "Your response to the user"
                    }
                },
                "required": ["user_message", "agent_response"]
            }
        }
    ]