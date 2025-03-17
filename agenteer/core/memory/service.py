"""
Memory management service for Agenteer.

This service provides memory storage and retrieval capabilities using either:
1. Engram when available, leveraging its advanced memory features
2. A fallback file-based implementation when Engram is not available
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the Engram adapter
from agenteer.core.memory.engram_adapter import EngramAdapter

from agenteer.core.database.engine import get_db_session
from agenteer.core.database.models import Agent
from agenteer.utils.config.settings import settings

logger = logging.getLogger(__name__)

class MemoryService:
    """
    Memory service for agents with Engram integration.
    
    This service provides a uniform interface for memory operations,
    automatically using Engram when available and falling
    back to local storage when it's not.
    """
    
    def __init__(self, agent_id: int):
        """
        Initialize the memory service.
        
        Args:
            agent_id: The ID of the agent to manage memories for
        """
        self.agent_id = agent_id
        
        # Get agent details
        with get_db_session() as db:
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            if not agent:
                raise ValueError(f"Agent with ID {self.agent_id} not found")
            self.agent_name = agent.name
            
        # Initialize the Engram adapter which handles both Engram and fallback
        self.adapter = EngramAdapter(agent_id=agent_id, agent_name=self.agent_name)
        logger.info(f"Memory service initialized for agent {self.agent_id} ({self.agent_name})")
        
        # For compatibility with old code
        self.mem0_available = self.adapter.engram_available
    
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
            # Use the Engram adapter to add memory
            return await self.adapter.add(messages, user_id)
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
            # Use the Engram adapter to search
            return await self.adapter.search(query, user_id, limit)
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
        try:
            # Use the Engram adapter to get relevant context
            return await self.adapter.get_relevant_context(query, user_id, limit)
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return ""
    
    async def clear(self, user_id: str = "default") -> bool:
        """
        Clear all memories for a user.
        
        Args:
            user_id: User identifier for memory separation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the Engram adapter to clear memories
            return await self.adapter.clear(user_id)
        except Exception as e:
            logger.error(f"Error clearing memories: {str(e)}")
            return False
            
    def close(self) -> bool:
        """
        Close the memory service and clean up resources.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Close the adapter to clean up resources
            return self.adapter.close()
        except Exception as e:
            logger.error(f"Error closing memory service: {str(e)}")
            return False