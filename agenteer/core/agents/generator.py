"""
Agent generator for creating new AI agents.
"""

from typing import Dict, Any, List, Optional
import json
import os
from pydantic import BaseModel
from datetime import datetime

from agenteer.utils.config.settings import settings


class AgentGenerator:
    """
    Generator for creating new AI agents.
    
    This class is responsible for generating the necessary code and
    configuration for a new AI agent.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the agent generator.
        
        Args:
            model: Model to use for generation (defaults to settings)
        """
        self.model_name = model or settings.default_model
    
    def generate(
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
        # TODO: Implement actual agent generation with LLM
        # This is a placeholder implementation
        
        # Generate a default system prompt
        system_prompt = f"""You are {name}, an AI assistant. {description}
        
Your goal is to provide helpful, accurate, and friendly responses to user queries.

Always be respectful and avoid any harmful, illegal, unethical or deceptive content.
If you're unsure about something, acknowledge that limitation rather than making up information.
"""
        
        # Generate agent files
        agent_file_content = f"""from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize model
model_name = os.getenv("AGENT_MODEL", "{self.model_name}")
api_key = os.getenv("ANTHROPIC_API_KEY" if "claude" in model_name.lower() else "OPENAI_API_KEY")
model = AnthropicModel(model_name, api_key=api_key) if "claude" in model_name.lower() else OpenAIModel(model_name, api_key=api_key)

# Create agent
{name.lower()}_agent = Agent(
    model,
    system_prompt=\"\"\"{system_prompt}\"\"\"
)

# Run agent
async def run_agent(user_input: str):
    result = await {name.lower()}_agent.run(user_input)
    return result.data

if __name__ == "__main__":
    import asyncio
    
    # Simple CLI for testing
    print(f"Welcome to {name}\! Type 'exit' to quit.")
    
    async def main():
        while True:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            response = await run_agent(user_input)
            print(f"{name}: {response}")
    
    asyncio.run(main())
"""
        
        # Create requirements file
        requirements_content = """pydantic-ai>=0.7.0
python-dotenv>=1.0.0
anthropic>=0.6.0
openai>=1.1.0
"""
        
        # Create .env example file
        env_example_content = f"""# API Keys (only one required)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Agent settings
AGENT_MODEL={self.model_name}
"""
        
        # Return agent data
        return {
            "name": name,
            "description": description,
            "model_name": self.model_name,
            "system_prompt": system_prompt,
            "tools": tools or [],
            "files": [
                {
                    "filename": "agent.py",
                    "file_type": "python",
                    "content": agent_file_content
                },
                {
                    "filename": "requirements.txt",
                    "file_type": "requirements",
                    "content": requirements_content
                },
                {
                    "filename": ".env.example",
                    "file_type": "env",
                    "content": env_example_content
                }
            ]
        }
