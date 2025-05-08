import os
import getpass
import logging
from typing import Dict, Tuple, Set
from dotenv import set_key

# Use absolute imports for clarity within the package
from pydantic_llm_tester.utils.common import get_default_dotenv_path
from pydantic_llm_tester.cli.core.provider_logic import get_discovered_providers # Use the discovered list
from pydantic_llm_tester.llms.provider_factory import load_provider_config, reset_caches # To get env_key from config

logger = logging.getLogger(__name__)

def check_and_configure_api_keys(prompt_user: bool = True) -> Tuple[bool, Dict[str, str]]:
    """
    Checks for required API keys based on discovered provider configurations.
    Optionally prompts the user for missing keys and offers to save them.

    Args:
        prompt_user: If True, interactively prompt for missing keys.

    Returns:
        Tuple:
            - bool: True if keys were successfully saved (or no save needed), False otherwise.
            - Dict[str, str]: Dictionary of keys that were entered by the user (if any).
    """
    logger.info("Checking API key configuration...")
    dotenv_path = get_default_dotenv_path()
    logger.debug(f"Target .env file path: {dotenv_path}")

    # Ensure caches are clear to get fresh provider info
    reset_caches()
    discovered_providers = get_discovered_providers()
    keys_to_set: Dict[str, str] = {}
    required_keys: Set[str] = set()
    providers_checked: Set[str] = set()

    print("Checking required API keys for discovered providers...")

    for provider_name in discovered_providers:
        if provider_name in providers_checked:
            continue
        providers_checked.add(provider_name)

        config = load_provider_config(provider_name)
        if not config or not config.env_key:
            logger.debug(f"Provider '{provider_name}' does not require an API key or config is missing.")
            continue

        env_key = config.env_key
        required_keys.add(env_key)
        api_key = os.getenv(env_key) # Check current environment

        if api_key:
            logger.info(f"API key '{env_key}' for provider '{provider_name}' found in environment.")
        elif prompt_user:
            logger.warning(f"API key '{env_key}' for provider '{provider_name}' not found in environment.")
            try:
                print(f"\nAPI key for provider '{provider_name}' ({env_key}) is missing.")
                key_value = getpass.getpass(f"Enter value for {env_key} (leave blank to skip): ")
                if key_value:
                    keys_to_set[env_key] = key_value
                    # Temporarily set in environment for subsequent checks within this run?
                    # os.environ[env_key] = key_value
                else:
                    print(f"Skipping configuration for {env_key}.")
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.")
                return False, {} # Indicate failure/cancellation

    if not keys_to_set:
        if prompt_user:
            print("\nAll required API keys seem to be present in the environment.")
        return True, {} # Success, nothing to save

    if not prompt_user:
        # If not prompting, just report which keys are missing
        missing_keys = required_keys - set(os.environ.keys())
        logger.warning(f"API keys missing (and not prompted for): {', '.join(missing_keys)}")
        return True, {} # Indicate success (no save attempted), but keys might be missing

    # --- Prompt to Save ---
    print("\nThe following keys were entered:")
    for key in keys_to_set:
        print(f"  {key}: ***")  # Don't print the actual key

    try:
        save_confirm = input(f"Save these keys to '{dotenv_path}'? (y/N): ").strip().lower()
        if save_confirm == 'y':
            # Ensure the directory exists
            dotenv_dir = os.path.dirname(dotenv_path)
            if not os.path.exists(dotenv_dir):
                logger.info(f"Creating directory for .env file: {dotenv_dir}")
                os.makedirs(dotenv_dir)
            # Ensure the file exists, even if empty, for set_key
            # set_key might create the file, but explicitly creating it first
            # is safer and ensures the directory exists beforehand.
            if not os.path.exists(dotenv_path):
                logger.info(f"Creating .env file: {dotenv_path}")
                try:
                    with open(dotenv_path, 'w') as f:
                        pass  # Create empty file
                except IOError as e:
                    logger.error(f"Failed to create .env file at {dotenv_path}: {e}")
                    print(f"Error creating .env file: {e}")
                    return False, {}  # Indicate failure

            # Use the predefined dotenv_path directly obtained from get_default_dotenv_path()
            target_dotenv_file = dotenv_path

            logger.info(f"Saving keys to: {target_dotenv_file}")
            saved_count = 0
            try:
                for key, value in keys_to_set.items():
                    # Use quote_mode='never' to avoid potential issues with quotes in keys/values
                    # set_key modifies the file directly.
                    success = set_key(target_dotenv_file, key, value, quote_mode='never')
                    if success:
                        logger.info(f"Successfully saved {key} to {target_dotenv_file}")
                        saved_count += 1
                    else:
                        # Note: python-dotenv set_key's return value can be unreliable.
                        # A common pattern is to just assume success if no exception
                        # was raised by set_key itself.
                        logger.warning(
                            f"set_key for {key} returned {success}. Verify file content: {target_dotenv_file}")

                print(f"Attempted to save {len(keys_to_set)} key(s) to {target_dotenv_file}.")
                print(
                    "Note: You might need to restart your terminal session or IDE for the changes to take full effect.")
                return True, keys_to_set  # Return success and the keys that were set

            except Exception as e:
                logger.error(f"An error occurred while using set_key: {e}", exc_info=True)
                print(f"An error occurred while saving keys: {e}")
                return False, {}


        else:
            print("Keys not saved.")
            return True, {}  # Success (user chose not to save)

    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.")
        return False, {}
    except Exception as e:
        # Catching other potential exceptions during the save confirmation prompt etc.
        logger.error(f"An unexpected error occurred during save confirmation: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")
        return False, {}


    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.")
        return False, {}
    except Exception as e:
        logger.error(f"An error occurred while saving keys: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        return False, {}
