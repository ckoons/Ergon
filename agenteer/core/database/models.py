"""
SQLAlchemy models for Agenteer database.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

Base = declarative_base()


class Agent(Base):
    """Agent model representing a created AI assistant."""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Agent configuration
    model_name = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=False)
    
    # Relationships
    tools = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")
    files = relationship("AgentFile", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")
    
    # Add type property to handle agents without type column in database
    @property
    def type(self) -> str:
        """Get the agent type from name"""
        # Infer type from name - avoid accessing relationships that might not be loaded
        name_lower = self.name.lower()
        if 'mail' in name_lower or 'email' in name_lower:
            return 'mail'
        elif 'browser' in name_lower:
            return 'browser'
        elif 'github' in name_lower:
            return 'github'
        elif 'nexus' in name_lower:
            return 'nexus'
        else:
            return 'standard'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "model_name": self.model_name,
            "system_prompt": self.system_prompt,
            "type": self.type,
            "tools": [tool.to_dict() for tool in self.tools],
            "files": [file.to_dict() for file in self.files],
        }


class AgentTool(Base):
    """Tool associated with an agent."""
    __tablename__ = "agent_tools"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    function_def = Column(Text, nullable=False)  # JSON string of function definition
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="tools")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "function_def": json.loads(self.function_def) if self.function_def else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentFile(Base):
    """File associated with an agent."""
    __tablename__ = "agent_files"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # e.g., "python", "requirements", "env"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="files")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert file to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentExecution(Base):
    """Record of an agent execution."""
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    success = Column(Boolean, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="executions")
    messages = relationship("AgentMessage", back_populates="execution", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success": self.success,
            "messages": [message.to_dict() for message in self.messages],
        }


class AgentMessage(Base):
    """Message in an agent execution."""
    __tablename__ = "agent_messages"
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey("agent_executions.id"))
    role = Column(String(50), nullable=False)  # "user", "assistant", "system", "tool"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    
    # For tool calls/responses
    tool_name = Column(String(255), nullable=True)
    tool_input = Column(Text, nullable=True)  # JSON string
    tool_output = Column(Text, nullable=True)
    
    # Relationships
    execution = relationship("AgentExecution", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        result = {
            "id": self.id,
            "execution_id": self.execution_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
        
        if self.role == "tool":
            result.update({
                "tool_name": self.tool_name,
                "tool_input": json.loads(self.tool_input) if self.tool_input else None,
                "tool_output": self.tool_output,
            })
            
        return result


class DocumentationPage(Base):
    """Documentation page for agent creation references."""
    __tablename__ = "documentation_pages"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(512), nullable=True)
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Vector embedding metadata
    embedding_id = Column(String(255), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert documentation page to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "embedding_id": self.embedding_id,
        }
