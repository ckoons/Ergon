# Ergon Agent Environments

This directory contains isolated virtual environments for each agent type, allowing them to have their own specific dependencies without affecting the main Ergon environment.

## Directory Structure

- `browser/` - Environment for Browser agents using Playwright
- `mail/` - Environment for Mail agents using Gmail/Outlook APIs
- `github/` - Environment for GitHub agents using PyGithub

## Setup

Run the setup script from the main Ergon directory:

```bash
./setup_agents.sh
```

This will create isolated virtual environments for each agent type and install their specific dependencies.

## Using Agent Environments

To activate an agent-specific environment:

```bash
# For Browser agents
cd agents/browser
source venv/bin/activate

# For Mail agents
cd agents/mail
source venv/bin/activate

# For GitHub agents
cd agents/github
source venv/bin/activate
```

## Benefits

- Isolates potentially conflicting dependencies
- Keeps the main Ergon environment lean
- Allows specialized libraries for each agent type
- Makes it easier to update specific agent dependencies