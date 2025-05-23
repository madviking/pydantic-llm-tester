"""Registry for LLM providers"""

import logging
from typing import Dict, Type, List, Optional, Any
import os
import importlib
import logging
from typing import Dict, Type, List, Optional, Any
import os
import importlib
import logging
from typing import Dict, Type, List, Optional, Any
import os
import importlib
import logging
from typing import Dict, Type, List, Optional, Any
import os
import importlib
import logging
from typing import Dict, Type, List, Optional, Any
import os
import importlib
import inspect
import time # Import time module
from unittest.mock import MagicMock # Import MagicMock for mocking

from .base import BaseLLM, ModelConfig # Import ModelConfig instead of LLMDetails

# Configure logging
logger = logging.getLogger(__name__)

# Temporary workaround for circular import during test collection
# This should be addressed with a proper architectural refactor later.
try:
    from .provider_factory import get_available_providers, create_provider # Import create_provider here too
except ImportError:
    # Provide mock implementations for test collection if circular import occurs.
    # This allows test collection to proceed by making the names available.
    import logging
    logging.getLogger(__name__).warning("Circular import detected during module import, providing mock provider factory functions.")
    def get_available_providers():
        return ["mock"] # Return a default mock provider for test collection
    def create_provider(provider_name, llm_models=None):
        # Return a mock provider instance
        mock_provider = MagicMock()
        mock_provider.name = provider_name
        mock_provider.llm_models_filter = llm_models
        return mock_provider


class LLMRegistry:
    """
    Registry for LLM providers and their model details.

    Manages provider instances and caches model configuration data.
    """
    _instance: Optional["LLMRegistry"] = None
    _provider_instances: Dict[str, BaseLLM] = {}
    _model_data: Dict[str, Dict[str, ModelConfig]] = {} # Use ModelConfig
    _cache_timestamps: Dict[str, float] = {} # New: Stores cache timestamps

    # Define a default cache expiry time (e.g., 1 hour)
    DEFAULT_CACHE_EXPIRY_SECONDS = 3600

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(LLMRegistry, cls).__new__(cls)
            # Initialize instance-specific attributes here if needed
        return cls._instance

    def get_llm_provider(self, provider_name: str, llm_models: Optional[List[str]] = None) -> Optional[BaseLLM]:
        """
        Get an LLM provider instance by name, creating it if needed.

        Args:
            provider_name: The name of the provider
            llm_models: Optional list of specific LLM model names to test

        Returns:
            The provider instance or None if not found/created
        """
        # Check cache first
        if provider_name in self._provider_instances:
            cached_instance = self._provider_instances[provider_name]
            # Access the filter the cached instance was initialized with
            # Ensure 'llm_models_filter' attribute exists, default to None if not (though it should exist via BaseLLM)
            cached_filter = getattr(cached_instance, 'llm_models_filter', None)

            # Normalize current and cached filters for comparison.
            # Sorting ensures that the order of model names in the list doesn't affect cache matching.
            current_filter_tuple = tuple(sorted(llm_models)) if llm_models is not None else None
            cached_filter_tuple = tuple(sorted(cached_filter)) if cached_filter is not None else None

            if current_filter_tuple == cached_filter_tuple:
                logger.debug(f"Returning cached instance of {provider_name} with matching llm_models_filter: {current_filter_tuple}")
                return cached_instance
            else:
                logger.info(f"Recreating instance for {provider_name} due to different llm_models_filter. "
                            f"Requested: {current_filter_tuple}, Cached instance had: {cached_filter_tuple}")
                # Proceed to create a new instance, which will replace the one in cache.

        # Create new provider instance, passing the llm_models filter
        # Note: create_provider might need access to the model registry later
        # For now, it still relies on provider config.json, which will be refactored later.
        provider = create_provider(provider_name, llm_models=llm_models)
        if provider:
            # Cache the new instance (or updated instance)
            self._provider_instances[provider_name] = provider
            logger.debug(f"Cached new/updated instance for {provider_name} with llm_models_filter: {tuple(sorted(llm_models)) if llm_models is not None else None}")
            return provider

        logger.warning(f"Failed to create provider {provider_name}.")
        return None

    def discover_providers(self) -> List[str]:
        """
        Discover all available LLM providers from config directories.

        Returns:
            List of discovered provider names
        """
        """
        Discover all available LLM providers from config directories.

        Returns:
            List of discovered provider names
        """
        try:
            # Import locally to avoid circular dependency
            from .provider_factory import get_available_providers
            return get_available_providers()
        except ImportError:
            # Provide a mock implementation for test collection if circular import occurs
            import logging
            logging.getLogger(__name__).warning("Circular import detected during discover_providers, returning mock providers.")
            return ["mock"] # Return a default mock provider for test collection

    def reset_provider_cache(self) -> None:
        """
        Reset the provider instance cache.
        Useful for testing or when you need to reload configurations.
        """
        self._provider_instances = {}
        logger.info("Provider instance cache has been reset")

    def store_provider_models(self, provider_name: str, models: Dict[str, ModelConfig]) -> None:
        """
        Stores model details for a specific provider.

        Args:
            provider_name: The name of the provider.
            models: A dictionary mapping model names to ModelConfig objects.
        """
        self._model_data[provider_name] = models
        self._cache_timestamps[provider_name] = time.time() # Record timestamp
        logger.debug(f"Stored model data for provider: {provider_name} with timestamp {self._cache_timestamps[provider_name]}")

    def _is_cache_fresh(self, provider_name: str, expiry_seconds: int) -> bool:
        """
        Checks if the cached data for a provider is still fresh.

        Args:
            provider_name: The name of the provider.
            expiry_seconds: The cache expiry time in seconds.

        Returns:
            True if the cache is fresh, False otherwise.
        """
        if provider_name not in self._cache_timestamps:
            return False # No cache exists

        time_since_cached = time.time() - self._cache_timestamps[provider_name]
        return time_since_cached < expiry_seconds

    def get_provider_models(self, provider_name: str, use_cache: bool = True, expiry_seconds: int = DEFAULT_CACHE_EXPIRY_SECONDS) -> Dict[str, ModelConfig]:
        """
        Retrieves all stored model details for a specific provider.

        Args:
            provider_name: The name of the provider.
            use_cache: Whether to use the cache if fresh.
            expiry_seconds: The cache expiry time in seconds if use_cache is True.

        Returns:
            A dictionary mapping model names to ModelConfig objects, or an empty dictionary
            if the provider is not found.

        Raises:
            ValueError: If the provider is not found in the registry and cache is not used or expired.
        """
        if use_cache and self._is_cache_fresh(provider_name, expiry_seconds):
            logger.debug(f"Returning cached model data for provider: {provider_name}")
            return self._model_data.get(provider_name, {}) # Return empty dict if provider somehow has no models but is in timestamps

        # If cache is not used or expired, check if data exists.
        # If not found, return an empty dictionary instead of raising an error,
        # allowing get_provider_info's fallback logic to handle it.
        if provider_name not in self._model_data:
            logger.debug(f"Provider '{provider_name}' not found in _model_data. Returning empty dict.")
            return {}

        return self._model_data[provider_name]

    def get_model_details(self, provider_name: str, model_name: str, use_cache: bool = True, expiry_seconds: int = DEFAULT_CACHE_EXPIRY_SECONDS) -> ModelConfig:
        """
        Retrieves details for a specific model of a given provider.

        Args:
            provider_name: The name of the provider.
            model_name: The name of the model.
            use_cache: Whether to use the cache if fresh.
            expiry_seconds: The cache expiry time in seconds if use_cache is True.

        Returns:
            The ModelConfig object for the model.

        Raises:
            ValueError: If the provider or model is not found, or cache expired.
        """
        # Use get_provider_models to handle cache check and provider existence
        provider_models = self.get_provider_models(provider_name, use_cache=use_cache, expiry_seconds=expiry_seconds)

        if model_name not in provider_models:
            raise ValueError(f"Model '{model_name}' not found for provider '{provider_name}'.")

        return provider_models[model_name]

    def get_all_model_details(self, use_cache: bool = True, expiry_seconds: int = DEFAULT_CACHE_EXPIRY_SECONDS, 
                           only_configured: bool = False) -> List[ModelConfig]:
        """
        Retrieves details for all models from all providers.
        
        Args:
            use_cache: Whether to use the cache if fresh.
            expiry_seconds: The cache expiry time in seconds if use_cache is True.
            only_configured: If True, return only models configured in pyllm_config.json.
            
        Returns:
            A list of ModelConfig objects for enabled models.
        """
        all_models = []
        
        # Get all provider names from the model data cache
        provider_names = list(self._model_data.keys())
        logger.debug(f"Found {len(provider_names)} providers in registry: {', '.join(provider_names)}")
        
        # Get configured model IDs if needed
        configured_model_ids = None
        if only_configured:
            from pydantic_llm_tester.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            configured_model_ids = set(config_manager.get_configured_models())
            logger.debug(f"Filtering to {len(configured_model_ids)} configured models: {', '.join(configured_model_ids)}")
        
        # Iterate through all providers
        for provider_name in provider_names:
            try:
                # Get models for this provider
                provider_models = self.get_provider_models(provider_name, use_cache=use_cache, expiry_seconds=expiry_seconds)
                
                # Add enabled models to the result list (filtering by configuration if needed)
                models_added = 0
                for model_name, model_config in provider_models.items():
                    # Skip disabled models
                    if not model_config.enabled:
                        continue
                    
                    # Apply configuration filter if needed
                    if only_configured:
                        # Check if this model is in the configured list
                        model_id = f"{provider_name}:{model_name}"
                        if model_id not in configured_model_ids:
                            continue
                    
                    # Add the model to the result list
                    all_models.append(model_config)
                    models_added += 1
                        
                logger.debug(f"Added {models_added} models from provider {provider_name}")
            except Exception as e:
                logger.warning(f"Error retrieving models for provider {provider_name}: {str(e)}")
                
        filter_desc = " configured" if only_configured else " enabled"
        logger.info(f"Retrieved {len(all_models)}{filter_desc} models from all providers")
        return all_models

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a provider, including its models from the registry.

        Args:
            provider_name: The name of the provider

        Returns:
            Dictionary with provider information
        """
        # First, check if we have model data stored for this provider
        models_data = self.get_provider_models(provider_name)

        # If model data is available, use it to construct the info
        if models_data:
             # Attempt to get a provider instance to get config details if needed,
             # but don't fail if instance creation fails.
            provider_instance = self.get_llm_provider(provider_name)
            config_info = None
            if provider_instance and provider_instance.config:
                 config_info = {
                    "provider_type": provider_instance.config.provider_type,
                    "env_key": provider_instance.config.env_key,
                 }

            info = {
                "name": provider_name,
                "available": True, # Assume available if we have model data
                "config": config_info,
                "llm_models": [
                    {
                        "name": model.name,
                        "default": model.default,
                        "preferred": model.preferred,
                        "cost_input": model.cost_input, # Include cost details from ModelConfig
                        "cost_output": model.cost_output,
                        "cost_category": model.cost_category, # Include cost_category
                        "max_input_tokens": model.max_input_tokens, # Include token limits
                        "max_output_tokens": model.max_output_tokens,
                        "enabled": model.enabled, # Include enabled status
                        "provider": provider_name # Use the provider_name argument
                    }
                    for model in models_data.values()
                ]
            }
            return info
        else:
            # If no model data is stored (get_provider_models returned {}),
            # the provider is considered unavailable for detailed info.
            return {"name": provider_name, "available": False}

# Replace global functions with methods on the singleton instance
# This requires updating any code that uses these global functions
# For now, keep the global functions as wrappers for backward compatibility
# but ideally, code should be updated to use LLMRegistry().method_name
def get_llm_provider(provider_name: str, llm_models: Optional[List[str]] = None) -> Optional[BaseLLM]:
    return LLMRegistry().get_llm_provider(provider_name, llm_models)

def discover_providers() -> List[str]:
    return LLMRegistry().discover_providers()

def reset_provider_cache() -> None:
    LLMRegistry().reset_provider_cache()

def get_provider_info(provider_name: str) -> Dict[str, Any]:
    return LLMRegistry().get_provider_info(provider_name)

# Add global accessors for the new model data methods for now
def store_provider_models(provider_name: str, models: Dict[str, ModelConfig]) -> None:
    LLMRegistry().store_provider_models(provider_name, models)

def get_provider_models(provider_name: str, use_cache: bool = True, expiry_seconds: int = LLMRegistry.DEFAULT_CACHE_EXPIRY_SECONDS) -> Dict[str, ModelConfig]:
    return LLMRegistry().get_provider_models(provider_name, use_cache=use_cache, expiry_seconds=expiry_seconds)

def get_model_details(provider_name: str, model_name: str, use_cache: bool = True, expiry_seconds: int = LLMRegistry.DEFAULT_CACHE_EXPIRY_SECONDS) -> ModelConfig:
    return LLMRegistry().get_model_details(provider_name, model_name, use_cache=use_cache, expiry_seconds=expiry_seconds)
    
def get_all_model_details(use_cache: bool = True, expiry_seconds: int = LLMRegistry.DEFAULT_CACHE_EXPIRY_SECONDS, 
                     only_configured: bool = False) -> List[ModelConfig]:
    return LLMRegistry().get_all_model_details(use_cache=use_cache, expiry_seconds=expiry_seconds, 
                                            only_configured=only_configured)
