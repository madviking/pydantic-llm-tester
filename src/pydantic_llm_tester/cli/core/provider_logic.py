import os
import logging
from typing import List, Set, Dict, Tuple

# Use absolute imports for clarity within the package
from pydantic_llm_tester.utils.common import (
    get_package_dir,
    read_json_file, # Keep read_json_file for other uses if any
    write_json_file # Keep write_json_file for other uses if any
)
from pydantic_llm_tester.utils.config_manager import ConfigManager # Import ConfigManager
# Import provider factory functions for discovery and cache management
from pydantic_llm_tester.llms.provider_factory import get_available_providers as factory_get_available # Renamed to avoid conflict

logger = logging.getLogger(__name__)

def get_discovered_providers() -> List[str]:
    """
    Discovers all potential provider subdirectories in src/llms/.
    Does not check for valid implementation, just directory structure.
    """
    llms_dir = os.path.join(get_package_dir(), 'llms')
    discovered = []
    try:
        if not os.path.isdir(llms_dir):
            logger.warning(f"LLM providers directory not found at: {llms_dir}")
            return []
        for item in os.listdir(llms_dir):
            item_path = os.path.join(llms_dir, item)
            # Check if it's a directory, not starting with '__', and contains '__init__.py'
            if os.path.isdir(item_path) and not item.startswith('__'):
                if os.path.exists(os.path.join(item_path, '__init__.py')):
                    discovered.append(item)
                else:
                     logger.debug(f"Directory '{item}' in '{llms_dir}' lacks __init__.py, skipping.")

    except Exception as e:
        logger.error(f"Error discovering providers in '{llms_dir}': {e}", exc_info=True)
        return []

    # TODO: Add external provider discovery if needed later
    return sorted(discovered)

def is_provider_enabled(provider_name: str) -> bool:
    """Checks if a specific provider is currently enabled based on ConfigManager."""
    config_manager = ConfigManager()
    providers_config = config_manager.get_providers()
    return providers_config.get(provider_name, {}).get("enabled", False) # Default to False if provider or enabled key missing

def get_enabled_status() -> Dict[str, bool]:
    """
    Gets the enabled status for all discovered providers based on ConfigManager.

    Returns:
        Dict mapping provider name to boolean enabled status.
    """
    all_providers = get_discovered_providers()
    config_manager = ConfigManager()
    providers_config = config_manager.get_providers()
    status = {}

    for provider in all_providers:
        # Get enabled status from config, default to False if provider or enabled key missing
        status[provider] = providers_config.get(provider, {}).get("enabled", False)

    return status


def enable_provider(provider_name: str) -> Tuple[bool, str]:
    """
    Enables a provider by setting its 'enabled' flag to true in pyllm_config.json.

    Args:
        provider_name: The name of the provider to enable.

    Returns:
        Tuple of (success: bool, message: str).
    """
    config_manager = ConfigManager()
    providers_config = config_manager.config.get("providers", {}) # Access the underlying config dict

    if provider_name not in providers_config:
        # Check if it's a discoverable provider at all before adding to config
        if provider_name not in get_discovered_providers():
             return False, f"Provider '{provider_name}' not found or not discoverable. Available: {', '.join(get_discovered_providers())}"

        # Provider is discoverable but not in config, add it and enable
        providers_config[provider_name] = {"enabled": True}
        config_manager.config["providers"] = providers_config # Ensure change is reflected
        config_manager.save_config()
        return True, f"Provider '{provider_name}' added to config and enabled."

    # Provider is in config, update enabled status
    if providers_config[provider_name].get("enabled", False):
        return True, f"Provider '{provider_name}' is already enabled."
    else:
        providers_config[provider_name]["enabled"] = True
        config_manager.config["providers"] = providers_config # Ensure change is reflected
        config_manager.save_config()
        return True, f"Provider '{provider_name}' enabled successfully."


def disable_provider(provider_name: str) -> Tuple[bool, str]:
    """
    Disables a provider by setting its 'enabled' flag to false in pyllm_config.json.

    Args:
        provider_name: The name of the provider to disable.

    Returns:
        Tuple of (success: bool, message: str).
    """
    config_manager = ConfigManager()
    providers_config = config_manager.config.get("providers", {}) # Access the underlying config dict

    if provider_name not in providers_config:
        # If provider not in config, it's implicitly disabled
        status_msg = f"Provider '{provider_name}' is not in pyllm_config.json, so it's already disabled."
        if provider_name not in get_discovered_providers():
             status_msg += f" It is also not a discoverable provider."
        return True, status_msg # Not an error if not in config

    # Provider is in config, update enabled status
    if not providers_config[provider_name].get("enabled", False):
        return True, f"Provider '{provider_name}' is already disabled."
    else:
        providers_config[provider_name]["enabled"] = False
        config_manager.config["providers"] = providers_config # Ensure change is reflected
        config_manager.save_config()
        return True, f"Provider '{provider_name}' disabled successfully."

def get_available_providers_from_factory() -> List[str]:
    """
    Gets the list of providers considered available by the provider_factory.
    This respects the enabled status in pyllm_config.json via the factory.
    """
    # The factory's get_available_providers already uses ConfigManager
    return factory_get_available()
