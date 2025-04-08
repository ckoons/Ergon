#!/bin/bash
# Script to apply Ergon integration to Tekton UI

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TEKTON_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}=== Ergon Integration for Tekton UI ===${NC}"
echo -e "${YELLOW}This script will help you apply the Ergon integration to ComponentView.js${NC}"
echo -e "${YELLOW}IMPORTANT: This integration will NOT modify the top page structure${NC}"

# Check that Hephaestus exists
if [ ! -d "$TEKTON_ROOT/Hephaestus" ]; then
    echo -e "${RED}ERROR: Hephaestus directory not found at $TEKTON_ROOT/Hephaestus${NC}"
    echo "Please make sure you have the Hephaestus component installed."
    exit 1
fi

# Check that ui_connector.js exists
if [ ! -f "$SCRIPT_DIR/ui_connector.js" ]; then
    echo -e "${RED}ERROR: ui_connector.js not found in $SCRIPT_DIR${NC}"
    echo "The UI connector file is required for Tekton UI integration."
    exit 1
fi

# Ensure Ergon components directory exists in Hephaestus
ERGON_COMP_DIR="$TEKTON_ROOT/Hephaestus/src/components/ergon"
if [ ! -d "$ERGON_COMP_DIR" ]; then
    echo -e "${YELLOW}Creating Ergon component directory in Hephaestus...${NC}"
    mkdir -p "$ERGON_COMP_DIR"
fi

# Create a symlink to ui_connector.js in Hephaestus
if [ ! -L "$ERGON_COMP_DIR/ui_connector.js" ]; then
    echo -e "${YELLOW}Creating symlink to ui_connector.js in Hephaestus...${NC}"
    ln -sf "$SCRIPT_DIR/ui_connector.js" "$ERGON_COMP_DIR/ui_connector.js"
fi

# Check if ComponentView.js exists
COMPONENT_VIEW="$TEKTON_ROOT/Hephaestus/src/pages/ComponentView.js"
if [ ! -f "$COMPONENT_VIEW" ]; then
    echo -e "${RED}ERROR: ComponentView.js not found at $COMPONENT_VIEW${NC}"
    exit 1
fi

# Open the integration instructions file
echo -e "${GREEN}Integration ready!${NC}"
echo -e "${YELLOW}To complete the integration, you need to modify ComponentView.js${NC}"
echo -e "${YELLOW}Detailed instructions are in:${NC} ${BLUE}$SCRIPT_DIR/ui/componentview_ergon_integration.js${NC}"

# Ask if the user wants to open the files
echo
echo -e "${YELLOW}Would you like to see the integration instructions? (y/n)${NC}"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Try to open the file using the appropriate command for the OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "$SCRIPT_DIR/ui/componentview_ergon_integration.js"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open > /dev/null; then
            xdg-open "$SCRIPT_DIR/ui/componentview_ergon_integration.js"
        else
            cat "$SCRIPT_DIR/ui/componentview_ergon_integration.js"
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        start "$SCRIPT_DIR/ui/componentview_ergon_integration.js"
    else
        cat "$SCRIPT_DIR/ui/componentview_ergon_integration.js"
    fi
fi

echo
echo -e "${GREEN}After applying the changes, run:${NC} ${BLUE}$SCRIPT_DIR/run_tekton_ui.sh${NC}"
echo -e "${GREEN}to start the Tekton UI with Ergon integration.${NC}"
echo
echo -e "${YELLOW}IMPORTANT:${NC} This integration keeps Ergon content ONLY in the RIGHT PANEL"
echo -e "and does not modify the top page structure."