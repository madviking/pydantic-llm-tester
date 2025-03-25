"""Factory for creating LLM provider instances"""

import logging
import os
import json
import importlib
from typing import Dict, Type, List, Optional, Any
import inspect

from .base import BaseLLM, ProviderConfig

# Configure logging
logger = logging.getLogger(__name__)

# Cache for provider implementations
_provider_classes: Dict[str, Type[BaseLLM]] = {}

# Cache for provider configurations
_provider_configs: Dict[str, ProviderConfig] = {}

def load_provider_config(provider_name: str) -> Optional[ProviderConfig]:
    """Load provider configuration from a JSON file
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        ProviderConfig object or None if not found
    """
    # Check if already loaded
    if provider_name in _provider_configs:
        return _provider_configs[provider_name]
    
    # Look for config file in the provider's directory
    config_path = os.path.join(os.path.dirname(__file__), provider_name, 'config.json')
    if not os.path.exists(config_path):
        logger.warning(f"No config file found for provider {provider_name}")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            
        # Parse config using Pydantic
        config = ProviderConfig(**config_data)
        _provider_configs[provider_name] = config
        return config
    except Exception as e:
        logger.error(f"Error loading config for provider {provider_name}: {str(e)}")
        return None

def discover_provider_classes() -> Dict[str, Type[BaseLLM]]:
    """Discover all provider classes in the llms directory
    
    Returns:
        Dictionary mapping provider names to provider classes
    """
    # Return cached result if already discovered
    if _provider_classes:
        return _provider_classes
    
    # Get all subdirectories in the llms directory
    current_dir = os.path.dirname(__file__)
    provider_dirs = []
    
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        if os.path.isdir(item_path) and not item.startswith('__'):
            # Check if this looks like a provider directory
            if os.path.exists(os.path.join(item_path, '__init__.py')):
                provider_dirs.append(item)
    
    logger.debug(f"Found potential provider directories: {', '.join(provider_dirs)}")
    
    # Import each provider module and find provider classes
    for provider_name in provider_dirs:
        try:
            # Import the provider package
            module_name = f"llm_tester.llms.{provider_name}"
            provider_module = importlib.import_module(module_name)
            
            # Look for a class named <Provider>Provider or matching name pattern
            provider_class = None
            
            # Try to find specifically exported classes
            if hasattr(provider_module, '__all__'):
                for class_name in provider_module.__all__:
                    if class_name.endswith('Provider'):
                        class_obj = getattr(provider_module, class_name, None)
                        if class_obj and inspect.isclass(class_obj) and issubclass(class_obj, BaseLLM):
                            provider_class = class_obj
                            break
            
            # If not found, search all members
            if not provider_class:
                for name, obj in inspect.getmembers(provider_module):
                    if inspect.isclass(obj) and issubclass(obj, BaseLLM) and obj != BaseLLM:
                        # Prefer classes ending with Provider
                        if name.endswith('Provider'):
                            provider_class = obj
                            break
            
            if provider_class:
                _provider_classes[provider_name] = provider_class
                logger.info(f"Discovered provider class {provider_class.__name__} for {provider_name}")
            else:
                logger.warning(f"No provider class found for {provider_name}")
                
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading provider module {provider_name}: {str(e)}")
    
    return _provider_classes

def create_provider(provider_name: str) -> Optional[BaseLLM]:
    """Create a provider instance by name
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Provider instance or None if not found
    """
    # Discover provider classes if needed
    provider_classes = discover_provider_classes()
    
    # Check if provider exists
    if provider_name not in provider_classes:
        logger.warning(f"Provider {provider_name} not found")
        return None
    
    # Get provider class
    provider_class = provider_classes[provider_name]
    
    # Load config for provider
    config = load_provider_config(provider_name)
    
    # Create instance
    try:
        provider = provider_class(config)
        logger.info(f"Created provider instance for {provider_name}")
        return provider
    except Exception as e:
        logger.error(f"Error creating provider instance for {provider_name}: {str(e)}")
        return None

def get_available_providers() -> List[str]:
    """Get a list of all available provider names
    
    Returns:
        List of provider names
    """
    # Discover provider classes
    provider_classes = discover_provider_classes()
    return list(provider_classes.keys())