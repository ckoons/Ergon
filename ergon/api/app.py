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
from ergon.utils.config.settings import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.value))

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

# Run with: uvicorn ergon.api.app:app --host 0.0.0.0 --port 8000
