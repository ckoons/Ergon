#!/bin/bash

# Set environment variables
export AGENTEER_AUTHENTICATION=false

# Activate virtual environment
source venv/bin/activate

# Run the UI
python -m agenteer.cli.main ui