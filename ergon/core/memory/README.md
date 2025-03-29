# Ergon Memory and RAG System

This directory contains the memory management components for Ergon, designed to provide Retrieval Augmented Generation (RAG) capabilities to agents and tools.

## Overview

The memory system is built with the following design principles:

1. **Modular Architecture**: Clean separation between agent logic and memory functionality
2. **Flexible Backend**: Primary support for Engram with fallback to file-based storage
3. **Lightweight Integration**: Easy to use in any agent or tool

## Components

- `engram_adapter.py`: Handles integration with Engram and provides fallback functionality
- `service.py`: Memory service used by agents to store and retrieve memories
- `rag.py`: Lightweight utility for RAG capabilities in any agent or tool

## Using the RAG Utility

The RAG utility provides a simple, consistent interface for using memory capabilities in any context.

### Basic Usage

```python
from ergon.core.memory.rag import rag

# Check if RAG capabilities are available
if rag.is_available():
    # Initialize for a specific agent
    rag.initialize_for_agent(agent_id=42, agent_name="MyAgent")
    
    # Use in async context
    async def process_query(user_query, system_prompt):
        # Augment prompt with relevant memories
        augmented_prompt = await rag.augment_prompt(system_prompt, user_query)
        
        # Use the augmented prompt with your LLM of choice
        # ...
        
        # Store the interaction in memory
        await rag.store([
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": "Response..."}
        ])
```

### Using RAG Tool Functions

You can easily add RAG capabilities to any agent by registering the tool functions:

```python
from ergon.core.memory.rag import RAGToolFunctions

def load_tool_functions(agent_id):
    tools = {}
    
    # Register RAG tools
    rag_tools = RAGToolFunctions(agent_id=agent_id)
    rag_tools.register_tools(tools)
    
    # Add other tool functions
    # ...
    
    return tools
```

This will register the following tool functions:
- `retrieve_memory`: Searches for relevant memories
- `store_memory`: Stores a new memory
- `remember_interaction`: Stores a user-assistant interaction

## Vector Search

The memory system automatically uses vector search capabilities if available through Engram. If not available, it falls back to simpler retrieval methods.

You can check if vector search is available:

```python
from ergon.core.memory.rag import rag

if rag.has_vector_search():
    print("Vector search capabilities are available")
else:
    print("Using fallback search (no vector capabilities)")
```

## Future Development

In future iterations, the memory system may evolve to:

1. Support additional backend providers beyond Engram
2. Implement more sophisticated memory reasoning capabilities
3. Add domain-specific memory tools for specialized agents

As Ergon's agent architecture evolves, this memory system is designed to be easily integrated into the new structure.