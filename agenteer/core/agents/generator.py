"""
Agent generator for creating new AI agents.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging
import importlib

from agenteer.core.database.engine import get_db_session
from agenteer.core.database.models import Agent, AgentFile, AgentTool, DocumentationPage
from agenteer.core.vector_store.faiss_store import FAISSDocumentStore
from agenteer.core.llm.client import LLMClient
from agenteer.utils.config.settings import settings

# Import file generators
from agenteer.core.agents.generators.code_generator import (
    generate_main_file,
    generate_tools_file,
    generate_prompts_file,
    generate_requirements_file,
    generate_env_file,
    generate_readme_file
)
from agenteer.core.agents.generators.fallbacks import (
    generate_fallback_main_file,
    generate_fallback_tools_file,
    generate_fallback_prompts_file,
    generate_fallback_requirements_file,
    generate_fallback_readme_file,
    generate_fallback_env_file
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.value))


class AgentGenerator:
    """
    Generator for creating new AI agents.
    
    This class is responsible for generating the necessary code and
    configuration for a new AI agent.
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """
        Initialize the agent generator.
        
        Args:
            model_name: Name of the model to use for generation (defaults to settings)
            temperature: Temperature for generation (0-1)
        """
        self.model_name = model_name or settings.default_model
        self.temperature = temperature
        self.llm_client = LLMClient(model_name=self.model_name, temperature=self.temperature)
        self.vector_store = FAISSDocumentStore()
    
    async def generate(
        self, 
        name: str, 
        description: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent
            tools: Optional list of tools for the agent
        
        Returns:
            Dictionary with agent details and files
        """
        # Validate name (alphanumeric with underscores)
        if not name.replace("_", "").isalnum():
            raise ValueError("Agent name must contain only alphanumeric characters and underscores")
        
        # Search for relevant documentation
        relevant_docs = await self._search_documentation(description, name, tools)
        
        # Generate agent code
        system_prompt = await self._generate_system_prompt(name, description, tools)
        agent_files = await self._generate_agent_files(name, description, tools, relevant_docs)
        
        # Return agent data
        return {
            "name": name,
            "description": description,
            "model_name": self.model_name,
            "system_prompt": system_prompt,
            "tools": tools or [],
            "files": agent_files
        }
    
    async def _search_documentation(
        self, 
        description: str,
        name: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documentation."""
        # Construct search query from description and tools
        query_parts = [f"Create an agent named {name} that {description}"]
        
        if tools:
            tool_names = [tool["name"] for tool in tools]
            query_parts.append(f"using tools: {', '.join(tool_names)}")
        
        query = " ".join(query_parts)
        
        # Search vector store
        docs = self.vector_store.search(query, top_k=5)
        
        # If no docs in vector store yet, get from database
        if not docs:
            with get_db_session() as db:
                db_docs = db.query(DocumentationPage).limit(5).all()
                docs = [
                    {
                        "id": f"doc_{doc.id}",
                        "content": doc.content,
                        "metadata": {
                            "title": doc.title,
                            "url": doc.url,
                            "source": doc.source
                        }
                    }
                    for doc in db_docs
                ]
        
        return docs
    
    async def _generate_system_prompt(
        self,
        name: str,
        description: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate system prompt for the agent."""
        template = f"""You are {name}, an AI assistant. {description}

Your goal is to provide helpful, accurate, and friendly responses to user queries.

Always be respectful and avoid any harmful, illegal, unethical or deceptive content.
If you're unsure about something, acknowledge that limitation rather than making up information.
"""
        
        if tools:
            tool_descriptions = "\n".join(f"- {tool['name']}: {tool.get('description', 'No description')}" for tool in tools)
            template += f"\n\nYou have access to the following tools:\n{tool_descriptions}\n"
            template += "\nWhen a tool would be helpful for answering a question, use it rather than making up information."
        
        # For simple agents, we can use the template directly
        # For more complex agents, we could use the LLM to generate a better prompt
        if len(description) > 100 or (tools and len(tools) > 2):
            # Use LLM to generate a better system prompt
            messages = [
                {"role": "system", "content": "You are an expert at creating system prompts for AI assistants. Your goal is to create a clear, concise, and effective system prompt based on the provided description and tools."},
                {"role": "user", "content": f"Create a system prompt for an AI assistant with these specifications:\n\nName: {name}\nDescription: {description}\nTools: {json.dumps(tools) if tools else 'None'}\n\nThe system prompt should be comprehensive and cover the assistant's purpose, tone, limitations, and how it should use its tools."}
            ]
            
            try:
                improved_prompt = await self.llm_client.acomplete(messages)
                if improved_prompt and len(improved_prompt) > len(template):
                    return improved_prompt
            except Exception as e:
                logger.error(f"Error generating system prompt: {str(e)}")
                # Fall back to template
        
        return template
    
    async def _generate_agent_files(
        self,
        name: str,
        description: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        relevant_docs: List[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Generate agent implementation files."""
        files = []
        
        # Prepare context for generation
        docs_text = ""
        if relevant_docs:
            docs_text = "\n\n".join([
                f"--- Document: {doc['metadata']['title']} ---\n{doc['content'][:500]}..."
                for doc in relevant_docs
            ])
        
        # Generate main agent file
        main_file = None
        try:
            main_file = await generate_main_file(
                self.llm_client, name, description, 
                tools, docs_text
            )
        except Exception as error:
            logger.error(f"Error generating main file: {str(error)}")
            main_file = generate_fallback_main_file(name, description, self.model_name)
            
        files.append({
            "filename": "agent.py",
            "file_type": "python",
            "content": main_file
        })
        
        # Generate tools file if needed
        if tools:
            tools_file = None
            try:
                tools_file = await generate_tools_file(
                    self.llm_client, name, tools, docs_text
                )
            except Exception as error:
                logger.error(f"Error generating tools file: {str(error)}")
                tools_file = generate_fallback_tools_file(name, tools)
                
            files.append({
                "filename": "agent_tools.py",
                "file_type": "python",
                "content": tools_file
            })
        
        # Generate prompts file
        prompts_file = None
        try:
            prompts_file = await generate_prompts_file(
                self.llm_client, name, description, tools
            )
        except Exception as error:
            logger.error(f"Error generating prompts file: {str(error)}")
            prompts_file = generate_fallback_prompts_file(name, description, tools)
            
        files.append({
            "filename": "agent_prompts.py",
            "file_type": "python",
            "content": prompts_file
        })
        
        # Generate requirements file
        requirements = None
        try:
            requirements = await generate_requirements_file(
                self.llm_client, name, description, tools
            )
        except Exception as error:
            logger.error(f"Error generating requirements file: {str(error)}")
            requirements = generate_fallback_requirements_file()
            
        files.append({
            "filename": "requirements.txt",
            "file_type": "requirements",
            "content": requirements
        })
        
        # Generate .env example file
        env_example = None
        try:
            env_example = await generate_env_file(
                self.llm_client, name, self.model_name
            )
        except Exception as error:
            logger.error(f"Error generating env file: {str(error)}")
            env_example = generate_fallback_env_file(name, self.model_name)
            
        files.append({
            "filename": ".env.example",
            "file_type": "env",
            "content": env_example
        })
        
        # Generate README
        readme = None
        try:
            readme = await generate_readme_file(
                self.llm_client, name, description, tools
            )
        except Exception as error:
            logger.error(f"Error generating README file: {str(error)}")
            readme = generate_fallback_readme_file(name, description, tools)
            
        files.append({
            "filename": "README.md",
            "file_type": "markdown",
            "content": readme
        })
        
        return files
        
    async def generate_github_agent(
        self, 
        name: str, 
        description: str,
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a GitHub agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent
            tools: List of GitHub tools for the agent
        
        Returns:
            Dictionary with agent details and files
        """
        # Validate name (alphanumeric with underscores)
        if not name.replace("_", "").isalnum():
            raise ValueError("Agent name must contain only alphanumeric characters and underscores")
        
        # Create GitHub-specific agent
        from agenteer.core.agents.generators.github_generator import (
            generate_github_tools_file,
            generate_github_agent_file
        )
        
        # Generate system prompt for GitHub agent
        system_prompt = f"""You are {name}, a GitHub agent assistant. {description}

Your goal is to help users interact with GitHub repositories, issues, pull requests, and other GitHub features.

You can create, delete, and manage repositories, create issues, list repositories, and perform other GitHub operations.

Always be respectful and avoid any harmful operations. When a user asks you to perform a GitHub operation,
use your tools to accomplish the task rather than explaining how to do it manually.

If you're asked to do something that could be destructive (like deleting a repository), ask for confirmation
before proceeding.
"""
        
        # Generate agent files
        files = []
        
        # Generate main agent file
        try:
            main_file = await generate_github_agent_file(self.llm_client, name)
            files.append({
                "filename": "agent.py",
                "file_type": "python",
                "content": main_file
            })
        except Exception as error:
            logger.error(f"Error generating GitHub agent file: {str(error)}")
            raise
        
        # Generate GitHub tools file
        try:
            tools_file = await generate_github_tools_file(self.llm_client, name)
            files.append({
                "filename": "agent_tools.py",
                "file_type": "python",
                "content": tools_file
            })
        except Exception as error:
            logger.error(f"Error generating GitHub tools file: {str(error)}")
            raise
        
        # Generate requirements file
        github_requirements = """
# GitHub agent requirements
PyGithub>=2.1.1
python-dotenv>=1.0.0
        """
        files.append({
            "filename": "requirements.txt",
            "file_type": "requirements",
            "content": github_requirements.strip()
        })
        
        # Generate .env example file
        env_example = f"""
# GitHub API settings
GITHUB_API_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username_here

# Model settings
MODEL_NAME={self.model_name}
        """
        files.append({
            "filename": ".env.example",
            "file_type": "env",
            "content": env_example.strip()
        })
        
        # Generate README
        readme = f"""
# {name} - GitHub Agent

{description}

## Features

This GitHub agent can:

- List repositories
- Create new repositories
- Delete repositories
- Get repository details
- Create issues
- List issues
- Create pull requests
- List branches

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Add your GitHub API token
   - Add your GitHub username

3. Run the agent:
   ```python
   from agent import process_request

   # Use the agent
   response = process_request("list my repositories")
   print(response)
   ```

## Example Commands

- "List my repositories"
- "Show my public repositories"
- "Create a repository named my-new-repo"
- "Create a private repository named secret-project"
- "Delete repository named old-repo"
- "Get repository details for my-repo"
- "Create an issue in repo my-repo titled 'Fix the bug'"
- "List issues in repo my-repo"
- "Create a pull request in repo my-repo titled 'Add new feature' from branch feature to branch main"
- "List branches in repo my-repo"
        """
        files.append({
            "filename": "README.md",
            "file_type": "markdown",
            "content": readme.strip()
        })
        
        # Return agent data
        return {
            "name": name,
            "description": description,
            "model_name": self.model_name,
            "system_prompt": system_prompt,
            "tools": tools,
            "files": files
        }


def _ensure_lowercase_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all keys in a dictionary are lowercase."""
    return {k.lower(): v for k, v in d.items()}


def generate_agent(
    name: str, 
    description: str,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    tools: Optional[List[Dict[str, Any]]] = None,
    agent_type: str = "standard"
) -> Dict[str, Any]:
    """
    Synchronous wrapper for agent generation.
    
    Args:
        name: Name of the agent
        description: Description of the agent
        model_name: Name of the model to use
        temperature: Temperature for generation
        tools: Optional list of tools for the agent
        agent_type: Type of agent to create (standard, github, mail, etc.)
    
    Returns:
        Dictionary with agent details and files
    """
    generator = AgentGenerator(model_name=model_name, temperature=temperature)
    
    if agent_type == "github":
        # Import the GitHub tools dynamically to avoid circular imports
        from agenteer.core.agents.generators.github_generator import get_github_tools
        # Override tools with GitHub tools
        github_tools = get_github_tools()
        return asyncio.run(generator.generate_github_agent(name, description, github_tools))
    elif agent_type == "mail":
        # Import the mail generator dynamically to avoid circular imports
        from agenteer.core.agents.generators.mail_generator import generate_mail_agent
        # Generate mail agent
        return generate_mail_agent(name, description, model_name or settings.default_model)
    elif agent_type == "browser":
        # Import the browser generator dynamically to avoid circular imports
        from agenteer.core.agents.generators.browser_generator import BrowserAgentGenerator
        # Generate browser agent
        browser_generator = BrowserAgentGenerator()
        browser_data = browser_generator.generate(name, description)
        
        return {
            "name": browser_data["name"],
            "description": browser_data["description"],
            "system_prompt": browser_data["system_prompt"],
            "tools": browser_data["tools"],
            "files": [] # No files for browser agent
        }
    else:
        return asyncio.run(generator.generate(name, description, tools))


async def generate_github_agent(
    name: str, 
    description: str,
    model_name: Optional[str] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Synchronous wrapper for GitHub agent generation.
    
    Args:
        name: Name of the agent
        description: Description of the agent
        model_name: Name of the model to use
        temperature: Temperature for generation
    
    Returns:
        Dictionary with agent details and files
    """
    generator = AgentGenerator(model_name=model_name, temperature=temperature)
    
    # Import the GitHub tools dynamically to avoid circular imports
    from agenteer.core.agents.generators.github_generator import get_github_tools
    github_tools = get_github_tools()
    
    return asyncio.run(generator.generate_github_agent(name, description, github_tools))
