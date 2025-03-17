# ClaudeMemoryBridge to Engram Migration Guide

## Overview

The ClaudeMemoryBridge (CMB) project has been renamed to Engram. This guide helps you migrate your Agenteer installation from CMB to Engram.

## Migration Steps

### 1. Install Engram

First, install Engram by cloning the repository and using our installation script:

```bash
# Clone the Engram repository if you don't have it yet
cd ~/projects/github
git clone https://github.com/anthropics/Engram.git  # Replace with the actual repo URL

# Install Engram in development mode
cd Agenteer
./scripts/install_engram.sh
```

Our updated installation script automatically detects whether you have Engram or ClaudeMemoryBridge installed, and configures Agenteer appropriately.

### 2. Migrate Memories (Optional)

If you have existing memories in CMB that you want to transfer to Engram, use our migration tool:

```bash
cd ~/projects/github/Agenteer
python scripts/migration/cmb_to_engram.py
```

This script:
- Checks if both CMB and Engram are installed
- Imports memories from CMB to Engram
- Updates configuration files to use Engram instead of CMB

For more advanced options:

```bash
# Just check package availability
python scripts/migration/cmb_to_engram.py --check-only

# Just import memories
python scripts/migration/cmb_to_engram.py --import-memories

# Force import even if Engram data already exists
python scripts/migration/cmb_to_engram.py --import-memories --force

# Just update configuration files
python scripts/migration/cmb_to_engram.py --update-config
```

### 3. Test Your Migration

After migrating, test that everything works correctly:

```bash
# Create a new Nexus agent
agenteer create -n "TestMemoryAgent" -d "Testing Engram integration" -t nexus

# Chat with the agent to test memory
agenteer nexus "TestMemoryAgent" --interactive
```

Try storing and retrieving memories to ensure the integration works properly.

### 4. Environment Variable Updates

If you're using environment variables directly, update them:

| Old (CMB)         | New (Engram)        |
|-------------------|---------------------|
| CMB_HTTP_URL      | ENGRAM_HTTP_URL     |
| CMB_CLIENT_ID     | ENGRAM_CLIENT_ID    |
| CMB_DATA_DIR      | ENGRAM_DATA_DIR     |

### 5. Cleanup (Optional)

Once you've confirmed everything works with Engram, you can remove CMB:

```bash
pip uninstall cmb
```

## Compatibility Mode

During the transition period, Agenteer is designed to work with both Engram and CMB. It tries to import from Engram first, and falls back to CMB if needed.

If you encounter issues, you can explicitly enable CMB compatibility:

```bash
export ENGRAM_ENABLE_CMB_COMPAT=true
```

## Troubleshooting

If you encounter issues during migration:

1. **Import Failures**: If memory import fails:
   - Check permissions on the data directories
   - Try manually copying memories from `~/.cmb/memories/` to `~/.engram/memories/`

2. **Module Not Found Errors**: Ensure both packages are installed:
   ```bash
   pip list | grep -E "cmb|engram"
   ```

3. **API Errors**: If you get HTTP errors:
   - Make sure the Engram service is running
   - Check that the HTTP URL is set correctly (default: http://127.0.0.1:8000)
   - Verify that you're using the latest version of both Agenteer and Engram

4. **Memory Not Working**: If memory functionality isn't working:
   - Check that the Engram client ID is set correctly
   - Verify that the memory directories exist and have the right permissions
   - Ensure the Engram service is running (try `pgrep -f "engram.api.consolidated_server"`)

## Technical Details

The migration to Engram includes several improvements:

1. **Structured Memory**: Enhanced organization with categories and importance ranking
2. **Improved HTTP API**: More consistent API endpoints with better documentation
3. **Better Multi-User Support**: Improved isolation between different client sessions
4. **Simplified Authentication**: Easier setup for API authentication

For deeper technical details, see the Engram documentation.