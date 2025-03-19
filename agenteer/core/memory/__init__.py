"""
Memory management module for Agenteer.

This module provides functionality for long-term memory storage and retrieval
using Engram or fallback mechanisms, with support for 
Retrieval Augmented Generation (RAG) capabilities.
"""

from agenteer.core.memory.service import MemoryService
from agenteer.core.memory.engram_adapter import EngramAdapter
from agenteer.core.memory.rag import RAGUtils, RAGToolFunctions, rag

# For backward compatibility
# This allows any existing code that was using memory functionality to work
try:
    from agenteer.core.memory.service import MemoryService as mem0ai
except ImportError:
    # Create a shim if needed
    mem0ai = MemoryService