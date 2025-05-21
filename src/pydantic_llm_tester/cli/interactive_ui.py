import logging
import typer
import os # Added import
from typing import Any, Dict, List, Optional, Tuple

# Import core logic functions that the UI will call
from pydantic_llm_tester.cli.core import config_logic, test_runner_logic, recommend_logic
from pydantic_llm_tester.cli.core import provider_logic, llm_model_logic as model_logic
from pydantic_llm_tester.cli.core import model_config_logic
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

    print("(Status based on pyllm_config.json)") # Updated message

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


def _manage_llm_models_config_menu():
    """Handles the LLM model configuration submenu."""
    provider_name = _prompt_for_provider_name()
    if not provider_name:
        return  # User cancelled selecting provider

    while True:
        print(f"\nLLM Model Configuration Menu ({provider_name}):")
        print("1. List Models")
        print("2. Add New Model")
        print("3. Edit Existing Model")
        print("4. Remove Model")
        print("5. Set Default Model")
        print("0. Back to Main Menu")

        try:
            choice = typer.prompt("Enter choice", type=int)
        except typer.Abort:
            print("\nReturning to main menu.")
            break

        if choice == 1:
            # List models
            config_data = model_config_logic.get_provider_config(provider_name)
            if not config_data:
                print(f"Error: Could not load configuration for provider '{provider_name}'.")
                typer.pause("Press Enter to continue...")
                continue

            models = config_data.get("llm_models", [])
            if not models:
                print(f"No models found for provider '{provider_name}'.")
                typer.pause("Press Enter to continue...")
                continue

            print(f"\nModels for provider '{provider_name}':")
            for model in models:
                name = model.get("name", "N/A")
                default = "Default" if model.get("default", False) else ""
                preferred = "Preferred" if model.get("preferred", False) else ""
                enabled = "Enabled" if model.get("enabled", True) else "Disabled"
                
                status = []
                if default:
                    status.append(default)
                if preferred:
                    status.append(preferred)
                status.append(enabled)
                
                print(f"  - {name} ({', '.join(status)})")
                print(f"    Cost: ${model.get('cost_input', 0.0)}/1M input tokens, ${model.get('cost_output', 0.0)}/1M output tokens ({model.get('cost_category', 'standard')})")
                print(f"    Max tokens: {model.get('max_input_tokens', 'N/A')} input, {model.get('max_output_tokens', 'N/A')} output")
            
            typer.pause("Press Enter to continue...")

        elif choice == 2:
            # Add new model
            print("\n--- Add New Model ---")
            
            # Get model name
            model_name = typer.prompt("Enter model name")
            if not model_name:
                print("Model name cannot be empty.")
                typer.pause("Press Enter to continue...")
                continue
            
            # Check if model already exists
            existing_model = model_config_logic.get_model_from_provider(provider_name, model_name)
            if existing_model:
                print(f"Model '{model_name}' already exists for provider '{provider_name}'.")
                typer.pause("Press Enter to continue...")
                continue
            
            # Get model configuration
            _, model_config = _prompt_for_model_config(provider_name, None, model_name)
            
            # Add model to provider
            success, message = model_config_logic.add_model_to_provider(provider_name, model_name, model_config)
            
            # If model is set as default, update other models
            if success and model_config.get("default", False):
                default_success, default_message = model_config_logic.set_default_model(provider_name, model_name)
                if not default_success:
                    print(f"Warning: {default_message}")
            
            print(message)
            typer.pause("Press Enter to continue...")

        elif choice == 3:
            # Edit existing model
            print("\n--- Edit Existing Model ---")
            
            # Get model name
            model_name = _prompt_for_model_name(provider_name)
            if not model_name:
                continue
            
            # Get current model config
            current_config = model_config_logic.get_model_from_provider(provider_name, model_name)
            if not current_config:
                print(f"Error: Model '{model_name}' not found in provider '{provider_name}'.")
                typer.pause("Press Enter to continue...")
                continue
            
            # Get updated model configuration
            _, updated_config = _prompt_for_model_config(provider_name, current_config, model_name)
            
            # Edit model in provider
            success, message = model_config_logic.edit_model_in_provider(provider_name, model_name, updated_config)
            
            # If model is set as default, update other models
            if success and updated_config.get("default", False):
                default_success, default_message = model_config_logic.set_default_model(provider_name, model_name)
                if not default_success:
                    print(f"Warning: {default_message}")
            
            print(message)
            typer.pause("Press Enter to continue...")

        elif choice == 4:
            # Remove model
            print("\n--- Remove Model ---")
            
            # Get model name
            model_name = _prompt_for_model_name(provider_name)
            if not model_name:
                continue
            
            # Confirm removal
            confirm = typer.confirm(f"Are you sure you want to remove model '{model_name}' from provider '{provider_name}'?")
            if not confirm:
                print("Operation cancelled.")
                typer.pause("Press Enter to continue...")
                continue
            
            # Remove model from provider
            success, message = model_config_logic.remove_model_from_provider(provider_name, model_name)
            print(message)
            typer.pause("Press Enter to continue...")

        elif choice == 5:
            # Set default model
            print("\n--- Set Default Model ---")
            
            # Get model name
            model_name = _prompt_for_model_name(provider_name)
            if not model_name:
                continue
            
            # Set model as default
            success, message = model_config_logic.set_default_model(provider_name, model_name)
            print(message)
            typer.pause("Press Enter to continue...")

        elif choice == 0:
            break
        else:
            print("Invalid choice.")


def _prompt_for_model_config(provider_name: str, current_config: Optional[Dict[str, Any]], model_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Prompt the user for model configuration values.
    
    Args:
        provider_name: The name of the provider.
        current_config: The current model configuration, if editing an existing model.
        model_name: Optional model name if already known.
        
    Returns:
        Tuple of (model_name, model_config).
    """
    is_edit = current_config is not None
    action = "Editing" if is_edit else "Adding"
    
    print(f"\n--- {action} Model for Provider: {provider_name} ---")
    
    # Start with template or current config
    if is_edit:
        model_config = current_config.copy()
        default_name = model_config.get("name", "")
    else:
        model_config = model_config_logic.get_model_template()
        default_name = model_name or ""
    
    # Prompt for values
    if not model_name:
        model_name = typer.prompt("Model name", default=default_name)
    
    # For editing, show current values as defaults
    if is_edit:
        model_config["default"] = typer.confirm(
            "Set as default model?",
            default=model_config.get("default", False)
        )
        model_config["preferred"] = typer.confirm(
            "Mark as preferred model?",
            default=model_config.get("preferred", False)
        )
        model_config["enabled"] = typer.confirm(
            "Enable model?",
            default=model_config.get("enabled", True)
        )
        model_config["cost_input"] = typer.prompt(
            "Cost per 1M input tokens (USD)",
            default=model_config.get("cost_input", 0.0),
            type=float
        )
        model_config["cost_output"] = typer.prompt(
            "Cost per 1M output tokens (USD)",
            default=model_config.get("cost_output", 0.0),
            type=float
        )
        
        # For cost category, show options
        print("\nCost categories:")
        print("1. cheap")
        print("2. standard")
        print("3. expensive")
        
        current_category = model_config.get("cost_category", "standard")
        category_map = {"1": "cheap", "2": "standard", "3": "expensive"}
        category_default = next((k for k, v in category_map.items() if v == current_category), "2")
        
        category_choice = typer.prompt(
            "Select cost category",
            default=category_default
        )
        model_config["cost_category"] = category_map.get(category_choice, "standard")
        
        model_config["max_input_tokens"] = typer.prompt(
            "Maximum input tokens",
            default=model_config.get("max_input_tokens", 4096),
            type=int
        )
        model_config["max_output_tokens"] = typer.prompt(
            "Maximum output tokens",
            default=model_config.get("max_output_tokens", 4096),
            type=int
        )
    else:
        # For new models, don't show defaults
        model_config["default"] = typer.confirm("Set as default model?")
        model_config["preferred"] = typer.confirm("Mark as preferred model?")
        model_config["enabled"] = typer.confirm("Enable model?", default=True)
        model_config["cost_input"] = typer.prompt("Cost per 1M input tokens (USD)", type=float)
        model_config["cost_output"] = typer.prompt("Cost per 1M output tokens (USD)", type=float)
        
        # For cost category, show options
        print("\nCost categories:")
        print("1. cheap")
        print("2. standard")
        print("3. expensive")
        
        category_choice = typer.prompt("Select cost category", default="2")
        category_map = {"1": "cheap", "2": "standard", "3": "expensive"}
        model_config["cost_category"] = category_map.get(category_choice, "standard")
        
        model_config["max_input_tokens"] = typer.prompt("Maximum input tokens", default=4096, type=int)
        model_config["max_output_tokens"] = typer.prompt("Maximum output tokens", default=4096, type=int)
    
    return model_name, model_config


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
        print("1. Manage Providers")
        print("2. Manage Extraction Schemas")
        print("3. Configure API Keys")
        print("4. Run Tests")
        print("5. Get Model Recommendation")
        print("6. Scaffold New Provider")
        print("7. Scaffold New Model")
        print("8. Manage Py Models")
        print("9. Manage LLM Models") # New menu item for model configuration
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
        elif choice == 8:
            _manage_py_models_menu()
        elif choice == 9: # Handle new menu item for model configuration
            _manage_llm_models_config_menu()
        elif choice == 0:
            print("Exiting interactive session.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    # Allows testing the interactive UI directly (optional)
    start_interactive_session()
