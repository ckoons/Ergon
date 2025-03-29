#!/usr/bin/env python3
"""
Tekton Suite Launcher - Unified launcher for the Tekton ecosystem.

This script orchestrates the startup of all Tekton components in the correct order,
ensuring that dependencies are properly initialized before dependent services.
"""

import os
import sys
import argparse
import asyncio
import json
import logging
import signal
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tekton")

# Add Ergon to the Python path if not already there
TEKTON_ROOT = Path.home() / ".tekton"
ERGON_ROOT = Path(__file__).parent.parent.absolute()
if str(ERGON_ROOT) not in sys.path:
    sys.path.insert(0, str(ERGON_ROOT))

# Import Ergon modules
try:
    from ergon.utils.config.settings import settings
    from ergon.core.database.engine import init_db
    from ergon.core.memory import client_manager
except ImportError as e:
    logger.error(f"Error importing Ergon modules: {e}")
    logger.error("Please make sure Ergon is installed correctly.")
    sys.exit(1)

# Component metadata
COMPONENTS = {
    "database": {
        "name": "Database Services",
        "description": "Core SQLite and vector databases",
        "dependencies": [],
        "startup_sequence": 1
    },
    "engram": {
        "name": "Engram Memory Service",
        "description": "Centralized memory and embedding service",
        "dependencies": ["database"],
        "startup_sequence": 2,
        "client_id": "engram_core"
    },
    "ergon": {
        "name": "Ergon Agent Framework",
        "description": "Agent and tool management framework",
        "dependencies": ["database", "engram"],
        "startup_sequence": 3,
        "client_id": "ergon_core" 
    },
    "ollama": {
        "name": "Ollama Integration",
        "description": "Local LLM integration through Ollama",
        "dependencies": ["database", "engram"],
        "startup_sequence": 10,
        "optional": True
    },
    "claude": {
        "name": "Claude Integration",
        "description": "Anthropic Claude API integration",
        "dependencies": ["database", "engram"],
        "startup_sequence": 11,
        "optional": True
    },
    "openai": {
        "name": "OpenAI Integration",
        "description": "OpenAI API integration",
        "dependencies": ["database", "engram"],
        "startup_sequence": 12,
        "optional": True
    }
}

# Tracks the running components and their processes
running_components = {}
component_processes = {}
running_lock = threading.RLock()

async def start_database() -> bool:
    """
    Initialize the database services.
    
    Returns:
        True if successful
    """
    logger.info("Starting database services...")
    
    try:
        # Ensure the Tekton home directory exists
        os.makedirs(settings.tekton_home, exist_ok=True)
        
        # Initialize the SQLite database if needed
        db_path = settings.database_url.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            logger.info("Initializing SQLite database...")
            init_db()
        
        # Initialize the vector database directory if needed
        os.makedirs(settings.vector_db_path, exist_ok=True)
        
        logger.info("Database services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database services: {e}")
        return False

async def start_engram() -> bool:
    """
    Start the Engram memory service.
    
    Returns:
        True if successful
    """
    logger.info("Starting Engram memory service...")
    
    try:
        # Initialize the client manager
        await client_manager.start()
        
        # Register Engram as a core service
        engram_config = {
            "service_type": "core",
            "description": "Central memory service"
        }
        
        client_id = COMPONENTS["engram"]["client_id"]
        success = await client_manager.register_client(
            client_id=client_id,
            client_type="engram",
            config=engram_config
        )
        
        if success:
            logger.info("Engram memory service started successfully")
            return True
        else:
            logger.error("Failed to register Engram client")
            return False
    except Exception as e:
        logger.error(f"Error starting Engram memory service: {e}")
        return False

async def start_ergon() -> bool:
    """
    Start the Ergon agent framework and register it with Engram.
    
    Returns:
        True if successful
    """
    logger.info("Starting Ergon agent framework...")
    
    try:
        # Register Ergon with Engram
        ergon_config = {
            "service_type": "framework",
            "description": "Agent and tool framework"
        }
        
        client_id = COMPONENTS["ergon"]["client_id"]
        success = await client_manager.register_client(
            client_id=client_id,
            client_type="ergon",
            config=ergon_config
        )
        
        if success:
            # Set metadata for Ergon client
            await client_manager.set_client_metadata(
                client_id=client_id,
                key="framework_version",
                value="1.0"
            )
            
            logger.info("Ergon agent framework started and registered with Engram")
            return True
        else:
            logger.error("Failed to register Ergon with Engram")
            return False
    except Exception as e:
        logger.error(f"Error starting Ergon agent framework: {e}")
        return False

async def start_ollama(model_name: str = "llama3") -> bool:
    """
    Start Ollama integration.
    
    Args:
        model_name: Ollama model to use
        
    Returns:
        True if successful
    """
    logger.info(f"Starting Ollama integration with model {model_name}...")
    
    try:
        # Register Ollama client
        success = await client_manager.register_client(
            client_id="ollama_service",
            client_type="ollama",
            config={"model": model_name}
        )
        
        if success:
            logger.info(f"Ollama integration started with model {model_name}")
            return True
        else:
            logger.error("Failed to register Ollama client")
            return False
    except Exception as e:
        logger.error(f"Error starting Ollama integration: {e}")
        return False

async def start_claude(model_name: str = "claude-3-sonnet-20240229") -> bool:
    """
    Start Claude integration.
    
    Args:
        model_name: Claude model to use
        
    Returns:
        True if successful
    """
    logger.info(f"Starting Claude integration with model {model_name}...")
    
    try:
        # Check if Anthropic API key is set
        if not settings.has_anthropic:
            logger.error("Anthropic API key not configured. Please set ANTHROPIC_API_KEY in your environment.")
            return False
        
        # Register Claude client
        success = await client_manager.register_client(
            client_id="claude_service",
            client_type="claude",
            config={"model": model_name}
        )
        
        if success:
            logger.info(f"Claude integration started with model {model_name}")
            return True
        else:
            logger.error("Failed to register Claude client")
            return False
    except Exception as e:
        logger.error(f"Error starting Claude integration: {e}")
        return False

async def start_openai(model_name: str = "gpt-4o-mini") -> bool:
    """
    Start OpenAI integration.
    
    Args:
        model_name: OpenAI model to use
        
    Returns:
        True if successful
    """
    logger.info(f"Starting OpenAI integration with model {model_name}...")
    
    try:
        # Check if OpenAI API key is set
        if not settings.has_openai:
            logger.error("OpenAI API key not configured. Please set OPENAI_API_KEY in your environment.")
            return False
        
        # Register OpenAI client
        success = await client_manager.register_client(
            client_id="openai_service",
            client_type="openai",
            config={"model": model_name}
        )
        
        if success:
            logger.info(f"OpenAI integration started with model {model_name}")
            return True
        else:
            logger.error("Failed to register OpenAI client")
            return False
    except Exception as e:
        logger.error(f"Error starting OpenAI integration: {e}")
        return False

async def stop_component(component_id: str) -> bool:
    """
    Stop a running component.
    
    Args:
        component_id: ID of the component to stop
        
    Returns:
        True if successful
    """
    logger.info(f"Stopping component: {component_id}...")
    
    # If there's a client registration, deregister it
    component = COMPONENTS.get(component_id)
    if component and "client_id" in component:
        client_id = component["client_id"]
        try:
            success = await client_manager.deregister_client(client_id)
            if success:
                logger.info(f"Deregistered client {client_id} for component {component_id}")
            else:
                logger.warning(f"Failed to deregister client {client_id} for component {component_id}")
        except Exception as e:
            logger.error(f"Error deregistering client {client_id}: {e}")
    
    # If the component has a process, terminate it
    with running_lock:
        if component_id in component_processes:
            process = component_processes[component_id]
            try:
                # Try to terminate gracefully
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if termination doesn't work
                    process.kill()
                
                logger.info(f"Stopped process for component {component_id}")
                # Remove from tracked processes
                del component_processes[component_id]
            except Exception as e:
                logger.error(f"Error stopping process for component {component_id}: {e}")
                return False
        
        # Mark as not running
        if component_id in running_components:
            del running_components[component_id]
    
    logger.info(f"Component {component_id} stopped successfully")
    return True

async def stop_all_components() -> bool:
    """
    Stop all running components in reverse dependency order.
    
    Returns:
        True if all components stopped successfully
    """
    logger.info("Stopping all Tekton components...")
    
    # Get components in reverse startup order
    component_ids = sorted(
        COMPONENTS.keys(),
        key=lambda c: COMPONENTS[c]["startup_sequence"],
        reverse=True
    )
    
    # Stop each component
    all_success = True
    for component_id in component_ids:
        if component_id in running_components:
            success = await stop_component(component_id)
            if not success:
                all_success = False
    
    logger.info("All Tekton components stopped")
    return all_success

def get_component_status() -> Dict[str, Dict[str, Any]]:
    """
    Get the status of all components.
    
    Returns:
        Dictionary of component status information
    """
    status = {}
    
    with running_lock:
        for component_id, component in COMPONENTS.items():
            status[component_id] = {
                "name": component["name"],
                "description": component["description"],
                "running": component_id in running_components,
                "optional": component.get("optional", False),
                "startup_sequence": component["startup_sequence"]
            }
    
    return status

async def start_component(component_id: str, config: Dict[str, Any] = None) -> bool:
    """
    Start a specific component.
    
    Args:
        component_id: ID of the component to start
        config: Optional configuration for the component
        
    Returns:
        True if successful
    """
    # Check if the component exists
    if component_id not in COMPONENTS:
        logger.error(f"Component {component_id} does not exist")
        return False
    
    # Check if the component is already running
    with running_lock:
        if component_id in running_components:
            logger.info(f"Component {component_id} is already running")
            return True
    
    # Check if dependencies are running
    component = COMPONENTS[component_id]
    for dependency in component["dependencies"]:
        with running_lock:
            if dependency not in running_components:
                logger.error(f"Cannot start {component_id} because dependency {dependency} is not running")
                return False
    
    # Start the component based on its type
    success = False
    if component_id == "database":
        success = await start_database()
    elif component_id == "engram":
        success = await start_engram()
    elif component_id == "ergon":
        success = await start_ergon()
    elif component_id == "ollama":
        model_name = config.get("model", "llama3") if config else "llama3"
        success = await start_ollama(model_name)
    elif component_id == "claude":
        model_name = config.get("model", "claude-3-sonnet-20240229") if config else "claude-3-sonnet-20240229"
        success = await start_claude(model_name)
    elif component_id == "openai":
        model_name = config.get("model", "gpt-4o-mini") if config else "gpt-4o-mini"
        success = await start_openai(model_name)
    
    # Update running components
    if success:
        with running_lock:
            running_components[component_id] = {
                "started_at": time.time(),
                "config": config or {}
            }
    
    return success

async def start_all_components(include_optional: bool = False) -> bool:
    """
    Start all Tekton components in the correct dependency order.
    
    Args:
        include_optional: Whether to include optional components
        
    Returns:
        True if all required components started successfully
    """
    logger.info(f"Starting all Tekton components (include_optional={include_optional})...")
    
    # Get components in startup order
    component_ids = sorted(
        COMPONENTS.keys(),
        key=lambda c: COMPONENTS[c]["startup_sequence"]
    )
    
    # Start each component
    all_required_success = True
    for component_id in component_ids:
        component = COMPONENTS[component_id]
        
        # Skip optional components if not requested
        if component.get("optional", False) and not include_optional:
            continue
        
        success = await start_component(component_id)
        
        # If a required component fails, mark the overall start as failed
        if not success and not component.get("optional", False):
            all_required_success = False
    
    # Return success only if all required components started
    return all_required_success

def print_component_status(status: Dict[str, Dict[str, Any]]) -> None:
    """
    Print the status of all components.
    
    Args:
        status: Dictionary of component status information
    """
    print("\nTekton Component Status:")
    print("========================")
    
    # Get components in startup order
    component_ids = sorted(
        status.keys(),
        key=lambda c: status[c]["startup_sequence"]
    )
    
    for component_id in component_ids:
        component = status[component_id]
        running_status = "✅ Running" if component["running"] else "❌ Stopped"
        optional_tag = " (Optional)" if component.get("optional", False) else ""
        
        print(f"{component['name']}{optional_tag}: {running_status}")
        print(f"  {component['description']}")
    
    print("")

def main():
    """Main entry point for the Tekton suite launcher."""
    parser = argparse.ArgumentParser(description="Tekton Suite Launcher")
    
    # Main commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start Tekton components")
    start_parser.add_argument("components", nargs="*", help="Component IDs to start (default: all core components)")
    start_parser.add_argument("--all", action="store_true", help="Include optional components")
    start_parser.add_argument("--ollama-model", type=str, default="llama3", help="Model for Ollama")
    start_parser.add_argument("--claude-model", type=str, default="claude-3-sonnet-20240229", help="Model for Claude")
    start_parser.add_argument("--openai-model", type=str, default="gpt-4o-mini", help="Model for OpenAI")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop Tekton components")
    stop_parser.add_argument("components", nargs="*", help="Component IDs to stop (default: all running components)")
    
    # Status command
    subparsers.add_parser("status", help="Show Tekton component status")
    
    # List command
    subparsers.add_parser("list", help="List available Tekton components")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle different commands
    if args.command == "start":
        if args.components:
            # Start specific components
            component_configs = {}
            
            # Add model configurations
            if "ollama" in args.components:
                component_configs["ollama"] = {"model": args.ollama_model}
            if "claude" in args.components:
                component_configs["claude"] = {"model": args.claude_model}
            if "openai" in args.components:
                component_configs["openai"] = {"model": args.openai_model}
            
            # First start the core dependencies
            core_components = ["database", "engram"]
            for component in core_components:
                if component not in args.components:
                    logger.info(f"Adding core dependency: {component}")
            
            # Combine core and requested components
            start_components = list(set(core_components + args.components))
            
            # Start each component
            for component in sorted(start_components, key=lambda c: COMPONENTS[c]["startup_sequence"]):
                if component in COMPONENTS:
                    config = component_configs.get(component)
                    result = asyncio.run(start_component(component, config))
                    if result:
                        print(f"✅ Started {COMPONENTS[component]['name']}")
                    else:
                        print(f"❌ Failed to start {COMPONENTS[component]['name']}")
                else:
                    print(f"Unknown component: {component}")
        else:
            # Start all core components (or all if --all specified)
            result = asyncio.run(start_all_components(include_optional=args.all))
            if result:
                print("✅ All required Tekton components started successfully")
            else:
                print("❌ Failed to start some required Tekton components")
                
        # Show component status after starting
        status = get_component_status()
        print_component_status(status)
            
    elif args.command == "stop":
        if args.components:
            # Stop specific components
            for component in args.components:
                if component in COMPONENTS:
                    result = asyncio.run(stop_component(component))
                    if result:
                        print(f"✅ Stopped {COMPONENTS[component]['name']}")
                    else:
                        print(f"❌ Failed to stop {COMPONENTS[component]['name']}")
                else:
                    print(f"Unknown component: {component}")
        else:
            # Stop all running components
            result = asyncio.run(stop_all_components())
            if result:
                print("✅ All Tekton components stopped successfully")
            else:
                print("❌ Failed to stop some Tekton components")
                
        # Show component status after stopping
        status = get_component_status()
        print_component_status(status)
    
    elif args.command == "status":
        # Show component status
        status = get_component_status()
        print_component_status(status)
        
        # Show additional system information
        print("System Information:")
        print(f"Tekton Home: {settings.tekton_home}")
        print(f"Database Path: {settings.database_url.replace('sqlite:///', '')}")
        print(f"Vector Store Path: {settings.vector_db_path}")
        
        # Show API key availability
        if settings.has_anthropic:
            print("Anthropic API: Available")
        else:
            print("Anthropic API: Not configured")
            
        if settings.has_openai:
            print("OpenAI API: Available")
        else:
            print("OpenAI API: Not configured")
            
        if settings.has_ollama:
            print("Ollama: Available")
        else:
            print("Ollama: Not available")
    
    elif args.command == "list":
        # List available components
        print("Available Tekton Components:")
        print("==========================")
        
        # Sort by startup sequence
        component_ids = sorted(
            COMPONENTS.keys(),
            key=lambda c: COMPONENTS[c]["startup_sequence"]
        )
        
        for component_id in component_ids:
            component = COMPONENTS[component_id]
            optional_tag = " (Optional)" if component.get("optional", False) else ""
            dependencies = ", ".join(component["dependencies"]) if component["dependencies"] else "None"
            
            print(f"{component_id}: {component['name']}{optional_tag}")
            print(f"  Description: {component['description']}")
            print(f"  Dependencies: {dependencies}")
            print(f"  Startup Sequence: {component['startup_sequence']}")
            print("")
    
    else:
        # Show help
        parser.print_help()

if __name__ == "__main__":
    # Set up signal handlers
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal, shutting down Tekton components...")
        asyncio.run(stop_all_components())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()