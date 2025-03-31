# Ergon Chatbot Interface

This directory contains the refactored chatbot interface for Ergon with memory and agent awareness.

## Overview

The Ergon chatbot provides a Streamlit-based user interface for interacting with AI agents, with a focus on memory-enabled agents (Nexus agents). The interface allows users to select, create, and interact with agents through natural language.

## Module Structure

The chatbot implementation has been refactored into the following modules:

- **__init__.py**: Main entry point and backward compatibility
- **agent_services.py**: Agent discovery, selection, and execution functions
- **constants.py**: Default settings, configurations, and static data
- **ui_components.py**: UI elements for feedback collection and plan reviews
- **session_management.py**: Session state initialization and management
- **sidebar.py**: Sidebar UI components for agent selection and configuration
- **chat_interface.py**: Main chat display and user interaction handling

## Key Features

- **Agent Discovery**: Recommends agents based on user queries and tasks
- **Memory Integration**: Works with memory-enabled Nexus agents for persistent context
- **Feedback Collection**: Rating tool for feature importance
- **Plan Reviews**: Implementation plan visualization and feedback collection
- **Command System**: Special commands (e.g., `!rate`, `!plan`) for additional functionality

## Usage

The main entry point is the `chatbot_interface()` function, which is called by Streamlit when loading the page. The original file at `ergon/ui/pages/chatbot.py` imports and re-exports this function for backward compatibility.

## Dependencies

This module requires the following dependencies:

- Streamlit for the UI components
- Ergon core components (agents, database, memory)
- Async support for agent execution

## Development

When extending or modifying the chatbot interface, please follow these guidelines:

1. Keep each module focused on a specific responsibility
2. Maintain backward compatibility through the main entry point
3. Use session state for persistent data between user interactions
4. Follow the existing patterns for agent discovery and execution
5. Add new UI components in the appropriate modules

The refactored structure allows for easier maintenance and extension of the chatbot functionality.