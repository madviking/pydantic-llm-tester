import logging
import typer
import os # Added import
from typing import List, Optional

# Import core logic functions that the UI will call
from pydantic_llm_tester.cli.core import config_logic, test_runner_logic, recommend_logic
from pydantic_llm_tester.cli.core import provider_logic, llm_model_logic as model_logic
# Import core scaffolding logic
from pydantic_llm_tester.cli.core.scaffold_logic import scaffold_provider_files, scaffold_model_files
# Import ConfigManager directly
from pydantic_llm_tester.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def _discover_builtin_py_models() -> List[str]:
    """Discovers the names of built-in py models."""
    builtin_models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "py_models")

    if not os.path.exists(builtin_models_dir):
        return []

    model_names = []
    for item_name in os.listdir(builtin_models_dir):
        item_path = os.path.join(builtin_models_dir, item_name)
        # Check if it's a directory and not a special directory/file
        if os.path.isdir(item_path) and not item_name.startswith("__") and not item_name.startswith("."):
            model_names.append(item_name)

    return model_names


# --- Helper Functions for Interactive Display ---

def _display_provider_status():
    """Displays the current provider status."""
    print("\n--- Provider Status ---")
    status_dict = provider_logic.get_enabled_status()
    if not status_dict:
        print("No providers discovered.")
        return

    enabled_file_path = provider_logic.get_enabled_providers_path()
    if not os.path.exists(enabled_file_path):
         print("(No 'enabled_providers.json' found. All discovered providers are enabled by default)")
    else:
         print(f"(Based on '{provider_logic.ENABLED_PROVIDERS_FILENAME}')")

    sorted_providers = sorted(status_dict.keys())
    for provider in sorted_providers:
        status = "Enabled" if status_dict[provider] else "Disabled"
        print(f"  - {provider} ({status})")
    print("-----------------------")

def _prompt_for_provider_name() -> Optional[str]:
    """Prompts the user to enter a provider name, showing available ones."""
    all_providers = provider_logic.get_discovered_providers()
    if not all_providers:
        print("Error: No providers discovered.")
        return None
    print(f"Available providers: {', '.join(all_providers)}")
    try:
        provider_name = typer.prompt("Enter provider name (or leave blank to cancel)", default="", show_default=False)
        return provider_name.strip() if provider_name else None
    except typer.Abort:
        print("\nOperation cancelled.")
        return None


# --- Submenus ---

def _manage_providers_menu():
    """Handles the provider management submenu."""
    while True:
        _display_provider_status()
        print("\nProvider Management Menu:")
        print("1. Enable Provider")
        print("2. Disable Provider")
        print("0. Back to Main Menu")

        try:
            choice = typer.prompt("Enter choice", type=int)
        except typer.Abort:
            print("\nReturning to main menu.")
            break

        if choice == 1:
            provider_name = _prompt_for_provider_name()
            if provider_name:
                success, message = provider_logic.enable_provider(provider_name)
                print(message) # Print success or error message from core logic
                typer.pause("Press Enter to continue...") # Pause to allow reading the message
        elif choice == 2:
            provider_name = _prompt_for_provider_name()
            if provider_name:
                success, message = provider_logic.disable_provider(provider_name)
                print(message)
                typer.pause("Press Enter to continue...")
        elif choice == 0:
            break
        else:
            print("Invalid choice.")


def _display_model_status(provider_name: str):
    """Displays the status of py_models for a given provider."""
    print(f"\n--- Model Status for Provider: {provider_name} ---")
    models = model_logic.get_models_from_provider(provider_name)
    if not models:
        print(f"No py_models found or configuration error for provider '{provider_name}'.")
    else:
        for model in models:
            name = model.get('name', 'N/A')
            enabled = model.get('enabled', True) # Default to True if key missing
            status = "Enabled" if enabled else "Disabled"
            print(f"  - {name} ({status})")
    print("---------------------------------------")

def _prompt_for_model_name(provider_name: str) -> Optional[str]:
    """Prompts the user for a model name within a provider."""
    models = model_logic.get_models_from_provider(provider_name)
    model_names = [m.get('name') for m in models if m.get('name')]
    if not model_names:
        print(f"No py_models found for provider '{provider_name}'.")
        return None

    print(f"Models available for '{provider_name}': {', '.join(model_names)}")
    try:
        model_name = typer.prompt("Enter model name (or leave blank to cancel)", default="", show_default=False)
        return model_name.strip() if model_name else None
    except typer.Abort:
        print("\nOperation cancelled.")
        return None


def _manage_llm_models_menu(): # Renamed function
    """Handles the LLM model management submenu."""
    provider_name = _prompt_for_provider_name()
    if not provider_name:
        return # User cancelled selecting provider

    while True:
        _display_model_status(provider_name) # This function name is still okay
        print(f"\nLLM Model Management Menu ({provider_name}):") # Updated text
        print("1. Enable LLM Model") # Updated text
        print("2. Disable LLM Model") # Updated text
        print("0. Back to Main Menu")

        try:
            choice = typer.prompt("Enter choice", type=int)
        except typer.Abort:
            print("\nReturning to main menu.")
            break

        if choice == 1:
            model_name = _prompt_for_model_name(provider_name) # This function name is still okay
            if model_name:
                success, message = model_logic.set_model_enabled_status(provider_name, model_name, enabled=True)
                print(message)
                typer.pause("Press Enter to continue...")
        elif choice == 2:
            model_name = _prompt_for_model_name(provider_name) # This function name is still okay
            if model_name:
                success, message = model_logic.set_model_enabled_status(provider_name, model_name, enabled=False)
                print(message)
                typer.pause("Press Enter to continue...")
        elif choice == 0:
            break
        else:
            print("Invalid choice.")


def _configure_keys_interactive():
    """Runs the interactive key configuration."""
    print("\n--- Configure API Keys ---")
    # The core logic function already handles the interaction
    success, _ = config_logic.check_and_configure_api_keys(prompt_user=True)
    if not success:
        print("API key configuration cancelled or failed.")
    typer.pause("Press Enter to continue...")


def _run_tests_interactive():
    """Handles running tests interactively."""
    print("\n--- Run Tests ---")

    # Get available providers to show user
    available_providers = provider_logic.get_available_providers_from_factory()
    if not available_providers:
        print("Error: No providers are enabled or available. Cannot run tests.")
        typer.pause("Press Enter to continue...")
        return

    try:
        # 1. Select Providers
        print(f"Available enabled providers: {', '.join(available_providers)}")
        providers_str = typer.prompt(
            "Enter providers to test (comma-separated, leave blank for all enabled)",
            default="", show_default=False
        )
        selected_providers: Optional[List[str]] = [p.strip() for p in providers_str.split(',') if p.strip()] or None

        # 2. Select Models (Optional Overrides)
        selected_models_list: List[str] = []
        while True:
            add_model = typer.confirm("Specify a model override? (e.g., use 'gpt-4o' for openai)", default=False)
            if not add_model:
                break
            model_spec = typer.prompt("Enter model override (format: provider:model_name or provider/model_name)")
            if model_spec:
                # Basic validation - could enhance later
                if ':' not in model_spec and '/' not in model_spec:
                     print("Invalid format. Use 'provider:model_name' or 'provider/model_name'.")
                     continue
                selected_models_list.append(model_spec)

        # 3. Optimize?
        optimize = typer.confirm("Run with prompt optimization?", default=False)

        # 4. Output Format
        json_output = typer.confirm("Output results as JSON instead of Markdown report?", default=False)

        # 5. Output File?
        output_file = typer.prompt(
            "Enter output file path (leave blank to print to console)",
            default="", show_default=False
        )
        output_file = output_file.strip() or None

        # TODO: Add prompt for test_dir and filter if needed

        print("\nStarting test run...")
        # Parse model overrides from the list collected
        model_overrides = test_runner_logic.parse_model_overrides(selected_models_list)

        success = test_runner_logic.run_test_suite(
            providers=selected_providers, # None means use defaults from factory
            model_overrides=model_overrides,
            test_dir=None, # Not prompting for this yet
            output_file=output_file,
            output_json=json_output,
            optimize=optimize,
            test_filter=None # Not prompting for this yet
        )

        if not success:
            print("Test run encountered an error.")
        # Success message/output handled by run_test_suite

    except typer.Abort:
        print("\nTest run cancelled.")

    typer.pause("Press Enter to continue...")


# --- Interactive Scaffolding Functions ---

def _scaffold_provider_interactive():
    """Handles interactive provider scaffolding."""
    print("\n--- Scaffold New Provider ---")
    try:
        provider_name = typer.prompt("Enter the name of the new provider")
        if not provider_name:
            print("Provider name cannot be empty. Aborting.")
            typer.pause("Press Enter to continue...")
            return

        # Determine the base directory for providers (same logic as scaffold.py)
        _current_file_dir = os.path.dirname(os.path.abspath(__file__))
        _cli_dir = os.path.dirname(_current_file_dir) # Go up one level to src/cli
        _llm_tester_dir = os.path.dirname(_cli_dir) # Go up another level to src
        base_dir = os.path.join(_llm_tester_dir, "llms")

        success, message = scaffold_provider_files(provider_name, base_dir)
        print(message)

        if success:
            # Attempt to enable the newly scaffolded provider in the config
            enable_success, enable_message = provider_logic.enable_provider(provider_name)
            if enable_success:
                print(f"Provider '{provider_name}' automatically enabled.")
            else:
                print(f"Warning: Could not automatically enable provider '{provider_name}'. {enable_message}")
                print("You may need to manually enable it using the 'Manage Providers' menu.")

    except typer.Abort:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"An unexpected error occurred during provider scaffolding: {e}")

    typer.pause("Press Enter to continue...")


def _scaffold_model_interactive():
    """Handles interactive model scaffolding."""
    print("\n--- Scaffold New Model ---")
    try:
        model_name = typer.prompt("Enter the name of the new model")
        if not model_name:
            print("Model name cannot be empty. Aborting.")
            typer.pause("Press Enter to continue...")
            return

        path = typer.prompt("Enter the directory to create the model in (default: ./py_models)", default="./py_models")

        # Call the core scaffolding logic
        success, message = scaffold_model_files(model_name, path)
        print(message)

        if success:
             # Note: Models are not automatically enabled in a central config like providers.
             # They are discovered based on the test_dir. No config update needed here.
             pass # Explicitly do nothing for model config update

    except typer.Abort:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"An unexpected error occurred during model scaffolding: {e}")

    typer.pause("Press Enter to continue...")


# --- Interactive Py Model Management ---

def _display_py_model_status():
    """Displays the current py model status from config."""
    print("\n--- Py Model Status ---")
    config_manager = ConfigManager() # Create an instance of ConfigManager
    py_models = config_manager.get_py_models()

    if not py_models:
        print("No py models registered in config.")
        # Also mention discovering models from directories?
        print("(Note: Py models in configured test directories are discovered automatically for runs,")
        print(" but registration here allows enabling/disabling specific ones.)")
        return

    sorted_models = sorted(py_models.keys())
    for model_name in sorted_models:
        config = py_models[model_name]
        enabled = config.get("enabled", True) # Default to True if key missing
        status = "Enabled" if enabled else "Disabled"
        print(f"  - {model_name} ({status})")
    print("-----------------------")

def _prompt_for_py_model_name() -> Optional[str]:
    """Prompts the user to enter a py model name, showing registered ones."""
    config_manager = ConfigManager() # Create an instance of ConfigManager
    py_models = config_manager.get_py_models()
    model_names = list(py_models.keys())

    if not model_names:
        print("No py models registered in config.")
        return None

    print(f"Registered py models: {', '.join(model_names)}")
    try:
        model_name = typer.prompt("Enter py model name (or leave blank to cancel)", default="", show_default=False)
        return model_name.strip() if model_name else None
    except typer.Abort:
        print("\nOperation cancelled.")
        return None


def _manage_py_models_menu():
    """Handles the py model management submenu."""
    while True:
        _display_py_model_status()
        print("\nPy Model Management Menu:")
        print("1. Enable Py Model")
        print("2. Disable Py Model")
        print("0. Back to Main Menu")

        try:
            choice = typer.prompt("Enter choice", type=int)
        except typer.Abort:
            print("\nReturning to main menu.")
            break

        config_manager = ConfigManager() # Create an instance of ConfigManager

        if choice == 1:
            model_name = _prompt_for_py_model_name()
            if model_name:
                if config_manager.set_py_model_enabled_status(model_name, enabled=True):
                    print(f"Py model '{model_name}' enabled.")
                else:
                    print(f"Error: Py model '{model_name}' not found in config.")
                typer.pause("Press Enter to continue...")
        elif choice == 2:
            model_name = _prompt_for_py_model_name()
            if model_name:
                if config_manager.set_py_model_enabled_status(model_name, enabled=False):
                    print(f"Py model '{model_name}' disabled.")
                else:
                    print(f"Error: Py model '{model_name}' not found in config.")
                typer.pause("Press Enter to continue...")
        elif choice == 0:
            break
        else:
            print("Invalid choice.")


def _manage_schemas_menu():
    """Placeholder for schema management submenu."""
    print("\nManage Schemas (Not Yet Implemented)")
    # TODO: Call schema_logic.get_discovered_schemas() to list
    # TODO: Add options like 'create', 'validate' later?
    typer.pause("Press Enter to continue...")


def _get_recommendation_interactive():
    """Handles getting model recommendations interactively."""
    print("\n--- Get Model Recommendation ---")
    try:
        task_description = typer.prompt(
            "Describe the task you need the model for (e.g., 'summarize long articles cheaply', 'generate creative Python code')",
            type=str
        )
        if not task_description:
            print("Task description cannot be empty. Aborting.")
            typer.pause("Press Enter to continue...")
            return

        print("\nGenerating recommendation (this may take a moment)...")
        success, message = recommend_logic.get_recommendation(task_description)

        if success:
            print("\n--- LLM Recommendation ---")
            print(message)
            print("--------------------------")
        else:
            print(f"\nError: {message}")

    except typer.Abort:
        print("\nOperation cancelled.")

    typer.pause("Press Enter to continue...")


# --- Main Interactive Loop ---

def start_interactive_session():
    """
    Launches the main interactive command-line session.
    """
    # Ensure config is loaded and default is created if necessary.
    # Built-in py models are now registered during ConfigManager initialization.
    config_manager = ConfigManager()

    # Discover built-in py models and register them if not in config
    # note that built-in models are usually coming from both sources
    builtin_models = _discover_builtin_py_models()
    registered_models = config_manager.get_py_models()

    for model_name in builtin_models:
        if model_name not in registered_models:
            print(f"DEBUG: Registering built-in py model '{model_name}' in config.") # <-- Debug print
            config_manager.register_py_model(model_name, {"enabled": True}) # Register and enable by default

    print("\nWelcome to the LLM Tester Interactive Session!")
    print("---------------------------------------------")

    while True:
        print("\nMain Menu:")
        print("1. Manage Providers (& their LLM Models)")
        print("2. Manage Extraction Schemas")
        print("3. Configure API Keys")
        print("4. Run Tests")
        print("5. Get Model Recommendation")
        print("6. Scaffold New Provider")
        print("7. Scaffold New Model")
        print("8. Manage Py Models") # New menu item
        print("0. Exit")

        try:
            choice = typer.prompt("Enter choice", type=int)
        except typer.Abort:
            print("\nExiting interactive session.")
            break # Exit on Ctrl+C

        if choice == 1:
            _manage_providers_menu()
        elif choice == 2:
            _manage_schemas_menu()
        elif choice == 3:
            _configure_keys_interactive()
        elif choice == 4:
            _run_tests_interactive()
        elif choice == 5:
            _get_recommendation_interactive()
        elif choice == 6:
            _scaffold_provider_interactive()
        elif choice == 7:
            _scaffold_model_interactive()
        elif choice == 8: # Handle new menu item
            _manage_py_models_menu()
        elif choice == 0:
            print("Exiting interactive session.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    # Allows testing the interactive UI directly (optional)
    start_interactive_session()
