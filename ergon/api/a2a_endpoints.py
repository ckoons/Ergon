"""
A2A endpoints for Ergon API.

This module provides REST API endpoints for A2A functionality in Ergon.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path
from fastapi.responses import JSONResponse

from ..core.a2a_client import A2AClient
from ..utils.tekton_integration import get_component_port

# Setup logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(tags=["a2a"])

# Create shared A2A client
a2a_client = A2AClient(
    agent_id="ergon-api",
    agent_name="Ergon API Agent",
    capabilities={"processing": ["agent_management", "workflow_execution"]}
)

# Initialize client when module loads
@router.on_event("startup")
async def initialize_a2a_client():
    """Initialize the A2A client on startup."""
    await a2a_client.initialize()
    await a2a_client.register()

@router.on_event("shutdown")
async def close_a2a_client():
    """Close the A2A client on shutdown."""
    await a2a_client.close()

@router.post("/register")
async def register_agent(
    agent_data: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Register an agent with the A2A service.
    
    Args:
        agent_data: Agent data for registration
        
    Returns:
        Registration result
    """
    try:
        # Extract agent details
        agent_id = agent_data.get("agent_id", f"ergon-agent-{uuid.uuid4()}")
        agent_name = agent_data.get("agent_name", "Ergon Agent")
        agent_version = agent_data.get("agent_version", "0.1.0")
        capabilities = agent_data.get("capabilities", {})
        metadata = agent_data.get("metadata", {})
        
        # Create a new A2A client for this agent
        agent_client = A2AClient(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_version=agent_version,
            capabilities=capabilities
        )
        
        # Initialize and register the client
        await agent_client.initialize()
        registered = await agent_client.register()
        
        # Close the client after registration
        await agent_client.close()
        
        if registered:
            return {"success": True, "agent_id": agent_id}
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to register agent"}
            )
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Registration error: {str(e)}"}
        )

@router.get("/agents")
async def discover_agents(
    capabilities: Optional[List[str]] = Query(None, description="Required capabilities"),
) -> List[Dict[str, Any]]:
    """
    Discover agents with specific capabilities.
    
    Args:
        capabilities: List of required capabilities
        
    Returns:
        List of discovered agents
    """
    try:
        agents = await a2a_client.discover_agents(capabilities)
        return agents
    except Exception as e:
        logger.error(f"Error discovering agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error discovering agents: {str(e)}"
        )

@router.post("/messages/send")
async def send_message(
    message_data: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Send a message to other agents.
    
    Args:
        message_data: Message data
        
    Returns:
        Message sending result
    """
    try:
        # Extract message details
        recipients = message_data.get("recipients", [])
        content = message_data.get("content", {})
        message_type = message_data.get("message_type", "request")
        intent = message_data.get("intent")
        conversation_id = message_data.get("conversation_id")
        reply_to = message_data.get("reply_to")
        priority = message_data.get("priority", "normal")
        metadata = message_data.get("metadata", {})
        
        # Send the message
        message_id = await a2a_client.send_message(
            recipients=recipients,
            content=content,
            message_type=message_type,
            intent=intent,
            conversation_id=conversation_id,
            reply_to=reply_to,
            priority=priority,
            metadata=metadata
        )
        
        if message_id:
            return {
                "success": True,
                "message_id": message_id,
                "conversation_id": conversation_id
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to send message"}
            )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Message sending error: {str(e)}"}
        )

@router.post("/tasks/create")
async def create_task(
    task_data: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Create a task for other agents.
    
    Args:
        task_data: Task data
        
    Returns:
        Task creation result
    """
    try:
        # Extract task details
        name = task_data.get("name", "Unnamed Task")
        description = task_data.get("description", "")
        required_capabilities = task_data.get("required_capabilities", [])
        parameters = task_data.get("parameters", {})
        preferred_agent = task_data.get("preferred_agent")
        deadline = task_data.get("deadline")
        priority = task_data.get("priority", "normal")
        metadata = task_data.get("metadata", {})
        
        # Create the task
        task_id = await a2a_client.create_task(
            name=name,
            description=description,
            required_capabilities=required_capabilities,
            parameters=parameters,
            preferred_agent=preferred_agent,
            deadline=deadline,
            priority=priority,
            metadata=metadata
        )
        
        if task_id:
            return {"success": True, "task_id": task_id}
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to create task"}
            )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Task creation error: {str(e)}"}
        )

@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str = Path(..., description="Task ID to retrieve"),
) -> Dict[str, Any]:
    """
    Get a task by ID.
    
    Args:
        task_id: ID of the task to retrieve
        
    Returns:
        Task details
    """
    try:
        task = await a2a_client.get_task(task_id)
        if task:
            return task
        else:
            return JSONResponse(
                status_code=404,
                content={"error": f"Task with ID {task_id} not found"}
            )
    except Exception as e:
        logger.error(f"Error retrieving task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving task: {str(e)}"
        )

@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str = Path(..., description="Task ID to complete"),
    result: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Complete a task.
    
    Args:
        task_id: ID of the task to complete
        result: Task result
        
    Returns:
        Task completion result
    """
    try:
        success = await a2a_client.complete_task(task_id, result)
        if success:
            return {"success": True, "task_id": task_id}
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to complete task"}
            )
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Task completion error: {str(e)}"}
        )

@router.post("/conversations/start")
async def start_conversation(
    conversation_data: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Start a new conversation.
    
    Args:
        conversation_data: Conversation data
        
    Returns:
        Conversation creation result
    """
    try:
        # Extract conversation details
        recipients = conversation_data.get("recipients", [])
        content = conversation_data.get("content", {})
        intent = conversation_data.get("intent")
        metadata = conversation_data.get("metadata", {})
        
        # Start the conversation
        message_id = await a2a_client.send_message(
            recipients=recipients,
            content=content,
            intent=intent,
            metadata=metadata
        )
        
        if message_id:
            # The conversation ID is the same as the first message ID
            return {
                "success": True,
                "conversation_id": message_id,
                "message_id": message_id
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to start conversation"}
            )
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Conversation creation error: {str(e)}"}
        )

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str = Path(..., description="Conversation ID to retrieve"),
) -> Dict[str, Any]:
    """
    Get a conversation by ID.
    
    Args:
        conversation_id: ID of the conversation to retrieve
        
    Returns:
        Conversation details
    """
    try:
        conversation = await a2a_client.get_conversation(conversation_id)
        if conversation:
            return conversation
        else:
            return JSONResponse(
                status_code=404,
                content={"error": f"Conversation with ID {conversation_id} not found"}
            )
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation: {str(e)}"
        )

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Check A2A client health.
    
    Returns:
        Health status
    """
    # Perform a simple check by trying to discover agents
    try:
        if not a2a_client.initialized:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "A2A client not initialized"
                }
            )
            
        # Try to discover agents as a health check
        await a2a_client.discover_agents()
        
        return {
            "status": "ok",
            "agent_id": a2a_client.agent_id,
            "agent_name": a2a_client.agent_name,
            "hermes_url": a2a_client.hermes_url
        }
    except Exception as e:
        logger.error(f"A2A health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": f"A2A health check failed: {str(e)}"
            }
        )