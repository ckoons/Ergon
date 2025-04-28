"""
A2A Client - Client for Agent-to-Agent Communication in Ergon.

This module provides a client for the A2A protocol, allowing Ergon
agents to register with the A2A service and communicate with other agents.
"""

import os
import time
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable

import aiohttp
from aiohttp import ClientSession, ClientResponseError, ClientConnectorError

from ergon.utils.hermes_helper import register_with_hermes

logger = logging.getLogger(__name__)

class A2AClient:
    """
    Client for Agent-to-Agent communication.
    
    This class provides methods for registering with the A2A service,
    sending messages to other agents, and managing tasks and conversations.
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_name: str = "Ergon Agent",
        agent_version: str = "0.1.0",
        capabilities: Optional[Dict[str, Any]] = None,
        hermes_url: Optional[str] = None
    ):
        """
        Initialize the A2A client.
        
        Args:
            agent_id: Unique identifier for the agent (generated if not provided)
            agent_name: Human-readable name for the agent
            agent_version: Agent version
            capabilities: Agent capabilities
            hermes_url: URL of the Hermes API server
        """
        self.agent_id = agent_id or f"agent-{uuid.uuid4()}"
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.capabilities = capabilities or {
            "communication": ["basic_messaging", "task_acceptance"],
            "domain": {}
        }
        self.hermes_url = hermes_url or self._get_hermes_url()
        
        # Internal state
        self.registered = False
        self.session: Optional[ClientSession] = None
        self.message_handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {
            "all": []
        }
        
        logger.info(f"A2A client initialized for agent {self.agent_id}")
    
    def _get_hermes_url(self) -> str:
        """
        Get the Hermes URL from environment variables or use the default.
        
        Returns:
            Hermes API URL
        """
        hermes_host = os.environ.get("HERMES_HOST", "localhost")
        hermes_port = os.environ.get("HERMES_PORT", "8001")
        return f"http://{hermes_host}:{hermes_port}/api"
    
    async def initialize(self) -> bool:
        """
        Initialize the client.
        
        Returns:
            True if initialization was successful
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        # Register with the A2A service
        if not self.registered:
            return await self.register()
            
        return True
    
    async def close(self) -> None:
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def register(self) -> bool:
        """
        Register with the A2A service.
        
        Returns:
            True if registration was successful
        """
        # Ensure session is initialized
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        # Create agent card
        agent_card = {
            "agent_id": self.agent_id,
            "name": self.agent_name,
            "version": self.agent_version,
            "description": f"{self.agent_name} powered by Ergon",
            "capabilities": self.capabilities,
            "limitations": {},
            "availability": {
                "status": "available",
                "capacity": 1.0,
                "response_time": "medium"
            },
            "endpoint": "",  # Will be set by the service
            "metadata": {
                "ergon_agent": True
            }
        }
        
        try:
            # Send registration request
            async with self.session.post(
                f"{self.hermes_url}/a2a/register",
                json=agent_card
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if result.get("success"):
                    self.registered = True
                    logger.info(f"Agent {self.agent_id} successfully registered with A2A service")
                    
                    # Also register with Hermes
                    await register_with_hermes(
                        service_id=self.agent_id,
                        name=self.agent_name,
                        capabilities=["a2a_agent"] + self._flatten_capabilities(),
                        metadata={
                            "agent_card": agent_card,
                            "type": "a2a_agent"
                        }
                    )
                    
                    return True
                else:
                    logger.error(f"A2A registration failed: {result.get('message')}")
                    return False
                    
        except (ClientResponseError, ClientConnectorError) as e:
            logger.error(f"Error connecting to A2A service: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error during A2A registration: {e}")
            return False
    
    async def unregister(self) -> bool:
        """
        Unregister from the A2A service.
        
        Returns:
            True if unregistration was successful
        """
        if not self.registered:
            return True
            
        # Ensure session is initialized
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        try:
            # Send unregistration request
            async with self.session.post(
                f"{self.hermes_url}/a2a/unregister",
                params={"agent_id": self.agent_id}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if result.get("success"):
                    self.registered = False
                    logger.info(f"Agent {self.agent_id} successfully unregistered from A2A service")
                    return True
                else:
                    logger.error(f"A2A unregistration failed: {result.get('message')}")
                    return False
                    
        except (ClientResponseError, ClientConnectorError) as e:
            logger.error(f"Error connecting to A2A service: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error during A2A unregistration: {e}")
            return False
    
    async def send_message(
        self,
        recipients: List[Dict[str, Any]],
        content: Dict[str, Any],
        message_type: str = "request",
        intent: Optional[str] = None,
        conversation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Send a message to one or more agents.
        
        Args:
            recipients: List of recipients
            content: Message content
            message_type: Type of message
            intent: Message intent
            conversation_id: ID of the conversation this message is part of
            reply_to: ID of the message this is a reply to
            priority: Message priority
            metadata: Additional metadata
            
        Returns:
            Message ID if sent successfully, None otherwise
        """
        # Ensure client is initialized
        if not await self.initialize():
            logger.error("Cannot send message: client not initialized")
            return None
            
        # Create message
        message = {
            "id": f"msg-{uuid.uuid4()}",
            "sender": {
                "id": self.agent_id,
                "name": self.agent_name,
                "version": self.agent_version
            },
            "recipients": recipients,
            "type": message_type,
            "content": content,
            "conversation_id": conversation_id,
            "reply_to": reply_to,
            "intent": intent,
            "priority": priority,
            "metadata": metadata or {}
        }
        
        try:
            # Send message
            async with self.session.post(
                f"{self.hermes_url}/a2a/message",
                json=message
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if result.get("success"):
                    logger.info(f"Message sent: {result.get('message_id')}")
                    return result.get("message_id")
                else:
                    logger.error(f"Message sending failed: {result}")
                    return None
                    
        except (ClientResponseError, ClientConnectorError) as e:
            logger.error(f"Error connecting to A2A service: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return None
    
    async def create_task(
        self,
        name: str,
        description: str,
        required_capabilities: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        preferred_agent: Optional[str] = None,
        deadline: Optional[float] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a new task.
        
        Args:
            name: Task name
            description: Task description
            required_capabilities: Capabilities required to complete the task
            parameters: Task parameters
            preferred_agent: ID of preferred agent
            deadline: Task deadline (Unix timestamp)
            priority: Task priority
            metadata: Additional metadata
            
        Returns:
            Task ID if created successfully, None otherwise
        """
        # Ensure client is initialized
        if not await self.initialize():
            logger.error("Cannot create task: client not initialized")
            return None
            
        # Create task specification
        task_spec = {
            "name": name,
            "description": description,
            "required_capabilities": required_capabilities,
            "parameters": parameters or {},
            "preferred_agent": preferred_agent,
            "deadline": deadline,
            "priority": priority,
            "metadata": metadata or {}
        }
        
        try:
            # Create task
            async with self.session.post(
                f"{self.hermes_url}/a2a/tasks",
                json=task_spec
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if "error" not in result:
                    logger.info(f"Task created: {result.get('task_id')}")
                    return result.get("task_id")
                else:
                    logger.error(f"Task creation failed: {result.get('error')}")
                    return None
                    
        except (ClientResponseError, ClientConnectorError) as e:
            logger.error(f"Error connecting to A2A service: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error creating task: {e}")
            return None
    
    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any],
        message: Optional[str] = None
    ) -> bool:
        """
        Mark a task as completed.
        
        Args:
            task_id: ID of the task to complete
            result: Task result
            message: Optional completion message
            
        Returns:
            True if task was successfully completed
        """
        # Ensure client is initialized
        if not await self.initialize():
            logger.error("Cannot complete task: client not initialized")
            return False
            
        # Create status update
        status_update = {
            "status": "completed",
            "agent_id": self.agent_id,
            "message": message or "Task completed successfully",
            "result": result
        }
        
        try:
            # Update task status
            async with self.session.post(
                f"{self.hermes_url}/a2a/tasks/{task_id}/status",
                json=status_update
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if result.get("success"):
                    logger.info(f"Task {task_id} marked as completed")
                    return True
                else:
                    logger.error(f"Task completion failed: {result}")
                    return False
                    
        except (ClientResponseError, ClientConnectorError) as e:
            logger.error(f"Error connecting to A2A service: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error completing task: {e}")
            return False
    
    async def start_conversation(
        self,
        participants: List[str],
        topic: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Start a new conversation.
        
        Args:
            participants: List of participant agent IDs
            topic: Conversation topic
            context: Conversation context
            
        Returns:
            Conversation ID if created successfully, None otherwise
        """
        # Ensure client is initialized
        if not await self.initialize():
            logger.error("Cannot start conversation: client not initialized")
            return None
            
        # Create conversation request
        conversation_req = {
            "participants": participants,
            "topic": topic,
            "context": context
        }
        
        try:
            # Start conversation
            async with self.session.post(
                f"{self.hermes_url}/a2a/conversations",
                json=conversation_req
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if "conversation_id" in result:
                    logger.info(f"Conversation started: {result.get('conversation_id')}")
                    return result.get("conversation_id")
                else:
                    logger.error(f"Conversation start failed: {result}")
                    return None
                    
        except (ClientResponseError, ClientConnectorError) as e:
            logger.error(f"Error connecting to A2A service: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error starting conversation: {e}")
            return None
    
    async def add_to_conversation(
        self,
        conversation_id: str,
        content: Dict[str, Any],
        message_type: str = "request",
        intent: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            content: Message content
            message_type: Type of message
            intent: Message intent
            reply_to: ID of the message this is a reply to
            metadata: Additional metadata
            
        Returns:
            Message ID if sent successfully, None otherwise
        """
        # Ensure client is initialized
        if not await self.initialize():
            logger.error("Cannot add to conversation: client not initialized")
            return None
            
        # Create message
        message = {
            "id": f"msg-{uuid.uuid4()}",
            "sender": {
                "id": self.agent_id,
                "name": self.agent_name,
                "version": self.agent_version
            },
            "recipients": [],  # Will be determined by the conversation
            "type": message_type,
            "content": content,
            "conversation_id": conversation_id,
            "reply_to": reply_to,
            "intent": intent,
            "metadata": metadata or {}
        }
        
        try:
            # Add message to conversation
            async with self.session.post(
                f"{self.hermes_url}/a2a/conversations/{conversation_id}/messages",
                json=message
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if result.get("success"):
                    logger.info(f"Message added to conversation: {result.get('message_id')}")
                    return result.get("message_id")
                else:
                    logger.error(f"Message addition failed: {result}")
                    return None
                    
        except (ClientResponseError, ClientConnectorError) as e:
            logger.error(f"Error connecting to A2A service: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error adding to conversation: {e}")
            return None
    
    def _flatten_capabilities(self) -> List[str]:
        """
        Flatten capabilities dictionary into a list of strings.
        
        Returns:
            Flattened list of capabilities
        """
        flattened = []
        
        for category, values in self.capabilities.items():
            if isinstance(values, list):
                flattened.extend(values)
            elif isinstance(values, dict):
                for domain, domain_capabilities in values.items():
                    if isinstance(domain_capabilities, list):
                        flattened.extend(domain_capabilities)
        
        return flattened
    
    # Context manager support
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()