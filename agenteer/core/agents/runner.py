"""
Agent runner for executing AI agents.
"""

import os
import sys
import json
import importlib.util
import tempfile
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import logging
import asyncio

from agenteer.core.database.engine import get_db_session
from agenteer.core.database.models import Agent, AgentExecution, AgentMessage, AgentTool, AgentFile
from agenteer.core.llm.client import LLMClient
from agenteer.utils.config.settings import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.value))


class AgentException(Exception):
    """Exception raised by the agent runner."""
    pass


class AgentRunner:
    """
    Runner for executing AI agents.
    
    This class is responsible for running existing AI agents and
    handling their interactions.
    """
    
    def __init__(
        self,
        agent: Agent,
        execution_id: Optional[int] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Initialize the agent runner.
        
        Args:
            agent: Agent to run
            execution_id: Optional execution ID for tracking
            model_name: Optional model name override
            temperature: Temperature for LLM
        """
        self.agent = agent
        self.execution_id = execution_id
        self.model_name = model_name or agent.model_name
        self.temperature = temperature
        
        # Initialize LLM client
        self.llm_client = LLMClient(model_name=self.model_name, temperature=self.temperature)
        
        # Create working directory if it doesn't exist
        self.working_dir = self._setup_agent_environment()
    
    def _setup_agent_environment(self) -> str:
        """
        Set up the agent's execution environment.
        
        Returns:
            Path to the agent's working directory
        """
        # Create temporary directory for agent
        working_dir = tempfile.mkdtemp(prefix=f"agenteer_{self.agent.name}_")
        
        # Get agent files from database
        with get_db_session() as db:
            files = db.query(AgentFile).filter(AgentFile.agent_id == self.agent.id).all()
            
            # Write files to disk
            for file in files:
                file_path = os.path.join(working_dir, file.filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file.content)
        
        return working_dir
    
    def run(self, input_text: str) -> str:
        """
        Run the agent with the given input.
        
        Args:
            input_text: Input to send to the agent
        
        Returns:
            Agent's response
        """
        return asyncio.run(self.arun(input_text))
    
    async def arun(self, input_text: str) -> str:
        """
        Run the agent with the given input asynchronously.
        
        Args:
            input_text: Input to send to the agent
        
        Returns:
            Agent's response
        """
        # Check if agent has tools
        with get_db_session() as db:
            tools = db.query(AgentTool).filter(AgentTool.agent_id == self.agent.id).all()
        
        if tools:
            # Agent has tools, use function calling
            return await self._run_with_tools(input_text, tools)
        else:
            # Simple agent, just use completion
            return await self._run_simple(input_text)
    
    async def _run_simple(self, input_text: str) -> str:
        """Run a simple agent without tools."""
        # Prepare messages
        messages = [
            {"role": "system", "content": self.agent.system_prompt},
            {"role": "user", "content": input_text}
        ]
        
        # Get response from LLM
        response = await self.llm_client.acomplete(messages)
        
        # Record in database if execution_id provided
        if self.execution_id:
            with get_db_session() as db:
                message = AgentMessage(
                    execution_id=self.execution_id,
                    role="assistant",
                    content=response
                )
                db.add(message)
                db.commit()
        
        return response
    
    async def _run_with_tools(self, input_text: str, tools: List[AgentTool]) -> str:
        """Run an agent with tools."""
        # Try to load tool implementations
        tool_funcs = self._load_tool_functions()
        
        # Register mail tools if this is a mail agent
        if "mail" in self.agent.name.lower() or "email" in self.agent.name.lower():
            try:
                from agenteer.core.agents.mail.tools import register_mail_tools
                register_mail_tools(tool_funcs)
            except ImportError as e:
                logger.error(f"Failed to import mail tools: {str(e)}")
        
        # For GitHub agent (or other agents with non-LLM implementation)
        if "github" in self.agent.name.lower() and "process_request" in tool_funcs:
            try:
                # Direct call to the agent's process_request function
                return tool_funcs["process_request"](input_text)
            except Exception as e:
                logger.error(f"Error calling GitHub agent: {str(e)}")
                return f"Error calling GitHub agent: {str(e)}"
        
        # Standard LLM-based agent path
        # Prepare tool definitions for the LLM
        tool_definitions = []
        for tool in tools:
            try:
                tool_def = json.loads(tool.function_def)
                tool_definitions.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool_def
                    }
                })
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse tool definition for {tool.name}: {str(e)}")
        
        # OpenAI-style messages with tool calling
        messages = [
            {"role": "system", "content": self.agent.system_prompt},
            {"role": "user", "content": input_text}
        ]
        
        # Simulate a conversation with tools
        for _ in range(5):  # Maximum 5 tool calls per conversation
            try:
                # Get response from LLM that may include a tool call
                # For simplicity, we're mocking this for now since our LLM client doesn't support function calling yet
                response = await self._mock_tool_calling(messages, tool_definitions, input_text)
                
                # Check if response includes a tool call
                if "function_call" in response:
                    function_call = response["function_call"]
                    tool_name = function_call["name"]
                    tool_arguments = json.loads(function_call["arguments"])
                    
                    # Record tool call in database
                    if self.execution_id:
                        with get_db_session() as db:
                            message = AgentMessage(
                                execution_id=self.execution_id,
                                role="tool",
                                content="",
                                tool_name=tool_name,
                                tool_input=json.dumps(tool_arguments)
                            )
                            db.add(message)
                            db.commit()
                    
                    # Execute tool if available
                    if tool_name in tool_funcs:
                        # Call the tool function - handle both async and sync functions
                        tool_func = tool_funcs[tool_name]
                        if asyncio.iscoroutinefunction(tool_func):
                            tool_result = await tool_func(**tool_arguments)
                        else:
                            # Handle synchronous function
                            tool_result = tool_func(**tool_arguments)
                    else:
                        tool_result = f"Tool {tool_name} not found"
                    
                    # Record tool result in database
                    if self.execution_id:
                        with get_db_session() as db:
                            message = db.query(AgentMessage).filter(
                                AgentMessage.execution_id == self.execution_id,
                                AgentMessage.tool_name == tool_name
                            ).order_by(AgentMessage.id.desc()).first()
                            
                            if message:
                                message.tool_output = tool_result
                                db.commit()
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "function",
                        "name": tool_name,
                        "content": tool_result
                    })
                else:
                    # Final response without tool call
                    if self.execution_id:
                        with get_db_session() as db:
                            message = AgentMessage(
                                execution_id=self.execution_id,
                                role="assistant",
                                content=response["content"]
                            )
                            db.add(message)
                            db.commit()
                    
                    return response["content"]
            
            except Exception as e:
                logger.error(f"Error in agent tool execution: {str(e)}")
                return f"Error executing agent: {str(e)}"
        
        # If we reach here, we've hit the maximum number of tool calls
        return "I've made too many tool calls without reaching a conclusion. Please try a more specific query."
    
    async def _mock_tool_calling(
        self, 
        messages: List[Dict[str, str]], 
        tool_definitions: List[Dict[str, Any]],
        user_input: str
    ) -> Dict[str, Any]:
        """
        Mock function calling until we implement it in the LLM client.
        
        In a real implementation, we would use the LLM's function calling API.
        """
        # Extract tool names for the prompt
        tool_names = [tool["function"]["name"] for tool in tool_definitions]
        tool_descriptions = [f"{tool['function']['name']}: {tool['function']['description']}" for tool in tool_definitions]
        
        tool_prompt = f"""Available tools: {', '.join(tool_names)}

Tool descriptions:
{os.linesep.join(tool_descriptions)}

To use a tool, respond with a JSON object with this format: 
{{"function_call": {{"name": "tool_name", "arguments": {{"arg1": "value1"}}}}}}

If you don't need to use a tool, respond with your regular text answer."""
        
        # Add tool instructions to the system message
        system_message_with_tools = f"{messages[0]['content']}\n\n{tool_prompt}"
        messages_with_tools = [{"role": "system", "content": system_message_with_tools}] + messages[1:]
        
        # Check if we're dealing with a GitHub agent request
        if any(tool["function"]["name"].startswith("list_repositories") for tool in tool_definitions):
            # Handle GitHub tools directly based on keywords
            for tool in tool_definitions:
                tool_name = tool["function"]["name"]
                
                if "list" in user_input.lower() and "repositories" in user_input.lower() and tool_name == "list_repositories":
                    return {
                        "function_call": {
                            "name": tool_name,
                            "arguments": json.dumps({"visibility": "all", "sort": "updated"})
                        }
                    }
                elif "create" in user_input.lower() and "repository" in user_input.lower() and tool_name == "create_repository":
                    # Try to extract name from input
                    name = user_input.split("called ")[-1].split()[0].strip() if "called " in user_input else "new-repo"
                    return {
                        "function_call": {
                            "name": tool_name,
                            "arguments": json.dumps({"name": name, "private": "private" in user_input.lower()})
                        }
                    }
                # Add more specialized GitHub tool handlers here
        
        # Generic approach for other tools
        for tool in tool_definitions:
            tool_name = tool["function"]["name"]
            tool_desc = tool["function"]["description"]
            
            # Simple heuristic to decide if tool might be needed
            if any(kw.lower() in user_input.lower() for kw in tool_name.split("_") + tool_desc.split()):
                # Simulate a function call response
                arguments = {}
                for param_name, param_def in tool["function"]["parameters"].get("properties", {}).items():
                    if param_name == "query":
                        arguments[param_name] = user_input
                    elif param_name == "input":
                        arguments[param_name] = user_input
                    else:
                        # For repo_name, try to extract from the input
                        if param_name == "repo_name" and "repo" in user_input.lower():
                            parts = user_input.lower().split("repo ")
                            if len(parts) > 1:
                                repo_name = parts[1].split()[0].strip()
                                arguments[param_name] = repo_name
                        else:
                            # Use default for required parameters
                            if param_name in tool["function"]["parameters"].get("required", []):
                                arguments[param_name] = f"default_{param_name}"
                
                return {
                    "function_call": {
                        "name": tool_name,
                        "arguments": json.dumps(arguments)
                    }
                }
        
        # If no tool needed, get regular completion
        try:
            response = await self.llm_client.acomplete(messages)
            return {"content": response}
        except Exception as e:
            # Fallback response if something goes wrong
            return {"content": f"I'm having trouble processing your request. Please try asking in a different way. Error: {str(e)}"}
        
    
    def _load_tool_functions(self) -> Dict[str, callable]:
        """
        Load tool functions from agent files.
        
        Returns:
            Dictionary mapping tool names to callable functions
        """
        tools = {}
        
        try:
            # Check if agent_tools.py exists
            tools_path = os.path.join(self.working_dir, "agent_tools.py")
            if not os.path.exists(tools_path):
                return tools
            
            # Load the module
            spec = importlib.util.spec_from_file_location("agent_tools", tools_path)
            if spec is None or spec.loader is None:
                return tools
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all callable functions in the module
            for name in dir(module):
                if name.startswith("_"):
                    continue
                
                func = getattr(module, name)
                if callable(func):
                    tools[name] = func
            
            return tools
            
        except Exception as e:
            logger.error(f"Error loading tool functions: {str(e)}")
            return {}
    
    async def arun_stream(self, input_text: str):
        """
        Run the agent with streaming response.
        
        Args:
            input_text: Input to send to the agent
        
        Yields:
            Chunks of the agent's response
        """
        # Simple streaming implementation
        messages = [
            {"role": "system", "content": self.agent.system_prompt},
            {"role": "user", "content": input_text}
        ]
        
        # Record in database if execution_id provided
        if self.execution_id:
            with get_db_session() as db:
                full_response = ""
                async for chunk in self.llm_client.acomplete_stream(messages):
                    full_response += chunk
                    yield chunk
                
                # Record the complete response
                message = AgentMessage(
                    execution_id=self.execution_id,
                    role="assistant",
                    content=full_response
                )
                db.add(message)
                db.commit()
        else:
            # Just stream the response without recording
            async for chunk in self.llm_client.acomplete_stream(messages):
                yield chunk
    
    def cleanup(self):
        """Clean up agent resources."""
        # Remove temporary directory
        if hasattr(self, 'working_dir') and os.path.exists(self.working_dir):
            import shutil
            shutil.rmtree(self.working_dir)
