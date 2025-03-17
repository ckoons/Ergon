#!/bin/bash
# Install Engram (formerly ClaudeMemoryBridge) for development

# Ensure we're in the Agenteer directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.." || exit 1

# Define paths
VENV_PATH="./venv"
ENGRAM_PATH="../Engram"
LEGACY_CMB_PATH="../ClaudeMemoryBridge"

# Check if Engram exists or fall back to legacy path
if [ -d "$ENGRAM_PATH" ]; then
    INSTALL_PATH="$ENGRAM_PATH"
    PACKAGE_NAME="Engram"
    START_SCRIPT="./engram_start_all"
elif [ -d "$LEGACY_CMB_PATH" ]; then
    INSTALL_PATH="$LEGACY_CMB_PATH"
    PACKAGE_NAME="ClaudeMemoryBridge"
    START_SCRIPT="./cmb_start_all"
else
    echo "Error: Neither Engram directory at $ENGRAM_PATH nor ClaudeMemoryBridge at $LEGACY_CMB_PATH found"
    echo "Please make sure either the Engram or ClaudeMemoryBridge repository is cloned at the same level as Agenteer."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please run setup.sh first to create the virtual environment."
    exit 1
fi

# Install package in development mode
echo "Installing $PACKAGE_NAME in development mode..."
pip install -e "$INSTALL_PATH"

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ $PACKAGE_NAME installed successfully!"
    echo "You can now use enhanced memory features in Agenteer."
else
    echo "❌ Failed to install $PACKAGE_NAME."
    echo "Please check the error messages above and try again."
    exit 1
fi

# Inform about service
echo ""
echo "To use the full features of $PACKAGE_NAME, you need to start the service:"
echo "1. Open a new terminal window"
echo "2. Navigate to the $PACKAGE_NAME directory: cd $INSTALL_PATH"
echo "3. Start the service: $START_SCRIPT"
echo ""
echo "Note: Agenteer will work with limited memory functionality even if the memory service is not running."

exit 0