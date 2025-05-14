"""
Factory for creating Prompt Provider instances.
"""

import importlib
import logging
import os
from typing import Any, Dict, Optional, Type

from .base import BasePromptProvider

logger = logging.getLogger(__name__)


def create_prompt_provider(provider_type: str, config: Optional[Dict[str, Any]] = None) -> Optional[BasePromptProvider]:
    """
    Create a prompt provider instance by type.
    
    Args:
        provider_type: Type of provider (e.g. "file", "database", "api")
        config: Optional configuration dictionary
        
    Returns:
        A BasePromptProvider instance or None if creation failed
    """
    try:
        # Import the provider module
        module_path = f"pydantic_llm_tester.prompt_providers.{provider_type}"
        try:
            provider_module = importlib.import_module(module_path)
        except ImportError as e:
            logger.error(f"Error importing prompt provider module '{module_path}': {e}")
            return None
        
        # Find the provider class
        provider_class = _find_provider_class(provider_module)
        if not provider_class:
            logger.error(f"No prompt provider class found in module '{module_path}'")
            return None
        
        # Create and return the provider instance
        return provider_class(config)
    
    except Exception as e:
        logger.error(f"Error creating prompt provider of type '{provider_type}': {e}")
        return None


def _find_provider_class(module: Any) -> Optional[Type[BasePromptProvider]]:
    """
    Find the provider class in a module.
    
    Args:
        module: The imported module
        
    Returns:
        The provider class or None if not found
    """
    # Try to find a class that ends with 'PromptProvider'
    for attr_name in dir(module):
        if attr_name.endswith('PromptProvider'):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BasePromptProvider) and attr != BasePromptProvider:
                return attr
    
    return None


def load_provider_config(provider_type: str) -> Optional[Dict[str, Any]]:
    """
    Load configuration for a prompt provider.
    
    Args:
        provider_type: Type of provider (e.g. "file", "database", "api")
        
    Returns:
        Configuration dictionary or None if loading failed
    """
    try:
        import json
        
        # Construct the path to the config file
        config_path = os.path.join(
            os.path.dirname(__file__),
            provider_type,
            'config.json'
        )
        
        # Check if the file exists
        if not os.path.exists(config_path):
            logger.warning(f"No config file found for prompt provider '{provider_type}' at '{config_path}'")
            return {}
        
        # Load and return the config
        with open(config_path, 'r') as f:
            return json.load(f)
    
    except Exception as e:
        logger.error(f"Error loading config for prompt provider '{provider_type}': {e}")
        return None