#!/bin/bash
# Script to launch Ergon UI through the Tekton UI framework

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to Tekton root directory
cd "$(dirname "$0")/../"

echo -e "${BLUE}=== Ergon Tekton UI Integration ===${NC}"
echo -e "${YELLOW}Initializing...${NC}"

# Check that Hephaestus exists
if [ ! -d "./Hephaestus" ]; then
    echo -e "${RED}ERROR: Hephaestus directory not found${NC}"
    echo "Please make sure you have the Hephaestus component installed."
    exit 1
fi

# Check if Tekton UI is already running
if pgrep -f "hephaestus_launch" > /dev/null; then
    echo -e "${YELLOW}Tekton UI is already running. Stopping existing instance...${NC}"
    ./scripts/tekton-kill
    sleep 2
fi

# Create necessary directories for the UI integration
ERGON_DIR="./Ergon"
HEPHAESTUS_SRC_DIR="./Hephaestus/src"

# Ensure that we have a components directory for ergon in Hephaestus
if [ ! -d "$HEPHAESTUS_SRC_DIR/components/ergon" ]; then
    echo -e "${YELLOW}Creating Ergon component directory in Hephaestus...${NC}"
    mkdir -p "$HEPHAESTUS_SRC_DIR/components/ergon"
fi

# Create a symlink to ui_connector.js in Hephaestus if it doesn't exist
if [ ! -L "$HEPHAESTUS_SRC_DIR/components/ergon/ui_connector.js" ]; then
    echo -e "${YELLOW}Creating symlink to ui_connector.js in Hephaestus...${NC}"
    ln -sf "../../../Ergon/ui_connector.js" "$HEPHAESTUS_SRC_DIR/components/ergon/ui_connector.js"
fi

# Launch Tekton UI
echo -e "${YELLOW}Starting Tekton UI...${NC}"
./hephaestus_launch &

# Wait for server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 5

# Open browser
echo -e "${YELLOW}Opening browser to Tekton UI...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "http://localhost:8080"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "http://localhost:8080"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    start "http://localhost:8080"
fi

echo -e "${GREEN}Ergon is now integrated with Tekton UI!${NC}"
echo -e "${BLUE}To view Ergon, click on it in the left sidebar of the Tekton UI.${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the script (Tekton UI will continue running in the background).${NC}"

# Keep script running to show logs
tail -f /dev/null