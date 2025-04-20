"""
Ergon API server.

This module provides a FastAPI-based REST API for Ergon,
allowing external systems to interact with the agent builder.
"""

import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
import time
import json
from enum import Enum
import logging

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Path, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ergon.core.database.engine import get_db_session, init_db
from ergon.core.database.models import Agent, AgentFile, AgentTool, AgentExecution, AgentMessage, DocumentationPage
from ergon.core.agents.generator import AgentGenerator
from ergon.core.agents.runner import AgentRunner
from ergon.core.docs.crawler import crawl_all_docs, crawl_pydantic_ai_docs, crawl_langchain_docs, crawl_anthropic_docs
from ergon.core.llm.client import LLMClient
from ergon.core.vector_store.faiss_store import FAISSDocumentStore
from ergon.core.memory.service import MemoryService
from ergon.utils.config.settings import settings

# Create terminal memory service as a global instance
terminal_memory = MemoryService()

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.value))

# Initialize memory service
memory_service = MemoryService()

# Initialize database if needed
if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
    init_db()

# Create FastAPI app
app = FastAPI(
    title="Ergon API",
    description="REST API for the Ergon AI agent builder",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "doc_count": doc_count
    }

@app.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, description="Number of agents to skip"),
    limit: int = Query(100, description="Maximum number of agents to return")
):
    """List all agents."""
    with get_db_session() as db:
        agents = db.query(Agent).offset(skip).limit(limit).all()
        return [agent.__dict__ for agent in agents]

@app.post("/agents", response_model=AgentResponse)
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

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int = Path(..., description="ID of the agent")):
    """Get agent by ID."""
    with get_db_session() as db:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        
        return agent.__dict__

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int = Path(..., description="ID of the agent")):
    """Delete agent by ID."""
    with get_db_session() as db:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        
        db.delete(agent)
        db.commit()
        
        return {"status": "deleted", "id": agent_id}

@app.post("/agents/{agent_id}/run", response_model=MessageResponse)
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

@app.post("/docs/crawl", response_model=DocCrawlResponse)
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

@app.get("/docs/search")
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

@app.post("/terminal/message", response_model=TerminalMessageResponse)
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

@app.post("/terminal/stream")
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

# Run with: uvicorn ergon.api.app:app --host 0.0.0.0 --port 8000
