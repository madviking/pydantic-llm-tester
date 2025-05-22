"""
Configuration manager for LLM Tester
"""

import os
import json
import time

import requests # Import requests
import logging # Import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path # Import Path

from .common import get_openrouter_models_path, OPENROUTER_MODELS_URL # Import paths from common

logger = logging.getLogger(__name__) # Get logger

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
        "bridge": {
            "default_provider": "openai",
            "default_model": "gpt-4",
            "secondary_provider": "anthropic",
            "secondary_model": "claude-3-opus"
        },
        "py_models": {}
    }

    def __init__(self, config_path: str = None, temp_mode: bool = False):
        from .common import get_default_config_path, get_py_models_dir
        
        self.temp_mode = temp_mode
        self.config_path = config_path or get_default_config_path()
        self.config = self._load_config()

        # Discover built-in py models and register them if not in config
        # This should only happen if py_models are enabled
        if self.is_py_models_enabled():
             try:
                 self._register_builtin_py_models()
             except Exception as e:
                 import logging
                 logging.getLogger(__name__).warning(f"Error registering built-in py models: {e}")
                 # Continue even if registration fails to allow tests to work

        fetch_and_save_openrouter_models() # Fetch and save models on boot


    def _discover_builtin_py_models(self) -> List[str]:
        """Discovers the names of built-in py models."""
        from .common import get_py_models_dir
        
        # Get the path to the built-in py_models directory
        builtin_models_dir = get_py_models_dir()

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

    # PyModel specific LLM model configuration
    def get_py_model_llm_models(self, model_name: str) -> List[str]:
        """
        Get the list of configured LLM models for a specific Pydantic model.
        Returns an empty list if no models are configured.
        """
        py_models = self.config.get("py_models", {})
        models = py_models.get(model_name, {}).get("llm_models", [])
        
        # Add debug logging
        import logging
        logger = logging.getLogger(__name__)
        if models:
            logger.info(f"Found LLM models for {model_name} in config: {models}")
        else:
            logger.info(f"No LLM models configured for {model_name} in pyllm_config.json")
            
        return models

    def set_py_model_llm_models(self, model_name: str, llm_models: List[str]) -> None:
        """
        Set the list of configured LLM models for a specific Pydantic model.
        Expects llm_models as a list of strings like ['provider:model'].
        """
        if "py_models" not in self.config:
            self.config["py_models"] = {}
        if model_name not in self.config["py_models"]:
            self.config["py_models"][model_name] = {}

        # TODO: Add validation for the format of llm_models list
        self.config["py_models"][model_name]["llm_models"] = llm_models
        self.save_config()

    # Bridge configuration methods
    def get_bridge_settings(self) -> Dict[str, Any]:
        """Get bridge configuration settings."""
        return self.config.get("bridge", {})

    def get_bridge_default_provider(self) -> Optional[str]:
        """Get the default provider for bridge."""
        return self.get_bridge_settings().get("default_provider")

    def get_bridge_default_model(self) -> Optional[str]:
        """Get the default model for bridge."""
        return self.get_bridge_settings().get("default_model")

    def get_bridge_secondary_provider(self) -> Optional[str]:
        """Get the secondary provider for bridge."""
        return self.get_bridge_settings().get("secondary_provider")

    def get_bridge_secondary_model(self) -> Optional[str]:
        """Get the secondary model for bridge."""
        return self.get_bridge_settings().get("secondary_model")

    def set_bridge_setting(self, setting_name: str, value: Any) -> None:
        """Update a bridge setting."""
        if "bridge" not in self.config:
            self.config["bridge"] = {}
        self.config["bridge"][setting_name] = value
        self.save_config()

    def _parse_model_string(self, model_string: str) -> Tuple[str, str]:
        """
        Helper method to parse a 'provider:model' string into provider and model names.
        Raises ValueError if the format is incorrect.
        """
        parts = model_string.split(':')
        if len(parts) != 2 or not all(parts):
            raise ValueError(f"Invalid model string format: {model_string}. Expected 'provider:model'.")
        return parts[0], parts[1]

def fetch_and_save_openrouter_models():
    """
    Fetches OpenRouter models and saves them to openrouter_models.json with 1-hour caching.
    The cache will be refreshed if the file doesn't exist or is older than 1 hour.
    """
    openrouter_models_path = get_openrouter_models_path()
    logger.debug(f"Checking for OpenRouter models file at: {openrouter_models_path}")
    
    # Check if cache is valid (exists and is less than 1 hour old)
    cache_valid = False
    if os.path.exists(openrouter_models_path):
        try:
            # Get file modification time
            file_mtime = os.path.getmtime(openrouter_models_path)
            file_age = time.time() - file_mtime
            cache_duration = 3600  # 1 hour in seconds
            
            if file_age < cache_duration:
                cache_valid = True
                logger.debug(f"Cache is valid. File age: {file_age:.0f}s (< {cache_duration}s)")
            else:
                logger.info(f"Cache expired. File age: {file_age:.0f}s (>= {cache_duration}s)")
        except OSError as e:
            logger.warning(f"Error checking file modification time: {e}")
            cache_valid = False
    else:
        logger.info(f"{openrouter_models_path} not found.")
    
    # Fetch and save if cache is invalid
    if not cache_valid:
        logger.info("Fetching models from OpenRouter API.")
        logger.debug("Attempting to fetch models from OpenRouter API.")
        try:
            response = requests.get(OPENROUTER_MODELS_URL)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            models_data = response.json()

            with open(openrouter_models_path, "w") as f:
                json.dump(models_data, f, indent=2)
            logger.info(f"Successfully fetched and saved OpenRouter models to {openrouter_models_path}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching OpenRouter models from {OPENROUTER_MODELS_URL}: {e}")
        except IOError as e:
            logger.error(f"Error writing OpenRouter models to {openrouter_models_path}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response from OpenRouter API: {e}")
    else:
        logger.debug("Using cached OpenRouter models (file is fresh).")
