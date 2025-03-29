# Ergon Memory System

The Ergon Memory System is a sophisticated vector-based persistent memory implementation for AI agents within the Tekton ecosystem. It provides long-term memory capabilities with automatic categorization, importance ranking, and hardware-optimized vector storage.

## Key Features

- **Persistence**: Memories persist across sessions and reboots using SQLite for metadata and hardware-optimized vector storage
- **Auto-categorization**: Memories are automatically categorized based on content patterns
- **Importance ranking**: 1-5 scale for prioritizing memories
- **RAG integration**: Retrieval Augmented Generation for enhancing prompts with relevant memories
- **Hardware optimization**: Automatic selection of vector store (Qdrant for Apple Silicon, FAISS for NVIDIA)
- **Async-first**: All operations support asynchronous execution
- **Client registration**: Dynamic registration and management of AI model clients

## Architecture

The memory system consists of several components:

1. **MemoryService**: Core service for storing and retrieving memories
2. **RAGService**: Enhances LLM prompts with relevant context from memory
3. **ClientManager**: Manages client registrations and lifecycle
4. **VectorService**: Provides vector store operations with hardware optimization
5. **EmbeddingService**: Handles embedding generation for semantic search
6. **MemoryCategory**: Defines categories and auto-categorization

## Memory Categories

Memories are organized into these categories:

- **Personal**: Personal details about the user
- **Factual**: Factual information learned
- **Session**: Current session details
- **Project**: Project-specific information
- **Preference**: User preferences
- **System**: System-related memories

## Usage

### Command Line Interface

```bash
# Register a new client
ergon memory register client_id client_type --model model_name

# List all registered clients
ergon memory clients

# Get client information
ergon memory client-info client_id

# Deregister a client
ergon memory deregister client_id

# Add a memory
ergon memory add agent_id "Memory content" --category factual --importance 3

# Search memories
ergon memory search agent_id "search query" --category factual --min-importance 2

# List memories
ergon memory list agent_id --category personal --min-importance 3

# Clear memories
ergon memory clear agent_id --category session
```

### Using the Tekton Client Launcher

```bash
# Launch Ollama with Tekton integration
tekton_client ollama --model llama3

# Launch Claude with Tekton integration
tekton_client claude --model claude-3-sonnet-20240229

# Launch OpenAI with Tekton integration
tekton_client openai --model gpt-4o-mini

# Launch Claude Code with Tekton integration
tekton_client claudecode

# List all active clients
tekton_client list

# Show system status
tekton_client status
```

### Programmatic Usage

```python
from ergon.core.memory import MemoryService, RAGService, client_manager

# Register a client
await client_manager.register_client(
    client_id="my_client",
    client_type="ollama",
    config={"model": "llama3"}
)

# Create a memory service for an agent
memory_service = MemoryService(agent_id=1, agent_name="TestAgent")
await memory_service.initialize()

# Add a memory
memory_id = await memory_service.add_memory(
    content="The user prefers dark mode", 
    category="preference",
    importance=4
)

# Search memories
results = await memory_service.search(
    query="dark mode",
    categories=["preference"],
    min_importance=2,
    limit=5
)

# Use RAG to enhance prompts
rag_service = RAGService(agent_id=1)
await rag_service.initialize()
enhanced_prompt = await rag_service.augment_prompt(
    system_prompt="You are a helpful assistant",
    user_query="What theme should I use?",
    categories=["preference", "personal"],
    min_importance=2
)

# Deregister a client
await client_manager.deregister_client("my_client")
```

## Client Registration

The client registration system manages the lifecycle of different AI model clients. It:

1. Registers clients with configuration details
2. Manages model resources (starting Ollama when needed)
3. Handles client deregistration and resource cleanup
4. Monitors health and automatically deregisters idle clients

## Hardware Optimization

The memory system automatically selects the appropriate vector store based on hardware:

- Apple Silicon: Qdrant with MPS acceleration
- NVIDIA GPUs: FAISS with CUDA support
- Other hardware: FAISS with CPU operation

## Database Schema

Memories are stored in two places:
1. SQLite database for metadata (category, importance, etc.)
2. Vector store for embeddings (for semantic search)

The SQLAlchemy models define the memory schema:

```python
class Memory(Base):
    """Individual memory entry."""
    __tablename__ = "memories"
    
    id = Column(String(255), primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    collection_id = Column(String(255), ForeignKey("memory_collections.id"), nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), index=True)
    importance = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
```