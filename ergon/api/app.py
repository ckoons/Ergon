"""
Ergon API server.

This module provides a FastAPI-based REST API for Ergon,
allowing external systems to interact with the agent builder.
"""

import os
import sys
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
import time
import json
from enum import Enum
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Path, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add Tekton root to path if not already present
tekton_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if tekton_root not in sys.path:
    sys.path.insert(0, tekton_root)

# Import shared utils
from shared.utils.hermes_registration import HermesRegistration, heartbeat_loop
from shared.utils.logging_setup import setup_component_logging
from shared.utils.env_config import get_component_config
from shared.utils.errors import StartupError
from shared.utils.startup import component_startup, StartupMetrics
from shared.utils.shutdown import GracefulShutdown

from ergon.core.database.engine import get_db_session, init_db
from ergon.core.database.models import Agent, AgentFile, AgentTool, AgentExecution, AgentMessage, DocumentationPage
from ergon.core.agents.generator import AgentGenerator
from ergon.core.agents.runner import AgentRunner
from ergon.core.docs.crawler import crawl_all_docs, crawl_pydantic_ai_docs, crawl_langchain_docs, crawl_anthropic_docs
from ergon.core.llm.client import LLMClient
from ergon.core.vector_store.faiss_store import FAISSDocumentStore
from ergon.core.memory.service import MemoryService
from ergon.utils.config.settings import settings
from ergon.utils.tekton_integration import get_component_port, configure_for_single_port

# Import A2A and MCP endpoints
from .a2a_endpoints import router as a2a_router
from .mcp_endpoints import router as mcp_router
from .fastmcp_endpoints import fastmcp_router, fastmcp_startup, fastmcp_shutdown

# Create terminal memory service as a global instance
terminal_memory = MemoryService()

# Use shared logger
logger = setup_component_logging("ergon")

# Initialize memory service
memory_service = MemoryService()

# Initialize database if needed
if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
    init_db()

# Get port configuration
port_config = configure_for_single_port()
logger.info(f"Ergon API configured with port {port_config['port']}")

# Global state for Hermes registration
hermes_registration = None
heartbeat_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for Ergon"""
    global hermes_registration, heartbeat_task
    
    # Startup
    logger.info("Starting Ergon API")
    
    async def ergon_startup():
        """Ergon-specific startup logic"""
        try:
            # Get configuration
            config = get_component_config()
            port = config.ergon.port if hasattr(config, 'ergon') else int(os.environ.get("ERGON_PORT", 8002))
            
            # Register with Hermes
            global hermes_registration, heartbeat_task
            hermes_registration = HermesRegistration()
            
            logger.info(f"Attempting to register Ergon with Hermes on port {port}")
            is_registered = await hermes_registration.register_component(
                component_name="ergon",
                port=port,
                version="0.1.0",
                capabilities=[
                    "agent_creation",
                    "agent_execution",
                    "memory_integration",
                    "specialized_tasks"
                ],
                metadata={
                    "description": "Agent system for specialized task execution",
                    "category": "execution"
                }
            )
            
            if is_registered:
                logger.info("Successfully registered with Hermes")
                # Start heartbeat task
                heartbeat_task = asyncio.create_task(
                    heartbeat_loop(hermes_registration, "ergon", interval=30)
                )
                logger.info("Started Hermes heartbeat task")
            else:
                logger.warning("Failed to register with Hermes - continuing without registration")
            
            # Initialize FastMCP
            await fastmcp_startup()
            logger.info("FastMCP initialized")
            
        except Exception as e:
            logger.error(f"Error during Ergon startup: {e}", exc_info=True)
            raise StartupError(str(e), "ergon", "STARTUP_FAILED")
    
    # Execute startup with metrics
    try:
        metrics = await component_startup("ergon", ergon_startup, timeout=30)
        logger.info(f"Ergon started successfully in {metrics.total_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to start Ergon: {e}")
        raise
    
    # Create shutdown handler
    shutdown = GracefulShutdown("ergon")
    
    # Register cleanup tasks
    async def cleanup_hermes():
        """Cleanup Hermes registration"""
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if hermes_registration and hermes_registration.is_registered:
            await hermes_registration.deregister("ergon")
            logger.info("Deregistered from Hermes")
    
    async def cleanup_fastmcp():
        """Cleanup FastMCP"""
        try:
            await fastmcp_shutdown()
            logger.info("FastMCP shut down")
        except Exception as e:
            logger.warning(f"Error shutting down FastMCP: {e}")
    
    async def cleanup_heartbeat():
        """Cancel heartbeat task if running"""
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("Heartbeat task cancelled")
    
    shutdown.register_cleanup(cleanup_heartbeat)
    shutdown.register_cleanup(cleanup_hermes)
    shutdown.register_cleanup(cleanup_fastmcp)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ergon API")
    await shutdown.shutdown_sequence(timeout=10)
    
    # Socket release delay for macOS
    await asyncio.sleep(0.5)

# Create FastAPI app
app = FastAPI(
    title="Ergon API",
    description="REST API for the Ergon AI agent builder and A2A/MCP services",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include A2A, MCP, and FastMCP routers
app.include_router(a2a_router)
app.include_router(mcp_router)
app.include_router(fastmcp_router, prefix="/api/mcp/v2")  # Mount FastMCP router under /api/mcp/v2


# ----- Models -----

class AgentCreate(BaseModel):
    """Model for creating a new agent."""
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent")
    model_name: Optional[str] = Field(None, description="Model to use (defaults to settings)")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="List of tools for the agent")
    temperature: float = Field(0.7, description="Temperature for generation (0-1)")

class AgentResponse(BaseModel):
    """Model for agent response."""
    id: int
    name: str
    description: Optional[str] = None
    model_name: str
    system_prompt: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MessageCreate(BaseModel):
    """Model for creating a new message."""
    content: str = Field(..., description="Content of the message")
    stream: bool = Field(False, description="Whether to stream the response")

class MessageResponse(BaseModel):
    """Model for message response."""
    role: str
    content: str
    timestamp: datetime

class StatusResponse(BaseModel):
    """Model for status response."""
    status: str
    version: str
    database: bool
    models: List[str]
    doc_count: int
    port: int
    single_port_enabled: bool

class DocCrawlRequest(BaseModel):
    """Model for doc crawl request."""
    source: str = Field(..., description="Source to crawl ('all', 'pydantic', 'langchain', 'anthropic')")
    max_pages: int = Field(100, description="Maximum number of pages to crawl")

class DocCrawlResponse(BaseModel):
    """Model for doc crawl response."""
    status: str
    pages_crawled: int
    source: str
    
class TerminalMessageRequest(BaseModel):
    """Model for terminal message request."""
    message: str = Field(..., description="Message content")
    context_id: str = Field("ergon", description="Context ID (e.g., 'ergon', 'awt-team')")
    model: Optional[str] = Field(None, description="LLM model to use (defaults to settings)")
    temperature: Optional[float] = Field(None, description="Temperature for generation (0-1)")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    streaming: bool = Field(True, description="Whether to stream the response")
    save_to_memory: bool = Field(True, description="Whether to save message to memory")
    
class TerminalMessageResponse(BaseModel):
    """Model for terminal message response."""
    status: str
    message: Optional[str] = None
    error: Optional[str] = None
    context_id: str

# ----- Routes -----

@app.get("/api", response_model=StatusResponse)
@app.get("/", response_model=StatusResponse)
async def get_status():
    """Get API status."""
    with get_db_session() as db:
        doc_count = db.query(DocumentationPage).count()
        
    return {
        "status": "ok",
        "version": "0.1.0",
        "database": os.path.exists(settings.database_url.replace("sqlite:///", "")),
        "models": settings.available_models,
        "doc_count": doc_count,
        "port": port_config["port"],
        "single_port_enabled": True
    }

@app.get("/health")
async def health_check():
    """Get API health status following Tekton standards."""
    from tekton.utils.port_config import get_ergon_port
    port = get_ergon_port()
    
    return {
        "status": "healthy",
        "component": "ergon",
        "version": "0.1.0",
        "port": port,
        "message": "Ergon is running normally"
    }

@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, description="Number of agents to skip"),
    limit: int = Query(100, description="Maximum number of agents to return")
):
    """List all agents."""
    with get_db_session() as db:
        agents = db.query(Agent).offset(skip).limit(limit).all()
        return [agent.__dict__ for agent in agents]

@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(agent_data: AgentCreate):
    """Create a new agent."""
    try:
        # Initialize agent generator
        generator = AgentGenerator(
            model_name=agent_data.model_name,
            temperature=agent_data.temperature
        )
        
        # Generate agent
        agent_result = await generator.generate(
            name=agent_data.name,
            description=agent_data.description,
            tools=agent_data.tools
        )
        
        # Save agent to database
        with get_db_session() as db:
            agent = Agent(
                name=agent_result["name"],
                description=agent_result["description"],
                model_name=agent_result["model_name"],
                system_prompt=agent_result["system_prompt"]
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            # Save agent files
            for file_data in agent_result["files"]:
                file = AgentFile(
                    agent_id=agent.id,
                    filename=file_data["filename"],
                    file_type=file_data["file_type"],
                    content=file_data["content"]
                )
                db.add(file)
            
            # Save agent tools
            for tool_data in agent_result.get("tools", []):
                tool = AgentTool(
                    agent_id=agent.id,
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    function_def=json.dumps(tool_data)
                )
                db.add(tool)
            
            db.commit()
            db.refresh(agent)
            
            return agent.__dict__
            
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int = Path(..., description="ID of the agent")):
    """Get agent by ID."""
    with get_db_session() as db:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        
        return agent.__dict__

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: int = Path(..., description="ID of the agent")):
    """Delete agent by ID."""
    with get_db_session() as db:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        
        db.delete(agent)
        db.commit()
        
        return {"status": "deleted", "id": agent_id}

@app.post("/api/agents/{agent_id}/run", response_model=MessageResponse)
async def run_agent(
    message: MessageCreate,
    agent_id: int = Path(..., description="ID of the agent")
):
    """Run an agent with the given input."""
    try:
        with get_db_session() as db:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
            
            # Create execution record
            execution = AgentExecution(agent_id=agent.id)
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # Record user message
            user_message = AgentMessage(
                execution_id=execution.id,
                role="user",
                content=message.content
            )
            db.add(user_message)
            db.commit()
        
        # Initialize runner
        runner = AgentRunner(agent=agent, execution_id=execution.id)
        
        if message.stream:
            async def generate():
                async for chunk in runner.arun_stream(message.content):
                    yield f"data: {chunk}\n\n"
                
                # Mark execution as completed
                with get_db_session() as db:
                    execution = db.query(AgentExecution).filter(AgentExecution.id == execution.id).first()
                    if execution:
                        execution.completed_at = datetime.now()
                        execution.success = True
                        db.commit()
                
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Run agent
            response = await runner.arun(message.content)
            
            # Mark execution as completed
            with get_db_session() as db:
                execution = db.query(AgentExecution).filter(AgentExecution.id == execution.id).first()
                if execution:
                    execution.completed_at = datetime.now()
                    execution.success = True
                    db.commit()
                
                # Get assistant message
                assistant_message = db.query(AgentMessage).filter(
                    AgentMessage.execution_id == execution.id,
                    AgentMessage.role == "assistant"
                ).order_by(AgentMessage.id.desc()).first()
                
                if assistant_message:
                    return {
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "timestamp": assistant_message.timestamp
                    }
                else:
                    # If no message found, create one
                    return {
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now()
                    }
            
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running agent: {str(e)}")

@app.post("/api/docs/crawl", response_model=DocCrawlResponse)
async def crawl_docs(request: DocCrawlRequest):
    """Crawl documentation from specified source."""
    try:
        pages_crawled = 0
        
        if request.source.lower() == "all":
            pages_crawled = await crawl_all_docs()
            source = "all"
        elif request.source.lower() == "pydantic":
            pages_crawled = await crawl_pydantic_ai_docs()
            source = "pydantic"
        elif request.source.lower() == "langchain":
            pages_crawled = await crawl_langchain_docs()
            source = "langchain"
        elif request.source.lower() == "anthropic":
            pages_crawled = await crawl_anthropic_docs()
            source = "anthropic"
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source: {request.source}")
        
        return {
            "status": "ok",
            "pages_crawled": pages_crawled,
            "source": source
        }
        
    except Exception as e:
        logger.error(f"Error crawling docs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error crawling docs: {str(e)}")

@app.get("/api/docs/search")
async def search_docs(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Maximum number of results to return")
):
    """Search documentation."""
    try:
        vector_store = FAISSDocumentStore()
        results = vector_store.search(query, top_k=limit)
        
        # Clean up results
        cleaned_results = []
        for result in results:
            # Truncate content if too long
            content = result["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            
            cleaned_results.append({
                "id": result["id"],
                "title": result["metadata"].get("title", "Untitled"),
                "url": result["metadata"].get("url", ""),
                "source": result["metadata"].get("source", ""),
                "content": content,
                "score": result["score"]
            })
        
        return cleaned_results
        
    except Exception as e:
        logger.error(f"Error searching docs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching docs: {str(e)}")

@app.post("/api/terminal/message", response_model=TerminalMessageResponse)
async def terminal_message(
    request: TerminalMessageRequest,
    background_tasks: BackgroundTasks
):
    """Handle terminal message from UI."""
    try:
        # Get appropriate LLM client based on settings
        llm_client = LLMClient(
            model_name=request.model,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens
        )
        
        # Prepare messages
        messages = []
        
        # Add a system message based on the context
        system_message = "You are a helpful assistant."
        if request.context_id == "ergon":
            system_message = "You are the Ergon AI assistant, specialized in agent creation, automation, and tool configuration for the Tekton system. Be concise and helpful."
        elif request.context_id == "awt-team":
            system_message = "You are the Advanced Workflow Team assistant for Tekton. You specialize in workflow automation, process design, and team collaboration. Be concise and helpful."
        elif request.context_id == "agora":
            system_message = "You are Agora, a multi-component AI assistant for Tekton. You coordinate between different AI systems to solve complex problems. Be concise and helpful."
        
        messages.append({"role": "system", "content": system_message})
        
        # Get previous messages from memory if applicable
        if request.save_to_memory:
            prev_messages = terminal_memory.get_recent_messages(request.context_id, limit=10)
            messages.extend(prev_messages)
        
        # Add the current user message
        messages.append({"role": "user", "content": request.message})
        
        # If streaming is requested, handle streaming response
        if request.streaming:
            return await terminal_stream(request, background_tasks)
        
        # Otherwise, handle regular response
        # Call LLM with the message
        response = await llm_client.acomplete(messages)
        
        # Save to memory if needed
        if request.save_to_memory:
            background_tasks.add_task(
                terminal_memory.add_message,
                context_id=request.context_id,
                message=request.message,
                role="user"
            )
            background_tasks.add_task(
                terminal_memory.add_message,
                context_id=request.context_id,
                message=response,
                role="assistant"
            )
        
        return {
            "status": "success",
            "message": response,
            "context_id": request.context_id
        }
    except Exception as e:
        logger.error(f"Error handling terminal message: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "context_id": request.context_id
        }

@app.post("/api/terminal/stream")
async def terminal_stream(
    request: TerminalMessageRequest,
    background_tasks: BackgroundTasks
):
    """Stream response from LLM for terminal."""
    try:
        # Get appropriate LLM client based on settings
        llm_client = LLMClient(
            model_name=request.model,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens
        )
        
        # Prepare messages
        messages = []
        
        # Add a system message based on the context
        system_message = "You are a helpful assistant."
        if request.context_id == "ergon":
            system_message = "You are the Ergon AI assistant, specialized in agent creation, automation, and tool configuration for the Tekton system. Be concise and helpful."
        elif request.context_id == "awt-team":
            system_message = "You are the Advanced Workflow Team assistant for Tekton. You specialize in workflow automation, process design, and team collaboration. Be concise and helpful."
        elif request.context_id == "agora":
            system_message = "You are Agora, a multi-component AI assistant for Tekton. You coordinate between different AI systems to solve complex problems. Be concise and helpful."
        
        messages.append({"role": "system", "content": system_message})
        
        # Get previous messages from memory if applicable
        if request.save_to_memory:
            prev_messages = terminal_memory.get_recent_messages(request.context_id, limit=10)
            messages.extend(prev_messages)
        
        # Add the current user message
        messages.append({"role": "user", "content": request.message})
        
        # Save user message to memory
        if request.save_to_memory:
            background_tasks.add_task(
                terminal_memory.add_message,
                context_id=request.context_id,
                message=request.message,
                role="user"
            )
        
        # Create string buffer to collect full response
        response_buffer = []
        
        # Define callback to save complete response to memory
        async def on_complete():
            if request.save_to_memory:
                full_response = "".join(response_buffer)
                await terminal_memory.add_message(
                    context_id=request.context_id,
                    message=full_response,
                    role="assistant"
                )
        
        # Stream generator function
        async def generate():
            async for chunk in llm_client.acomplete_stream(messages):
                # Add to buffer for saving later
                response_buffer.append(chunk)
                
                # Format as server-sent event
                yield f"data: {json.dumps({'chunk': chunk, 'context_id': request.context_id})}\n\n"
            
            # Complete streaming
            await on_complete()
            yield f"data: {json.dumps({'done': True, 'context_id': request.context_id})}\n\n"
        
        # Return streaming response
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error streaming terminal response: {str(e)}")
        # Return error as SSE
        async def error_response():
            yield f"data: {json.dumps({'error': str(e), 'context_id': request.context_id})}\n\n"
        
        return StreamingResponse(
            error_response(),
            media_type="text/event-stream"
        )

# Add WebSocket endpoint for A2A and MCP
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for A2A and MCP communication."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message based on its type
            if "protocol" in message:
                if message["protocol"] == "a2a":
                    # Handle A2A message
                    await websocket.send_text(json.dumps({
                        "type": "a2a_ack",
                        "status": "received",
                        "timestamp": time.time()
                    }))
                elif message["protocol"] == "mcp":
                    # Handle MCP message
                    await websocket.send_text(json.dumps({
                        "type": "mcp_ack",
                        "status": "received",
                        "timestamp": time.time()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown protocol: {message.get('protocol')}"
                    }))
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Missing protocol field"
                }))
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()


# Run with: uvicorn ergon.api.app:app --host 0.0.0.0 --port 8002

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable or use default
    port = int(os.environ.get("ERGON_PORT", "8002"))
    
    uvicorn.run(app, host="0.0.0.0", port=port)