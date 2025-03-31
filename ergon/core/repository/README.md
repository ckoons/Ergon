# Ergon Tool Generator

This directory contains a modular implementation of the AI-driven tool generator system for Ergon, which creates tools based on descriptions using LLMs and RAG.

## Architecture

The tool generator has been refactored from a monolithic `tool_generator.py` file into a modular structure with the following components:

### Core Components

- **`tool_generator.py`**: Compatibility layer that re-exports from the new structure
- **`generators/base.py`**: Contains the main ToolGenerator class that orchestrates tool generation

### Language-Specific Generators

- **`generators/python_generator.py`**: Generates Python tools and tests
- **`generators/javascript_generator.py`**: Generates JavaScript/TypeScript tools and tests
- **`generators/shell_generator.py`**: Generates shell script tools

### Documentation Generation

- **`generators/documentation_generator.py`**: Generates README, requirements.txt, and package.json files

### Analysis Tools

- **`analysis/code_analyzer.py`**: Analyzes code to extract parameters and capabilities

### Utility Modules

- **`utils/file_helpers.py`**: Provides file-related utility functions

## Backward Compatibility

The original `tool_generator.py` file now serves as a compatibility layer that re-exports all components from the new modular structure. This ensures that existing code will continue to work without requiring changes.

## Features

- **Multi-language Support**: Generate tools in Python, JavaScript, TypeScript, or shell script
- **Test Generation**: Automatically create test files for generated tools
- **Documentation Generation**: Generate README and dependency files
- **Parameter Extraction**: Analyze code to identify parameters
- **Capability Extraction**: Identify tool capabilities from implementation
- **Fallback Mechanisms**: Provide basic implementations when LLM generation fails

## Usage Example

```python
from ergon.core.repository.tool_generator import ToolGenerator

# Initialize generator
generator = ToolGenerator(model_name="model-name", temperature=0.7)

# Generate a tool
tool_data = await generator.generate(
    name="weather_lookup",
    description="Get weather information for a given location",
    implementation_type="python",
    capabilities=[{"name": "get_weather", "description": "Retrieve weather data for location"}],
    parameters=[
        {
            "name": "location",
            "description": "City name or zip code",
            "type": "string",
            "required": True
        }
    ]
)

# Access generated files
for file in tool_data["files"]:
    print(f"File: {file['filename']}")
    print(file['content'])
```

## Maintainer Notes

When modifying the tool generator:

1. Ensure backward compatibility is maintained
2. Add appropriate error handling and fallbacks
3. Keep language-specific code in the appropriate generator modules
4. Update this README for any significant changes