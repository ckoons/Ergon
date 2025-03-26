"""
Memory management module for Ergon.

This module provides functionality for long-term memory storage and retrieval
using Engram or fallback mechanisms, with support for 
Retrieval Augmented Generation (RAG) capabilities.
"""

from ergon.core.memory.service import MemoryService
from ergon.core.memory.engram_adapter import EngramAdapter
from ergon.core.memory.rag import RAGUtils, RAGToolFunctions, rag

# For backward compatibility
# This allows any existing code that was using memory functionality to work
try:
    from ergon.core.memory.service import MemoryService as mem0ai
except ImportError:
    # Create a shim if needed
    mem0ai = MemoryService