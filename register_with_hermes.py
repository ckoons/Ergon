#!/usr/bin/env python3
"""Register Ergon with Hermes service registry.

This script registers all Ergon services with the Hermes service registry.
"""

import os
import sys
import logging
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ergon_registration")

# Add Ergon to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Find the parent directory (Tekton root)
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import registration helper
try:
    from ergon.utils.hermes_helper import register_with_hermes
except ImportError as e:
    logger.error(f"Could not import registration helper: {e}")
    logger.error("Make sure to run setup.sh first")
    sys.exit(1)

async def register_ergon_services():
    """Register all Ergon services with Hermes."""
    
    # Register main Ergon service
    main_success = await register_with_hermes(
        service_id="ergon-core",
        name="Ergon Agent Builder",
        capabilities=["agent_building", "agent_management", "agent_execution"],
        metadata={
            "component_type": "core",
            "description": "AI agent creation and management system",
            "ui_enabled": True,
            "ui_component": "ergon"
        }
    )
    
    # Register workflow service
    workflow_success = await register_with_hermes(
        service_id="ergon-workflow",
        name="Ergon Workflow Engine",
        capabilities=["workflow_execution", "task_planning", "task_delegation"],
        metadata={
            "component_type": "core",
            "description": "AI workflow planning and execution"
        }
    )
    
    # Register memory service
    memory_success = await register_with_hermes(
        service_id="ergon-memory",
        name="Ergon Memory Service",
        capabilities=["document_storage", "vector_search", "memory_management"],
        metadata={
            "component_type": "service",
            "description": "Document and memory management for agents"
        }
    )
    
    # Display results
    if main_success and workflow_success and memory_success:
        logger.info("Successfully registered all Ergon services with Hermes")
        return True
    else:
        failures = []
        if not main_success:
            failures.append("main service")
        if not workflow_success:
            failures.append("workflow service")
        if not memory_success:
            failures.append("memory service")
        
        logger.warning(f"Failed to register the following Ergon services: {', '.join(failures)}")
        return False

if __name__ == "__main__":
    # Run in the virtual environment if available
    venv_dir = os.path.join(script_dir, "venv")
    if os.path.exists(venv_dir):
        # Activate the virtual environment if not already activated
        if not os.environ.get("VIRTUAL_ENV"):
            print(f"Please run this script within the Ergon virtual environment:")
            print(f"source {venv_dir}/bin/activate")
            print(f"python {os.path.basename(__file__)}")
            sys.exit(1)
    
    success = asyncio.run(register_ergon_services())
    sys.exit(0 if success else 1)