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
        
        console.print("[bold green]Agenteer initialized successfully\![/bold green]")
        
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
        sys.argv = ["streamlit", "run", f"{settings.app_root}/agenteer/ui/app.py", "--server.port", str(port), "--server.address", host]
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
):
    """Create a new AI agent with the given specifications."""
    try:
        from agenteer.core.agents.generator import AgentGenerator
        from agenteer.core.database.engine import get_db_session
        from agenteer.core.database.models import Agent
        
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
        
        # Create agent
        with console.status(f"[bold green]Creating agent '{name}'..."):
            # Initialize agent generator
            generator = AgentGenerator(model=model)
            
            # Generate agent
            agent_data = generator.generate(
                name=name,
                description=description or f"An AI assistant named {name}"
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
                    tool = AgentTool(
                        agent_id=agent.id,
                        name=tool_data["name"],
                        description=tool_data["description"],
                        function_def=json.dumps(tool_data["function_def"])
                    )
                    db.add(tool)
                
                db.commit()
        
        console.print(f"[bold green]Agent '{name}' created successfully with ID {agent.id}\![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error creating agent: {str(e)}[/bold red]")
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
    agent_id: int = typer.Argument(..., help="ID of the agent to run"),
    input: str = typer.Option(None, "--input", "-i", help="Input to send to the agent"),
    interactive: bool = typer.Option(False, "--interactive", help="Run in interactive mode"),
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
        
        # Get agent
        with get_db_session() as db:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                console.print(f"[bold red]Agent with ID {agent_id} not found.[/bold red]")
                raise typer.Exit(1)
            
            # Create execution record
            execution = AgentExecution(agent_id=agent.id)
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # Initialize runner
            runner = AgentRunner(agent=agent, execution_id=execution.id)
            
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
