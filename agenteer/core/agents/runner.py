"""
Agent runner for executing AI agents.
"""

import os
import sys
import json
import importlib.util
import tempfile
import re
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
        temperature: float = 0.7,
        timeout: Optional[int] = None,
        timeout_action: str = "log"
    ):
        """
        Initialize the agent runner.
        
        Args:
            agent: Agent to run
            execution_id: Optional execution ID for tracking
            model_name: Optional model name override
            temperature: Temperature for LLM
            timeout: Optional timeout in seconds for agent execution
            timeout_action: Action to take on timeout ('log', 'alarm', or 'kill')
        """
        self.agent = agent
        self.execution_id = execution_id
        self.model_name = model_name or agent.model_name
        self.temperature = temperature
        self.timeout = timeout
        self.timeout_action = timeout_action.lower() if timeout_action else "log"
        
        # Validate timeout action
        if self.timeout_action not in ["log", "alarm", "kill"]:
            logger.warning(f"Invalid timeout action '{timeout_action}'. Using 'log' instead.")
            self.timeout_action = "log"
        
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
    
    async def run(self, input_text: str) -> str:
        """
        Run the agent with the given input.
        
        Args:
            input_text: Input to send to the agent
        
        Returns:
            Agent's response
        """
        start_time = datetime.now()
        
        # Log agent execution with name for better traceability
        logger.info(f"Running agent '{self.agent.name}' (ID: {self.agent.id})")
        
        try:
            if self.timeout:
                # Run with timeout
                try:
                    return asyncio.run(self._run_with_timeout(input_text))
                except asyncio.TimeoutError:
                    elapsed_time = (datetime.now() - start_time).total_seconds()
                    error_msg = f"Agent '{self.agent.name}' execution timed out after {elapsed_time:.2f} seconds (timeout: {self.timeout}s)"
                    
                    # Log the timeout with agent name
                    logger.warning(error_msg)
                    
                    # Record the timeout in the database if execution_id is provided
                    if self.execution_id:
                        with get_db_session() as db:
                            execution = db.query(AgentExecution).filter(AgentExecution.id == self.execution_id).first()
                            if execution:
                                execution.success = False
                                execution.error = error_msg
                                execution.completed_at = datetime.now()
                                db.commit()
                            
                            # Add error message to the conversation
                            message = AgentMessage(
                                execution_id=self.execution_id,
                                role="system",
                                content=error_msg
                            )
                            db.add(message)
                            db.commit()
                    
                    # Return appropriate message based on timeout action
                    if self.timeout_action == "alarm":
                        return f"⚠️ TIMEOUT ALARM: {error_msg}"
                    elif self.timeout_action == "kill":
                        return f"❌ EXECUTION TERMINATED: {error_msg}"
                    else:  # "log"
                        return f"I wasn't able to complete the task in the allowed time. {error_msg}"
            else:
                # Run without timeout - use direct await as we're likely already in an async context
                response = await self.arun(input_text)
                
                # Log successful completion with timing
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Agent '{self.agent.name}' (ID: {self.agent.id}) completed successfully in {elapsed_time:.2f} seconds")
                
                return response
        except Exception as e:
            # Handle other exceptions with agent name
            elapsed_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Error in agent '{self.agent.name}' after {elapsed_time:.2f} seconds: {str(e)}"
            logger.error(error_msg)
            
            if self.execution_id:
                with get_db_session() as db:
                    execution = db.query(AgentExecution).filter(AgentExecution.id == self.execution_id).first()
                    if execution:
                        execution.success = False
                        execution.error = error_msg
                        execution.completed_at = datetime.now()
                        db.commit()
            
            return f"I encountered an error while processing your request: {str(e)}"
    
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
        
        # Register browser tools if this is a browser agent
        if "browser" in self.agent.name.lower() or self.agent.type == "browser":
            try:
                from agenteer.core.agents.browser.handler import BrowserToolHandler
                browser_handler = BrowserToolHandler()
                # Register browser tool handler
                for tool in tools:
                    if tool.name.startswith("browse_"):
                        # Use a closure to capture each tool name
                        def create_tool_func(tool_name):
                            async def tool_func(**params):
                                return await browser_handler.execute_tool(tool_name, params)
                            return tool_func
                        
                        # Register the tool function
                        tool_funcs[tool.name] = create_tool_func(tool.name)
            except ImportError as e:
                logger.error(f"Failed to import browser tools: {str(e)}")
        
        # Special handling for browser agents with direct workflow
        if self.agent.type == "browser" and "go to" in input_text.lower() and any(x in input_text.lower() for x in ["title", "text", "content"]):
            try:
                # Extract URL from input
                url_pattern = r"go to\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?)"
                url_match = re.search(url_pattern, input_text, re.IGNORECASE)
                
                if url_match and "browse_navigate" in tool_funcs and "browse_get_text" in tool_funcs:
                    url = url_match.group(1)
                    if not url.startswith("http"):
                        url = "https://" + url
                    
                    # First, navigate to the URL
                    logger.info(f"Direct browser workflow: navigating to {url}")
                    navigate_result = await tool_funcs["browse_navigate"](url=url)
                    logger.info(f"Navigation result: {navigate_result}")
                    
                    # Then get the page text
                    logger.info("Direct browser workflow: getting page text")
                    text_result = await tool_funcs["browse_get_text"]()
                    logger.info(f"Got page text (first 100 chars): {text_result[:100] if isinstance(text_result, str) else 'Not a string'}")
                    
                    # Check if we need the title specifically
                    if "title" in input_text.lower() and "browse_get_html" in tool_funcs:
                        # Get HTML to extract title
                        html_result = await tool_funcs["browse_get_html"]()
                        title_pattern = r"<title>(.*?)</title>"
                        title_match = re.search(title_pattern, html_result if isinstance(html_result, str) else "")
                        if title_match:
                            title = title_match.group(1)
                            return f"The title of the page at {url} is: {title}"
                        else:
                            return f"I visited {url} but couldn't find a title tag. Here's some text content: {text_result[:200] if isinstance(text_result, str) else 'Not available'}"
                    else:
                        return f"I visited {url}. Here's the text content: {text_result[:500] if isinstance(text_result, str) else 'Not available'}"
            except Exception as e:
                logger.error(f"Error in direct browser workflow: {str(e)}")
                # Continue with standard workflow if direct approach fails
        
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
                                # Make sure tool_output is stored as a string
                                if isinstance(tool_result, (dict, list)):
                                    message.tool_output = json.dumps(tool_result)
                                else:
                                    message.tool_output = str(tool_result)
                                db.commit()
                    
                    # Add tool result to messages
                    # Convert tool result to string if it's a dict or list
                    if isinstance(tool_result, (dict, list)):
                        messages.append({
                            "role": "function",
                            "name": tool_name,
                            "content": json.dumps(tool_result)
                        })
                    else:
                        messages.append({
                            "role": "function",
                            "name": tool_name,
                            "content": str(tool_result)
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
        logger.warning(f"Maximum tool calls reached. Tool calls made: {len(messages) - 2}")
        for i, msg in enumerate(messages[2:]):
            logger.warning(f"Tool call {i+1}: {json.dumps(msg)}")
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
                
        # Check if we're dealing with a Browser agent request
        elif any(tool["function"]["name"].startswith("browse_") for tool in tool_definitions):
            # Special handling for browser tools
            for tool in tool_definitions:
                tool_name = tool["function"]["name"]
                
                # Handle browse_navigate for URL navigation
                if tool_name == "browse_navigate" and "go to" in user_input.lower():
                    # Extract URL from input
                    url_pattern = r"go to\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?)"
                    url_match = re.search(url_pattern, user_input, re.IGNORECASE)
                    
                    if url_match:
                        url = url_match.group(1)
                        if not url.startswith("http"):
                            url = "https://" + url
                        
                        logger.info(f"Extracted URL for navigation: {url}")
                        return {
                            "function_call": {
                                "name": tool_name,
                                "arguments": json.dumps({"url": url})
                            }
                        }
                
                # Handle get_text after navigation
                if tool_name == "browse_get_text" and any(x in user_input.lower() for x in ["content", "text", "title"]):
                    return {
                        "function_call": {
                            "name": tool_name,
                            "arguments": json.dumps({})
                        }
                    }
        
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
            # Load special tools based on agent type
            agent_type = self.agent.type if hasattr(self.agent, 'type') else None
            if agent_type:
                # Load browser tools if this is a browser agent
                if agent_type == "browser":
                    logger.info("Loading browser tools for browser agent")
                    from agenteer.core.agents.browser.handler import BrowserToolHandler
                    from agenteer.core.agents.browser.tools import BROWSER_TOOLS
                    
                    # Initialize browser tool handler
                    browser_handler = BrowserToolHandler()
                    
                    # Create async wrapper function for each browser tool
                    for tool in BROWSER_TOOLS:
                        tool_name = tool["name"]
                        
                        # Create a closure to capture the tool name
                        async def browser_tool_wrapper(tool_name=tool_name, **kwargs):
                            logger.info(f"Executing browser tool: {tool_name} with args: {kwargs}")
                            return await browser_handler.execute_tool(tool_name, kwargs)
                        
                        # Add wrapper function to tools with the correct name
                        tools[tool_name] = browser_tool_wrapper
                    
                    logger.info(f"Loaded browser tools: {list(tools.keys())}")
                    return tools
            
            # If not a special agent type or special tools failed to load,
            # fall back to loading tools from the agent_tools.py file
            
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
    
    async def _run_with_timeout(self, input_text: str) -> str:
        """
        Run the agent with a timeout.
        
        Args:
            input_text: Input to send to the agent
            
        Returns:
            Agent's response
            
        Raises:
            asyncio.TimeoutError: If the execution exceeds the timeout
        """
        # Log the timeout attempt
        logger.info(f"Running agent '{self.agent.name}' with {self.timeout}s timeout and '{self.timeout_action}' action")
        
        # Create a task for running the agent
        task = asyncio.create_task(self.arun(input_text))
        
        # Wait for the task to complete or timeout
        response = await asyncio.wait_for(task, timeout=self.timeout)
        
        # Log successful completion
        logger.info(f"Agent '{self.agent.name}' completed successfully within timeout period")
        
        return response
    
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
