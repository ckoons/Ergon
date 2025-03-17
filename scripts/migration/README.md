# ClaudeMemoryBridge to Engram Migration

This directory contains tools and documentation to help migrate from ClaudeMemoryBridge (CMB) to Engram, its successor.

## Background

ClaudeMemoryBridge (CMB) has been renamed to Engram. The project has the same core functionality but has been restructured and enhanced. This migration guide helps you transition your Agenteer installation to use Engram.

## Migration Steps

### 1. Check Environment

First, check if you have Engram and/or CMB installed:

```bash
python scripts/migration/cmb_to_engram.py --check-only
```

### 2. Install Engram

If you don't have Engram installed, clone the repository and install it:

```bash
# Clone the repository if you don't have it
cd ~/projects/github
git clone https://github.com/anthropics/Engram.git

# Install Engram in development mode
cd Agenteer
./scripts/install_engram.sh
```

### 3. Import Memories

If you have existing memories in CMB that you want to transfer to Engram:

```bash
python scripts/migration/cmb_to_engram.py --import-memories
```

If you've already used Engram and want to overwrite its memories with those from CMB:

```bash
python scripts/migration/cmb_to_engram.py --import-memories --force
```

### 4. Update Configuration

Update your environment variables and configuration files:

```bash
python scripts/migration/cmb_to_engram.py --update-config
```

### 5. Run Everything at Once

You can also run all steps together:

```bash
python scripts/migration/cmb_to_engram.py
```

## Verification

After migration, verify that everything works correctly:

1. Create a new Nexus agent:
   ```bash
   agenteer create -n "TestMemoryAgent" -d "Testing Engram integration" -t nexus
   ```

2. Chat with the agent to test memory:
   ```bash
   agenteer nexus "TestMemoryAgent" --interactive
   ```

## Troubleshooting

If you encounter issues during migration:

1. Check the logs for detailed error messages
2. Ensure both Engram and Agenteer are using compatible versions
3. If memory import fails, try manually copying memories:
   - From: `~/.cmb/memories/`
   - To: `~/.engram/memories/`
4. If you continue to see issues, you can temporarily enable CMB compatibility by setting:
   ```
   export ENGRAM_ENABLE_CMB_COMPAT=true
   ```

## Cleanup (After Successful Migration)

Once you've confirmed everything works with Engram, you can remove CMB:

```bash
pip uninstall cmb
```

And remove any CMB-specific environment variables from your configuration.