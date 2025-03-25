"""Factory for creating LLM provider instances"""

import logging
import os
import json
import importlib
import sys
from typing import Dict, Type, List, Optional, Any, Tuple
import inspect
import importlib.util

from .base import BaseLLM, ProviderConfig

# Configure logging
logger = logging.getLogger(__name__)

# Cache for provider implementations
_provider_classes: Dict[str, Type[BaseLLM]] = {}

# Cache for provider configurations
_provider_configs: Dict[str, ProviderConfig] = {}

# Cache for external provider mappings
_external_providers: Dict[str, Dict[str, str]] = {}

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
    
    try:
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
                    # Validate the provider implementation
                    if validate_provider_implementation(provider_class):
                        _provider_classes[provider_name] = provider_class
                        logger.info(f"Discovered valid provider class {provider_class.__name__} for {provider_name}")
                    else:
                        logger.warning(f"Provider class {provider_class.__name__} does not pass validation")
                else:
                    logger.warning(f"No provider class found for {provider_name}")
                    
            except (ImportError, AttributeError) as e:
                logger.error(f"Error loading provider module {provider_name}: {str(e)}")
        
        # For testing - allow direct class registration
        # This is handled in the RegisterProviderForTesting class context manager
        # that is used in tests to directly register provider classes without importing
        
    except FileNotFoundError as e:
        logger.warning(f"Error accessing provider directories: {str(e)}")
    
    return _provider_classes


class RegisterProviderForTesting:
    """Context manager for testing to register provider classes directly"""
    
    def __init__(self, provider_name: str, provider_class: Type[BaseLLM]):
        """Initialize with a provider name and class"""
        self.provider_name = provider_name
        self.provider_class = provider_class
        self.was_registered = False
    
    def __enter__(self):
        """Register the provider class when entering the context"""
        if validate_provider_implementation(self.provider_class):
            _provider_classes[self.provider_name] = self.provider_class
            self.was_registered = True
            logger.info(f"Registered test provider class {self.provider_class.__name__} as {self.provider_name}")
        else:
            logger.warning(f"Test provider class {self.provider_class.__name__} does not pass validation")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove the provider class when exiting the context"""
        if self.was_registered and self.provider_name in _provider_classes:
            del _provider_classes[self.provider_name]
            logger.info(f"Unregistered test provider class {self.provider_class.__name__}")


def register_provider_class(provider_name: str, provider_class: Type[BaseLLM]) -> bool:
    """Register a provider class directly (primarily for testing)
    
    Args:
        provider_name: Name to register the provider as
        provider_class: Provider class to register
        
    Returns:
        True if registration succeeded, False otherwise
    """
    if validate_provider_implementation(provider_class):
        _provider_classes[provider_name] = provider_class
        logger.info(f"Registered provider class {provider_class.__name__} as {provider_name}")
        return True
    else:
        logger.warning(f"Provider class {provider_class.__name__} does not pass validation")
        return False

def validate_provider_implementation(provider_class: Type) -> bool:
    """Validate that a provider class implements the required interface
    
    Args:
        provider_class: The provider class to validate
        
    Returns:
        True if the class is a valid provider, False otherwise
    """
    logger.debug(f"Validating provider class: {provider_class.__name__}")
    
    # Check that the class inherits from BaseLLM
    if not issubclass(provider_class, BaseLLM):
        logger.warning(f"Provider class {provider_class.__name__} does not inherit from BaseLLM")
        return False
    
    # Check that the class implements _call_llm_api
    if not hasattr(provider_class, '_call_llm_api'):
        logger.warning(f"Provider class {provider_class.__name__} does not implement _call_llm_api")
        return False
    
    # Check that _call_llm_api has the correct signature
    call_sig = inspect.signature(provider_class._call_llm_api)
    required_params = ['self', 'prompt', 'system_prompt', 'model_name', 'model_config']
    for param in required_params:
        if param not in call_sig.parameters:
            logger.warning(f"Provider class {provider_class.__name__} _call_llm_api method is missing required parameter: {param}")
            return False
    
    logger.debug(f"Provider class {provider_class.__name__} is valid")
    return True


def create_provider(provider_name: str) -> Optional[BaseLLM]:
    """Create a provider instance by name
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Provider instance or None if not found
    """
    logger.info(f"Creating provider instance for {provider_name}")
    
    # Check if this is an external provider
    if provider_name in _external_providers:
        logger.info(f"Provider {provider_name} is an external provider")
        try:
            return _create_external_provider(provider_name)
        except Exception as e:
            logger.error(f"Error creating external provider {provider_name}: {str(e)}")
            return None
    
    # Discover provider classes if needed
    provider_classes = discover_provider_classes()
    
    # Check if provider exists
    if provider_name not in provider_classes:
        logger.warning(f"Provider {provider_name} not found")
        return None
    
    # Get provider class
    provider_class = provider_classes[provider_name]
    
    # Validate provider implementation
    if not validate_provider_implementation(provider_class):
        logger.error(f"Provider {provider_name} has an invalid implementation")
        return None
    
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

def _create_external_provider(provider_name: str) -> Optional[BaseLLM]:
    """Create a provider instance from an external module
    
    Args:
        provider_name: Name of the external provider
        
    Returns:
        Provider instance or None if not found
    """
    if provider_name not in _external_providers:
        logger.warning(f"External provider {provider_name} not found")
        return None
    
    provider_info = _external_providers[provider_name]
    module_name = provider_info.get('module')
    class_name = provider_info.get('class')
    
    if not module_name or not class_name:
        logger.warning(f"Invalid configuration for external provider {provider_name}")
        return None
    
    logger.info(f"Importing external provider {provider_name} from module {module_name}")
    
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Get the provider class
        provider_class = getattr(module, class_name)
        
        # Validate the provider implementation
        if not validate_provider_implementation(provider_class):
            logger.error(f"External provider {provider_name} has an invalid implementation")
            return None
        
        # Load provider config if available
        config_path = provider_info.get('config_path')
        config = None
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    config = ProviderConfig(**config_data)
            except Exception as e:
                logger.warning(f"Error loading config for external provider {provider_name}: {str(e)}")
        
        # Create instance
        provider = provider_class(config)
        logger.info(f"Created external provider instance for {provider_name}")
        return provider
    except Exception as e:
        logger.error(f"Error creating external provider {provider_name}: {str(e)}")
        return None


def load_external_providers() -> Dict[str, Dict[str, str]]:
    """Load external provider configurations from external_providers.json
    
    Returns:
        Dictionary mapping provider names to their module and class names
    """
    # Check for the external providers file
    external_providers_path = os.path.join(os.path.dirname(__file__), '..', '..', 'external_providers.json')
    if not os.path.exists(external_providers_path):
        logger.debug("No external_providers.json file found")
        return {}
    
    try:
        with open(external_providers_path, 'r') as f:
            providers = json.load(f)
            logger.info(f"Loaded {len(providers)} external providers from {external_providers_path}")
            return providers
    except Exception as e:
        logger.error(f"Error loading external providers: {str(e)}")
        return {}


def register_external_provider(provider_name: str, module_name: str, class_name: str, 
                               config_path: Optional[str] = None) -> bool:
    """Register an external provider
    
    Args:
        provider_name: Name to use for the provider
        module_name: Name of the module containing the provider
        class_name: Name of the provider class
        config_path: Optional path to the provider config file
        
    Returns:
        True if the provider was registered successfully, False otherwise
    """
    logger.info(f"Registering external provider {provider_name} from {module_name}.{class_name}")
    
    # Store the provider info in the cache
    _external_providers[provider_name] = {
        'module': module_name,
        'class': class_name
    }
    
    if config_path:
        _external_providers[provider_name]['config_path'] = config_path
    
    # Try to update the external_providers.json file
    try:
        # Get existing external providers
        external_providers = load_external_providers()
        
        # Add/update this provider
        external_providers[provider_name] = _external_providers[provider_name]
        
        # Save the updated file
        external_providers_path = os.path.join(os.path.dirname(__file__), '..', '..', 'external_providers.json')
        with open(external_providers_path, 'w') as f:
            json.dump(external_providers, f, indent=2)
            
        logger.info(f"Updated external_providers.json with provider {provider_name}")
        return True
    except Exception as e:
        logger.error(f"Error saving external provider {provider_name}: {str(e)}")
        # It's still registered in memory, so we return True
        return True


def get_available_providers() -> List[str]:
    """Get a list of all available provider names
    
    Returns:
        List of provider names
    """
    # Discover provider classes
    provider_classes = discover_provider_classes()
    
    # Load external providers
    external_providers = load_external_providers()
    
    # Update the cache
    _external_providers.update(external_providers)
    
    # Combine both types of providers
    providers = list(provider_classes.keys())
    providers.extend(list(external_providers.keys()))
    
    return providers