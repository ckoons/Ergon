"""
AI-driven tool generator.

This module provides functionality for generating tools based on descriptions,
using LLMs and RAG to create high-quality tools for the repository.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging
import tempfile

from ergon.core.database.engine import get_db_session
from ergon.core.repository.models import Tool, Capability, Parameter, Metadata, ComponentFile
from ergon.core.llm.client import LLMClient
from ergon.core.docs.document_store import document_store
from ergon.utils.config.settings import settings
from ergon.core.configuration.wrapper import ConfigurationGenerator
from ergon.core.memory.rag import RAGUtils

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.value))


class ToolGenerator:
    """
    AI-driven tool generator.
    
    This class leverages LLMs and RAG to generate tools based on descriptions.
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """
        Initialize the tool generator.
        
        Args:
            model_name: Name of the model to use for generation (defaults to settings)
            temperature: Temperature for generation (0-1)
        """
        self.model_name = model_name or settings.default_model
        self.temperature = temperature
        self.llm_client = LLMClient(model_name=self.model_name, temperature=self.temperature)
        self.configuration_generator = ConfigurationGenerator()
        self.rag = RAGUtils()
    
    async def generate(
        self, 
        name: str, 
        description: str,
        implementation_type: str = "python",
        capabilities: Optional[List[Dict[str, str]]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a new tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            implementation_type: Implementation type (python, js, bash, etc.)
            capabilities: Optional list of capabilities
            parameters: Optional list of parameters
        
        Returns:
            Dictionary with tool details and files
        """
        # Validate name (alphanumeric with underscores)
        if not name.replace("_", "").isalnum():
            raise ValueError("Tool name must contain only alphanumeric characters and underscores")
        
        # Get relevant documentation
        relevant_docs = await self._get_relevant_documentation(name, description, implementation_type)
        
        # Generate tool files and metadata
        tool_files = await self._generate_tool_files(name, description, implementation_type, capabilities, parameters, relevant_docs)
        
        # Generate parameters if not provided
        if not parameters:
            parameters = await self._generate_parameters(name, description, implementation_type, tool_files)
        
        # Generate capabilities if not provided
        if not capabilities:
            capabilities = await self._generate_capabilities(name, description, implementation_type, tool_files)
        
        # Return tool data
        return {
            "name": name,
            "description": description,
            "implementation_type": implementation_type,
            "entry_point": f"{name.lower()}.py" if implementation_type == "python" else f"{name.lower()}.{self._get_extension(implementation_type)}",
            "capabilities": capabilities,
            "parameters": parameters,
            "files": tool_files
        }
    
    async def _get_relevant_documentation(self, name: str, description: str, implementation_type: str) -> str:
        """Get relevant documentation for tool generation."""
        # Construct search query
        query = f"Generate a {implementation_type} tool named {name} that {description}"
        
        # Get relevant documentation
        documentation = await document_store.get_relevant_documentation(query, limit=3)
        
        return documentation
    
    def _get_extension(self, implementation_type: str) -> str:
        """Get file extension for implementation type."""
        extensions = {
            "python": "py",
            "js": "js",
            "javascript": "js",
            "typescript": "ts",
            "bash": "sh",
            "shell": "sh",
            "ruby": "rb",
            "go": "go",
            "rust": "rs"
        }
        return extensions.get(implementation_type.lower(), implementation_type.lower())
    
    async def _generate_tool_files(
        self,
        name: str,
        description: str,
        implementation_type: str,
        capabilities: Optional[List[Dict[str, str]]],
        parameters: Optional[List[Dict[str, Any]]],
        relevant_docs: str
    ) -> List[Dict[str, str]]:
        """Generate tool implementation files."""
        files = []
        
        if implementation_type == "python":
            # Generate main Python file
            main_file = await self._generate_python_tool(name, description, capabilities, parameters, relevant_docs)
            files.append({
                "filename": f"{name.lower()}.py",
                "file_type": "python",
                "content": main_file
            })
            
            # Generate test file
            test_file = await self._generate_python_test(name, description)
            files.append({
                "filename": f"test_{name.lower()}.py",
                "file_type": "python",
                "content": test_file
            })
            
            # Generate README
            readme = await self._generate_readme(name, description, implementation_type, capabilities, parameters)
            files.append({
                "filename": "README.md",
                "file_type": "markdown",
                "content": readme
            })
            
            # Generate requirements.txt
            requirements = await self._generate_requirements(name, description, implementation_type)
            files.append({
                "filename": "requirements.txt",
                "file_type": "requirements",
                "content": requirements
            })
        
        elif implementation_type in ["js", "javascript", "typescript"]:
            # Generate main JS/TS file
            main_file = await self._generate_js_tool(name, description, capabilities, parameters, relevant_docs)
            ext = "ts" if implementation_type == "typescript" else "js"
            files.append({
                "filename": f"{name.lower()}.{ext}",
                "file_type": implementation_type,
                "content": main_file
            })
            
            # Generate test file
            test_file = await self._generate_js_test(name, description, implementation_type)
            files.append({
                "filename": f"{name.lower()}.test.{ext}",
                "file_type": implementation_type,
                "content": test_file
            })
            
            # Generate README
            readme = await self._generate_readme(name, description, implementation_type, capabilities, parameters)
            files.append({
                "filename": "README.md",
                "file_type": "markdown",
                "content": readme
            })
            
            # Generate package.json
            package_json = await self._generate_package_json(name, description, implementation_type)
            files.append({
                "filename": "package.json",
                "file_type": "json",
                "content": package_json
            })
        
        elif implementation_type in ["bash", "shell"]:
            # Generate main shell script
            main_file = await self._generate_shell_tool(name, description, capabilities, parameters, relevant_docs)
            files.append({
                "filename": f"{name.lower()}.sh",
                "file_type": "shell",
                "content": main_file
            })
            
            # Generate README
            readme = await self._generate_readme(name, description, implementation_type, capabilities, parameters)
            files.append({
                "filename": "README.md",
                "file_type": "markdown",
                "content": readme
            })
        
        # Generate any additional files needed
        return files
    
    async def _generate_python_tool(
        self,
        name: str,
        description: str,
        capabilities: Optional[List[Dict[str, str]]],
        parameters: Optional[List[Dict[str, Any]]],
        relevant_docs: str
    ) -> str:
        """Generate Python tool implementation."""
        # Create prompt for the tool generation
        system_prompt = """You are an expert Python developer tasked with creating a tool for an AI agent system.
Your goal is to create a clean, well-documented Python module that implements the requested functionality.

Follow these guidelines:
1. Use type hints consistently
2. Add comprehensive docstrings and comments
3. Handle errors gracefully with appropriate exceptions
4. Include all necessary imports
5. Create well-structured functions with clear purposes
6. Implement the core functionality described in the request
7. Make the code easy to use and integrate with other systems
8. Ensure the code is secure and follows best practices"""

        capabilities_text = ""
        if capabilities:
            capabilities_text = "The tool has these capabilities:\n" + "\n".join([f"- {c['name']}: {c['description']}" for c in capabilities])
        
        parameters_text = ""
        if parameters:
            parameters_text += "The tool has these parameters:\n"
            for param in parameters:
                required = "Required" if param.get("required", False) else "Optional"
                default = f" (default: {param.get('default_value', 'None')})" if "default_value" in param else ""
                parameters_text += f"- {param['name']} ({param.get('type', 'string')}, {required}){default}: {param['description']}\n"

        user_prompt = f"""Create a Python tool named '{name}' that {description}.

{capabilities_text}
{parameters_text}

Here's some relevant documentation that might help:
{relevant_docs}

Return only the Python code with no additional text. Include imports, docstrings, and full implementation. The tool should be a standalone Python module that can be imported and used directly.
"""

        try:
            # Generate the tool code
            tool_code = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response (remove markdown code blocks if present)
            tool_code = tool_code.strip()
            if tool_code.startswith("```python"):
                tool_code = tool_code[len("```python"):].strip()
            if tool_code.startswith("```"):
                tool_code = tool_code[3:].strip()
            if tool_code.endswith("```"):
                tool_code = tool_code[:-3].strip()
            
            return tool_code
        except Exception as e:
            logger.error(f"Error generating Python tool: {str(e)}")
            # Return a fallback implementation
            return self._generate_fallback_python_tool(name, description)
    
    def _generate_fallback_python_tool(self, name: str, description: str) -> str:
        """Generate fallback Python tool when LLM fails."""
        return f'''"""
{name.title()} Tool.

{description}
"""

from typing import Dict, Any, Optional


def main(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main function for the {name} tool.
    
    Args:
        params: Dictionary of parameters
        
    Returns:
        Result dictionary
    """
    params = params or {{}}
    
    # TODO: Implement tool functionality
    
    return {{
        "success": True,
        "message": "Tool executed successfully. Please implement the actual functionality.",
        "data": {{}}
    }}


if __name__ == "__main__":
    # Example usage
    result = main({{"param1": "value1"}})
    print(result)
'''
    
    async def _generate_python_test(self, name: str, description: str) -> str:
        """Generate Python test file."""
        system_prompt = """You are an expert Python developer tasked with creating tests for a tool.
Create a comprehensive test file using pytest that tests all aspects of the tool."""

        user_prompt = f"""Create a test file for a Python tool named '{name}' that {description}.

The test file should:
1. Import pytest and the tool module
2. Test all main functionality
3. Include test cases for both success and failure scenarios
4. Use proper pytest fixtures and assertions
5. Follow best practices for test design

Return only the Python test code with no additional text."""

        try:
            # Generate the test code
            test_code = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response
            test_code = test_code.strip()
            if test_code.startswith("```python"):
                test_code = test_code[len("```python"):].strip()
            if test_code.startswith("```"):
                test_code = test_code[3:].strip()
            if test_code.endswith("```"):
                test_code = test_code[:-3].strip()
            
            return test_code
        except Exception as e:
            logger.error(f"Error generating Python test: {str(e)}")
            # Return a fallback test implementation
            return f'''"""
Tests for {name.title()} Tool.
"""

import pytest
from {name.lower()} import main


def test_{name.lower()}_success():
    """Test successful execution of {name} tool."""
    result = main({{"param1": "value1"}})
    assert result["success"] is True


def test_{name.lower()}_missing_params():
    """Test {name} tool with missing parameters."""
    result = main({{}})
    assert result["success"] is True  # Default params should work


def test_{name.lower()}_invalid_params():
    """Test {name} tool with invalid parameters."""
    # TODO: Implement test with invalid parameters
    pass
'''
    
    async def _generate_js_tool(
        self,
        name: str,
        description: str,
        capabilities: Optional[List[Dict[str, str]]],
        parameters: Optional[List[Dict[str, Any]]],
        relevant_docs: str
    ) -> str:
        """Generate JavaScript/TypeScript tool implementation."""
        # Implementation details similar to Python generator
        is_typescript = "typescript" in name.lower() or "ts" in name.lower()
        language = "TypeScript" if is_typescript else "JavaScript"
        
        system_prompt = f"""You are an expert {language} developer tasked with creating a tool for an AI agent system.
Your goal is to create a clean, well-documented {language} module that implements the requested functionality.

Follow these guidelines:
1. Use proper types (interfaces/types for TypeScript, JSDoc for JavaScript)
2. Add comprehensive comments
3. Handle errors gracefully
4. Include all necessary imports
5. Create well-structured functions with clear purposes
6. Implement the core functionality described in the request
7. Make the code easy to use and integrate with other systems
8. Ensure the code is secure and follows best practices"""

        capabilities_text = ""
        if capabilities:
            capabilities_text = "The tool has these capabilities:\n" + "\n".join([f"- {c['name']}: {c['description']}" for c in capabilities])
        
        parameters_text = ""
        if parameters:
            parameters_text += "The tool has these parameters:\n"
            for param in parameters:
                required = "Required" if param.get("required", False) else "Optional"
                default = f" (default: {param.get('default_value', 'None')})" if "default_value" in param else ""
                parameters_text += f"- {param['name']} ({param.get('type', 'string')}, {required}){default}: {param['description']}\n"

        user_prompt = f"""Create a {language} tool named '{name}' that {description}.

{capabilities_text}
{parameters_text}

Here's some relevant documentation that might help:
{relevant_docs}

Return only the {language} code with no additional text. Include imports, comments, and full implementation. The tool should be a standalone module that can be imported and used directly.
"""

        try:
            # Generate the tool code
            tool_code = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response
            tool_code = tool_code.strip()
            if tool_code.startswith(f"```{language.lower()}"):
                tool_code = tool_code[len(f"```{language.lower()}"):].strip()
            elif tool_code.startswith("```js") or tool_code.startswith("```ts"):
                tool_code = tool_code[5:].strip()
            elif tool_code.startswith("```javascript") or tool_code.startswith("```typescript"):
                tool_code = tool_code[14:].strip()
            if tool_code.startswith("```"):
                tool_code = tool_code[3:].strip()
            if tool_code.endswith("```"):
                tool_code = tool_code[:-3].strip()
            
            return tool_code
        except Exception as e:
            logger.error(f"Error generating {language} tool: {str(e)}")
            # Return a fallback implementation
            if is_typescript:
                return self._generate_fallback_typescript_tool(name, description)
            else:
                return self._generate_fallback_js_tool(name, description)
    
    def _generate_fallback_js_tool(self, name: str, description: str) -> str:
        """Generate fallback JavaScript tool when LLM fails."""
        return f'''/**
 * {name.title()} Tool.
 *
 * {description}
 */

/**
 * Main function for the {name} tool.
 * @param {{Object}} params - Dictionary of parameters
 * @returns {{Object}} Result object
 */
function main(params = {{}}) {{
  // TODO: Implement tool functionality
  
  return {{
    success: true,
    message: "Tool executed successfully. Please implement the actual functionality.",
    data: {{}}
  }};
}}

module.exports = {{ main }};
'''
    
    def _generate_fallback_typescript_tool(self, name: str, description: str) -> str:
        """Generate fallback TypeScript tool when LLM fails."""
        return f'''/**
 * {name.title()} Tool.
 *
 * {description}
 */

interface Params {{
  [key: string]: any;
}}

interface Result {{
  success: boolean;
  message: string;
  data: any;
}}

/**
 * Main function for the {name} tool.
 * @param params - Dictionary of parameters
 * @returns Result object
 */
export function main(params: Params = {{}}): Result {{
  // TODO: Implement tool functionality
  
  return {{
    success: true,
    message: "Tool executed successfully. Please implement the actual functionality.",
    data: {{}}
  }};
}}

// For CommonJS compatibility
export default {{ main }};
'''
    
    async def _generate_js_test(self, name: str, description: str, implementation_type: str) -> str:
        """Generate JavaScript/TypeScript test file."""
        # Implementation details similar to Python test generator
        is_typescript = implementation_type == "typescript"
        language = "TypeScript" if is_typescript else "JavaScript"
        framework = "Jest"
        
        system_prompt = f"""You are an expert {language} developer tasked with creating tests for a tool.
Create a comprehensive test file using {framework} that tests all aspects of the tool."""

        user_prompt = f"""Create a test file for a {language} tool named '{name}' that {description}.

The test file should:
1. Import {framework} and the tool module
2. Test all main functionality
3. Include test cases for both success and failure scenarios
4. Use proper {framework} matchers and assertions
5. Follow best practices for test design

Return only the {language} test code with no additional text."""

        try:
            # Generate the test code
            test_code = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response
            test_code = test_code.strip()
            if test_code.startswith(f"```{language.lower()}"):
                test_code = test_code[len(f"```{language.lower()}"):].strip()
            elif test_code.startswith("```js") or test_code.startswith("```ts"):
                test_code = test_code[5:].strip()
            elif test_code.startswith("```javascript") or test_code.startswith("```typescript"):
                test_code = test_code[14:].strip()
            if test_code.startswith("```"):
                test_code = test_code[3:].strip()
            if test_code.endswith("```"):
                test_code = test_code[:-3].strip()
            
            return test_code
        except Exception as e:
            logger.error(f"Error generating {language} test: {str(e)}")
            # Return a fallback test implementation
            if is_typescript:
                return self._generate_fallback_typescript_test(name, description)
            else:
                return self._generate_fallback_js_test(name, description)
    
    def _generate_fallback_js_test(self, name: str, description: str) -> str:
        """Generate fallback JavaScript test when LLM fails."""
        return f'''/**
 * Tests for {name.title()} Tool.
 */

const {{ main }} = require('./{name.lower()}');

describe('{name} Tool', () => {{
  test('should execute successfully with parameters', () => {{
    const result = main({{ param1: 'value1' }});
    expect(result.success).toBe(true);
  }});

  test('should execute successfully with no parameters', () => {{
    const result = main();
    expect(result.success).toBe(true);
  }});

  test('should handle invalid parameters', () => {{
    // TODO: Implement test with invalid parameters
  }});
}});
'''
    
    def _generate_fallback_typescript_test(self, name: str, description: str) -> str:
        """Generate fallback TypeScript test when LLM fails."""
        return f'''/**
 * Tests for {name.title()} Tool.
 */

import {{ main }} from './{name.lower()}';

describe('{name} Tool', () => {{
  test('should execute successfully with parameters', () => {{
    const result = main({{ param1: 'value1' }});
    expect(result.success).toBe(true);
  }});

  test('should execute successfully with no parameters', () => {{
    const result = main();
    expect(result.success).toBe(true);
  }});

  test('should handle invalid parameters', () => {{
    // TODO: Implement test with invalid parameters
  }});
}});
'''
    
    async def _generate_shell_tool(
        self,
        name: str,
        description: str,
        capabilities: Optional[List[Dict[str, str]]],
        parameters: Optional[List[Dict[str, Any]]],
        relevant_docs: str
    ) -> str:
        """Generate shell script tool implementation."""
        system_prompt = """You are an expert shell script developer tasked with creating a tool for an AI agent system.
Your goal is to create a clean, well-documented shell script that implements the requested functionality.

Follow these guidelines:
1. Add comprehensive comments
2. Handle errors gracefully
3. Include proper parameter parsing
4. Create well-structured functions with clear purposes
5. Implement the core functionality described in the request
6. Make the script easy to use and integrate with other systems
7. Ensure the code is secure and follows best practices"""

        capabilities_text = ""
        if capabilities:
            capabilities_text = "The tool has these capabilities:\n" + "\n".join([f"- {c['name']}: {c['description']}" for c in capabilities])
        
        parameters_text = ""
        if parameters:
            parameters_text += "The tool has these parameters:\n"
            for param in parameters:
                required = "Required" if param.get("required", False) else "Optional"
                default = f" (default: {param.get('default_value', 'None')})" if "default_value" in param else ""
                parameters_text += f"- {param['name']} ({param.get('type', 'string')}, {required}){default}: {param['description']}\n"

        user_prompt = f"""Create a shell script tool named '{name}' that {description}.

{capabilities_text}
{parameters_text}

Here's some relevant documentation that might help:
{relevant_docs}

Return only the shell script code with no additional text. Include comments and full implementation. The tool should be a standalone shell script that can be executed directly.
"""

        try:
            # Generate the tool code
            tool_code = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response
            tool_code = tool_code.strip()
            if tool_code.startswith("```bash") or tool_code.startswith("```sh"):
                tool_code = tool_code[7:].strip()
            if tool_code.startswith("```shell"):
                tool_code = tool_code[9:].strip()
            if tool_code.startswith("```"):
                tool_code = tool_code[3:].strip()
            if tool_code.endswith("```"):
                tool_code = tool_code[:-3].strip()
            
            # Ensure script is executable
            if not tool_code.startswith("#!/"):
                tool_code = "#!/bin/bash\n\n" + tool_code
            
            return tool_code
        except Exception as e:
            logger.error(f"Error generating shell tool: {str(e)}")
            # Return a fallback implementation
            return self._generate_fallback_shell_tool(name, description)
    
    def _generate_fallback_shell_tool(self, name: str, description: str) -> str:
        """Generate fallback shell script tool when LLM fails."""
        return f'''#!/bin/bash
# {name.title()} Tool
#
# {description}

# Function to display usage
function show_usage() {{
  echo "Usage: $(basename $0) [options]"
  echo "Options:"
  echo "  -h, --help     Show this help message"
  echo "  -p, --param1   Parameter 1 (example)"
  echo ""
  echo "Example: $(basename $0) --param1 value1"
}}

# Function to display error message
function error() {{
  echo "ERROR: $1" >&2
  show_usage
  exit 1
}}

# Parse command line arguments
PARAM1=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_usage
      exit 0
      ;;
    -p|--param1)
      PARAM1="$2"
      shift 2
      ;;
    *)
      error "Unknown option: $1"
      ;;
  esac
done

# TODO: Implement tool functionality

echo "Tool executed successfully. Please implement the actual functionality."
echo "Parameters:"
echo "  param1: $PARAM1"

exit 0
'''
    
    async def _generate_readme(
        self,
        name: str,
        description: str,
        implementation_type: str,
        capabilities: Optional[List[Dict[str, str]]],
        parameters: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Generate README file."""
        system_prompt = """You are an expert technical writer tasked with creating a README for a tool.
Create a comprehensive README that explains how to use the tool, its purpose, and provides examples."""

        capabilities_text = ""
        if capabilities:
            capabilities_text = "## Capabilities\n\n" + "\n".join([f"- **{c['name']}**: {c['description']}" for c in capabilities]) + "\n\n"
        
        parameters_text = ""
        if parameters:
            parameters_text += "## Parameters\n\n"
            for param in parameters:
                required = "Required" if param.get("required", False) else "Optional"
                default = f" (default: `{param.get('default_value', 'None')})`" if "default_value" in param else ""
                parameters_text += f"- **{param['name']}** ({param.get('type', 'string')}, {required}){default}: {param['description']}\n"
            parameters_text += "\n"

        user_prompt = f"""Create a README for a {implementation_type} tool named '{name}' that {description}.

Include these sections:
1. Introduction/Overview
2. Installation
3. Usage
4. Examples
5. Parameters (if applicable)
6. Capabilities (if applicable)
7. License

{capabilities_text}
{parameters_text}

Return only the markdown content with no additional text."""

        try:
            # Generate the README
            readme = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            return readme
        except Exception as e:
            logger.error(f"Error generating README: {str(e)}")
            # Return a fallback README
            return f"""# {name.title()} Tool

{description}

## Installation

```bash
# Python tool
pip install -r requirements.txt

# JavaScript tool
npm install
```

## Usage

```python
# Python example
from {name.lower()} import main

result = main({"param1": "value1"})
print(result)
```

## Parameters

- **param1** (string, Optional): Example parameter

## License

MIT
"""
    
    async def _generate_requirements(self, name: str, description: str, implementation_type: str) -> str:
        """Generate requirements file for Python tools."""
        if implementation_type != "python":
            return ""
            
        system_prompt = """You are an expert Python developer tasked with creating a requirements.txt file for a tool.
Create a concise requirements.txt with the minimal dependencies needed for the tool to function."""

        user_prompt = f"""Create a requirements.txt file for a Python tool named '{name}' that {description}.

List only the essential dependencies with appropriate version constraints.
Do not include development dependencies like pytest or flake8.
"""

        try:
            # Generate the requirements
            requirements = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response
            requirements = requirements.strip()
            if requirements.startswith("```"):
                requirements = requirements[3:].strip()
            if requirements.endswith("```"):
                requirements = requirements[:-3].strip()
            
            return requirements
        except Exception as e:
            logger.error(f"Error generating requirements: {str(e)}")
            # Return a fallback requirements file
            return """# Core dependencies
requests>=2.25.0
pydantic>=1.8.0
"""
    
    async def _generate_package_json(self, name: str, description: str, implementation_type: str) -> str:
        """Generate package.json for JavaScript/TypeScript tools."""
        if implementation_type not in ["js", "javascript", "typescript"]:
            return ""
            
        system_prompt = """You are an expert JavaScript/TypeScript developer tasked with creating a package.json file for a tool.
Create a concise package.json with the minimal dependencies needed for the tool to function."""

        user_prompt = f"""Create a package.json file for a {implementation_type} tool named '{name}' that {description}.

Include:
1. Basic package info (name, version, description)
2. Main script entry point
3. Essential dependencies
4. Scripts for testing
5. Appropriate license
"""

        try:
            # Generate the package.json
            package_json = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response
            package_json = package_json.strip()
            if package_json.startswith("```json"):
                package_json = package_json[7:].strip()
            if package_json.startswith("```"):
                package_json = package_json[3:].strip()
            if package_json.endswith("```"):
                package_json = package_json[:-3].strip()
            
            return package_json
        except Exception as e:
            logger.error(f"Error generating package.json: {str(e)}")
            # Return a fallback package.json
            is_ts = implementation_type == "typescript"
            ts_deps = """,
  "devDependencies": {
    "@types/jest": "^29.5.0",
    "@types/node": "^18.15.0",
    "typescript": "^5.0.0",
    "ts-jest": "^29.1.0"
  }""" if is_ts else ""
            
            return f"""{{
  "name": "{name.lower()}",
  "version": "0.1.0",
  "description": "{description}",
  "main": "{name.lower()}.{is_ts and 'js' or 'js'}",
  "scripts": {{
    "test": "jest"{is_ts and ',\n    "build": "tsc"' or ''}
  }},
  "keywords": [
    "ergon",
    "tool",
    "{name.lower()}"
  ],
  "author": "Ergon",
  "license": "MIT",
  "dependencies": {{
    "axios": "^1.3.0"
  }}{"" if not is_ts else ts_deps}
}}
"""
    
    async def _generate_parameters(
        self, 
        name: str, 
        description: str, 
        implementation_type: str,
        tool_files: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Generate parameters based on tool files."""
        system_prompt = """You are an expert developer tasked with analyzing a tool implementation and extracting its parameters.
Analyze the code and identify all parameters that the tool accepts, along with their types, descriptions, and whether they are required."""

        # Find the main implementation file
        main_file = None
        for file in tool_files:
            if file["filename"] == f"{name.lower()}.py" or file["filename"] == f"{name.lower()}.{self._get_extension(implementation_type)}":
                main_file = file
                break
        
        if not main_file:
            return []
        
        user_prompt = f"""Analyze this {implementation_type} tool code and extract all parameters:

```
{main_file["content"]}
```

Return a JSON array of parameter objects with these properties:
- name: The parameter name
- description: Brief description of what the parameter does
- type: Data type (string, number, boolean, array, object)
- required: Whether the parameter is required (true/false)
- default_value: Default value if any

Format your response as a valid JSON array, nothing else.
"""

        try:
            # Generate parameters
            parameters_json = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response and parse JSON
            parameters_json = parameters_json.strip()
            if parameters_json.startswith("```json"):
                parameters_json = parameters_json[7:].strip()
            if parameters_json.startswith("```"):
                parameters_json = parameters_json[3:].strip()
            if parameters_json.endswith("```"):
                parameters_json = parameters_json[:-3].strip()
            
            parameters = json.loads(parameters_json)
            return parameters
        except Exception as e:
            logger.error(f"Error generating parameters: {str(e)}")
            # Return default parameters
            return [
                {
                    "name": "param1",
                    "description": "Example parameter",
                    "type": "string",
                    "required": False,
                    "default_value": None
                }
            ]
    
    async def _generate_capabilities(
        self, 
        name: str, 
        description: str, 
        implementation_type: str,
        tool_files: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Generate capabilities based on tool files."""
        system_prompt = """You are an expert developer tasked with analyzing a tool implementation and extracting its capabilities.
Analyze the code and identify all capabilities that the tool provides."""

        # Find the main implementation file
        main_file = None
        for file in tool_files:
            if file["filename"] == f"{name.lower()}.py" or file["filename"] == f"{name.lower()}.{self._get_extension(implementation_type)}":
                main_file = file
                break
        
        if not main_file:
            return []
        
        user_prompt = f"""Analyze this {implementation_type} tool code and extract its capabilities:

```
{main_file["content"]}
```

Return a JSON array of capability objects with these properties:
- name: Short name for the capability
- description: Detailed description of what the capability does

Format your response as a valid JSON array, nothing else.
"""

        try:
            # Generate capabilities
            capabilities_json = await self.llm_client.acomplete([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Clean up the response and parse JSON
            capabilities_json = capabilities_json.strip()
            if capabilities_json.startswith("```json"):
                capabilities_json = capabilities_json[7:].strip()
            if capabilities_json.startswith("```"):
                capabilities_json = capabilities_json[3:].strip()
            if capabilities_json.endswith("```"):
                capabilities_json = capabilities_json[:-3].strip()
            
            capabilities = json.loads(capabilities_json)
            return capabilities
        except Exception as e:
            logger.error(f"Error generating capabilities: {str(e)}")
            # Return default capabilities based on description
            return [
                {
                    "name": name.lower().replace("_", "-"),
                    "description": description
                }
            ]


# Convenience function to generate a tool synchronously
def generate_tool(
    name: str, 
    description: str,
    implementation_type: str = "python",
    capabilities: Optional[List[Dict[str, str]]] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate a new tool.
    
    Args:
        name: Name of the tool
        description: Description of the tool
        implementation_type: Implementation type (python, js, bash, etc.)
        capabilities: Optional list of capabilities
        parameters: Optional list of parameters
        model_name: Name of the model to use for generation
        temperature: Temperature for generation
    
    Returns:
        Dictionary with tool details and files
    """
    generator = ToolGenerator(model_name=model_name, temperature=temperature)
    return asyncio.run(generator.generate(name, description, implementation_type, capabilities, parameters))