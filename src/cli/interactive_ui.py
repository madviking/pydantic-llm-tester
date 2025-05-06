import logging
import typer
import os # Added import
from typing import List, Dict, Optional

# Import core logic functions that the UI will call
from src.cli.core import provider_logic, llm_model_logic as model_logic, config_logic, test_runner_logic, recommend_logic # Renamed import

logger = logging.getLogger(__name__)

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
    print("\nWelcome to the LLM Tester Interactive Session!")
    print("---------------------------------------------")

    while True:
        print("\nMain Menu:")
        print("1. Manage Providers (& their LLM Models)") # Clarified menu item
        print("2. Manage Extraction Schemas") # New menu item
        print("3. Configure API Keys")
        print("4. Run Tests")
        print("5. Get Model Recommendation")
        print("0. Exit")

        try:
            choice = typer.prompt("Enter choice", type=int)
        except typer.Abort:
            print("\nExiting interactive session.")
            break # Exit on Ctrl+C

        if choice == 1:
            _manage_providers_menu() # This now implicitly includes LLM model management via its submenu logic
        elif choice == 2:
            _manage_schemas_menu() # Call the new placeholder
        elif choice == 3:
            _configure_keys_interactive()
        elif choice == 4:
            _run_tests_interactive()
        elif choice == 5:
            _get_recommendation_interactive()
        elif choice == 0:
            print("Exiting interactive session.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    # Allows testing the interactive UI directly (optional)
    start_interactive_session()
