# Ergon UI - Tekton Integration Guide

This guide explains how the Ergon GUI component integrates with the existing Ergon CLI functions.

## Architecture Overview

The Ergon UI in Tekton uses a wrapper architecture to leverage the existing CLI functionality:

```
┌─────────────────┐    ┌───────────────┐    ┌────────────────┐
│                 │    │               │    │                │
│  React UI       │───▶│  API Service  │───▶│  CLI Functions │
│  Components     │◀───│  (Wrapper)    │◀───│                │
│                 │    │               │    │                │
└─────────────────┘    └───────────────┘    └────────────────┘
```

## Key Components

### 1. ErgonView.jsx

The main React component that provides the GUI for Ergon. It handles:

- Tab-based navigation (Agents, Chat, Documents, Settings)
- Agent creation, selection, and deletion
- Chat interface with memory toggle
- Loading states and error handling

### 2. ApiService.js

Wraps CLI functions and provides a JavaScript API for the UI:

- `getAgents()` - Lists all available agents
- `createAgent()` - Creates a new agent
- `runAgent()` - Runs a one-time agent interaction
- `deleteAgent()` - Deletes an agent
- `startInteractiveChat()` - Sets up a persistent chat session
- `preloadDocuments()` - Loads documents for knowledge retrieval

### 3. execute.js

Low-level utility that handles communication with the Python CLI:

- Creates Python processes to run CLI commands
- Handles streaming for interactive sessions
- Manages process lifecycle

### 4. json_formatter.py

Converts CLI output to structured JSON for the UI:

- Standardizes response format
- Handles various data types
- Creates consistent success/error patterns

## Integration Approach

1. **No Business Logic Duplication**
   - All agent functionality remains in the CLI
   - UI merely passes commands to CLI functions

2. **Process Communication**
   - Python processes execute CLI commands
   - JSON is used for passing data between JS and Python

3. **Interactive Sessions**
   - Long-running processes handle chat interactions
   - State maintained in the Python process

## Adding New Features

To add a new feature to the Ergon UI:

1. Add the corresponding CLI function in `agent_commands.py` or other CLI module
2. Add a wrapper method in `ApiService.js`
3. Add the UI components in `ErgonView.jsx`
4. Ensure proper error handling and loading states

## Example Usage

```javascript
// Setting up a chat session
const session = await ErgonApiService.startInteractiveChat(agent.id, {
  onMessage: (message) => {
    setMessages(prev => [...prev, { role: 'assistant', content: message }]);
    setThinking(false);
  },
  disableMemory: !memoryEnabled
});

// Sending a message
await session.sendMessage(userInput);

// Ending a session
await session.endChat();
```