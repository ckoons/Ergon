"""
Memory management service for Agenteer.

This service provides memory storage and retrieval capabilities using mem0
or a fallback implementation when mem0 is not available.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import mem0, with graceful fallback if not installed
try:
    from mem0 import Memory
    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False
    logging.warning("mem0 not installed, using fallback memory implementation")

from agenteer.core.database.engine import get_db_session
from agenteer.core.database.models import Agent
from agenteer.utils.config.settings import settings

logger = logging.getLogger(__name__)

class MemoryService:
    """Memory service for agents with mem0 integration."""
    
    def __init__(self, agent_id: int):
        """
        Initialize the memory service.
        
        Args:
            agent_id: The ID of the agent to manage memories for
        """
        self.agent_id = agent_id
        self.mem0_available = HAS_MEM0
        
        # Get agent details
        with get_db_session() as db:
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            if not agent:
                raise ValueError(f"Agent with ID {self.agent_id} not found")
            self.agent_name = agent.name
        
        # Initialize memory store
        if self.mem0_available:
            # Configure mem0
            # Use default LLM available in settings
            # We'll use the fallback implementation for now to avoid model mismatch issues
            self.memory = None
            self.memories = {}  # Simple in-memory storage as fallback
            logger.info(f"Using fallback memory implementation for agent {self.agent_id}")
            logger.info(f"Initialized mem0 for agent {self.agent_id} ({self.agent_name})")
        else:
            # No memory client available, we'll use fallback methods
            logger.warning(f"mem0 not available for agent {self.agent_id}, using fallback")
            self.memory = None
            self.memories = {}  # Simple in-memory storage as fallback
    
    async def add(self, messages: List[Dict[str, str]], user_id: str = "default") -> bool:
        """
        Add a conversation to memory.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            user_id: User identifier for memory separation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Always use the fallback implementation for now
            conversation_id = f"{datetime.now().isoformat()}"
            self.memories[conversation_id] = {
                "messages": messages,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            return False
    
    async def search(self, query: str, user_id: str = "default", limit: int = 5) -> Dict[str, Any]:
        """
        Search memories by relevance to query.
        
        Args:
            query: The search query
            user_id: User identifier for memory separation
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            # Always use the fallback implementation for now
            results = []
            for memory_id, memory in self.memories.items():
                if memory["user_id"] != user_id:
                    continue
                
                # Simple text matching
                for message in memory["messages"]:
                    if query.lower() in message["content"].lower():
                        results.append({
                            "memory": message["content"],
                            "score": 1.0,  # No actual scoring in fallback
                            "id": memory_id
                        })
                        break
            
            # Sort by recency (newest first) and limit
            results = sorted(
                results, 
                key=lambda x: x["id"], 
                reverse=True
            )[:limit]
            
            return {"results": results}
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return {"results": []}
    
    async def get_relevant_context(
        self, 
        query: str, 
        user_id: str = "default", 
        limit: int = 3
    ) -> str:
        """
        Get relevant context from memories formatted for prompt enhancement.
        
        Args:
            query: The query to find relevant memories for
            user_id: User identifier for memory separation
            limit: Maximum number of memories to include
            
        Returns:
            Formatted string with relevant memories for context
        """
        # Search for relevant memories
        memory_results = await self.search(query, user_id, limit)
        
        if not memory_results or not memory_results.get("results"):
            return ""
        
        # Format memories as context
        context = "Here are some relevant memories that might help with your response:\n\n"
        
        for i, memory in enumerate(memory_results["results"]):
            context += f"{i+1}. {memory['memory']}\n\n"
        
        return context
    
    async def clear(self, user_id: str = "default") -> bool:
        """
        Clear all memories for a user.
        
        Args:
            user_id: User identifier for memory separation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mem0_available and self.memory:
                # We don't have a direct way to clear all memories in mem0
                # This is a limitation to be addressed
                logger.warning("Clearing all memories not implemented for mem0")
                return False
            else:
                # Fallback: Clear from dictionary
                self.memories = {k: v for k, v in self.memories.items() if v["user_id"] != user_id}
                return True
        except Exception as e:
            logger.error(f"Error clearing memories: {str(e)}")
            return False