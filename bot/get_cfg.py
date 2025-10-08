# 3. bot/get_cfg.py - Enhanced configuration getter

import os
import json
from typing import Any, Optional

def get_config(name: str, d_v: Any = None, should_prompt: bool = False) -> Any:
    """
    Enhanced configuration getter with better error handling
    """
    try:
        val = os.environ.get(name, d_v)
        
        if not val and should_prompt:
            try:
                val = input(f"Enter {name}'s value: ")
            except (EOFError, KeyboardInterrupt):
                val = d_v
            print()
            
        # Type conversion for specific config values
        if name.endswith('_ID') or name.endswith('_SIZE') or name.endswith('_LIMIT'):
            if val and str(val).isdigit():
                val = int(val)
                
        elif name.startswith('ENABLE_') or name.endswith('_ENABLED'):
            if isinstance(val, str):
                val = val.lower() in ['true', '1', 'yes', 'on']
                
        return val
        
    except Exception as e:
        print(f"Error getting config {name}: {e}")
        return d_v

def load_config_from_file(file_path: str) -> dict:
    """Load configuration from JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config file {file_path}: {e}")
    return {}

def save_config_to_file(config: dict, file_path: str) -> bool:
    """Save configuration to JSON file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config file {file_path}: {e}")
        return False
print("Created configuration files")
