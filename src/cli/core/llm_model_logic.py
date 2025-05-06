import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

# Use absolute imports for clarity within the package
from src.cli.core.common import (
    get_provider_config_path,
    read_json_file,
    write_json_file
)
# Import provider factory functions and helpers for updates
from src.llms.provider_factory import (
    reset_caches,
    _fetch_openrouter_models_with_cache,
    _merge_static_and_api_models,
    load_provider_config # To parse config into Pydantic py_models
)
from src.llms.base import ProviderConfig, ModelConfig # Import config py_models

logger = logging.getLogger(__name__)


def parse_full_model_id(model_id_arg: str, provider_arg: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses a potentially combined model ID (provider/model_name) or separate args.

    Args:
        model_id_arg: The model identifier string (e.g., "openrouter/google/gemini-pro" or "gpt-4o").
        provider_arg: Optional provider name specified separately.

    Returns:
        Tuple of (provider_name, model_name) or (None, None) if parsing fails.
    """
    if '/' in model_id_arg:
        # Assume format provider/model/name or provider/model_name
        # Split only on the first '/' to handle py_models with '/' in their name
        parts = model_id_arg.split('/', 1)
        provider = parts[0]
        model_name = parts[1]
        if provider_arg and provider_arg != provider:
             logger.warning(f"Provider mismatch: '{provider_arg}' from argument vs '{provider}' from model ID '{model_id_arg}'. Using provider from model ID.")
        return provider, model_name
    elif provider_arg:
        # Assume model_id_arg is just the model name if provider is given separately
        return provider_arg, model_id_arg
    else:
        # Cannot determine provider
        logger.error(f"Cannot determine provider for model '{model_id_arg}'. Use format 'provider/model_name' or specify --provider.")
        return None, None


def get_models_from_provider(provider_name: str) -> List[Dict[str, Any]]:
    """
    Reads the py_models list directly from a provider's config JSON file.

    Returns:
        List of model dictionaries, or an empty list on error.
    """
    config_path = get_provider_config_path(provider_name)
    config_data = read_json_file(config_path)
    if not config_data:
        logger.error(f"Could not load configuration for provider '{provider_name}' from {config_path}.")
        return []

    models = config_data.get('py_models', [])
    if not isinstance(models, list):
        logger.error(f"Invalid 'py_models' format in {config_path}. Expected a list.")
        return []

    # Sort by name for consistent listing
    models.sort(key=lambda m: m.get('name', ''))
    return models


def set_model_enabled_status(provider_name: str, model_name: str, enabled: bool) -> Tuple[bool, str]:
    """
    Sets the 'enabled' status for a specific model in its provider's config file.

    Args:
        provider_name: The provider whose config to modify.
        model_name: The name of the model to modify.
        enabled: The desired enabled status (True or False).

    Returns:
        Tuple of (success: bool, message: str).
    """
    config_path = get_provider_config_path(provider_name)
    config_data = read_json_file(config_path)
    if not config_data:
        return False, f"Could not load configuration for provider '{provider_name}' from {config_path}."

    models = config_data.get('py_models', [])
    if not isinstance(models, list):
        return False, f"Invalid 'py_models' format in {config_path}. Expected a list."

    model_found = False
    updated = False
    status_str = "enabled" if enabled else "disabled"

    for model_dict in models:
        if isinstance(model_dict, dict) and model_dict.get('name') == model_name:
            model_found = True
            current_status = model_dict.get('enabled', True) # Default to True if missing
            if current_status == enabled:
                return True, f"Model '{provider_name}/{model_name}' is already {status_str}."
            else:
                model_dict['enabled'] = enabled
                updated = True
                break # Found and updated

    if not model_found:
        available = [m.get('name') for m in models if isinstance(m, dict) and m.get('name')]
        available_str = f" Available py_models: {', '.join(available)}" if available else ""
        return False, f"Model '{model_name}' not found in configuration for provider '{provider_name}'.{available_str}"

    if updated:
        if write_json_file(config_path, config_data):
            reset_caches() # Clear factory cache so changes are reflected
            return True, f"Model '{provider_name}/{model_name}' {status_str} successfully."
        else:
            return False, f"Error writing updated configuration to {config_path}."
    else:
         # Should not happen if logic is correct, but as a safeguard
         logger.warning("Model found but state indicates no update occurred. Logic error?")
         return False, f"Internal error: Model '{model_name}' found but not updated."


def update_provider_models_from_api(provider_name: str) -> Tuple[bool, str]:
    """
    Updates model details (cost, limits) for a provider from its API.
    Currently only supports 'openrouter'.

    Args:
        provider_name: The name of the provider to update.

    Returns:
        Tuple of (success: bool, message: str).
    """
    logger.info(f"Attempting to update model information for provider: {provider_name}")

    if provider_name != "openrouter":
        return False, f"Dynamic model updates currently only supported for 'openrouter'."

    # --- Fetch API Data ---
    api_models_data = _fetch_openrouter_models_with_cache()
    if not api_models_data:
        return False, "Failed to fetch model data from OpenRouter API. Cannot update."

    # --- Load Static Config ---
    config_path = get_provider_config_path(provider_name)
    static_config_data = read_json_file(config_path)
    if not static_config_data:
        return False, f"Static config file not found or could not be read at {config_path}"

    try:
        # Parse static config using Pydantic py_models to ensure structure
        static_config = ProviderConfig(**static_config_data)
        current_models = static_config.llm_models
        logger.info(f"Loaded {len(current_models)} py_models from static config: {config_path}")
    except Exception as e:
        logger.error(f"Error parsing static config file {config_path}: {e}", exc_info=True)
        return False, f"Error parsing static config file {config_path}: {e}"

    # --- Merge and Prepare Updated Config ---
    try:
        updated_model_configs: List[ModelConfig] = _merge_static_and_api_models(current_models, api_models_data)
        logger.info(f"Merged API data. Total py_models after merge: {len(updated_model_configs)}")

        # Prepare the full config data to be written back
        output_config_data = static_config_data.copy()
        # Convert ModelConfig objects back to dictionaries for JSON serialization
        output_config_data['py_models'] = [model.model_dump(exclude_none=True) for model in updated_model_configs]

    except Exception as e:
        logger.error(f"Failed during model merging: {e}", exc_info=True)
        return False, f"Error merging API data with static config: {e}"

    # --- Write Updated Config Back ---
    # Compare before writing
    if static_config_data == output_config_data:
         return True, f"No changes detected between API data and static config for {provider_name}. File not modified."

    if write_json_file(config_path, output_config_data):
        reset_caches() # Clear factory cache
        logger.info(f"Wrote updated config to {config_path}")
        return True, f"Successfully updated model information in {config_path}"
    else:
        return False, f"Error writing updated config file {config_path}"
