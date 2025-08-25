"""
API Key Manager for DataPM Processor
Handles multiple API keys and automatic switching
"""

import os
import random
import time
from typing import List, Optional
from datetime import datetime, timedelta

class DataPMAPIKeyManager:
    """Manages API keys with automatic rotation for DataPM"""
    
    def __init__(self, keys: List[str] = None, rotation_strategy: str = "round_robin"):
        self.keys = keys or []
        self.rotation_strategy = rotation_strategy
        self.current_index = 0
        self.key_usage = {}  # Track usage per key
        self.key_errors = {}  # Track errors per key
        
        # Load keys from environment if not provided
        if not self.keys:
            self._load_keys_from_env()
    
    def _load_keys_from_env(self):
        """Load API keys from DataPM file, environment variables, or fallback locations"""
        from pathlib import Path
        
        # PRIORITY 1: Load from DataPM API_keys.txt file (ALWAYS check this first)
        datapm_api_file = Path("API_keys.txt")  # Local to DataPM directory
        if datapm_api_file.exists():
            try:
                with open(datapm_api_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
                    if keys:
                        self.keys = keys
                        print(f"✅ DataPM: Loaded {len(keys)} API keys from local API_keys.txt")
                        return
            except Exception as e:
                print(f"⚠️ DataPM: Error reading local API keys file: {e}")
        
        # PRIORITY 2: Try absolute path to DataPM API keys
        abs_datapm_api_file = Path("D:/Work Work/Upwork/DataPM/csv_engine/engines/API_keys.txt")
        if abs_datapm_api_file.exists():
            try:
                with open(abs_datapm_api_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
                    if keys:
                        self.keys = keys
                        print(f"✅ DataPM: Loaded {len(keys)} API keys from DataPM API_keys.txt")
                        return
            except Exception as e:
                print(f"⚠️ DataPM: Error reading DataPM API keys file: {e}")
        
        # PRIORITY 3: Try environment variables
        env_vars = [
            'GEMINI_API_KEYS',
            'OPENAI_API_KEYS', 
            'ANTHROPIC_API_KEYS',
            'API_KEYS'
        ]
        
        for env_var in env_vars:
            keys_str = os.getenv(env_var)
            if keys_str:
                # Split by comma and clean up
                keys = [key.strip() for key in keys_str.split(',') if key.strip()]
                if keys:
                    self.keys = keys
                    print(f"✅ DataPM: Loaded {len(keys)} API keys from {env_var}")
                    return
        
        if not self.keys:
            print("❌ DataPM: No API keys found in DataPM file, environment variables, or local files")
    
    def get_key(self, strategy: str = None) -> Optional[str]:
        """Get next API key based on strategy"""
        if not self.keys:
            return None
        
        strategy = strategy or self.rotation_strategy
        
        if strategy == "round_robin":
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
        
        elif strategy == "random":
            key = random.choice(self.keys)
        
        elif strategy == "least_used":
            # Get key with least usage
            key = min(self.keys, key=lambda k: self.key_usage.get(k, 0))
        
        elif strategy == "least_errors":
            # Get key with least errors
            key = min(self.keys, key=lambda k: self.key_errors.get(k, 0))
        
        else:
            key = self.keys[0]  # Default to first key
        
        # Track usage
        self.key_usage[key] = self.key_usage.get(key, 0) + 1
        
        return key
    
    def mark_error(self, key: str, error_type: str = "rate_limit"):
        """Mark a key as having an error"""
        if key in self.keys:
            self.key_errors[key] = self.key_errors.get(key, 0) + 1
            print(f"⚠️ DataPM API key error: {error_type} for key ending in ...{key[-4:]}")
    
    def get_healthy_keys(self) -> List[str]:
        """Get keys with fewest errors"""
        if not self.key_errors:
            return self.keys
        
        # Filter out keys with too many errors
        max_errors = 3
        healthy_keys = [key for key in self.keys if self.key_errors.get(key, 0) < max_errors]
        
        if not healthy_keys:
            # Reset error counts if all keys have too many errors
            self.key_errors.clear()
            healthy_keys = self.keys
        
        return healthy_keys
    
    def get_stats(self) -> dict:
        """Get usage statistics"""
        return {
            'total_keys': len(self.keys),
            'healthy_keys': len(self.get_healthy_keys()),
            'key_usage': self.key_usage.copy(),
            'key_errors': self.key_errors.copy(),
            'current_index': self.current_index,
            'rotation_strategy': self.rotation_strategy
        }
    
    def reset_errors(self):
        """Reset error counts for all keys"""
        self.key_errors.clear()
        print("✅ DataPM: Reset API key error counts")

# Global instance for DataPM
datapm_api_manager = DataPMAPIKeyManager()

def get_datapm_api_key(strategy: str = "round_robin") -> Optional[str]:
    """Get API key from DataPM manager"""
    return datapm_api_manager.get_key(strategy)

def mark_datapm_api_error(key: str, error_type: str = "rate_limit"):
    """Mark API error for DataPM manager"""
    datapm_api_manager.mark_error(key, error_type)

def get_datapm_api_stats() -> dict:
    """Get DataPM API key statistics"""
    return datapm_api_manager.get_stats()
