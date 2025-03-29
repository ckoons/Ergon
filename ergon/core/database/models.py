"""Database models for Ergon."""
import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, JSON, Enum, Table, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Create base class for declarative models
Base = declarative_base()

# Association table for agent <-> tools
agent_tool = Table(
    'agent_tools',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('agents.id'), primary_key=True),
    Column('tool_id', Integer, ForeignKey('tools.id'), primary_key=True)
)

# Association table for agent <-> component
agent_component = Table(
    'agent_components',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('agents.id'), primary_key=True),
    Column('component_id', Integer, ForeignKey('components.id'), primary_key=True)
)

class AgentType(enum.Enum):
    """Agent type enumeration."""
    CUSTOM = "custom"
    MAIL = "mail"
    BROWSER = "browser"
    GITHUB = "github"
    NEXUS = "nexus"
    CODE = "code"
    
class ComponentType(enum.Enum):
    """Component type enumeration."""
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"

class Agent(Base):
    """Agent model representing an AI agent instance."""
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    agent_type = Column(Enum(AgentType), default=AgentType.CUSTOM)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Agent configuration
    model_name = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=True)
    
    # Relationships
    tools = relationship("Tool", secondary=agent_tool, back_populates="agents")
    components = relationship("Component", secondary=agent_component, back_populates="agents")
    memories = relationship("Memory", back_populates="agent")

class Tool(Base):
    """Tool model representing a function an agent can use."""
    __tablename__ = 'tools'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    function_name = Column(String(255), nullable=False)
    module_path = Column(String(255), nullable=False)
    is_async = Column(Boolean, default=False)
    
    # Relationships
    agents = relationship("Agent", secondary=agent_tool, back_populates="tools")

class Component(Base):
    """Component model representing a reusable component."""
    __tablename__ = 'components'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    component_type = Column(Enum(ComponentType), default=ComponentType.TOOL)
    source_code = Column(Text, nullable=False)
    
    # Relationships
    meta_items = relationship("ComponentMetadata", back_populates="component")
    agents = relationship("Agent", secondary=agent_component, back_populates="components")
    
class ComponentMetadata(Base):
    """Metadata for components."""
    __tablename__ = 'component_metadata'
    
    id = Column(Integer, primary_key=True)
    component_id = Column(Integer, ForeignKey('components.id'))
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    
    # Relationships
    component = relationship("Component", back_populates="meta_items")

# Import memory models
try:
    from ergon.core.memory.models.schema import Memory, MemoryCollection
except ImportError:
    # If memory models aren't available yet, define placeholder classes
    # This allows the database to be created even without the memory module
    
    class Memory(Base):
        """Memory model for agent memory storage."""
        __tablename__ = 'memories'
        
        id = Column(String(255), primary_key=True)
        agent_id = Column(Integer, ForeignKey('agents.id'))
        collection_id = Column(String(255), ForeignKey('memory_collections.id'), nullable=True)
        content = Column(Text, nullable=False)
        category = Column(String(50), index=True)
        importance = Column(Integer, default=3)
        created_at = Column(DateTime, default=datetime.utcnow)
        metadata = Column(JSON, nullable=True)
        
        # Relationships
        agent = relationship("Agent", back_populates="memories")
        collection = relationship("MemoryCollection", back_populates="memories")
    
    class MemoryCollection(Base):
        """Collection of memories for organizational purposes."""
        __tablename__ = "memory_collections"
        
        id = Column(String(255), primary_key=True)
        name = Column(String(255), nullable=False)
        description = Column(Text, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        # Relationships
        memories = relationship("Memory", back_populates="collection")