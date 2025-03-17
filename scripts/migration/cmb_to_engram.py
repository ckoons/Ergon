#!/usr/bin/env python3
"""
Migration script for transitioning from ClaudeMemoryBridge to Engram.

This script facilitates the migration process to help users:
1. Check if Engram is installed
2. Import memories from ClaudeMemoryBridge to Engram
3. Update configuration to use Engram instead of CMB

Usage:
python cmb_to_engram.py [--check-only] [--import-memories] [--update-config]
"""

import argparse
import importlib.util
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb_to_engram")

def check_package_availability() -> Tuple[bool, bool]:
    """Check if Engram and/or CMB packages are available."""
    
    has_engram = importlib.util.find_spec("engram") is not None
    has_cmb = importlib.util.find_spec("cmb") is not None
    
    return has_engram, has_cmb

def import_memories(force: bool = False) -> bool:
    """Import memories from CMB to Engram."""
    
    has_engram, has_cmb = check_package_availability()
    
    if not has_engram:
        logger.error("Engram package is not installed. Import failed.")
        return False
    
    if not has_cmb:
        logger.warning("CMB package is not installed. No memories to import.")
        return False
    
    # Import CMB and Engram modules
    try:
        # First, import paths
        from cmb.core.paths import CMB_DATA_DIR
        from engram.core.paths import ENGRAM_DATA_DIR
        
        logger.info(f"CMB data directory: {CMB_DATA_DIR}")
        logger.info(f"Engram data directory: {ENGRAM_DATA_DIR}")
        
        # Check if data directories exist
        if not os.path.exists(CMB_DATA_DIR):
            logger.warning(f"CMB data directory not found: {CMB_DATA_DIR}")
            return False
        
        # Create Engram data directory if it doesn't exist
        os.makedirs(ENGRAM_DATA_DIR, exist_ok=True)
        
        # Check if Engram data directory already has content and force is False
        if os.path.exists(os.path.join(ENGRAM_DATA_DIR, "memories")) and not force:
            logger.warning("Engram already has memories. Use --force to overwrite.")
            return False
        
        # Copy memory files from CMB to Engram
        shutil.copytree(
            os.path.join(CMB_DATA_DIR, "memories"),
            os.path.join(ENGRAM_DATA_DIR, "memories"),
            dirs_exist_ok=True
        )
        
        # Copy index files if they exist
        cmb_index_path = os.path.join(CMB_DATA_DIR, "indexes")
        engram_index_path = os.path.join(ENGRAM_DATA_DIR, "indexes")
        
        if os.path.exists(cmb_index_path):
            os.makedirs(engram_index_path, exist_ok=True)
            for item in os.listdir(cmb_index_path):
                s = os.path.join(cmb_index_path, item)
                d = os.path.join(engram_index_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        
        logger.info("Successfully imported memories from CMB to Engram")
        return True
        
    except Exception as e:
        logger.error(f"Error importing memories: {e}")
        return False

def update_config() -> bool:
    """Update configuration files to use Engram instead of CMB."""
    
    # Look for common config locations
    home_dir = str(Path.home())
    config_locations = [
        os.path.join(home_dir, ".env"),
        os.path.join(home_dir, ".config", "agenteer", "config.env"),
        os.path.join(home_dir, ".agenteer", "config.env"),
        ".env"
    ]
    
    updated = False
    
    for config_file in config_locations:
        if os.path.exists(config_file):
            try:
                # Read the current config
                with open(config_file, "r") as f:
                    content = f.read()
                
                # Replace CMB variables with Engram variables
                replacements = [
                    ("CMB_HTTP_URL", "ENGRAM_HTTP_URL"),
                    ("CMB_CLIENT_ID", "ENGRAM_CLIENT_ID"),
                    ("CMB_DATA_DIR", "ENGRAM_DATA_DIR")
                ]
                
                new_content = content
                for old, new in replacements:
                    new_content = new_content.replace(old, new)
                
                # Write updated config back
                if new_content != content:
                    # Create backup
                    backup_file = f"{config_file}.bak"
                    shutil.copy2(config_file, backup_file)
                    logger.info(f"Created backup of {config_file} at {backup_file}")
                    
                    with open(config_file, "w") as f:
                        f.write(new_content)
                    
                    logger.info(f"Updated configuration in {config_file}")
                    updated = True
                else:
                    logger.info(f"No CMB variables found in {config_file}")
            
            except Exception as e:
                logger.error(f"Error updating config file {config_file}: {e}")
    
    return updated

def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description="CMB to Engram Migration Tool")
    parser.add_argument("--check-only", action="store_true", help="Only check package availability")
    parser.add_argument("--import-memories", action="store_true", help="Import memories from CMB to Engram")
    parser.add_argument("--update-config", action="store_true", help="Update configuration files")
    parser.add_argument("--force", action="store_true", help="Force import even if Engram data already exists")
    
    args = parser.parse_args()
    
    # If no arguments provided, run everything
    if not (args.check_only or args.import_memories or args.update_config):
        args.check_only = True
        args.import_memories = True
        args.update_config = True
    
    if args.check_only:
        has_engram, has_cmb = check_package_availability()
        logger.info(f"Engram package available: {has_engram}")
        logger.info(f"CMB package available: {has_cmb}")
        
        if has_engram:
            logger.info("✅ Engram is installed, ready for migration")
        else:
            logger.warning("⚠️ Engram is not installed, install with: pip install -e /path/to/Engram")
        
        if has_cmb:
            logger.info("📦 ClaudeMemoryBridge is installed, can import memories")
        else:
            logger.info("❌ ClaudeMemoryBridge is not installed, memory import will be skipped")
    
    if args.import_memories:
        success = import_memories(force=args.force)
        if success:
            logger.info("✅ Successfully imported memories from CMB to Engram")
        else:
            logger.warning("⚠️ Failed to import memories. See log for details.")
    
    if args.update_config:
        success = update_config()
        if success:
            logger.info("✅ Successfully updated configuration files")
        else:
            logger.warning("⚠️ No configuration files updated")

if __name__ == "__main__":
    main()