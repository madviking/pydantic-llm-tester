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
            "default_modules": ["job_ads"],
            "py_models_path": "./py_models",
            "py_models_enabled": True # Added py_models_enabled flag
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

        # Discover built-in py models and register them if not in config
        # This should only happen if py_models are enabled
        if self.is_py_models_enabled():
             self._register_builtin_py_models()

    def _discover_builtin_py_models(self) -> List[str]:
        """Discovers the names of built-in py models."""
        # Determine the directory containing the built-in py_models relative to this file
        _current_file_dir = os.path.dirname(os.path.abspath(__file__))
        _src_dir = os.path.dirname(_current_file_dir) # Go up one level to src
        builtin_models_dir = os.path.join(_src_dir, "py_models")

        if not os.path.exists(builtin_models_dir):
            return []

        model_names = []
        for item_name in os.listdir(builtin_models_dir):
            item_path = os.path.join(builtin_models_dir, item_name)
            # Check if it's a directory and not a special directory/file
            if os.path.isdir(item_path) and not item_name.startswith("__") and not item_name.startswith("."):
                model_names.append(item_name)
        return model_names

    def _register_builtin_py_models(self):
        """Discovers built-in py models and registers them in the config if not present."""
        builtin_models = self._discover_builtin_py_models()
        registered_models = self.get_py_models()

        needs_save = False
        for model_name in builtin_models:
            if model_name not in registered_models:
                # Register and enable by default
                self.config["py_models"][model_name] = {"enabled": True}
                needs_save = True

        if needs_save:
            self.save_config()

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

    def is_py_models_enabled(self) -> bool:
        """Check if py_models functionality is enabled."""
        return self.config.get("test_settings", {}).get("py_models_enabled", True)

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

    def get_py_models_path(self) -> str:
        """Get the configured path for py_models"""
        return self.config.get("test_settings", {}).get("py_models_path", "./py_models") # Default if not set

    def update_py_models_path(self, path: str) -> None:
        """Update the configured path for py_models"""
        if "test_settings" not in self.config:
            self.config["test_settings"] = {}
        self.config["test_settings"]["py_models_path"] = path
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

    def set_py_model_enabled_status(self, model_name: str, enabled: bool) -> bool:
        """Set the enabled status of a specific Python model."""
        py_models = self.config.get("py_models", {})
        if model_name in py_models:
            py_models[model_name]["enabled"] = enabled
            self.config["py_models"] = py_models # Ensure the change is reflected in the main config dict
            self.save_config()
            return True
        return False

    def get_py_model_enabled_status(self, model_name: str) -> Optional[bool]:
        """Get the enabled status of a specific Python model."""
        py_models = self.config.get("py_models", {})
        return py_models.get(model_name, {}).get("enabled")

    def get_enabled_py_models(self) -> Dict[str, Any]:
        """Get only enabled Python models"""
        return {
            name: config
            for name, config in self.get_py_models().items()
            if config.get("enabled", False)
        }
