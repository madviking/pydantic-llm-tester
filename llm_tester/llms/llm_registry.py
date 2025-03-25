"""Registry for LLM providers"""

import logging
from typing import Dict, Type, List, Optional
import os
import importlib

from .base import BaseLLM
from .provider_factory import create_provider, get_available_providers

# Configure logging
logger = logging.getLogger(__name__)


# Global cache for provider instances
_provider_instances: Dict[str, BaseLLM] = {}


def get_llm_provider(provider_name: str) -> Optional[BaseLLM]:
    """
    Get an LLM provider instance by name, creating it if needed.
    
    Args:
        provider_name: The name of the provider
        
    Returns:
        The provider instance or None if not found/created
    """
    # Check cache first
    if provider_name in _provider_instances:
        return _provider_instances[provider_name]
    
    # Create new provider instance
    provider = create_provider(provider_name)
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