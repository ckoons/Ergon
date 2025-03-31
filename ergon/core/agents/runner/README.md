# Agent Runner Refactored Structure

This directory contains the refactored Agent Runner components for Ergon. The original monolithic `runner.py` has been split into multiple modules for better maintainability and readability.

## Directory Structure

- `base/`: Core agent runner functionality
  - `runner.py`: Main AgentRunner class with initialization logic
  - `exceptions.py`: Custom exceptions for agent runner

- `tools/`: Tool loading and execution functionality
  - `loader.py`: Functions for loading tool implementations
  - `mock.py`: Mock implementations for function calling
  - `registry.py`: Tool registry for special agent types

- `handlers/`: Special agent type handlers
  - `browser.py`: Browser agent specific functionality
  - `github.py`: GitHub agent specific functionality
  - `mail.py`: Mail agent specific functionality

- `memory/`: Memory integration for agents
  - `service.py`: Memory service integration
  - `operations.py`: Functions for memory operations

- `execution/`: Execution management
  - `timeout.py`: Timeout handling
  - `streaming.py`: Streaming response handling
  - `db.py`: Database interactions

- `utils/`: Utility functions
  - `environment.py`: Environment setup utilities
  - `logging.py`: Logging utilities

## Usage

The original `runner.py` file is maintained as a compatibility layer that imports from this refactored structure, ensuring backwards compatibility while providing a more modular codebase.