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
        # If llm_models filter is provided, we might need to re-initialize
        # or ensure the cached instance is compatible. For simplicity now,
        # if a filter is provided and the instance is cached, we'll assume
        # the cached instance is sufficient or will handle filtering internally.
        # A more robust approach might involve caching based on provider+models.
        # For now, just return the cached instance.
        return _provider_instances[provider_name]
    
    # Create new provider instance, passing the llm_models filter
    provider = create_provider(provider_name, llm_models=llm_models)
    if provider:
        _provider_instances[provider_name] = provider
        return provider
    
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
