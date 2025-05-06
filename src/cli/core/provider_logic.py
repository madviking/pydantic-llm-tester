import os
import logging
from typing import List, Set, Dict, Tuple # Added Dict and Tuple

# Use absolute imports for clarity within the package
from src.cli.core.common import (
    get_llm_tester_dir,
    get_enabled_providers_path,
    read_json_file,
    write_json_file,
    ENABLED_PROVIDERS_FILENAME
)
# Import provider factory functions for discovery and cache management
from src.llms.provider_factory import reset_caches, get_available_providers as factory_get_available # Renamed to avoid conflict

logger = logging.getLogger(__name__)

def get_discovered_providers() -> List[str]:
    """
    Discovers all potential provider subdirectories in src/llms/.
    Does not check for valid implementation, just directory structure.
    """
    llms_dir = os.path.join(get_llm_tester_dir(), 'llms')
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

def read_enabled_providers() -> Set[str]:
    """
    Reads the set of enabled providers from the enabled_providers.json file.
    Returns an empty set if the file doesn't exist or is invalid.
    """
    enabled_file_path = get_enabled_providers_path()
    data = read_json_file(enabled_file_path)

    if data is None:
        # File doesn't exist or couldn't be read/parsed
        return set() # Treat as empty list

    if isinstance(data, list) and all(isinstance(item, str) for item in data):
        return set(data)
    else:
        logger.warning(f"Invalid format in '{enabled_file_path}'. Expected list of strings. Treating as empty.")
        return set()

def write_enabled_providers(providers: Set[str]) -> bool:
    """
    Writes the set of enabled providers to the enabled_providers.json file.
    Returns True on success, False on failure.
    """
    enabled_file_path = get_enabled_providers_path()
    # Convert set to sorted list for consistent file output
    sorted_list = sorted(list(providers))
    return write_json_file(enabled_file_path, sorted_list)

def is_provider_enabled(provider_name: str) -> bool:
    """Checks if a specific provider is currently enabled."""
    enabled_file_path = get_enabled_providers_path()
    if not os.path.exists(enabled_file_path):
        # If file doesn't exist, all discovered providers are implicitly enabled
        return provider_name in get_discovered_providers()
    else:
        # If file exists, only those listed are enabled
        return provider_name in read_enabled_providers()

def get_enabled_status() -> Dict[str, bool]:
    """
    Gets the enabled status for all discovered providers.

    Returns:
        Dict mapping provider name to boolean enabled status.
    """
    all_providers = get_discovered_providers()
    enabled_file_path = get_enabled_providers_path()
    status = {}

    if not os.path.exists(enabled_file_path):
        logger.info(f"'{ENABLED_PROVIDERS_FILENAME}' not found. All discovered providers considered enabled.")
        for provider in all_providers:
            status[provider] = True
    else:
        enabled_set = read_enabled_providers()
        logger.info(f"Read enabled providers from '{enabled_file_path}': {enabled_set}")
        for provider in all_providers:
            status[provider] = provider in enabled_set

    return status


def enable_provider(provider_name: str) -> Tuple[bool, str]:
    """
    Enables a provider by adding it to enabled_providers.json.

    Args:
        provider_name: The name of the provider to enable.

    Returns:
        Tuple of (success: bool, message: str).
    """
    all_providers = get_discovered_providers()
    if provider_name not in all_providers:
        return False, f"Provider '{provider_name}' not found or not discoverable. Available: {', '.join(all_providers)}"

    enabled_file_path = get_enabled_providers_path()
    enabled_set = read_enabled_providers()

    if not os.path.exists(enabled_file_path):
        # File doesn't exist, create it with just this provider
        if write_enabled_providers({provider_name}):
            reset_caches() # Clear factory cache
            return True, f"Created '{ENABLED_PROVIDERS_FILENAME}' and enabled '{provider_name}'."
        else:
            return False, f"Error writing to {enabled_file_path}."
    else:
        # File exists, add if not present
        if provider_name in enabled_set:
            return True, f"Provider '{provider_name}' is already enabled."
        else:
            enabled_set.add(provider_name)
            if write_enabled_providers(enabled_set):
                reset_caches() # Clear factory cache
                return True, f"Provider '{provider_name}' enabled successfully."
            else:
                return False, f"Error writing to {enabled_file_path}."

def disable_provider(provider_name: str) -> Tuple[bool, str]:
    """
    Disables a provider by removing it from enabled_providers.json.

    Args:
        provider_name: The name of the provider to disable.

    Returns:
        Tuple of (success: bool, message: str).
    """
    enabled_file_path = get_enabled_providers_path()

    if not os.path.exists(enabled_file_path):
        return False, f"'{ENABLED_PROVIDERS_FILENAME}' not found. Cannot disable '{provider_name}'. (All discovered providers are enabled by default)."

    enabled_set = read_enabled_providers()

    if provider_name not in enabled_set:
        # Check if it's a valid provider at all
        status_msg = f"Provider '{provider_name}' is not currently enabled in {ENABLED_PROVIDERS_FILENAME}."
        if provider_name not in get_discovered_providers():
             status_msg += f" It is also not a discoverable provider."
        return True, status_msg # Not an error if already disabled

    # Remove the provider and write back
    enabled_set.discard(provider_name) # Use discard to avoid error if somehow not present
    if write_enabled_providers(enabled_set):
        reset_caches() # Clear factory cache
        return True, f"Provider '{provider_name}' disabled successfully."
    else:
        return False, f"Error writing to {enabled_file_path}."

def get_available_providers_from_factory() -> List[str]:
    """
    Gets the list of providers considered available by the provider_factory.
    This respects the enabled_providers.json file.
    """
    reset_caches() # Ensure cache is clear before checking
    return factory_get_available()
