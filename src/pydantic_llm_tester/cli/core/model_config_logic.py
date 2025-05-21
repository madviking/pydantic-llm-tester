import logging
import os
from typing import Dict, Any, List, Optional, Tuple, Union

from pydantic import ValidationError

from pydantic_llm_tester.utils.common import (
    get_provider_config_path,
    read_json_file,
    write_json_file
)
from pydantic_llm_tester.llms.base import ModelConfig, ProviderConfig
from pydantic_llm_tester.llms.provider_factory import reset_caches

logger = logging.getLogger(__name__)

def get_provider_config(provider_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the configuration for a provider.
    
    Args:
        provider_name: The name of the provider.
        
    Returns:
        The provider configuration as a dictionary, or None if not found.
    """
    config_path = get_provider_config_path(provider_name)
    config_data = read_json_file(config_path)
    if not config_data:
        logger.error(f"Could not load configuration for provider '{provider_name}' from {config_path}.")
        return None
    
    return config_data

def validate_model_config(model_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a model configuration using the ModelConfig Pydantic model.
    
    Args:
        model_data: The model configuration data to validate.
        
    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        ModelConfig(**model_data)
        return True, "Model configuration is valid."
    except ValidationError as e:
        return False, f"Invalid model configuration: {str(e)}"

def add_model_to_provider(
    provider_name: str, 
    model_name: str,
    model_config: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Add a new model to a provider's configuration.
    
    Args:
        provider_name: The name of the provider.
        model_name: The name of the model to add.
        model_config: The model configuration data.
        
    Returns:
        Tuple of (success: bool, message: str).
    """
    # Get provider config
    config_path = get_provider_config_path(provider_name)
    config_data = read_json_file(config_path)
    if not config_data:
        return False, f"Could not load configuration for provider '{provider_name}' from {config_path}."
    
    # Ensure model_name is set in the config
    model_config["name"] = model_name
    
    # Validate model config
    is_valid, validation_message = validate_model_config(model_config)
    if not is_valid:
        return False, validation_message
    
    # Check if model already exists
    models = config_data.get("llm_models", [])
    for model in models:
        if model.get("name") == model_name:
            return False, f"Model '{model_name}' already exists for provider '{provider_name}'."
    
    # Add model to config
    models.append(model_config)
    config_data["llm_models"] = models
    
    # Write updated config
    if write_json_file(config_path, config_data):
        reset_caches()  # Clear factory cache so changes are reflected
        return True, f"Model '{model_name}' added to provider '{provider_name}' successfully."
    else:
        return False, f"Error writing updated configuration to {config_path}."

def edit_model_in_provider(
    provider_name: str, 
    model_name: str,
    updated_config: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Edit an existing model in a provider's configuration.
    
    Args:
        provider_name: The name of the provider.
        model_name: The name of the model to edit.
        updated_config: The updated model configuration data.
        
    Returns:
        Tuple of (success: bool, message: str).
    """
    # Get provider config
    config_path = get_provider_config_path(provider_name)
    config_data = read_json_file(config_path)
    if not config_data:
        return False, f"Could not load configuration for provider '{provider_name}' from {config_path}."
    
    # Ensure model_name is set in the config
    updated_config["name"] = model_name
    
    # Validate model config
    is_valid, validation_message = validate_model_config(updated_config)
    if not is_valid:
        return False, validation_message
    
    # Find and update model
    models = config_data.get("llm_models", [])
    model_found = False
    
    for i, model in enumerate(models):
        if model.get("name") == model_name:
            models[i] = updated_config
            model_found = True
            break
    
    if not model_found:
        return False, f"Model '{model_name}' not found in provider '{provider_name}'."
    
    config_data["llm_models"] = models
    
    # Write updated config
    if write_json_file(config_path, config_data):
        reset_caches()  # Clear factory cache so changes are reflected
        return True, f"Model '{model_name}' updated in provider '{provider_name}' successfully."
    else:
        return False, f"Error writing updated configuration to {config_path}."

def remove_model_from_provider(
    provider_name: str, 
    model_name: str
) -> Tuple[bool, str]:
    """
    Remove a model from a provider's configuration.
    
    Args:
        provider_name: The name of the provider.
        model_name: The name of the model to remove.
        
    Returns:
        Tuple of (success: bool, message: str).
    """
    # Get provider config
    config_path = get_provider_config_path(provider_name)
    config_data = read_json_file(config_path)
    if not config_data:
        return False, f"Could not load configuration for provider '{provider_name}' from {config_path}."
    
    # Find and remove model
    models = config_data.get("llm_models", [])
    original_count = len(models)
    
    models = [model for model in models if model.get("name") != model_name]
    
    if len(models) == original_count:
        return False, f"Model '{model_name}' not found in provider '{provider_name}'."
    
    config_data["llm_models"] = models
    
    # Write updated config
    if write_json_file(config_path, config_data):
        reset_caches()  # Clear factory cache so changes are reflected
        return True, f"Model '{model_name}' removed from provider '{provider_name}' successfully."
    else:
        return False, f"Error writing updated configuration to {config_path}."

def get_model_template() -> Dict[str, Any]:
    """
    Get a template for a new model configuration.
    
    Returns:
        A dictionary with default values for a new model.
    """
    return {
        "name": "",
        "default": False,
        "preferred": False,
        "enabled": True,
        "cost_input": 0.0,
        "cost_output": 0.0,
        "cost_category": "standard",
        "max_input_tokens": 4096,
        "max_output_tokens": 4096
    }

def get_model_from_provider(provider_name: str, model_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific model configuration from a provider.
    
    Args:
        provider_name: The name of the provider.
        model_name: The name of the model to get.
        
    Returns:
        The model configuration as a dictionary, or None if not found.
    """
    config_data = get_provider_config(provider_name)
    if not config_data:
        return None
    
    models = config_data.get("llm_models", [])
    for model in models:
        if model.get("name") == model_name:
            return model
    
    return None

def set_default_model(provider_name: str, model_name: str) -> Tuple[bool, str]:
    """
    Set a model as the default for a provider.
    
    Args:
        provider_name: The name of the provider.
        model_name: The name of the model to set as default.
        
    Returns:
        Tuple of (success: bool, message: str).
    """
    # Validate provider name
    if not provider_name:
        logger.error("Provider name cannot be empty")
        return False, "Provider name cannot be empty."
        
    # Get provider config
    config_path = get_provider_config_path(provider_name)
    if not os.path.exists(config_path):
        logger.error(f"Provider config file not found at {config_path}")
        return False, f"Provider '{provider_name}' not found. Config file does not exist at {config_path}."
        
    config_data = read_json_file(config_path)
    if not config_data:
        return False, f"Could not load configuration for provider '{provider_name}' from {config_path}."
    
    # Find model and update default status
    models = config_data.get("llm_models", [])
    model_found = False
    
    for model in models:
        if model.get("name") == model_name:
            model["default"] = True
            model_found = True
        else:
            model["default"] = False
    
    if not model_found:
        return False, f"Model '{model_name}' not found in provider '{provider_name}'."
    
    config_data["llm_models"] = models
    
    # Write updated config
    if write_json_file(config_path, config_data):
        reset_caches()  # Clear factory cache so changes are reflected
        return True, f"Model '{model_name}' set as default for provider '{provider_name}' successfully."
    else:
        return False, f"Error writing updated configuration to {config_path}."