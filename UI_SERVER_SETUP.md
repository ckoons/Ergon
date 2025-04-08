# Ergon UI Server Setup

This guide explains how to set up and run the Ergon UI server for integration with Tekton.

## Prerequisites

1. Node.js 16+ installed
2. Python 3.8+ installed
3. Ergon CLI installed and functional
4. Tekton UI framework installed

## Setup Steps

### 1. Install Dependencies

```bash
# Install Node.js dependencies
cd /Users/cskoons/projects/github/Tekton/Ergon
npm install --save @mui/material @emotion/react @emotion/styled @mui/icons-material uuid
```

### 2. Configure Tekton Integration

Make sure Ergon is registered in the Tekton component configuration:

```bash
# Verify Ergon in the Tekton config
cat /Users/cskoons/projects/github/Tekton/config/components.json
```

If needed, add Ergon to the configuration:

```json
{
  "components": [
    {
      "name": "Ergon",
      "path": "./Ergon/ui_connector.js",
      "enabled": true,
      "order": 3
    }
  ]
}
```

### 3. Set Up Environment

Ensure the necessary environment variables are set:

```bash
# Create or edit .env file
cat > /Users/cskoons/projects/github/Tekton/Ergon/.env << EOF
ERGON_AUTHENTICATION=false
ERGON_DEFAULT_MODEL=claude-3-sonnet
EOF
```

### 4. Start the Server

There are two ways to start the server:

#### Option 1: Through Tekton

```bash
# Start the entire Tekton framework including Ergon
cd /Users/cskoons/projects/github/Tekton
./hephaestus_launch
```

#### Option 2: Standalone Ergon UI (for development)

```bash
# Start just the Ergon UI server
cd /Users/cskoons/projects/github/Tekton/Ergon
./run_ui_no_auth.sh
```

## Accessing the UI

Once started:

- **With Tekton**: Access via http://localhost:8080 and navigate to Ergon via the left panel
- **Standalone**: Access via http://localhost:8501 directly

## Troubleshooting

### Common Issues

1. **Missing dependencies**:
   ```
   npm ERR! Cannot find module '@mui/material'
   ```
   Solution: Install missing npm packages with `npm install`

2. **Python CLI not found**:
   ```
   Error: Python module 'ergon' not found
   ```
   Solution: Make sure Ergon is installed and in your PYTHONPATH

3. **Port conflicts**:
   ```
   Error: Address already in use
   ```
   Solution: Stop other services using port 8080 (Tekton) or 8501 (Standalone)

4. **Authentication issues**:
   ```
   Error: Unauthorized
   ```
   Solution: Set `ERGON_AUTHENTICATION=false` in your .env file for development

### Logs

Check the following logs for more information:

```bash
# Tekton logs
cat /Users/cskoons/projects/github/Tekton/logs/hephaestus.log

# Ergon UI logs
cat /Users/cskoons/projects/github/Tekton/Ergon/logs/ui.log
```

## Restarting Services

To restart:

```bash
# Kill running services
pkill -f hephaestus
pkill -f streamlit

# Start again
cd /Users/cskoons/projects/github/Tekton
./hephaestus_launch
```