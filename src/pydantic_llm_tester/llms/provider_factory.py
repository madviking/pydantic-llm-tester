"""Factory for creating LLM provider instances"""

import logging
import os
import json
import importlib
import sys
from typing import Dict, Type, List, Optional, Any, Tuple
import inspect
import importlib.util
import time
import requests # Added

from .base import BaseLLM, ProviderConfig, ModelConfig # Added ModelConfig

# Configure logging
logger = logging.getLogger(__name__)

# --- Constants ---
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
CACHE_DURATION_SECONDS = 3600 * 6 # Cache API response for 6 hours

# --- Constants ---
ENABLED_PROVIDERS_FILENAME = "enabled_providers.json" # In project root

# --- Caches ---
# Cache for provider implementations
_provider_classes: Dict[str, Type[BaseLLM]] = {}

# Cache for provider configurations
_provider_configs: Dict[str, ProviderConfig] = {}

# Cache for external provider mappings
_external_providers: Dict[str, Dict[str, str]] = {}

# Cache for OpenRouter API data
_openrouter_api_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": 0
}

# Reset caches (for development/testing - remove in production)
def reset_caches():
    """Reset all provider caches to force rediscovery"""
    global _provider_classes, _provider_configs, _external_providers
    """Reset all provider caches to force rediscovery"""
    global _provider_classes, _provider_configs, _external_providers, _openrouter_api_cache
    _provider_classes = {}
    _provider_configs = {}
    _external_providers = {}
    # Also reset OpenRouter cache if needed, or handle separately
    _openrouter_api_cache = {"data": None, "timestamp": 0}

def load_provider_config(provider_name: str) -> Optional[ProviderConfig]:
    """Load provider configuration from a JSON file
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        ProviderConfig object or None if not found
    """
    # Check cache first (covers both static and dynamically loaded)
    if provider_name in _provider_configs:
        # Check if OpenRouter cache needs refresh (if applicable)
        if provider_name == "openrouter" and _is_cache_stale():
             logger.info("OpenRouter cache is stale, attempting refresh.")
             # Proceed to load and potentially refresh below
        else:
            # Return cached config if not OpenRouter or if cache is fresh
            return _provider_configs[provider_name]

    # Load static config first
    config_path = os.path.join(os.path.dirname(__file__), provider_name, 'config.json')
    if not os.path.exists(config_path):
        logger.warning(f"No config file found for provider {provider_name}")
        return None

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        static_config = ProviderConfig(**config_data)
    except Exception as e:
        logger.error(f"Error loading static config for provider {provider_name}: {str(e)}")
        return None

    # --- Dynamic Loading for OpenRouter ---
    if provider_name == "openrouter":
        logger.info("Attempting to dynamically load OpenRouter py_models...")
        api_models_data = _fetch_openrouter_models_with_cache()

        if api_models_data:
            try:
                updated_models = _merge_static_and_api_models(static_config.llm_models, api_models_data)
                static_config.llm_models = updated_models # Replace py_models in the config object
                logger.info(f"Successfully updated OpenRouter config with {len(updated_models)} py_models from API.")
            except Exception as e:
                logger.error(f"Error processing OpenRouter API data: {e}. Falling back to static config.")
                # Fallback handled by returning static_config below
        else:
            logger.warning("Failed to fetch OpenRouter py_models from API. Using static config only.")
            # Fallback handled by returning static_config below

    # Store the final config (static or updated) in the cache and return
    _provider_configs[provider_name] = static_config
    return static_config


# --- Helper Functions for OpenRouter Dynamic Loading ---

def _is_cache_stale() -> bool:
    """Check if the OpenRouter API cache is stale."""
    return (time.time() - _openrouter_api_cache.get("timestamp", 0)) > CACHE_DURATION_SECONDS

def _fetch_openrouter_models_with_cache() -> Optional[List[Dict[str, Any]]]:
    """Fetch OpenRouter py_models from API, using cache."""
    global _openrouter_api_cache

    if not _is_cache_stale() and _openrouter_api_cache.get("data"):
        logger.info("Using cached OpenRouter py_models data.")
        return _openrouter_api_cache["data"]

    logger.info(f"Fetching py_models from OpenRouter API: {OPENROUTER_API_URL}")
    try:
        # Add headers to mimic browser request, as requested by OpenRouter API docs
        headers = {
            'User-Agent': 'llm-tester (https://github.com/your-repo/llm-tester)', # Replace with actual repo URL if available
            'Referer': 'https://your-app-domain.com' # Replace with actual domain if applicable
        }
        response = requests.get(OPENROUTER_API_URL, timeout=15, headers=headers)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "data" not in data or not isinstance(data["data"], list):
             logger.error("Invalid format received from OpenRouter API.")
             return None

        _openrouter_api_cache = {
            "data": data["data"],
            "timestamp": time.time()
        }
        logger.info(f"Successfully fetched and cached {len(data['data'])} py_models from OpenRouter.")
        return data["data"]

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching OpenRouter py_models: {e}")
        # Optionally return stale cache data if available?
        # if _openrouter_api_cache.get("data"):
        #     logger.warning("Returning stale cache data due to API fetch error.")
        #     return _openrouter_api_cache["data"]
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response from OpenRouter API: {e}")
        return None


def _merge_static_and_api_models(
    static_models: List[ModelConfig],
    api_models_data: List[Dict[str, Any]]
) -> List[ModelConfig]:
    """Merges py_models from static config and OpenRouter API response."""
    static_models_dict = {model.name: model for model in static_models}
    final_models = []
    api_model_ids = set()

    for api_model in api_models_data:
        model_id = api_model.get("id")
        if not model_id:
            logger.debug("Skipping API model entry without an 'id'.")
            continue # Skip py_models without an ID

        api_model_ids.add(model_id)
        static_model_config = static_models_dict.get(model_id)

        try:
            # --- Pricing ---
            pricing = api_model.get("pricing", {})
            cost_input_str = pricing.get("prompt", "0.0")
            cost_output_str = pricing.get("completion", "0.0")
            # Convert cost per token to cost per 1M tokens
            cost_input = float(cost_input_str) * 1_000_000 if cost_input_str else 0.0
            cost_output = float(cost_output_str) * 1_000_000 if cost_output_str else 0.0

            # --- Token Limits ---
            context_length = api_model.get("context_length")
            # OpenRouter API often provides max_completion_tokens within top_provider details
            max_output_tokens_api = api_model.get("top_provider", {}).get("max_completion_tokens")

            # Determine max_output_tokens
            if max_output_tokens_api is not None:
                max_output_tokens = int(max_output_tokens_api)
            elif static_model_config and static_model_config.max_output_tokens:
                 max_output_tokens = static_model_config.max_output_tokens # Use static if API doesn't provide
            else:
                 # Fallback default if neither API nor static config provides it
                 max_output_tokens = min(4096, int(context_length) // 2) if context_length else 4096

            # Determine max_input_tokens
            if context_length is not None:
                 # Calculate based on context_length minus determined output tokens
                 max_input_tokens = int(context_length) - max_output_tokens
                 # Ensure it's positive and at least 1, fallback if calculation is weird
                 if max_input_tokens <= 0:
                     # Use context_length // 2, but ensure it's at least 1
                     fallback_input_tokens = max(1, int(context_length) // 2)
                     logger.warning(f"Calculated non-positive max_input_tokens for {model_id} (context: {context_length}, output: {max_output_tokens}). Using max(1, context_length // 2) = {fallback_input_tokens}.")
                     max_input_tokens = fallback_input_tokens
            elif static_model_config and static_model_config.max_input_tokens:
                 max_input_tokens = static_model_config.max_input_tokens # Use static if API doesn't provide context
            else:
                 max_input_tokens = 8192 # Fallback default if no info available

            # --- Flags (Default, Preferred, Enabled) ---
            # Prioritize static config for these flags, default to enabled=True if new
            default = static_model_config.default if static_model_config else False
            preferred = static_model_config.preferred if static_model_config else False
            enabled = static_model_config.enabled if static_model_config else True

            # --- Cost Category (Infer or use static) ---
            if static_model_config and static_model_config.cost_category:
                cost_category = static_model_config.cost_category
            elif cost_input == 0 and cost_output == 0:
                cost_category = "free"
            elif cost_input < 1.0 and cost_output < 2.0: # Simple heuristic
                cost_category = "cheap"
            elif cost_input > 10.0 or cost_output > 20.0: # Simple heuristic
                cost_category = "premium"
            else:
                cost_category = "standard" # Default category


            model_config = ModelConfig(
                name=model_id,
                default=default,
                preferred=preferred,
                enabled=enabled,
                cost_input=cost_input,
                cost_output=cost_output,
                cost_category=cost_category,
                max_input_tokens=max_input_tokens,
                max_output_tokens=max_output_tokens,
            )
            final_models.append(model_config)
            logger.debug(f"Processed model '{model_id}' from API.")

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning(f"Could not process model '{model_id}' from OpenRouter API: {e}. Skipping.")
            # If it was in static config, maybe add it back? For now, skip.

    # Add py_models from static config that were NOT in the API response
    # This preserves manually added py_models or py_models temporarily missing from API
    added_static_count = 0
    for static_model in static_models:
        if static_model.name not in api_model_ids:
            logger.warning(f"Model '{static_model.name}' found in static config but not in OpenRouter API response. Keeping static definition.")
            final_models.append(static_model)
            added_static_count += 1
    if added_static_count > 0:
        logger.info(f"Added {added_static_count} py_models defined only in static config.")

    # Sort py_models alphabetically by name for consistent ordering
    final_models.sort(key=lambda m: m.name)

    return final_models

# --- End Helper Functions ---


# --- Helper Function for Enabled Providers ---

def _load_enabled_providers() -> Optional[List[str]]:
    """Loads the list of enabled providers from enabled_providers.json in the project root."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    enabled_file_path = os.path.join(project_root, ENABLED_PROVIDERS_FILENAME)

    if not os.path.exists(enabled_file_path):
        logger.debug(f"'{ENABLED_PROVIDERS_FILENAME}' not found. All discovered providers are considered enabled.")
        return None # Indicate all enabled

    try:
        with open(enabled_file_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            logger.info(f"Loaded {len(data)} enabled providers from {enabled_file_path}")
            return data
        else:
            logger.warning(f"Invalid format in '{enabled_file_path}'. Expected a list of strings. Ignoring file.")
            return None # Treat invalid format as all enabled
    except json.JSONDecodeError:
        logger.warning(f"Error decoding JSON from '{enabled_file_path}'. Ignoring file.")
        return None # Treat invalid JSON as all enabled
    except Exception as e:
        logger.error(f"Error reading '{enabled_file_path}': {e}. Ignoring file.")
        return None # Treat other errors as all enabled

# --- End Enabled Providers Helper ---

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
                module_name = f"src.llms.{provider_name}"
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


def create_provider(provider_name: str, config: Optional[ProviderConfig] = None, llm_models: Optional[List[str]] = None) -> Optional[BaseLLM]:
    """Create a provider instance by name
    
    Args:
        provider_name: Name of the provider
        config: Optional ProviderConfig object to use instead of loading internally
        llm_models: Optional list of specific LLM model names to test
        
    Returns:
        Provider instance or None if not found
    """
    logger.info(f"Creating provider instance for {provider_name} with models filter: {llm_models}")
    
    # Check if this is an external provider
    if provider_name in _external_providers:
        logger.info(f"Provider {provider_name} is an external provider")
        try:
            # For external providers, we still rely on their internal config loading for now
            # If needed, we could extend _create_external_provider to accept config
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
    
    # Use provided config or load internally
    if config is None:
        config = load_provider_config(provider_name)
        
    if config is None:
        logger.error(f"Could not load or find config for provider {provider_name}")
        return None
    
    # Create instance
    try:
        # Pass the llm_models list to the provider class constructor
        provider = provider_class(config, llm_models=llm_models)
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
    
    # Combine internal and external provider names
    all_providers = sorted(list(set(list(provider_classes.keys()) + list(external_providers.keys()))))

    # Load the list of enabled providers
    enabled_providers_list = _load_enabled_providers()

    if enabled_providers_list is None:
        # If file doesn't exist or is invalid, return all discovered providers
        logger.debug("Returning all discovered providers as enabled list is not configured.")
        return all_providers
    else:
        # Filter the discovered providers based on the enabled list
        filtered_providers = [p for p in all_providers if p in enabled_providers_list]
        logger.debug(f"Returning filtered list of enabled providers: {', '.join(filtered_providers)}")
        return filtered_providers
