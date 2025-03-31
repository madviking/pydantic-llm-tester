#!/usr/bin/env python3
"""
Command-line interface for LLM Tester
"""

import argparse
import json
import sys
import os
import getpass # Added
from datetime import datetime
from typing import List, Dict, Optional, Tuple # Added Tuple
from dotenv import load_dotenv, set_key, find_dotenv # Import load_dotenv, set_key, find_dotenv
import logging # Import logging

# Configure basic logging early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load .env file at module level ---
# Assume .env is inside the llm_tester directory, relative to this cli.py file
_script_dir = os.path.dirname(os.path.abspath(__file__))
_dotenv_path = os.path.join(_script_dir, '.env') # Path is llm_tester/.env
if os.path.exists(_dotenv_path):
    # Force override in case variable exists but is empty in parent environment
    load_dotenv(dotenv_path=_dotenv_path, override=True)
    logger.info(f"Loaded environment variables from: {_dotenv_path} (override=True)")
else:
    logger.warning(f"Default .env file not found at {_dotenv_path}")
# --- End .env loading ---


from llm_tester import LLMTester
# Import provider factory functions and helpers
from llm_tester.llms.provider_factory import (
    get_available_providers, load_provider_config, reset_caches, create_provider, # Added create_provider
    _fetch_openrouter_models_with_cache, _merge_static_and_api_models # Import helpers
)
from llm_tester.llms.base import ProviderConfig, ModelConfig, BaseLLM # Import config models and BaseLLM


# Default model configurations for each provider
DEFAULT_MODELS = {
    "openai": "gpt-4",
    "anthropic": "claude-3-opus-20240229",
    "mistral": "mistral-large-latest",
    "google": "gemini-pro"
}


def handle_run_tests(args):
    """Handler for the default 'run' command (testing)."""
    logger.debug("Handling 'run tests' command.")
    # Handle model specifications
    models = parse_model_args(args.models)

    # Initialize tester
    # Note: We might want to filter providers based on a global config later
    tester = LLMTester(
        providers=args.providers,
        test_dir=args.test_dir
    )

    # List test cases
    if args.list:
        test_cases = tester.discover_test_cases()
        print(f"Found {len(test_cases)} test cases:")
        for test_case in test_cases:
            print(f"  {test_case['module']}/{test_case['name']}")

        # Also list available providers and models
            print("\nAvailable providers:")
            # Ensure providers list is populated if None (when --list is used without --providers)
            current_providers = args.providers
            if current_providers is None:
                 reset_caches() # Ensure fresh list
                 current_providers = get_available_providers()
                 logger.info(f"--list used without --providers, listing all available: {', '.join(current_providers)}")

            # TODO: Get available providers dynamically later
            for provider in current_providers:
                config = load_provider_config(provider)
                default_model = "N/A"
            if config and config.models:
                default_model_obj = next((m for m in config.models if m.default), None)
                if default_model_obj:
                    default_model = default_model_obj.name
                elif config.models: # Fallback to first model if no default
                    default_model = config.models[0].name

            if provider in models:
                print(f"  {provider} (using model: {models[provider]})")
            else:
                print(f"  {provider} (using default model: {default_model})")

        return 0

    # Run tests with specific models if provided
    # TODO: Implement filtering logic within LLMTester or before calling run_tests
    if args.optimize:
        print("Running optimized tests...")
        # Removed test_filter=args.filter as it's not supported by the method
        results = tester.run_optimized_tests(model_overrides=models)
    else:
        print("Running tests...")
        # Removed test_filter=args.filter as it's not supported by the method
        results = tester.run_tests(model_overrides=models)

    # Generate output
    if args.json:
        # Convert any non-serializable objects to strings
        serializable_results = _make_serializable(results)
        output = json.dumps(serializable_results, indent=2)
    else:
        output = tester.generate_report(results, optimized=args.optimize)

    # Write output
    output_str = str(output) # Ensure output is a string, even if it's an error dict/object
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output_str)
            print(f"Results written to {args.output}")
        except Exception as e:
            logger.error(f"Failed to write report to {args.output}: {e}")
            print("\n--- Report / Results ---")
            print(output_str) # Print to stdout as fallback
            print("--- End Report / Results ---")
    else:
        print("\n" + output_str)

    return 0


def handle_configure_keys(args):
    """Handler for the 'configure keys' command."""
    logger.info("Checking API key configuration...")
    # Use the default .env path determined at the start
    dotenv_path = _dotenv_path # Use the path found earlier
    logger.debug(f"Target .env file path: {dotenv_path}")

    # Ensure caches are clear to get fresh provider info
    reset_caches()
    available_providers = get_available_providers()
    keys_to_set = {}
    keys_found = {}
    providers_checked = set()

    print("Checking required API keys for available providers...")

    for provider_name in available_providers:
        if provider_name in providers_checked:
            continue
        providers_checked.add(provider_name)

        config = load_provider_config(provider_name)
        if not config or not config.env_key:
            logger.debug(f"Provider '{provider_name}' does not require an API key or config is missing.")
            continue

        env_key = config.env_key
        api_key = os.getenv(env_key)

        if api_key:
            logger.info(f"API key '{env_key}' for provider '{provider_name}' found in environment.")
            keys_found[env_key] = True
        else:
            logger.warning(f"API key '{env_key}' for provider '{provider_name}' not found in environment.")
            try:
                print(f"\nAPI key for provider '{provider_name}' ({env_key}) is missing.")
                key_value = getpass.getpass(f"Enter value for {env_key} (leave blank to skip): ")
                if key_value:
                    keys_to_set[env_key] = key_value
                else:
                    print(f"Skipping configuration for {env_key}.")
            except EOFError:
                print("\nOperation cancelled by user.")
                return 1 # Indicate error/cancellation
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                return 1 # Indicate error/cancellation


    if not keys_to_set:
        print("\nAll required API keys seem to be present in the environment.")
        return 0

    print("\nThe following keys were entered:")
    for key, value in keys_to_set.items():
        print(f"  {key}: ***") # Don't print the actual key

    try:
        save_confirm = input(f"Save these keys to '{dotenv_path}'? (y/N): ").strip().lower()
        if save_confirm == 'y':
            # Ensure the directory exists
            dotenv_dir = os.path.dirname(dotenv_path)
            if not os.path.exists(dotenv_dir):
                 logger.info(f"Creating directory for .env file: {dotenv_dir}")
                 os.makedirs(dotenv_dir)
            # Ensure the file exists, even if empty, for set_key
            if not os.path.exists(dotenv_path):
                 logger.info(f"Creating .env file: {dotenv_path}")
                 with open(dotenv_path, 'w') as f:
                     pass # Create empty file

            # Find the .env file again to be sure after potential creation
            found_dotenv_path = find_dotenv(filename=os.path.basename(dotenv_path), raise_error_if_not_found=False, usecwd=True)
            if not found_dotenv_path or not os.path.exists(found_dotenv_path):
                 # Fallback if find_dotenv fails strangely after creation
                 found_dotenv_path = dotenv_path

            logger.info(f"Saving keys to: {found_dotenv_path}")
            saved_count = 0
            for key, value in keys_to_set.items():
                success = set_key(found_dotenv_path, key, value)
                if success:
                    logger.info(f"Successfully saved {key} to {found_dotenv_path}")
                    saved_count += 1
                else:
                    logger.error(f"Failed to save {key} to {found_dotenv_path}")

            if saved_count == len(keys_to_set):
                print(f"Successfully saved {saved_count} key(s) to {found_dotenv_path}.")
                print("Note: You might need to restart your terminal session or IDE for the changes to take effect.")
            else:
                print(f"Warning: Only saved {saved_count} out of {len(keys_to_set)} key(s). Check logs for errors.")
                return 1 # Indicate partial failure
        else:
            print("Keys not saved.")

    except EOFError:
        print("\nOperation cancelled by user.")
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logger.error(f"An error occurred while saving keys: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        return 1

    return 0


def handle_update_models(args):
    """Handler for the 'update-models' command."""
    provider_name = args.provider
    logger.info(f"Attempting to update model information for provider: {provider_name}")

    if provider_name != "openrouter":
        print(f"Error: Dynamic model updates currently only supported for 'openrouter'.")
        logger.error(f"Update requested for unsupported provider: {provider_name}")
        return 1

    # --- Fetch API Data ---
    # Use the helper from provider_factory which includes caching
    api_models_data = _fetch_openrouter_models_with_cache()
    if not api_models_data:
        print("Error: Failed to fetch model data from OpenRouter API. Cannot update.")
        logger.error("Aborting update-models due to API fetch failure.")
        return 1

    # --- Load Static Config ---
    # Construct path relative to this script's directory
    config_path = os.path.join(_script_dir, 'llms', provider_name, 'config.json')
    if not os.path.exists(config_path):
        print(f"Error: Static config file not found at {config_path}")
        logger.error(f"Static config missing for {provider_name} at {config_path}")
        return 1

    try:
        with open(config_path, 'r') as f:
            static_config_data = json.load(f)
        # Validate and parse static config to get current models
        static_config = ProviderConfig(**static_config_data)
        current_models = static_config.models
        logger.info(f"Loaded {len(current_models)} models from static config: {config_path}")
    except Exception as e:
        print(f"Error loading or parsing static config file {config_path}: {e}")
        logger.error(f"Failed to load static config {config_path}: {e}", exc_info=True)
        return 1

    # --- Merge and Prepare Updated Config ---
    try:
        # Use the merge logic from provider_factory
        updated_model_configs: List[ModelConfig] = _merge_static_and_api_models(current_models, api_models_data)
        logger.info(f"Merged API data. Total models after merge: {len(updated_model_configs)}")

        # Prepare the full config data to be written back
        # Start with the original static data, then replace the models list
        output_config_data = static_config_data.copy()
        # Convert ModelConfig objects back to dictionaries for JSON serialization
        output_config_data['models'] = [model.model_dump(exclude_none=True) for model in updated_model_configs]

    except Exception as e:
        print(f"Error merging API data with static config: {e}")
        logger.error(f"Failed during model merging: {e}", exc_info=True)
        return 1

    # --- Write Updated Config Back ---
    try:
        # Compare before asking to write
        if static_config_data == output_config_data:
             print(f"No changes detected between API data and static config for {provider_name}. File not modified.")
             return 0

        print(f"Changes detected for provider '{provider_name}'.")
        write_confirm = input(f"Update '{config_path}' with new model data? (y/N): ").strip().lower()
        if write_confirm == 'y':
            with open(config_path, 'w') as f:
                json.dump(output_config_data, f, indent=2) # Use indent for readability
            print(f"Successfully updated model information in {config_path}")
            logger.info(f"Wrote updated config to {config_path}")
            # Clear the in-memory cache so next load gets the updated file
            reset_caches()
            logger.info("Provider configuration cache cleared.")
        else:
            print("Update cancelled. No changes written.")
            return 0

    except EOFError:
        print("\nOperation cancelled by user.")
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error writing updated config file {config_path}: {e}")
        logger.error(f"Failed to write updated config {config_path}: {e}", exc_info=True)
        return 1

    return 0


# --- Provider Management Helpers ---

def _get_project_root() -> str:
    """Gets the absolute path to the project root directory."""
    return os.path.abspath(os.path.join(_script_dir, '..'))

def _get_enabled_providers_path() -> str:
    """Gets the absolute path to the enabled_providers.json file."""
    return os.path.join(_get_project_root(), ENABLED_PROVIDERS_FILENAME)

def _read_enabled_providers_file() -> List[str]:
    """Reads the enabled providers list from the file, returns empty list if error."""
    enabled_file_path = _get_enabled_providers_path()
    if not os.path.exists(enabled_file_path):
        return [] # No file means no specific providers enabled (or all, depending on interpretation)
    try:
        with open(enabled_file_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            return sorted(list(set(data))) # Return sorted unique list
        else:
            logger.warning(f"Invalid format in '{enabled_file_path}'. Expected list of strings.")
            return []
    except Exception as e:
        logger.error(f"Error reading '{enabled_file_path}': {e}")
        return []

def _write_enabled_providers_file(providers_list: List[str]) -> bool:
    """Writes the list of enabled providers to the file."""
    enabled_file_path = _get_enabled_providers_path()
    try:
        # Ensure the list contains unique, sorted strings
        unique_sorted_list = sorted(list(set(providers_list)))
        with open(enabled_file_path, 'w') as f:
            json.dump(unique_sorted_list, f, indent=2)
        logger.info(f"Wrote {len(unique_sorted_list)} providers to {enabled_file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing to '{enabled_file_path}': {e}")
        return False

def _get_all_discovered_providers() -> List[str]:
    """Gets all providers discoverable by the factory, ignoring the enabled list."""
    # Temporarily bypass the enabled list filtering in get_available_providers
    # This requires a slight modification or a new function in provider_factory,
    # or we can just re-implement the discovery logic here for simplicity.
    # Re-implementing discovery logic here for now:
    provider_classes = {}
    current_dir = os.path.join(_script_dir, 'llms')
    provider_dirs = []
    try:
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path) and not item.startswith('__'):
                if os.path.exists(os.path.join(item_path, '__init__.py')):
                    provider_dirs.append(item)
    except FileNotFoundError:
        pass # Ignore if llms dir doesn't exist

    # TODO: Add external provider discovery here as well if needed
    # external_providers = load_external_providers() # From provider_factory
    # all_providers = sorted(list(set(provider_dirs + list(external_providers.keys()))))

    # TODO: Add external provider discovery here as well if needed
    # external_providers = load_external_providers() # From provider_factory
    # all_providers = sorted(list(set(provider_dirs + list(external_providers.keys()))))

    return sorted(provider_dirs)


# --- Model Management Helpers ---

def _get_provider_config_path(provider_name: str) -> str:
    """Gets the absolute path to a provider's config.json file."""
    return os.path.join(_script_dir, 'llms', provider_name, 'config.json')

def _read_provider_config_file(provider_name: str) -> Optional[Dict]:
    """Reads a provider's config file directly as JSON, returns None on error."""
    config_path = _get_provider_config_path(provider_name)
    if not os.path.exists(config_path):
        logger.error(f"Config file not found for provider '{provider_name}' at {config_path}")
        return None
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading config file {config_path}: {e}")
        return None

def _write_provider_config_file(provider_name: str, config_data: Dict) -> bool:
    """Writes data to a provider's config file."""
    config_path = _get_provider_config_path(provider_name)
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        logger.info(f"Successfully wrote config to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing config file {config_path}: {e}")
        return False

def _parse_full_model_id(model_id_arg: str, provider_arg: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Parses model ID, potentially extracting provider. Returns (provider, model_name)."""
    if '/' in model_id_arg:
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


# --- Provider Management Command Handlers ---

def handle_providers_list(args):
    """Handler for 'providers list' command."""
    reset_caches() # Ensure we check the file system
    all_providers = _get_all_discovered_providers()
    enabled_providers_from_file = _read_enabled_providers_file()
    enabled_providers_path = _get_enabled_providers_path()

    if not os.path.exists(enabled_providers_path):
        print("No 'enabled_providers.json' found. All discovered providers are considered enabled:")
        if not all_providers:
            print("  (No providers discovered)")
        else:
            for provider in all_providers:
                print(f"  - {provider} (Enabled by default)")
    else:
        print("Provider Status (based on 'enabled_providers.json'):")
        if not all_providers:
             print("  (No providers discovered)")
        else:
            for provider in all_providers:
                status = "Enabled" if provider in enabled_providers_from_file else "Disabled"
                print(f"  - {provider} ({status})")

    return 0

def handle_providers_enable(args):
    """Handler for 'providers enable' command."""
    provider_name = args.provider_name
    all_providers = _get_all_discovered_providers()

    if provider_name not in all_providers:
        print(f"Error: Provider '{provider_name}' not found or not discoverable.")
        print(f"Available providers: {', '.join(all_providers)}")
        return 1

    enabled_providers = _read_enabled_providers_file()
    enabled_providers_path = _get_enabled_providers_path()

    # If the file didn't exist, enabling one means creating the file with just that one
    if not os.path.exists(enabled_providers_path):
         print(f"Creating '{ENABLED_PROVIDERS_FILENAME}' and enabling '{provider_name}'.")
         if _write_enabled_providers_file([provider_name]):
             print(f"Provider '{provider_name}' enabled successfully.")
             return 0
         else:
             print(f"Error writing to {enabled_providers_path}.")
             return 1
    else:
        # File exists, add the provider if not already present
        if provider_name in enabled_providers:
            print(f"Provider '{provider_name}' is already enabled.")
            return 0
        else:
            enabled_providers.append(provider_name)
            if _write_enabled_providers_file(enabled_providers):
                print(f"Provider '{provider_name}' enabled successfully.")
                return 0
            else:
                print(f"Error writing to {enabled_providers_path}.")
                return 1

def handle_providers_disable(args):
    """Handler for 'providers disable' command."""
    provider_name = args.provider_name
    all_providers = _get_all_discovered_providers()
    enabled_providers = _read_enabled_providers_file()
    enabled_providers_path = _get_enabled_providers_path()

    if not os.path.exists(enabled_providers_path):
        print(f"No '{ENABLED_PROVIDERS_FILENAME}' found. Cannot disable '{provider_name}'.")
        print("(All discovered providers are currently enabled by default)")
        return 1

    if provider_name not in enabled_providers:
        print(f"Provider '{provider_name}' is not currently enabled in {enabled_providers_path}.")
        # Check if it's a valid provider at all
        if provider_name not in all_providers:
             print(f"Provider '{provider_name}' is also not a discoverable provider.")
        return 0 # Or 1? Arguably not an error if already disabled.

    # Remove the provider and write back
    enabled_providers.remove(provider_name)
    if _write_enabled_providers_file(enabled_providers):
        print(f"Provider '{provider_name}' disabled successfully.")
        return 0
    else:
        print(f"Error writing to {enabled_providers_path}.")
        return 1


# --- Model Management Command Handlers ---

def handle_models_list(args):
    """Handler for 'models list' command."""
    provider_name = args.provider
    config_data = _read_provider_config_file(provider_name)
    if not config_data:
        print(f"Could not load configuration for provider '{provider_name}'.")
        return 1

    models = config_data.get('models', [])
    if not models:
        print(f"No models found in configuration for provider '{provider_name}'.")
        return 0

    print(f"Models for provider '{provider_name}':")
    # Default enabled=True if not present in the file
    models.sort(key=lambda m: m.get('name', ''))
    for model in models:
        name = model.get('name', 'N/A')
        enabled = model.get('enabled', True) # Default to True if key missing
        status = "Enabled" if enabled else "Disabled"
        print(f"  - {name} ({status})")

    return 0

def handle_models_enable_disable(args, enable: bool):
    """Handler for 'models enable' and 'models disable' commands."""
    target_provider, target_model_name = _parse_full_model_id(args.model_id, args.provider)

    if not target_provider or not target_model_name:
        return 1 # Error message already printed by parser

    config_data = _read_provider_config_file(target_provider)
    if not config_data:
        print(f"Could not load configuration for provider '{target_provider}'.")
        return 1

    models = config_data.get('models', [])
    model_found = False
    updated = False

    for model in models:
        if model.get('name') == target_model_name:
            model_found = True
            current_status = model.get('enabled', True) # Default to True if missing
            if current_status == enable:
                status_str = "enabled" if enable else "disabled"
                print(f"Model '{target_provider}/{target_model_name}' is already {status_str}.")
                return 0 # Not an error, just no change needed
            else:
                model['enabled'] = enable
                updated = True
                break # Found and updated

    if not model_found:
        print(f"Error: Model '{target_model_name}' not found in configuration for provider '{target_provider}'.")
        # Optionally list available models?
        available = [m.get('name') for m in models if m.get('name')]
        if available:
             print(f"Available models: {', '.join(available)}")
        return 1

    if updated:
        if _write_provider_config_file(target_provider, config_data):
            status_str = "enabled" if enable else "disabled"
            print(f"Model '{target_provider}/{target_model_name}' {status_str} successfully.")
            reset_caches() # Clear cache so changes are reflected
            return 0
        else:
            print(f"Error writing updated configuration for provider '{target_provider}'.")
            return 1
    else:
         # Should not happen if logic is correct, but as a safeguard
         logger.warning("Model found but not updated, state might be inconsistent.")
         return 1


# --- Recommendation Command Handler ---

def handle_recommend_model(args):
    """Handler for 'recommend-model' command."""
    print("Gathering information about enabled models...")
    reset_caches() # Ensure fresh data
    enabled_providers = get_available_providers() # This now respects enabled_providers.json
    enabled_models_details = []

    if not enabled_providers:
        print("Error: No providers are currently enabled. Use 'llm-tester providers list' and 'llm-tester providers enable <name>'.")
        return 1

    for provider_name in enabled_providers:
        config = load_provider_config(provider_name)
        if config and config.models:
            for model_config in config.models:
                # Check the 'enabled' flag from the config (defaults to True if missing)
                if model_config.enabled:
                    details = (
                        f"- Provider: {provider_name}, Model: {model_config.name}\n"
                        f"  Cost (Input/Output per 1M tokens): ${model_config.cost_input:.2f} / ${model_config.cost_output:.2f}\n"
                        f"  Max Tokens (Input/Output): {model_config.max_input_tokens} / {model_config.max_output_tokens}\n"
                        f"  Category: {model_config.cost_category}"
                    )
                    enabled_models_details.append(details)

    if not enabled_models_details:
        print("Error: No models are enabled across the enabled providers.")
        print("Use 'llm-tester models list --provider <name>' and 'llm-tester models enable <provider>/<model_name>'.")
        return 1

    print(f"Found {len(enabled_models_details)} enabled models.")

    try:
        task_description = input("Describe the task you need the model for (e.g., 'summarize long articles cheaply', 'generate creative Python code'):\n> ")
        if not task_description:
            print("Task description cannot be empty. Aborting.")
            return 1
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.")
        return 1

    # --- Select LLM for Recommendation ---
    # Prioritize OpenRouter Haiku if available and key exists, fallback to others
    recommendation_provider_name = None
    recommendation_model_name = None
    llm_provider: Optional[BaseLLM] = None

    # Check OpenRouter first
    if "openrouter" in enabled_providers:
        or_config = load_provider_config("openrouter")
        # Check if Haiku is enabled within OpenRouter config
        haiku_config = next((m for m in or_config.models if m.name == "anthropic/claude-3-haiku" and m.enabled), None) if or_config else None
        if haiku_config and os.getenv("OPENROUTER_API_KEY"):
            recommendation_provider_name = "openrouter"
            recommendation_model_name = "anthropic/claude-3-haiku"
            llm_provider = create_provider(recommendation_provider_name)

    # Add fallbacks here if needed (e.g., check google gemini-pro, openai gpt-3.5-turbo)
    # Example fallback (needs Google provider enabled and key):
    # if not llm_provider and "google" in enabled_providers and os.getenv("GOOGLE_API_KEY"):
    #     google_config = load_provider_config("google")
    #     gemini_config = next((m for m in google_config.models if "gemini-pro" in m.name and m.enabled), None) if google_config else None
    #     if gemini_config:
    #          recommendation_provider_name = "google"
    #          recommendation_model_name = gemini_config.name # Use the actual enabled gemini model name
    #          llm_provider = create_provider(recommendation_provider_name)

    if not llm_provider or not recommendation_model_name:
        print("\nError: Could not find a suitable LLM provider/model with an available API key to generate recommendations.")
        print("Please ensure at least one provider (like OpenRouter with key OPENROUTER_API_KEY) is configured and enabled.")
        return 1

    print(f"\nUsing '{recommendation_model_name}' via provider '{recommendation_provider_name}' to generate recommendation...")

    # --- Craft Prompt ---
    available_models_text = "\n\n".join(enabled_models_details)
    system_prompt = "You are an expert assistant helping users choose the best Large Language Model (LLM) for their task based on provided model details."
    prompt = (
        f"The user wants to perform the following task: '{task_description}'\n\n"
        f"Here are the available LLM models with their details:\n"
        f"{available_models_text}\n\n"
        f"Based ONLY on the information provided above, please recommend the top 1-3 models best suited for the user's task. "
        f"Explain your reasoning for each recommendation briefly, considering factors like cost, token limits, and potential suitability for the task described. "
        f"Format your response clearly."
    )

    # --- Call LLM ---
    try:
        # Use a dummy source for get_response as it's not relevant here
        response_text, usage_data = llm_provider.get_response(
            prompt=prompt,
            source="N/A", # Source text is not needed for this meta-task
            model_name=recommendation_model_name
        )
        print("\n--- LLM Recommendation ---")
        print(response_text)
        print("--------------------------")
        logger.info(f"Recommendation generated. Usage: {usage_data.total_tokens} tokens, Cost: ${usage_data.total_cost:.6f}")

    except Exception as e:
        print(f"\nError getting recommendation from LLM: {e}")
        logger.error(f"Failed to get recommendation using {recommendation_model_name}: {e}", exc_info=True)
        return 1

    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Test and manage LLM performance with pydantic models.",
        formatter_class=argparse.RawDescriptionHelpFormatter # Keep formatting in description
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count', default=0,
        help="Increase verbosity level (e.g., -v for INFO, -vv for DEBUG)"
    )
    parser.add_argument(
        "--env",
        type=str,
        help="Path to .env file with API keys (overrides default llm_tester/.env)"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = False # Make default command possible if no subcommand is given

    # --- Default command (run tests) ---
    # If no command is specified, we'll default to running tests.
    # We add arguments directly to the main parser for this default case.
    parser.add_argument(
        "--providers",
        type=str,
        nargs="+",
        # default=["openai", "anthropic", "mistral", "google"], # Default handled later if command is None
        help="LLM providers to test (default: all configured)"
    )
    parser.add_argument(
        "--test-dir",
        type=str,
        help="Directory containing test files (default: llm_tester/tests)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for report (default: stdout)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of a report"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize prompts and run tests again"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available test cases and providers/models without running tests"
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="Filter test cases by module/name pattern (e.g. 'job_ads/simple')"
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        help="Specify models to use in format 'provider:model_name' (e.g., 'openai:gpt-4' 'google:gemini-pro-1.5')"
    )
    # Set default function for the main parser (when no subcommand is given)
    parser.set_defaults(func=handle_run_tests)


    # --- 'configure' command ---
    parser_configure = subparsers.add_parser(
        'configure',
        help='Configure llm-tester settings (e.g., API keys)'
    )
    configure_subparsers = parser_configure.add_subparsers(dest='configure_command', help='Configuration actions')
    configure_subparsers.required = True

    # --- 'configure keys' command ---
    parser_configure_keys = configure_subparsers.add_parser(
        'keys',
        help='Check for and configure missing API keys'
    )
    parser_configure_keys.set_defaults(func=handle_configure_keys)

    # --- 'update-models' command ---
    parser_update = subparsers.add_parser(
        'update-models',
        help='Update model pricing/limits from provider APIs (currently OpenRouter only)'
    )
    parser_update.add_argument(
        '--provider',
        type=str,
        default='openrouter',
        help="Provider to update (default: openrouter)"
    )
    parser_update.set_defaults(func=handle_update_models)

    # --- 'providers' command ---
    parser_providers = subparsers.add_parser(
        'providers',
        help='Manage LLM provider configurations'
    )
    providers_subparsers = parser_providers.add_subparsers(dest='providers_command', help='Provider actions')
    providers_subparsers.required = True

    # --- 'providers list' command ---
    parser_providers_list = providers_subparsers.add_parser(
        'list',
        help='List all discoverable providers and their enabled/disabled status'
    )
    # parser_providers_list.add_argument('--all', action='store_true', help='Include disabled providers') # Maybe add later
    parser_providers_list.set_defaults(func=handle_providers_list)

    # --- 'providers enable' command ---
    parser_providers_enable = providers_subparsers.add_parser(
        'enable',
        help='Enable a specific provider'
    )
    parser_providers_enable.add_argument('provider_name', help='Name of the provider to enable')
    parser_providers_enable.set_defaults(func=handle_providers_enable)

    # --- 'providers disable' command ---
    parser_providers_disable = providers_subparsers.add_parser(
        'disable',
        help='Disable a specific provider'
    )
    parser_providers_disable.add_argument('provider_name', help='Name of the provider to disable')
    parser_providers_disable.set_defaults(func=handle_providers_disable)

    # --- 'models' command ---
    parser_models = subparsers.add_parser(
        'models',
        help='Manage model configurations within a provider'
    )
    models_subparsers = parser_models.add_subparsers(dest='models_command', help='Model actions')
    models_subparsers.required = True

    # --- 'models list' command ---
    parser_models_list = models_subparsers.add_parser(
        'list',
        help='List models for a provider and their enabled/disabled status'
    )
    parser_models_list.add_argument(
        '--provider',
        required=True,
        help='Name of the provider whose models to list'
    )
    parser_models_list.set_defaults(func=handle_models_list)

    # --- 'models enable' command ---
    parser_models_enable = models_subparsers.add_parser(
        'enable',
        help='Enable a specific model within a provider config'
    )
    parser_models_enable.add_argument(
        'model_id',
        help="Model ID to enable (e.g., 'provider/model_name' or just 'model_name' if --provider is specified)"
    )
    parser_models_enable.add_argument(
        '--provider',
        help='Provider name (required if not included in model_id)'
    )
    parser_models_enable.set_defaults(func=lambda args: handle_models_enable_disable(args, enable=True))

    # --- 'models disable' command ---
    parser_models_disable = models_subparsers.add_parser(
        'disable',
        help='Disable a specific model within a provider config'
    )
    parser_models_disable.add_argument(
        'model_id',
        help="Model ID to disable (e.g., 'provider/model_name' or just 'model_name' if --provider is specified)"
    )
    parser_models_disable.add_argument(
        '--provider',
        help='Provider name (required if not included in model_id)'
    )
    parser_models_disable.set_defaults(func=lambda args: handle_models_enable_disable(args, enable=False))

    # --- 'recommend-model' command ---
    parser_recommend = subparsers.add_parser(
        'recommend-model',
        help='Get LLM-assisted model recommendations for a task'
    )
    parser_recommend.set_defaults(func=handle_recommend_model)

    # ... etc ...


    # Parse arguments fully now
    args = parser.parse_args()

    # --- Setup Logging Level based on verbosity ---
    log_level = logging.WARNING # Default level if not verbose
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    # Apply log level to root logger and llm_tester logger
    logging.getLogger().setLevel(log_level)
    logging.getLogger('llm_tester').setLevel(log_level)
    logger.info(f"Logging level set to {logging.getLevelName(log_level)}")
    # --- End Logging Setup ---

    # --- Handle explicit --env argument (overrides module-level load) ---
    # This needs to happen *before* any command logic that relies on env vars
    if args.env:
        if os.path.exists(args.env):
            # Reload with override=True using the specified file
            load_dotenv(dotenv_path=args.env, override=True)
            logger.info(f"Loaded/Overridden environment variables from specified --env file: {args.env}")
        else:
            logger.warning(f"Specified --env file not found: {args.env}. Using previously loaded environment.")
    # --- End explicit --env handling ---


    # --- Execute the appropriate command handler ---
    if hasattr(args, 'func'):
        # If a subcommand was specified and has a handler
        return args.func(args)
    else:
        # If no subcommand was specified, default to running tests
        # Need to set default providers if not specified for the run command
        if not args.providers:
             # Get all available providers if none are specified for the run command
             reset_caches() # Ensure fresh list
             args.providers = get_available_providers()
             logger.info(f"No providers specified, defaulting to all available: {', '.join(args.providers)}")
        return handle_run_tests(args)


def parse_model_args(model_args: Optional[List[str]]) -> Dict[str, str]:
    """
    Parse model arguments in the format 'provider:model_name'
    
    Args:
        model_args: List of model specifications
        
    Returns:
        Dictionary mapping providers to model names
    """
    models = {}
    
    if not model_args:
        return models
    
    for arg in model_args:
        if ":" not in arg:
            print(f"Warning: Ignoring invalid model specification '{arg}'. Format should be 'provider:model_name'")
            continue
        
        provider, model_name = arg.split(":", 1)
        models[provider.strip()] = model_name.strip() # Add strip() for robustness
    
    return models # Re-added return statement

def _make_serializable(obj):
    """
    Convert non-JSON-serializable objects to strings
    
    Args:
        obj: Object to make serializable
        
    Returns:
        JSON-serializable object
    """
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


if __name__ == "__main__":
    sys.exit(main())
