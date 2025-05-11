"""Registry for LLM providers"""

import logging
from typing import Dict, Type, List, Optional, Any
import os
import importlib
import inspect

from .base import BaseLLM
from .provider_factory import create_provider, get_available_providers

# Configure logging
logger = logging.getLogger(__name__)


# Global cache for provider instances
_provider_instances: Dict[str, BaseLLM] = {}


def get_llm_provider(provider_name: str, llm_models: Optional[List[str]] = None) -> Optional[BaseLLM]:
    """
    Get an LLM provider instance by name, creating it if needed.
    
    Args:
        provider_name: The name of the provider
        llm_models: Optional list of specific LLM model names to test
        
    Returns:
        The provider instance or None if not found/created
    """
    # Check cache first
    if provider_name in _provider_instances:
        cached_instance = _provider_instances[provider_name]
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
    provider = create_provider(provider_name, llm_models=llm_models)
    if provider:
        # Cache the new instance (or updated instance)
        _provider_instances[provider_name] = provider
        logger.debug(f"Cached new/updated instance for {provider_name} with llm_models_filter: {tuple(sorted(llm_models)) if llm_models is not None else None}")
        return provider
    
    logger.warning(f"Failed to create provider {provider_name}.")
    return None


def discover_providers() -> List[str]:
    """
    Discover all available LLM providers from config directories.
    
    Returns:
        List of discovered provider names
    """
    return get_available_providers()


def reset_provider_cache() -> None:
    """
    Reset the provider instance cache.
    Useful for testing or when you need to reload configurations.
    """
    global _provider_instances
    _provider_instances = {}
    logger.info("Provider cache has been reset")


def get_provider_info(provider_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a provider.
    
    Args:
        provider_name: The name of the provider
        
    Returns:
        Dictionary with provider information
    """
    provider = get_llm_provider(provider_name)
    if not provider:
        return {"name": provider_name, "available": False}
    
    # Get basic provider info
    info = {
        "name": provider_name,
        "available": True,
        "config": None,
        "py_models": []
    }
    
    # Add configuration details if available
    if provider.config:
        info["config"] = {
            "provider_type": provider.config.provider_type,
            "env_key": provider.config.env_key,
        }
        
        # Add model information
        info["py_models"] = [
            {
                "name": model.name,
                "default": model.default,
                "preferred": model.preferred,
                "cost_category": model.cost_category
            }
            for model in provider.config.llm_models
        ]
        
    return info
