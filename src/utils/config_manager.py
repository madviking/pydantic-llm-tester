"""
Configuration manager for LLM Tester
"""

import os
import json
from typing import Dict, Any, Optional, List


class ConfigManager:
    """Centralized configuration management for LLM providers and models"""
    
    DEFAULT_CONFIG = {
        "providers": {
            "openai": {
                "enabled": True,
                "default_model": "gpt-4",
                "api_key": None
            },
            "anthropic": {
                "enabled": True,
                "default_model": "claude-3-opus",
                "api_key": None
            },
            "mock": {
                "enabled": False,
                "default_model": "mock-model"
            }
        },
        "test_settings": {
            "output_dir": "test_results",
            "save_optimized_prompts": True,
            "default_modules": ["job_ads"]
        },
        "py_models": {}
    }

    def __init__(self, config_path: str = None, temp_mode: bool = False):
        self.temp_mode = temp_mode
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'pyllm_config.json'
        )
        self.config = self._load_config()
        
    def create_temp_config(self) -> str:
        """Create a temporary config file and return its path"""
        import tempfile
        temp_path = os.path.join(tempfile.gettempdir(), f"pyllm_test_config_{os.getpid()}.json")
        with open(temp_path, 'w') as f:
            json.dump(self.DEFAULT_CONFIG, f)
        return temp_path
        
    def cleanup_temp_config(self) -> None:
        """Remove temporary config file if in temp mode"""
        if self.temp_mode and os.path.exists(self.config_path):
            os.remove(self.config_path)

    def _load_config(self) -> Dict[str, Any]:
        """Load config from file or create default if not exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._create_default_config()
        return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create and save default config"""
        with open(self.config_path, 'w') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=2)
        return self.DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        """Save current config to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    # Provider management
    def get_providers(self) -> Dict[str, Any]:
        """Get all provider configurations"""
        return self.config.get("providers", {})

    def get_enabled_providers(self) -> Dict[str, Any]:
        """Get only enabled providers"""
        return {
            name: config 
            for name, config in self.get_providers().items() 
            if config.get("enabled", False)
        }

    def register_provider(self, name: str, config: Dict[str, Any]) -> None:
        """Register a new provider"""
        if name not in self.config["providers"]:
            self.config["providers"][name] = config
            self.save_config()

    def update_provider(self, name: str, updates: Dict[str, Any]) -> None:
        """Update an existing provider"""
        if name in self.config["providers"]:
            self.config["providers"][name].update(updates)
            self.save_config()

    # Model management
    def get_available_models(self) -> List[str]:
        """Get list of available models from enabled providers"""
        return [
            provider["default_model"]
            for provider in self.get_enabled_providers().values()
            if "default_model" in provider
        ]

    def get_provider_model(self, provider_name: str) -> Optional[str]:
        """Get the default model for a provider"""
        provider_config = self.get_providers().get(provider_name, {})
        return provider_config.get("default_model")

    # Test settings
    def get_test_setting(self, setting_name: str, default: Any = None) -> Any:
        """Get a test setting value"""
        return self.config.get("test_settings", {}).get(setting_name, default)

    def update_test_setting(self, setting_name: str, value: Any) -> None:
        """Update a test setting"""
        if "test_settings" not in self.config:
            self.config["test_settings"] = {}
        self.config["test_settings"][setting_name] = value
        self.save_config()

    # Scaffolding registration
    def register_py_model(self, model_name: str, config: Dict[str, Any]) -> None:
        """Register a new Python model"""
        if "py_models" not in self.config:
            self.config["py_models"] = {}
        self.config["py_models"][model_name] = config
        self.save_config()

    def get_py_models(self) -> Dict[str, Any]:
        """Get all registered Python models"""
        return self.config.get("py_models", {})
