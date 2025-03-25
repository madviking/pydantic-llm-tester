"""
Configuration manager for LLM Tester
"""

import os
import json
from typing import Dict, Any, Optional


# Default configuration
DEFAULT_CONFIG = {
    "providers": {
        "openai": {
            "enabled": True,
            "default_model": "gpt-4"
        },
        "anthropic": {
            "enabled": True,
            "default_model": "claude-3-opus-20240229"
        },
        "mistral": {
            "enabled": True,
            "default_model": "mistral-large-latest"
        },
        "google": {
            "enabled": True,
            "default_model": "gemini-1.5-flash"
        },
        "mock_provider": {
            "enabled": False,
            "default_model": "mock-model"
        }
    },
    "test_settings": {
        "output_dir": "test_results",
        "save_optimized_prompts": True,
        "default_modules": ["job_ads"]
    }
}


def get_config_path() -> str:
    """Get the path to the config file"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json
    
    Returns:
        Dict containing configuration values
    """
    config_path = get_config_path()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to config.json
    
    Args:
        config: Configuration dictionary to save
    """
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"Error saving config: {e}")


def get_enabled_providers() -> Dict[str, Dict[str, Any]]:
    """
    Get dictionary of enabled providers with their configurations
    
    Returns:
        Dictionary of enabled providers
    """
    config = load_config()
    providers = config.get("providers", {})
    return {name: details for name, details in providers.items() 
            if details.get("enabled", False)}


def get_provider_model(provider_name: str) -> Optional[str]:
    """
    Get the default model for a provider
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Model name or None if provider not found
    """
    config = load_config()
    provider_config = config.get("providers", {}).get(provider_name, {})
    return provider_config.get("default_model")


def get_test_setting(setting_name: str, default: Any = None) -> Any:
    """
    Get a test setting value
    
    Args:
        setting_name: Name of the setting
        default: Default value if setting not found
        
    Returns:
        Setting value or default if not found
    """
    config = load_config()
    return config.get("test_settings", {}).get(setting_name, default)


def update_test_setting(setting_name: str, value: Any) -> None:
    """
    Update a test setting
    
    Args:
        setting_name: Name of the setting
        value: New setting value
    """
    config = load_config()
    
    if "test_settings" not in config:
        config["test_settings"] = {}
        
    config["test_settings"][setting_name] = value
    save_config(config)