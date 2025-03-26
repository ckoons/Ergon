#!/bin/bash
# Script to run Agenteer UI with suppressed warnings

# Install watchdog if not already installed
pip install -q watchdog

# Set environment variables to suppress unimportant warnings
export PYTHONWARNINGS=ignore
export STREAMLIT_SILENCE_TORCH_WARNINGS=1

# Run the UI
echo "Starting Ergon UI..."
python -m ergon.cli.main ui