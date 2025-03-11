"""
Agenteer Command Line Interface
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

from agenteer.utils.config.settings import settings
from agenteer.core.database.engine import init_db

# Initialize console for rich output
console = Console()

# Create Typer app
app = typer.Typer(
    name="agenteer",
    help="Agenteer: AI agent builder with minimal configuration",
    add_completion=False,
)


def version_callback(value: bool):
    """Display version information."""
    if value:
        from agenteer import __version__
        console.print(f"Agenteer CLI v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", callback=version_callback, help="Show version information."
    ),
):
    """Agenteer CLI: Build and run AI agents with minimal configuration."""
    pass


@app.command("init")
def init(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force initialization (overwrite existing setup)"
    ),
):
    """Initialize Agenteer database and configuration."""
    try:
        # Check if database already exists
        if os.path.exists(settings.database_url.replace("sqlite:///", "")) and not force:
            console.print("[yellow]Database already exists. Use --force to reinitialize.[/yellow]")
            raise typer.Exit(1)
        
        with console.status("[bold green]Initializing Agenteer..."):
            # Initialize database
            init_db()
            
            console.print("[bold green]✓[/bold green] Database initialized")
            
            # Check API keys
            if settings.has_openai:
                console.print("[bold green]✓[/bold green] OpenAI API key detected")
            if settings.has_anthropic:
                console.print("[bold green]✓[/bold green] Anthropic API key detected")
            if settings.has_ollama:
                console.print("[bold green]✓[/bold green] Ollama instance detected")
                
            if not (settings.has_openai or settings.has_anthropic or settings.has_ollama):
                console.print("[yellow]⚠ No LLM API keys or local models detected.[/yellow]")
                console.print("  Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or ensure Ollama is running.")
        
        console.print("[bold green]Agenteer initialized successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error during initialization: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command("ui")
def ui(
    port: int = typer.Option(8501, "--port", "-p", help="Port for the Streamlit UI"),
    host: str = typer.Option("localhost", "--host", "-h", help="Host for the Streamlit UI"),
):
    """Start the Agenteer web UI (Streamlit)."""
    try:
        import streamlit.web.cli as stcli
        
        # Initialize database if not exists
        if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
            console.print("[yellow]Database not initialized. Running initialization...[/yellow]")
            init_db()
        
        console.print(f"[bold green]Starting Agenteer UI on http://{host}:{port} ...[/bold green]")
        
        # Run Streamlit app
        ui_path = str(Path(__file__).parent.parent / "ui" / "app.py")
        console.print(f"Starting Streamlit with path: {ui_path}")
        sys.argv = ["streamlit", "run", ui_path, "--server.port", str(port), "--server.address", host]
        stcli.main()
        
    except ImportError:
        console.print("[bold red]Streamlit is not installed. Please install it with 'pip install streamlit'.[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error starting UI: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command("create")
def create(
    name: str = typer.Option(..., "--name", "-n", help="Name for the agent"),
    description: str = typer.Option(None, "--description", "-d", help="Description for the agent"),
    model: str = typer.Option(None, "--model", "-m", help="Model to use (defaults to settings)"),
    agent_type: str = typer.Option("standard", "--type", "-t", help="Type of agent to create (standard, github, mail)"),
):
    """Create a new AI agent with the given specifications."""
    try:
        from agenteer.core.agents.generator import AgentGenerator, generate_agent
        from agenteer.core.database.engine import get_db_session
        from agenteer.core.database.models import Agent, AgentFile, AgentTool
        
        # Initialize database if not exists
        if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
            console.print("[yellow]Database not initialized. Running initialization...[/yellow]")
            init_db()
        
        # Set model if not specified
        if not model:
            model = settings.default_model
        
        # Validate model
        if model not in settings.available_models:
            available = "\n".join([f"  - {m}" for m in settings.available_models])
            console.print(f"[bold red]Model '{model}' not available. Available models:[/bold red]\n{available}")
            raise typer.Exit(1)
        
        # Validate agent type
        valid_types = ["standard", "github", "mail"]
        if agent_type not in valid_types:
            console.print(f"[bold red]Invalid agent type: {agent_type}. Valid types: {', '.join(valid_types)}[/bold red]")
            raise typer.Exit(1)
        
        # Check if creating GitHub agent and validate requirements
        if agent_type == "github" and not settings.has_github:
            console.print("[bold yellow]Warning: GitHub API token not configured.[/bold yellow]")
            console.print("Set GITHUB_API_TOKEN and GITHUB_USERNAME in your .env file for GitHub agent to work.")
            
            if not typer.confirm("Continue anyway?"):
                raise typer.Exit(0)
        
        # Create agent
        with console.status(f"[bold green]Creating {agent_type} agent '{name}'..."):
            # Generate agent data
            agent_data = generate_agent(
                name=name,
                description=description or f"An AI assistant named {name}",
                model_name=model,
                agent_type=agent_type
            )
            
            # Save agent to database
            with get_db_session() as db:
                agent = Agent(
                    name=agent_data["name"],
                    description=agent_data["description"],
                    model_name=model,
                    system_prompt=agent_data["system_prompt"]
                )
                db.add(agent)
                db.commit()
                db.refresh(agent)
                
                # Save agent files
                for file_data in agent_data["files"]:
                    file = AgentFile(
                        agent_id=agent.id,
                        filename=file_data["filename"],
                        file_type=file_data["file_type"],
                        content=file_data["content"]
                    )
                    db.add(file)
                
                # Save agent tools
                for tool_data in agent_data["tools"]:
                    # For GitHub agent, function_def may already be a string
                    function_def = tool_data["function_def"]
                    if not isinstance(function_def, str):
                        function_def = json.dumps(function_def)
                    
                    tool = AgentTool(
                        agent_id=agent.id,
                        name=tool_data["name"],
                        description=tool_data["description"],
                        function_def=function_def
                    )
                    db.add(tool)
                
                db.commit()
                # Store ID before closing session
                agent_id = agent.id
        
        console.print(f"[bold green]{agent_type.capitalize()} agent '{name}' created successfully with ID {agent_id}![/bold green]")
        
        # Special instructions for different agent types
        if agent_type == "github":
            console.print("\n[bold cyan]GitHub Agent Setup Instructions:[/bold cyan]")
            console.print("1. Make sure you have a GitHub personal access token with appropriate permissions")
            console.print("2. Set these environment variables in your .env file:")
            console.print("   - GITHUB_API_TOKEN=your_token_here")
            console.print("   - GITHUB_USERNAME=your_username_here\n")
            console.print(f"Run the agent with: [bold]agenteer run {agent_id} --interactive[/bold]")
        elif agent_type == "mail":
            console.print("\n[bold cyan]Mail Agent Setup Instructions:[/bold cyan]")
            console.print("1. When you first run the agent, it will guide you through OAuth authentication")
            console.print("2. You'll need to complete the authentication process in your web browser")
            console.print("3. For Gmail:")
            console.print("   - Go to console.cloud.google.com and create a project")
            console.print("   - Enable the Gmail API")
            console.print("   - Create OAuth credentials (Desktop application type)")
            console.print("   - Download the credentials.json file")
            console.print("   - Place it in your config directory as 'gmail_credentials.json'")
            console.print("4. For Outlook/Microsoft 365:")
            console.print("   - Go to portal.azure.com and register a new application")
            console.print("   - Add Microsoft Graph permissions for Mail.Read and Mail.Send")
            console.print("   - Configure authentication with a redirect URI")
            console.print("   - Create a client secret (or use public client flow)")
            console.print("   - Set OUTLOOK_CLIENT_ID in your .env file\n")
            console.print(f"Run the agent with: [bold]agenteer run {agent_id} --interactive[/bold]")
        
    except Exception as error:
        console.print(f"[bold red]Error creating agent: {str(error)}[/bold red]")
        import traceback
        console.print(f"[dim red]{traceback.format_exc()}[/dim red]")
        raise typer.Exit(1)


@app.command("list")
def list_agents():
    """List all available agents."""
    try:
        from agenteer.core.database.engine import get_db_session
        from agenteer.core.database.models import Agent
        
        # Initialize database if not exists
        if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
            console.print("[yellow]Database not initialized. Running initialization...[/yellow]")
            init_db()
        
        # List agents
        with get_db_session() as db:
            agents = db.query(Agent).all()
            
            if not agents:
                console.print("[yellow]No agents found. Create one with 'agenteer create'.[/yellow]")
                return
            
            table = Table(title="Available Agents")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="blue")
            table.add_column("Model", style="yellow")
            table.add_column("Created", style="magenta")
            
            for agent in agents:
                table.add_row(
                    str(agent.id),
                    agent.name,
                    agent.description or "",
                    agent.model_name,
                    agent.created_at.strftime("%Y-%m-%d %H:%M") if agent.created_at else ""
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error listing agents: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command("run")
def run_agent(
    agent_identifier: str = typer.Argument(..., help="Name or ID of the agent to run"),
    input: str = typer.Option(None, "--input", "-i", help="Input to send to the agent"),
    interactive: bool = typer.Option(False, "--interactive", help="Run in interactive mode"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Timeout in seconds for agent execution"),
    timeout_action: str = typer.Option("log", "--timeout-action", "-a", help="Action on timeout: log, alarm, or kill"),
):
    """Run an AI agent with the given input."""
    try:
        from agenteer.core.agents.runner import AgentRunner
        from agenteer.core.database.engine import get_db_session
        from agenteer.core.database.models import Agent, AgentExecution, AgentMessage
        
        # Initialize database if not exists
        if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
            console.print("[yellow]Database not initialized. Running initialization...[/yellow]")
            init_db()
        
        # Get agent by ID or name
        with get_db_session() as db:
            # Check if identifier is an integer (likely an ID)
            try:
                agent_id = int(agent_identifier)
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    identifier_type = "ID"
                else:
                    # Fallback to name search if ID not found
                    agent = db.query(Agent).filter(Agent.name == agent_identifier).first()
                    identifier_type = "name"
            except ValueError:
                # Not an integer, so search by name
                agent = db.query(Agent).filter(Agent.name == agent_identifier).first()
                identifier_type = "name"
            
            if not agent:
                # If still not found, try a case-insensitive partial match on name
                agent = db.query(Agent).filter(Agent.name.ilike(f"%{agent_identifier}%")).first()
                
                if agent:
                    console.print(f"[yellow]Agent with exact {identifier_type} '{agent_identifier}' not found, but found matching agent '{agent.name}'.[/yellow]")
                else:
                    console.print(f"[bold red]Agent with {identifier_type} '{agent_identifier}' not found.[/bold red]")
                    
                    # Provide helpful suggestions
                    agents = db.query(Agent).all()
                    if agents:
                        console.print("[yellow]Available agents:[/yellow]")
                        for a in agents:
                            console.print(f"  {a.id}: {a.name}")
                    
                    raise typer.Exit(1)
            
            # Create execution record
            execution = AgentExecution(agent_id=agent.id)
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # Initialize runner with timeout if specified
            runner = AgentRunner(
                agent=agent, 
                execution_id=execution.id,
                timeout=timeout,
                timeout_action=timeout_action
            )
            
            if interactive:
                # Interactive mode
                console.print(f"[bold green]Running agent '{agent.name}' in interactive mode. Type 'exit' to quit.[/bold green]")
                
                while True:
                    user_input = console.input("[bold blue]> [/bold blue]")
                    
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    
                    # Record user message
                    message = AgentMessage(
                        execution_id=execution.id,
                        role="user",
                        content=user_input
                    )
                    db.add(message)
                    db.commit()
                    
                    # Run agent
                    with console.status("[bold green]Agent thinking..."):
                        response = runner.run(user_input)
                    
                    # Print response
                    console.print(f"[bold green]{agent.name}:[/bold green] {response}")
                    
                    # Record assistant message
                    message = AgentMessage(
                        execution_id=execution.id,
                        role="assistant",
                        content=response
                    )
                    db.add(message)
                    db.commit()
                
                # Mark execution as completed
                execution.completed_at = datetime.now()
                execution.success = True
                db.commit()
                
            elif input:
                # Run with provided input
                with console.status(f"[bold green]Running agent '{agent.name}'..."):
                    # Record user message
                    message = AgentMessage(
                        execution_id=execution.id,
                        role="user",
                        content=input
                    )
                    db.add(message)
                    db.commit()
                    
                    # Run agent
                    response = runner.run(input)
                    
                    # Record assistant message
                    message = AgentMessage(
                        execution_id=execution.id,
                        role="assistant",
                        content=response
                    )
                    db.add(message)
                    
                    # Mark execution as completed
                    execution.completed_at = datetime.now()
                    execution.success = True
                    db.commit()
                
                # Print response
                console.print(f"[bold green]{agent.name}:[/bold green] {response}")
                
            else:
                console.print("[yellow]No input provided. Use --input or --interactive.[/yellow]")
                db.delete(execution)
                db.commit()
        
    except Exception as e:
        console.print(f"[bold red]Error running agent: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command("preload-docs")
def preload_docs(
    source: str = typer.Option("all", "--source", "-s", help="Documentation source(s) to preload: all, pydantic, langchain, langgraph, anthropic"),
    max_pages: int = typer.Option(300, "--max-pages", "-m", help="Maximum number of pages to crawl"),
    max_depth: int = typer.Option(3, "--max-depth", "-d", help="Maximum link depth to crawl"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="HTTP request timeout in seconds (max 600)")
):
    """Preload documentation from specified sources for agent context augmentation."""
    try:
        from agenteer.core.docs.crawler import (
            crawl_all_docs, 
            crawl_pydantic_ai_docs, 
            crawl_langchain_docs,
            crawl_langgraph_docs,
            crawl_anthropic_docs
        )
        from agenteer.core.database.engine import get_db_session, init_db
        from agenteer.core.database.models import DocumentationPage
        
        # Ensure timeout is within bounds (1-600 seconds)
        timeout = max(1, min(600, timeout))
        
        # Initialize database if not exists
        if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
            console.print("[yellow]Database not initialized. Running initialization...[/yellow]")
            init_db()
        
        # Get current doc count
        with get_db_session() as db:
            initial_doc_count = db.query(DocumentationPage).count()
        
        # Preload documentation based on source
        if source.lower() == "all":
            with console.status("[bold green]Preloading all documentation sources..."):
                pages_crawled = asyncio.run(crawl_all_docs(
                    max_pages=max_pages,
                    max_depth=max_depth,
                    timeout=timeout
                ))
            console.print(f"[bold green]Successfully preloaded {pages_crawled} documentation pages from all sources![/bold green]")
        
        elif source.lower() == "pydantic":
            with console.status("[bold green]Preloading Pydantic documentation..."):
                pages_crawled = asyncio.run(crawl_pydantic_ai_docs(
                    max_pages=max_pages,
                    max_depth=max_depth,
                    timeout=timeout
                ))
            console.print(f"[bold green]Successfully preloaded {pages_crawled} Pydantic documentation pages![/bold green]")
        
        elif source.lower() == "langchain":
            with console.status("[bold green]Preloading LangChain documentation..."):
                pages_crawled = asyncio.run(crawl_langchain_docs(
                    max_pages=max_pages,
                    max_depth=max_depth,
                    timeout=timeout
                ))
            console.print(f"[bold green]Successfully preloaded {pages_crawled} LangChain documentation pages![/bold green]")
        
        elif source.lower() == "langgraph":
            with console.status("[bold green]Preloading LangGraph documentation..."):
                pages_crawled = asyncio.run(crawl_langgraph_docs(
                    max_pages=max_pages,
                    max_depth=max_depth,
                    timeout=timeout
                ))
            console.print(f"[bold green]Successfully preloaded {pages_crawled} LangGraph documentation pages![/bold green]")
        
        elif source.lower() == "anthropic":
            with console.status("[bold green]Preloading Anthropic documentation..."):
                pages_crawled = asyncio.run(crawl_anthropic_docs(
                    max_pages=max_pages,
                    max_depth=max_depth,
                    timeout=timeout
                ))
            console.print(f"[bold green]Successfully preloaded {pages_crawled} Anthropic documentation pages![/bold green]")
        
        else:
            console.print(f"[bold red]Invalid source: {source}[/bold red]")
            console.print("Valid sources: all, pydantic, langchain, langgraph, anthropic")
            raise typer.Exit(1)
        
        # Get updated doc count
        with get_db_session() as db:
            final_doc_count = db.query(DocumentationPage).count()
            new_docs = final_doc_count - initial_doc_count
        
        console.print(f"[bold green]Documentation preloading complete![/bold green]")
        console.print(f"[green]Added {new_docs} new document(s). Total document count: {final_doc_count}[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error preloading documentation: {str(e)}[/bold red]")
        import traceback
        console.print(f"[dim red]{traceback.format_exc()}[/dim red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_agent(
    agent_identifier: str = typer.Argument(..., help="Name or ID of the agent to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion without confirmation"),
):
    """Delete an AI agent and associated data."""
    try:
        from agenteer.core.database.engine import get_db_session
        from agenteer.core.database.models import Agent, AgentFile, AgentTool, AgentExecution, AgentMessage
        
        # Initialize database if not exists
        if not os.path.exists(settings.database_url.replace("sqlite:///", "")):
            console.print("[yellow]Database not initialized. Nothing to delete.[/yellow]")
            raise typer.Exit(1)
        
        # Get agent by ID or name
        with get_db_session() as db:
            # Check if identifier is an integer (likely an ID)
            try:
                agent_id = int(agent_identifier)
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    identifier_type = "ID"
                else:
                    # Fallback to name search if ID not found
                    agent = db.query(Agent).filter(Agent.name == agent_identifier).first()
                    identifier_type = "name"
            except ValueError:
                # Not an integer, so search by name
                agent = db.query(Agent).filter(Agent.name == agent_identifier).first()
                identifier_type = "name"
            
            if not agent:
                # If still not found, try a case-insensitive partial match on name
                agent = db.query(Agent).filter(Agent.name.ilike(f"%{agent_identifier}%")).first()
                
                if agent:
                    console.print(f"[yellow]Agent with exact {identifier_type} '{agent_identifier}' not found, but found matching agent '{agent.name}'.[/yellow]")
                else:
                    console.print(f"[bold red]Agent with {identifier_type} '{agent_identifier}' not found.[/bold red]")
                    
                    # Provide helpful suggestions
                    agents = db.query(Agent).all()
                    if agents:
                        console.print("[yellow]Available agents:[/yellow]")
                        for a in agents:
                            console.print(f"  {a.id}: {a.name}")
                    
                    raise typer.Exit(1)
            
            # Confirm deletion
            if not force:
                console.print(f"[bold yellow]Are you sure you want to delete agent '{agent.name}' (ID: {agent.id})?[/bold yellow]")
                console.print(f"Description: {agent.description}")
                console.print(f"Model: {agent.model_name}")
                if not typer.confirm("Delete this agent?"):
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                    raise typer.Exit(0)
            
            # Store agent info before deletion
            agent_name = agent.name
            agent_id_val = agent.id
            
            # Count related records
            tool_count = db.query(AgentTool).filter(AgentTool.agent_id == agent_id).count()
            file_count = db.query(AgentFile).filter(AgentFile.agent_id == agent_id).count()
            execution_count = db.query(AgentExecution).filter(AgentExecution.agent_id == agent_id).count()
            
            # Start deletion with status
            with console.status(f"[bold red]Deleting agent '{agent_name}' and associated data..."):
                # First delete messages (due to foreign key constraints)
                execution_ids = [row[0] for row in db.query(AgentExecution.id).filter(AgentExecution.agent_id == agent_id).all()]
                if execution_ids:
                    message_count = db.query(AgentMessage).filter(AgentMessage.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                else:
                    message_count = 0
                
                # Then delete executions
                db.query(AgentExecution).filter(AgentExecution.agent_id == agent_id).delete(synchronize_session=False)
                
                # Delete tools and files
                db.query(AgentTool).filter(AgentTool.agent_id == agent_id).delete(synchronize_session=False)
                db.query(AgentFile).filter(AgentFile.agent_id == agent_id).delete(synchronize_session=False)
                
                # Finally delete the agent
                db.query(Agent).filter(Agent.id == agent_id).delete(synchronize_session=False)
                
                # Commit changes
                db.commit()
            
            # Show deletion summary
            console.print(f"[bold green]Successfully deleted agent '{agent_name}' (ID: {agent_id_val})![/bold green]")
            console.print(f"Removed:")
            console.print(f"- {tool_count} tool definition(s)")
            console.print(f"- {file_count} agent file(s)")
            console.print(f"- {execution_count} execution record(s)")
            console.print(f"- {message_count} message(s)")
        
    except Exception as e:
        console.print(f"[bold red]Error deleting agent: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command("status")
def status():
    """Check Agenteer status and configuration."""
    try:
        from agenteer.core.database.engine import get_db_session
        from agenteer.core.database.models import Agent, DocumentationPage
        
        # Initialize database if not exists
        db_initialized = os.path.exists(settings.database_url.replace("sqlite:///", ""))
        
        table = Table(title="Agenteer Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="blue")
        
        # Database status
        if db_initialized:
            table.add_row("Database", "✓", settings.database_url)
        else:
            table.add_row("Database", "✗", f"{settings.database_url} (not initialized)")
        
        # API Keys
        if settings.has_openai:
            table.add_row("OpenAI API", "✓", "API key configured")
        else:
            table.add_row("OpenAI API", "✗", "API key not configured")
            
        if settings.has_anthropic:
            table.add_row("Anthropic API", "✓", "API key configured")
        else:
            table.add_row("Anthropic API", "✗", "API key not configured")
            
        if settings.has_ollama:
            table.add_row("Ollama", "✓", settings.ollama_base_url)
        else:
            table.add_row("Ollama", "✗", f"{settings.ollama_base_url} (not available)")
            
        if settings.has_github:
            table.add_row("GitHub API", "✓", "API token configured")
        else:
            table.add_row("GitHub API", "✗", "API token not configured")
        
        # Vector store
        vector_db_exists = os.path.exists(os.path.join(settings.vector_db_path, "faiss.index"))
        if vector_db_exists:
            table.add_row("Vector Store", "✓", settings.vector_db_path)
        else:
            table.add_row("Vector Store", "✗", f"{settings.vector_db_path} (not initialized)")
        
        # Agent count
        if db_initialized:
            with get_db_session() as db:
                agent_count = db.query(Agent).count()
                doc_count = db.query(DocumentationPage).count()
                
                table.add_row("Agents", "✓" if agent_count > 0 else "✗", f"{agent_count} agent(s) available")
                table.add_row("Documentation", "✓" if doc_count > 0 else "✗", f"{doc_count} page(s) available")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error checking status: {str(e)}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
