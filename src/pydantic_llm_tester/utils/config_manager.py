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

from .common import get_openrouter_models_path, OPENROUTER_MODELS_URL, read_json_file # Import paths and utilities from common
# Note: ModelConfig is imported locally in methods to avoid circular imports

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

        # Fetch and save OpenRouter models on boot - all systems use it for reference
        fetch_and_save_openrouter_models()
        
        # If OpenRouter is enabled, process the models and store them in the registry
        if self.is_openrouter_enabled():
            self.process_openrouter_models()


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
        
    def is_openrouter_enabled(self) -> bool:
        """
        Check if OpenRouter is enabled in the configuration.
        
        Returns:
            bool: True if OpenRouter is enabled, False otherwise
        """
        providers = self.get_providers()
        openrouter_config = providers.get("openrouter", {})
        return openrouter_config.get("enabled", False)

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
        
    def process_openrouter_models(self) -> None:
        """
        Process OpenRouter models from openrouter_models.json and store them in the central registry.
        This converts the OpenRouter API format to our internal ModelConfig format.
        """
        from .common import get_openrouter_models_path
        from ..llms.llm_registry import LLMRegistry
        # Import ModelConfig locally to avoid circular imports
        from ..llms.base import ModelConfig
        
        # Read the OpenRouter models from the JSON file
        models_data = read_json_file(get_openrouter_models_path())
        if not models_data:
            logger.warning("No OpenRouter model data found in file.")
            return
            
        if not isinstance(models_data, dict):
            logger.warning(f"OpenRouter model data is not a dictionary. Got: {type(models_data)}")
            return
            
        if "data" not in models_data:
            logger.warning("OpenRouter model data does not contain 'data' key.")
            return
            
        if not isinstance(models_data["data"], list):
            logger.warning(f"OpenRouter 'data' is not a list. Got: {type(models_data['data'])}")
            return
            
        # Process the models and convert to ModelConfig objects
        model_configs = {}
        for model_data in models_data["data"]:
            model_id = model_data.get("id", "")
            # Skip models that don't have a valid ID
            if not model_id:
                continue
                
            # Clean up the model ID to get just the model name part
            # OpenRouter model IDs can have several formats:
            # 1. 'openrouter/model-name' - Standard format where openrouter is the provider prefix
            # 2. 'openrouter/provider/model-name' - Models from specific providers like anthropic
            # 3. Sometimes more complex paths like 'openrouter/provider/family/model-name'
            if "/" in model_id:
                parts = model_id.split("/")
                if len(parts) == 2:
                    # Format: 'openrouter/model-name'
                    # Example: 'openrouter/mistral-large-latest'
                    # We extract just 'mistral-large-latest'
                    model_name = parts[1]
                elif len(parts) >= 3:
                    # Format: 'openrouter/provider/model-name' or more complex paths
                    # Example: 'openrouter/anthropic/claude-3-opus'
                    # We extract everything after the second slash: 'claude-3-opus'
                    # This handles nested paths by joining with '/' if needed
                    model_name = "/".join(parts[2:])
                else:
                    # Fallback for unexpected formats - use the full ID
                    logger.warning(f"Unexpected OpenRouter model ID format: {model_id}")
                    model_name = model_id
            else:
                # If there's no slash, use the ID as is (unlikely but handled)
                model_name = model_id
                
            # Create the full prefixed model name for our system
            full_model_name = f"openrouter:{model_name}"
            
            # Extract pricing information with validation
            pricing = model_data.get("pricing", {})
            if not isinstance(pricing, dict):
                logger.warning(f"Invalid pricing format for model {model_id}: {pricing}")
                pricing = {}
                
            # Get prompt and completion costs with validation
            try:
                prompt_cost = pricing.get("prompt", 0.0)
                prompt_cost = float(prompt_cost) if prompt_cost is not None else 0.0
                cost_input = prompt_cost * 1000000  # Convert to per 1M tokens
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid prompt cost for model {model_id}: {pricing.get('prompt')}: {e}")
                cost_input = 0.0
                
            try:
                completion_cost = pricing.get("completion", 0.0)
                completion_cost = float(completion_cost) if completion_cost is not None else 0.0
                cost_output = completion_cost * 1000000  # Convert to per 1M tokens
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid completion cost for model {model_id}: {pricing.get('completion')}: {e}")
                cost_output = 0.0
            
            # Extract context length with validation
            try:
                context_length = model_data.get("context_length", 4096)
                context_length = int(context_length) if context_length is not None else 4096
                # Sanity check for unreasonably large or small values
                if context_length <= 0 or context_length > 1000000:
                    logger.warning(f"Unreasonable context length for model {model_id}: {context_length}, using default")
                    context_length = 4096
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid context length for model {model_id}: {model_data.get('context_length')}: {e}")
                context_length = 4096
            
            # Create ModelConfig object
            model_config = ModelConfig(
                name=full_model_name,
                default=False,  # Will be set based on config later
                preferred=False,  # Will be set based on config later
                enabled=True,   # All models from API are enabled by default
                cost_input=cost_input,
                cost_output=cost_output,
                max_input_tokens=context_length,
                max_output_tokens=context_length
            )
            
            # Store in our dictionary
            model_configs[full_model_name] = model_config
            
        # Store all processed models in the central registry
        registry = LLMRegistry()
        registry.store_provider_models("openrouter", model_configs)
        logger.info(f"Stored {len(model_configs)} OpenRouter models in the central registry.")
        
    def get_model_details_from_registry(self, model_string: str):
        """
        Get model details from the central registry for a model specified in 'provider:model-name' format.
        
        Args:
            model_string: The model string in 'provider:model-name' format
            
        Returns:
            The ModelConfig object for the model
            
        Raises:
            ValueError: If the provider is not enabled or the model is not found
        """
        # Import ModelConfig locally to avoid circular imports
        from ..llms.base import ModelConfig
        # Parse the provider and model name
        provider, model_name = self._parse_model_string(model_string)
        
        # Check if the provider is enabled
        self.check_provider_enabled(provider)
        
        # Get model details from the registry
        from ..llms.llm_registry import LLMRegistry
        registry = LLMRegistry()
        return registry.get_model_details(provider, model_name)
        
    def check_provider_enabled(self, provider_name: str) -> None:
        """
        Check if a provider is enabled in the configuration.
        
        Args:
            provider_name: The name of the provider
            
        Raises:
            ValueError: If the provider is not enabled
        """
        if not self.is_provider_enabled(provider_name):
            raise ValueError(f"Provider '{provider_name}' is not enabled in the configuration.")
            
    def is_provider_enabled(self, provider_name: str) -> bool:
        """
        Check if a provider is enabled in the configuration.
        
        Args:
            provider_name: The name of the provider
            
        Returns:
            True if the provider is enabled, False otherwise
        """
        providers = self.get_providers()
        provider_config = providers.get(provider_name, {})
        return provider_config.get("enabled", False)

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
