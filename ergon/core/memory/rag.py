"""
Lightweight RAG (Retrieval Augmented Generation) utility for Ergon.

This module provides a simple interface for using RAG capabilities
with any agent or tool, abstracting away the details of the underlying
memory systems (Engram or fallback storage).
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

from ergon.core.memory.engram_adapter import EngramAdapter, _check_engram_status

logger = logging.getLogger(__name__)

class RAGUtils:
    """
    Utility class for Retrieval Augmented Generation.
    
    This lightweight class wraps the EngramAdapter to provide RAG functionality
    that can be easily imported and used by any agent or tool.
    """
    
    def __init__(self, agent_id: Optional[int] = None, agent_name: Optional[str] = None):
        """
        Initialize the RAG utility.
        
        Args:
            agent_id: Optional agent ID for memory isolation
            agent_name: Optional agent name for better logging
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        
        # Initialize the adapter if agent_id is provided
        self.adapter = None
        if agent_id:
            self.adapter = EngramAdapter(agent_id=agent_id, agent_name=agent_name)
        
        # Check if Engram is available (even without an adapter)
        self.engram_status = _check_engram_status()
        self.engram_available = self.engram_status.get("available", False)
        self.vector_search_available = self.engram_status.get("vector_search_available", False)
    
    def initialize_for_agent(self, agent_id: int, agent_name: Optional[str] = None) -> bool:
        """
        Initialize the RAG utility for a specific agent.
        
        Args:
            agent_id: The agent ID to use for memory isolation
            agent_name: Optional agent name for better logging
            
        Returns:
            True if initialization was successful
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        
        try:
            self.adapter = EngramAdapter(agent_id=agent_id, agent_name=agent_name)
            return True
        except Exception as e:
            logger.error(f"Error initializing RAG for agent {agent_id}: {e}")
            return False
    
    async def retrieve_context(self, query: str, limit: int = 3) -> str:
        """
        Retrieve context relevant to the query.
        
        Args:
            query: The query to find relevant memories for
            limit: Maximum number of memories to include
            
        Returns:
            Formatted string with relevant memories
        """
        if not self.adapter:
            logger.warning("RAG utility not initialized with an agent_id")
            return ""
        
        try:
            return await self.adapter.get_relevant_context(query, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    async def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search memories by relevance to query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        if not self.adapter:
            logger.warning("RAG utility not initialized with an agent_id")
            return {"results": []}
        
        try:
            return await self.adapter.search(query, limit=limit)
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return {"results": []}
    
    async def store(self, content: Union[str, List[Dict[str, str]]], memory_type: str = "session") -> bool:
        """
        Store content in memory.
        
        Args:
            content: Text content or list of message objects to store
            memory_type: Type of memory (e.g., "session", "personal", "fact")
            
        Returns:
            True if successful, False otherwise
        """
        if not self.adapter:
            logger.warning("RAG utility not initialized with an agent_id")
            return False
        
        try:
            # Convert string content to message format if needed
            if isinstance(content, str):
                messages = [{"role": "system", "content": content}]
            else:
                messages = content
            
            # Store the memory
            return await self.adapter.add(messages, user_id=memory_type)
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    async def augment_prompt(self, original_prompt: str, user_query: str, limit: int = 3) -> str:
        """
        Augment a prompt with relevant context.
        
        Args:
            original_prompt: The original system prompt
            user_query: The user's query to find relevant context for
            limit: Maximum number of memories to include
            
        Returns:
            Augmented prompt with relevant memories
        """
        if not self.adapter:
            logger.warning("RAG utility not initialized with an agent_id")
            return original_prompt
        
        try:
            # Get relevant context
            context = await self.adapter.get_relevant_context(user_query, limit=limit)
            
            # If context was found, append it to the prompt
            if context:
                return f"{original_prompt}\n\n{context}"
            
            # Otherwise return the original prompt
            return original_prompt
        except Exception as e:
            logger.error(f"Error augmenting prompt: {e}")
            return original_prompt
    
    def is_available(self) -> bool:
        """
        Check if RAG capabilities are available.
        
        Returns:
            True if RAG capabilities are available
        """
        return self.engram_available
    
    def has_vector_search(self) -> bool:
        """
        Check if vector search capabilities are available.
        
        Returns:
            True if vector search is available
        """
        return self.vector_search_available
    
    def close(self) -> bool:
        """
        Clean up resources.
        
        Returns:
            True if successful
        """
        if self.adapter:
            return self.adapter.close()
        return True


# Create a singleton instance for easy import
rag = RAGUtils()


class RAGToolFunctions:
    """
    Tool functions that can be registered with agents to provide RAG capabilities.
    
    Usage:
        # Initialize with an agent ID
        rag_tools = RAGToolFunctions(agent_id=42)
        
        # Register with an agent's tool functions
        tools = {}
        rag_tools.register_tools(tools)
    """
    
    def __init__(self, agent_id: int, agent_name: Optional[str] = None):
        """
        Initialize RAG tool functions.
        
        Args:
            agent_id: The agent ID to use for memory isolation
            agent_name: Optional agent name for better logging
        """
        self.utils = RAGUtils(agent_id=agent_id, agent_name=agent_name)
    
    async def retrieve_memory(self, query: str, limit: int = 3) -> str:
        """Tool function to search memories for relevant information."""
        try:
            memory_results = await self.utils.search(query, limit=limit)
            
            if not memory_results or not memory_results.get("results"):
                return "No relevant memories found."
            
            response = "Found the following relevant memories:\n\n"
            for i, memory in enumerate(memory_results["results"]):
                response += f"{i+1}. {memory['memory']}\n\n"
            
            return response
        except Exception as e:
            logger.error(f"Error in retrieve_memory tool: {e}")
            return f"Error retrieving memories: {str(e)}"
    
    async def store_memory(self, content: str, memory_type: str = "personal") -> str:
        """Tool function to store a memory for future reference."""
        try:
            success = await self.utils.store(content, memory_type=memory_type)
            
            if success:
                return f"Successfully stored memory as {memory_type} memory"
            else:
                return f"Failed to store memory"
        except Exception as e:
            logger.error(f"Error in store_memory tool: {e}")
            return f"Error storing memory: {str(e)}"
    
    async def remember_interaction(self, user_message: str, agent_response: str) -> str:
        """Tool function to store an interaction in memory."""
        try:
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": agent_response}
            ]
            success = await self.utils.store(messages, memory_type="session")
            
            if success:
                return "Interaction stored in memory successfully."
            else:
                return "Failed to store interaction in memory."
        except Exception as e:
            logger.error(f"Error in remember_interaction tool: {e}")
            return f"Error storing interaction: {str(e)}"
    
    def register_tools(self, tools_dict: Dict[str, callable]) -> None:
        """
        Register RAG tool functions in a tools dictionary.
        
        Args:
            tools_dict: Dictionary to register the tools in
        """
        tools_dict["retrieve_memory"] = self.retrieve_memory
        tools_dict["store_memory"] = self.store_memory
        tools_dict["remember_interaction"] = self.remember_interaction