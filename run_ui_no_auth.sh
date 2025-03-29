#!/bin/bash

# Set environment variables
export ERGON_AUTHENTICATION=false

# Activate virtual environment
source venv/bin/activate

# Run the UI
python -m ergon.cli.main ui