import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# --- Constants ---
ENABLED_PROVIDERS_FILENAME = "enabled_providers.json"

# --- Path Helpers ---

def get_cli_package_dir() -> str:
    """Gets the absolute path to the src/cli directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Go up one level from core

def get_llm_tester_dir() -> str:
    """Gets the absolute path to the src package directory."""
    return os.path.dirname(get_cli_package_dir()) # Go up one level from cli

def get_project_root() -> str:
    """Gets the absolute path to the project root directory (one level above src)."""
    # This assumes the script is run from within the standard project structure
    return os.path.dirname(get_llm_tester_dir())

def get_provider_config_dir(provider_name: str) -> str:
    """Gets the absolute path to a specific provider's directory."""
    return os.path.join(get_llm_tester_dir(), 'llms', provider_name)

def get_provider_config_path(provider_name: str) -> str:
    """Gets the absolute path to a provider's config.json file."""
    return os.path.join(get_provider_config_dir(provider_name), 'config.json')

def get_enabled_providers_path() -> str:
    """Gets the absolute path to the enabled_providers.json file in the project root."""
    return os.path.join(get_project_root(), ENABLED_PROVIDERS_FILENAME)

def get_default_dotenv_path() -> str:
    """Gets the absolute path to the default .env file within src."""
    return os.path.join(get_llm_tester_dir(), '.env')


# --- File I/O Helpers ---

def read_json_file(file_path: str) -> Optional[Any]:
    """Reads a JSON file and returns its content, or None on error."""
    if not os.path.exists(file_path):
        logger.debug(f"JSON file not found at: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from '{file_path}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {e}")
        return None

def write_json_file(file_path: str, data: Any) -> bool:
    """Writes data to a JSON file, returns True on success, False on error."""
    try:
        # Ensure directory exists
        dir_path = os.path.dirname(file_path)
        if dir_path: # Avoid error if writing to root (though unlikely here)
            os.makedirs(dir_path, exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2) # Use indent for readability
        logger.info(f"Successfully wrote JSON data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing JSON to '{file_path}': {e}")
        return False
