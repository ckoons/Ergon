"""
Generate a Nexus agent with enhanced memory capabilities using Engram.
"""

import json
from typing import Dict, Any, List, Optional
import logging
import sys

from ergon.core.database.engine import get_db_session
from ergon.core.database.models import Agent, AgentTool, AgentFile

logger = logging.getLogger(__name__)

def generate_nexus_agent(name: str, description: str, model_name: str) -> Agent:
    """
    Generate a Nexus agent with enhanced memory capabilities using Engram.
    
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
            model_name=model_name,  # Type will be inferred from the "Nexus-" prefix
            system_prompt="""You are Nexus, an AI assistant with long-term memory capabilities powered by Engram.

You can remember information across multiple sessions and have several sophisticated memory capabilities:
1. Memory Categories: personal, projects, facts, preferences, session, and private
2. Memory Importance: 1-5 ranking system (5 being most important)
3. Auto-categorization: Automatically organizing memories by content
4. Contextual Retrieval: Finding relevant memories based on the current conversation

When you recall something from memory, mention it to the user in a natural way.
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
import asyncio

# Ergon imports (will be available when running the agent)
from ergon.core.memory.service import MemoryService

# Try to import Engram directly (optional)
try:
    # Try engram package
    from engram.cli.quickmem import auto_remember, memory_digest, z, d
    HAS_ENGRAM_DIRECT = True
    logger.info("Using Engram package for Nexus agent")
except ImportError:
    HAS_ENGRAM_DIRECT = False
    logger.warning("Engram package is not available for Nexus agent")

logger = logging.getLogger(__name__)

# These functions will be available to the agent
async def store_memory(key: str, value: str, importance: int = None, category: str = None) -> str:
    # Store a memory for future reference with optional importance and category
    # agent_id is injected by the runner
    try:
        memory_service = MemoryService(agent_id)
        
        # Create metadata with key and optional category/importance
        metadata = {"key": key}
        if category:
            metadata["category"] = category
        if importance:
            metadata["importance"] = importance
            
        # Store message
        message = {"role": "system", "content": value}
        success = await memory_service.add([message], user_id=key)
        
        if success:
            return f"Successfully stored memory with key: {key}"
        else:
            return f"Failed to store memory with key: {key}"
    except Exception as e:
        logger.error(f"Error in store_memory: {str(e)}")
        return f"Error storing memory: {str(e)}"

async def retrieve_memory(query: str, limit: int = 3, min_importance: int = 1) -> str:
    # Search memories for relevant information
    # agent_id is injected by the runner
    try:
        memory_service = MemoryService(agent_id)
        memory_results = await memory_service.search(query, limit=limit)
        
        if not memory_results or not memory_results.get("results"):
            return "No relevant memories found."
        
        response = "Found the following relevant memories:\\n\\n"
        for i, memory in enumerate(memory_results["results"]):
            # Add importance stars if available
            importance_str = ""
            if "importance" in memory:
                importance_str = "★" * memory.get("importance", 3) + " "
                
            response += f"{i+1}. {importance_str}{memory['memory']}\\n\\n"
        
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

async def auto_categorize_memory(content: str) -> str:
    # Store a memory with automatic categorization and importance detection
    # agent_id is injected by the runner
    try:
        memory_service = MemoryService(agent_id)
        
        # Convert to memory adapter and access underlying components
        adapter = getattr(memory_service, "adapter", None)
        
        if adapter and hasattr(adapter, "structured_memory"):
            # Use structured memory directly if available
            memory_id = await adapter.structured_memory.add_auto_categorized_memory(
                content=content,
                metadata={"agent_id": agent_id}
            )
            
            if memory_id:
                memory = await adapter.structured_memory.get_memory(memory_id)
                category = memory.get("category", "unknown")
                importance = memory.get("importance", 3)
                return f"Memory stored with auto-categorization. Category: {category}, Importance: {importance}"
            else:
                return "Failed to store auto-categorized memory"
                
        else:
            # Use adapter's add method with standard message format
            message = {"role": "system", "content": content}
            success = await memory_service.add([message], user_id="auto_categorized")
            return "Memory stored successfully" if success else "Failed to store memory"
            
    except Exception as e:
        logger.error(f"Error in auto_categorize_memory: {str(e)}")
        return f"Error storing auto-categorized memory: {str(e)}"

async def get_memory_digest(max_memories: int = 10) -> str:
    # Get a digest of important memories across categories
    # agent_id is injected by the runner
    try:
        memory_service = MemoryService(agent_id)
        
        # Convert to memory adapter and access underlying components
        adapter = getattr(memory_service, "adapter", None)
        
        if adapter and hasattr(adapter, "structured_memory"):
            # Use structured memory directly if available
            digest = await adapter.structured_memory.get_memory_digest(
                max_memories=max_memories,
                include_private=False
            )
            return digest
        else:
            # Use regular search as fallback
            results = await memory_service.search("", limit=max_memories)
            
            if not results or not results.get("results"):
                return "No memories available for digest."
                
            digest = "# Memory Digest\\n\\n"
            
            for i, memory in enumerate(results.get("results", [])):
                digest += f"{i+1}. {memory.get('memory', '')}\\n\\n"
                
            return digest
            
    except Exception as e:
        logger.error(f"Error in get_memory_digest: {str(e)}")
        return f"Error generating memory digest: {str(e)}"
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
    """Create enhanced tool definitions for memory operations."""
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
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance level (1-5, with 5 being most important)",
                        "minimum": 1,
                        "maximum": 5
                    },
                    "category": {
                        "type": "string",
                        "description": "Memory category (personal, projects, facts, preferences, session)",
                        "enum": ["personal", "projects", "facts", "preferences", "session"]
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
                    },
                    "min_importance": {
                        "type": "integer",
                        "description": "Minimum importance level (1-5)",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 5
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
        },
        {
            "name": "auto_categorize_memory",
            "description": "Store information with automatic category and importance detection",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember and auto-categorize"
                    }
                },
                "required": ["content"]
            }
        },
        {
            "name": "get_memory_digest",
            "description": "Get a digest of important memories across categories",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_memories": {
                        "type": "integer",
                        "description": "Maximum memories to include in the digest",
                        "default": 10
                    }
                }
            }
        }
    ]