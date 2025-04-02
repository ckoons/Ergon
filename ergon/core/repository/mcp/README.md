# MCP Tool Registration for Ergon

This module provides integration with MCP (Model Control Protocol) for tool registration and management in Ergon's repository.

## Overview

The MCP Tool Registration system allows external tools to be registered with Ergon's repository and made available to other components in the Tekton ecosystem. It provides:

- Tool registration with validation
- Schema generation for functions
- Execution adaptation for MCP protocol
- Integration with the Ergon repository database

## Usage

### Basic Tool Registration

```python
from ergon.core.repository.mcp import register_tool, unregister_tool

# Register a tool with a schema
def my_tool(input_text: str, max_length: int = 100) -> str:
    """Process the input text and return a result."""
    # Tool implementation
    return processed_result

register_tool(
    name="text_processor",
    description="Processes text input with various options",
    function=my_tool,
    schema={
        "name": "text_processor",
        "parameters": {
            "type": "object",
            "properties": {
                "input_text": {
                    "type": "string",
                    "description": "Text to process"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of output",
                    "default": 100
                }
            },
            "required": ["input_text"]
        }
    },
    tags=["text", "processing"],
    version="1.0.0"
)

# Unregister a tool when no longer needed
unregister_tool("text_processor")
```

### Using the Decorator

```python
from ergon.core.repository.mcp import mcp_tool

@mcp_tool(
    name="image_analyzer",
    description="Analyzes images and returns metadata",
    schema={
        "name": "image_analyzer",
        "parameters": {
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string", 
                    "description": "URL of the image to analyze"
                },
                "analyze_colors": {
                    "type": "boolean",
                    "description": "Whether to analyze colors",
                    "default": True
                }
            },
            "required": ["image_url"]
        }
    },
    tags=["image", "analysis"],
    version="1.0.0"
)
def analyze_image(image_url: str, analyze_colors: bool = True) -> dict:
    """Analyze an image and return metadata."""
    # Implementation
    return result
```

### Automatic Schema Generation

```python
from ergon.core.repository.mcp import adapt_tool_for_mcp, register_tool

def calculate_statistics(
    numbers: List[float], 
    include_median: bool = False
) -> Dict[str, float]:
    """Calculate statistical measures for a list of numbers."""
    # Implementation
    return stats

# Auto-generate schema from function signature
tool_def = adapt_tool_for_mcp(
    func=calculate_statistics,
    tags=["math", "statistics"],
    version="1.1.0"
)

# Register the adapted tool
register_tool(**tool_def)
```

## Integration with Tekton Components

Other Tekton components can discover and use registered tools:

```python
from ergon.core.repository.repository import RepositoryService
from ergon.core.repository.mcp import get_registered_tools, get_tool, MCPToolAdapter

# Get all registered MCP tools
all_tools = get_registered_tools()

# Get a specific tool
text_tool = get_tool("text_processor")

# Execute a tool through the adapter
success, result = MCPToolAdapter.execute_tool(
    text_tool["function"],
    {"input_text": "Process this text", "max_length": 50}
)

# Search for tools in the repository
repo = RepositoryService()
stat_tools = repo.search_components("statistics")
```

## Tool Listing and Discovery

Ergon provides multiple ways to list and discover tools:

### Listing All Tools

```python
from ergon.core.repository.mcp import get_registered_tools

# Get all registered tools with their metadata
all_tools = get_registered_tools()

# Print tool information
for name, info in all_tools.items():
    print(f"Tool: {name}")
    print(f"  Description: {info['description']}")
    print(f"  Version: {info['version']}")
    print(f"  Schema Parameters:")
    for param_name, param_info in info['schema']['parameters']['properties'].items():
        required = "Required" if param_name in info['schema']['parameters'].get('required', []) else "Optional"
        print(f"    - {param_name}: {param_info['type']} ({required})")
        print(f"      Description: {param_info.get('description', 'No description')}")
        if 'default' in param_info:
            print(f"      Default: {param_info['default']}")
```

### Command Line Listing

Tools can be listed through the Ergon CLI:

```bash
# List all tools
ergon tools list

# List tools with a specific tag
ergon tools list --tag text

# Show details for a specific tool
ergon tools show text_processor

# Search for tools
ergon tools search summarize
```

### Repository Search

The repository service provides advanced search capabilities:

```python
from ergon.core.repository.repository import RepositoryService

repo = RepositoryService()

# Search by keyword
tools = repo.search_components("image processing", limit=10)

# Filter by component type
from ergon.core.repository.models import ComponentType
tools = repo.list_components(component_type=ComponentType.TOOL)

# Get tool details with capabilities and parameters
tool = repo.get_component_by_name("text_summarizer")
print(f"Tool: {tool.name}")
print(f"Capabilities:")
for cap in tool.capabilities:
    print(f"  - {cap.name}: {cap.description}")
print(f"Parameters:")
for param in tool.parameters:
    print(f"  - {param.name}: {param.type} ({'Required' if param.required else 'Optional'})")
    print(f"    Description: {param.description}")
    if param.default_value:
        print(f"    Default: {param.default_value}")
```