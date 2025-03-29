# Claude Memory Bridge

> **Note**: This implementation has been moved to a dedicated repository: [ClaudeMemoryBridge](https://github.com/ckoons/ClaudeMemoryBridge)

The Claude Memory Bridge provides Claude with persistent memory across conversations, enabling continuous learning and relationship building.

## Why a Dedicated Repository?

This tool has been moved to its own repository to:

1. Allow it to be used independently of Ergon
2. Provide more focused development and versioning
3. Enable easier integration with other projects

## Features in the New Repository

- Multiple memory namespaces (conversations, thinking, longterm, projects)
- Ultra-short memory commands for more natural integration
- Memory management with forget and ignore capabilities
- Tool-approval-free memory access via HTTP
- Comprehensive documentation and examples

## How to Use

Visit the [ClaudeMemoryBridge](https://github.com/ckoons/ClaudeMemoryBridge) repository for installation and usage instructions.

```bash
# Install
cd ~/projects/github
git clone https://github.com/ckoons/ClaudeMemoryBridge.git
cd ClaudeMemoryBridge

# Start all services
./cmb_start_all

# In Claude Code
from cmb.cli.quickmem import m, t, r, f, i
```