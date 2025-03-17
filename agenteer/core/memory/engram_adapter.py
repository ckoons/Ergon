"""
Engram Memory adapter for Agenteer.

This module provides an adapter for integrating Engram with Agenteer, 
supporting both direct Engram service usage and fallback to 
file-based storage when Engram is not available.
"""

import json
import logging
import os
import sys
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Engram packages
try:
    # Direct imports from Engram
    from engram.cli.quickmem import (
        status, process_message, start_nexus, end_nexus, auto_remember,
        memory_digest, s, q, n, y, z, d,
    )
    
    # Check if we can import core modules directly
    from engram.core.structured_memory import StructuredMemory
    from engram.core.nexus import NexusInterface
    from engram.core.memory import MemoryService as EngramMemoryService
    HAS_ENGRAM_CORE = True
        
    HAS_ENGRAM = True
except ImportError:
    HAS_ENGRAM = False
    HAS_ENGRAM_CORE = False
    logger.warning("Engram not installed. Using fallback file-based memory.")

# Default HTTP URL for the Engram API
DEFAULT_ENGRAM_HTTP_URL = "http://127.0.0.1:8000"

def _get_engram_http_url():
    """Get the HTTP URL for Engram API."""
    return os.environ.get("ENGRAM_HTTP_URL", DEFAULT_ENGRAM_HTTP_URL)

def _safe_string(text: str) -> str:
    """URL-encode a string to make it safe for GET requests."""
    return urllib.parse.quote_plus(text)

def _check_engram_status(start_if_not_running: bool = False) -> bool:
    """
    Check if Engram service is running.
    
    Args:
        start_if_not_running: Whether to start Engram if it's not running
        
    Returns:
        True if Engram is running, False otherwise
    """
    # Try to use quickmem status function if Engram is installed
    if HAS_ENGRAM:
        # First check if services are running using pgrep
        try:
            import subprocess
            result = subprocess.run(
                ["pgrep", "-f", "engram.api.consolidated_server"],
                capture_output=True
            )
            if result.returncode == 0:
                return True
        except:
            # Fall back to quickmem status function
            try:
                # Use asyncio to run the async function if needed
                if asyncio.iscoroutinefunction(status):
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(status(start_if_not_running))
                else:
                    return status(start_if_not_running)
            except Exception as e:
                logger.error(f"Error checking Engram status: {e}")
                return False
    
    # Try checking HTTP API directly
    try:
        url = f"{_get_engram_http_url()}/http/health"
        with urllib.request.urlopen(url, timeout=3) as response:
            health_data = json.loads(response.read().decode())
            return health_data.get("status") == "ok"
    except Exception as e:
        logger.error(f"Error checking Engram HTTP status: {e}")
        return False

class EngramAdapter:
    """
    Adapter for integrating Engram with Agenteer.
    
    This adapter provides a uniform interface for memory operations,
    regardless of whether Engram is available or not. When Engram is not 
    available, it falls back to a simple file-based implementation.
    """
    
    def __init__(self, agent_id: int, agent_name: str = None):
        """
        Initialize the Engram adapter.
        
        Args:
            agent_id: The ID of the agent to manage memories for
            agent_name: Optional name of the agent (for better logging)
        """
        self.agent_id = agent_id
        self.agent_name = agent_name or f"Agent-{agent_id}"
        self.client_id = f"agenteer_{agent_id}"
        
        # Set client ID for Engram
        os.environ["ENGRAM_CLIENT_ID"] = self.client_id
        self.engram_available = _check_engram_status()
        
        # For fallback: initialize file storage
        self.memories_dir = os.path.expanduser(f"~/.agenteer/memories/{agent_id}")
        os.makedirs(self.memories_dir, exist_ok=True)
        self.memories_file = os.path.join(self.memories_dir, "memories.json")
        
        # Load existing memories if file exists
        self.memories = self._load_memories()
        
        # Initialize direct core components if available
        if HAS_ENGRAM_CORE and self.engram_available:
            # Try to initialize Engram core components
            try:
                # Create memory services
                self.engram_memory_service = EngramMemoryService(client_id=self.client_id)
                self.structured_memory = StructuredMemory(client_id=self.client_id)
                
                # Create Nexus interface with both memory systems
                self.nexus = NexusInterface(
                    memory_service=self.engram_memory_service,
                    structured_memory=self.structured_memory
                )
                
                # Start a Nexus session for this agent
                asyncio.create_task(self.nexus.start_session(self.agent_name))
                
                logger.info(f"Initialized Engram core components for agent {self.agent_id} ({self.agent_name})")
            except Exception as e:
                logger.error(f"Error initializing Engram core components: {e}")
                self.engram_memory_service = None
                self.structured_memory = None
                self.nexus = None
        else:
            self.engram_memory_service = None
            self.structured_memory = None
            self.nexus = None
            
        # Create session ID for this instance
        self.session_id = f"session-{int(time.time())}"
        logger.info(f"EngramAdapter initialized for agent {self.agent_id} ({self.agent_name}), Engram available: {self.engram_available}")
    
    def _load_memories(self) -> Dict[str, Any]:
        """Load memories from file for fallback mode."""
        if os.path.exists(self.memories_file):
            try:
                with open(self.memories_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memories from file: {e}")
                return {}
        return {}
    
    def _save_memories(self) -> bool:
        """Save memories to file for fallback mode."""
        try:
            with open(self.memories_file, "w") as f:
                json.dump(self.memories, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving memories to file: {e}")
            return False
    
    async def add(self, messages: List[Dict[str, str]], user_id: str = "default") -> bool:
        """
        Add a conversation to memory.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            user_id: User identifier for memory separation
            
        Returns:
            True if successful, False otherwise
        """
        # Try to use Engram if available
        if self.engram_available:
            try:
                # Process each message through Nexus if we have direct access
                if self.nexus:
                    for message in messages:
                        role = message.get("role", "user")
                        content = message.get("content", "")
                        is_user = role == "user"
                        await self.nexus.process_message(content, is_user=is_user)
                    return True
                
                # Use HTTP API if direct access not available
                content = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in messages])
                metadata = json.dumps({"user_id": user_id, "agent_id": self.agent_id, "session_id": self.session_id})
                
                # Auto-categorize the memory
                url = f"{_get_engram_http_url()}/http/structured/auto?content={_safe_string(content)}&metadata={_safe_string(metadata)}"
                with urllib.request.urlopen(url) as response:
                    result = json.loads(response.read().decode())
                    return result.get("success", False)
            except Exception as e:
                logger.error(f"Error adding memory via Engram: {e}")
                # Fall back to file storage
        
        # Fallback: Store in local memory dictionary
        try:
            memory_id = f"{int(time.time())}_{hash(str(messages)) % 1000}"
            self.memories[memory_id] = {
                "messages": messages,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            self._save_memories()
            return True
        except Exception as e:
            logger.error(f"Error adding memory to fallback storage: {e}")
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
        # Try to use Engram if available
        if self.engram_available:
            try:
                # Search via Nexus if we have direct access
                if self.nexus:
                    results = await self.nexus.search_memories(
                        query=query,
                        min_importance=1,
                        limit=limit
                    )
                    
                    # Convert to our expected format
                    formatted_results = []
                    for memory in results.get("combined", []):
                        formatted_results.append({
                            "memory": memory.get("content", ""),
                            "score": memory.get("relevance_score", 1.0),
                            "id": memory.get("id", "unknown"),
                            "importance": memory.get("importance", 3)
                        })
                    
                    return {"results": formatted_results}
                
                # Use HTTP API if direct access not available
                url = f"{_get_engram_http_url()}/http/structured/search?query={_safe_string(query)}&limit={limit}"
                with urllib.request.urlopen(url) as response:
                    result = json.loads(response.read().decode())
                    
                    # Convert to our expected format
                    formatted_results = []
                    for memory in result.get("results", []):
                        formatted_results.append({
                            "memory": memory.get("content", ""),
                            "score": memory.get("relevance_score", 1.0),
                            "id": memory.get("id", "unknown"),
                            "importance": memory.get("importance", 3)
                        })
                    
                    return {"results": formatted_results}
            except Exception as e:
                logger.error(f"Error searching memories via Engram: {e}")
                # Fall back to file storage
        
        # Fallback: Search in local memory dictionary
        try:
            results = []
            for memory_id, memory in self.memories.items():
                if memory["user_id"] != user_id:
                    continue
                
                # Simple text matching for each message
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
            logger.error(f"Error searching memories in fallback storage: {e}")
            return {"results": []}
    
    async def get_relevant_context(self, query: str, user_id: str = "default", limit: int = 3) -> str:
        """
        Get relevant context from memories formatted for prompt enhancement.
        
        Args:
            query: The query to find relevant memories for
            user_id: User identifier for memory separation
            limit: Maximum number of memories to include
            
        Returns:
            Formatted string with relevant memories for context
        """
        # Try to use Engram if available
        if self.engram_available:
            try:
                # If we have direct Nexus access, process the message as user input
                if self.nexus:
                    return await self.nexus.process_message(query, is_user=True)
                
                # Use HTTP API if direct access not available
                url = f"{_get_engram_http_url()}/http/nexus/process?message={_safe_string(query)}&is_user=true"
                with urllib.request.urlopen(url) as response:
                    result = json.loads(response.read().decode())
                    if result.get("success", False):
                        return result.get("result", "")
            except Exception as e:
                logger.error(f"Error getting context via Engram: {e}")
                # Fall back to standard search
        
        # Use standard search results to build context
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
        # No direct way to clear memories in CMB API currently
        # Just clear the fallback memories
        try:
            self.memories = {k: v for k, v in self.memories.items() if v["user_id"] != user_id}
            self._save_memories()
            return True
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return False
    
    def close(self) -> bool:
        """
        Close the memory adapter and clean up resources.
        
        Returns:
            True if successful, False otherwise
        """
        # End Nexus session if we have direct access
        if self.engram_available and self.nexus:
            try:
                # Create a new event loop for ending the session
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # End Nexus session
                summary = f"Session for agent {self.agent_id} ({self.agent_name}) ended"
                loop.run_until_complete(self.nexus.end_session(summary))
                loop.close()
                
                return True
            except Exception as e:
                logger.error(f"Error ending Nexus session: {e}")
                return False
        
        # Just save memories for fallback
        return self._save_memories()