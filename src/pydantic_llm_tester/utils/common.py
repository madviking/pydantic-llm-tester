import os
import sys
import importlib.util
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_CONFIG_FILENAME = "pyllm_config.json"

# --- Path Helpers ---

def get_package_dir() -> str:
    """
    Gets the absolute path to the pydantic_llm_tester package directory.
    Works whether the package is installed or run from source.
    """
    # __file__ is something like /path/to/src/pydantic_llm_tester/utils/common.py
    # We need to go up two levels to get the package directory
    return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))

def get_cli_dir() -> str:
    """
    Gets the absolute path to the CLI directory within the package.
    Works whether the package is installed or run from source.
    """
    return os.path.join(get_package_dir(), "cli")

def is_installed_package() -> bool:
    """
    Determine if this is running as an installed package or from source.
    """
    # Check if __file__ is in site-packages or similar
    package_dir = get_package_dir()
    return ('site-packages' in package_dir or 
            'dist-packages' in package_dir or
            os.path.basename(os.path.dirname(package_dir)) == 'src' or
            os.path.basename(os.path.dirname(os.path.dirname(package_dir))) == 'src')

def get_project_root() -> str:
    """
    Gets the absolute path to the project root directory.
    - If run as a standalone repo, returns the directory containing src/
    - If installed, returns the directory where the command was invoked
    """
    if is_installed_package():
        # If installed, project root is wherever the command is being run
        return os.getcwd()
    else:
        # If running from source, project root is one level above package dir
        # (assuming src/pydantic_llm_tester structure)
        package_dir = get_package_dir()
        
        # Check the hierarchy for 'src'
        if os.path.basename(os.path.dirname(package_dir)) == 'src':
            # We're likely in a 'src/pydantic_llm_tester' structure
            return os.path.dirname(os.path.dirname(package_dir))
        elif os.path.basename(os.path.dirname(os.path.dirname(package_dir))) == 'src':
            # We might be in 'src/pydantic_llm_tester/utils' structure
            return os.path.dirname(os.path.dirname(os.path.dirname(package_dir)))
        else:
            # Fallback: just go up one level from package dir
            return os.path.dirname(package_dir)

def get_provider_config_dir(provider_name: str) -> str:
    """Gets the absolute path to a specific provider's directory."""
    return os.path.join(get_package_dir(), 'llms', provider_name)

def get_provider_config_path(provider_name: str) -> str:
    """Gets the absolute path to a provider's config.json file."""
    return os.path.join(get_provider_config_dir(provider_name), 'config.json')

def get_templates_dir() -> str:
    """Gets the absolute path to the templates directory."""
    return os.path.join(get_cli_dir(), 'templates')

def get_default_config_path() -> str:
    """Gets the absolute path to the pyllm_config.json file in the project root."""
    return os.path.join(get_project_root(), DEFAULT_CONFIG_FILENAME)

def get_default_dotenv_path() -> str:
    """Gets the absolute path to the default .env file within src."""
    return os.path.join(get_project_root(), '.env')

def get_py_models_dir() -> str:
    """
    Gets the absolute path to the built-in py_models directory within the package.
    """
    return os.path.join(get_package_dir(), 'py_models')

def get_external_py_models_dir() -> str:
    """
    Gets the absolute path to the external py_models directory in the project root.
    This is where user-created py_models should be placed.
    """
    return os.path.join(get_project_root(), 'py_models')

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
