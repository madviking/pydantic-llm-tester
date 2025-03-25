"""Menu handlers for the interactive runner"""

import os
import sys
import importlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Tuple
from unittest.mock import patch

from llm_tester import LLMTester
from .config import load_config, save_config, check_api_keys, load_env_file
from .ui import clear_screen, print_header

# Import utilities from the main package
from llm_tester.utils.provider_manager import ProviderManager
from llm_tester.utils.cost_manager import cost_tracker

# Import mock responses
from llm_tester.utils.mock_responses import mock_get_response

def check_setup():
    """Check if the environment is properly set up"""
    clear_screen()
    print_header("Environment Setup Check")
    
    # Check for required packages
    print("Checking required packages...")
    required_packages = ['pydantic', 'dotenv', 'openai', 'anthropic', 'mistralai']
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ✗ {package} - not found")
    
    if missing_packages:
        print("\n📦 Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        
        install = input("\nDo you want to install the missing packages? (y/n): ").strip().lower()
        if install == 'y':
            for package in missing_packages:
                os.system(f"pip install {package}")
                print(f"Installed {package}")
    
    # Load environment variables
    print("\nChecking environment variables...")
    loaded = load_env_file()
    
    # Check API keys
    api_keys = check_api_keys()
    available_providers = [provider for provider, info in api_keys.items() if info["available"]]
    
    print("\n🔑 API Key Status:")
    for provider, info in api_keys.items():
        if info["available"]:
            print(f"  ✓ {provider:<10} - API key found and valid")
        else:
            if provider == "google":
                if info["missing"]:
                    print(f"  ✗ {provider:<10} - Missing: {', '.join(info['missing'])}")
                elif info["status"] == "invalid":
                    print(f"  ✗ {provider:<10} - Error: {info.get('error', 'Invalid configuration')}")
            else:
                print(f"  ✗ {provider:<10} - API key missing")
    
    print("\n📝 Summary:")
    if not available_providers:
        print("  - No API keys found. You can still use the mock provider for testing.")
        print("  - To use real providers, add your API keys to a .env file in the project root.")
        print("\nRequired environment variables:")
        print("  OPENAI_API_KEY=your_openai_key")
        print("  ANTHROPIC_API_KEY=your_anthropic_key")
        print("  MISTRAL_API_KEY=your_mistral_key")
        print("  GOOGLE_PROJECT_ID=your_google_project_id")
        print("  GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json")
    else:
        print(f"  - {len(available_providers)} of {len(api_keys)} providers configured correctly")
        print(f"  - Available providers: {', '.join(available_providers)}")
        
        if len(available_providers) < len(api_keys):
            print("\nMissing API keys:")
            for provider, info in api_keys.items():
                if not info["available"]:
                    if provider == "google":
                        for key in info["missing"]:
                            print(f"  {key}=your_{key.lower()}")
                    else:
                        print(f"  {info['key_name']}=your_{provider.lower()}_key")
    
    input("\nPress Enter to continue...")

def list_test_cases(tester: LLMTester):
    """List all available test cases"""
    clear_screen()
    print_header("Available Test Cases")
    
    test_cases = tester.discover_test_cases()
    
    if not test_cases:
        print("No test cases found.")
        return
    
    # Group by module
    grouped_cases = {}
    for test_case in test_cases:
        module = test_case['module']
        if module not in grouped_cases:
            grouped_cases[module] = []
        grouped_cases[module].append(test_case)
    
    for module, cases in grouped_cases.items():
        print(f"\n[{module}]")
        for i, case in enumerate(cases, 1):
            print(f"  {i}. {case['name']}")
    
    print("\nTotal test cases: ", len(test_cases))
    input("\nPress Enter to return to the main menu...")

def select_modules_to_test(tester: LLMTester) -> List[str]:
    """Allow the user to select which modules to test"""
    clear_screen()
    print_header("Select Modules to Test")
    
    # Load config for default modules
    config = load_config()
    test_settings = config.get("test_settings", {})
    default_modules = test_settings.get("default_modules", [])
    
    # Get all available modules
    test_cases = tester.discover_test_cases()
    available_modules = sorted(set(case['module'] for case in test_cases))
    
    print("Available modules:")
    for i, module in enumerate(available_modules, 1):
        is_default = module in default_modules
        default_str = " (default)" if is_default else ""
        print(f"  {i}. {module}{default_str}")
    
    print("\nSelect modules to test:")
    print("1. All modules")
    print("2. Default modules only")
    print("3. Custom selection")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        return available_modules
    elif choice == "2":
        if not default_modules:
            print("\nNo default modules configured. Using all modules.")
            return available_modules
        return default_modules
    elif choice == "3":
        # Custom selection
        selected_modules = []
        print("\nEnter module numbers separated by commas (e.g., '1,3'), or leave empty to select all:")
        selection = input("> ").strip()
        
        if not selection:
            return available_modules
        
        try:
            selected_indices = [int(idx.strip()) for idx in selection.split(",")]
            selected_modules = [available_modules[idx-1] for idx in selected_indices 
                              if 0 < idx <= len(available_modules)]
            
            if not selected_modules:
                print("\nNo valid modules selected. Using all modules.")
                return available_modules
            
            # Ask if user wants to save this as the default selection
            save_as_default = input("\nSave this selection as default? (y/n): ").strip().lower()
            if save_as_default == 'y':
                if "test_settings" not in config:
                    config["test_settings"] = {}
                config["test_settings"]["default_modules"] = selected_modules
                save_config(config)
                print(f"Default modules updated: {', '.join(selected_modules)}")
            
            return selected_modules
        except (ValueError, IndexError):
            print("\nInvalid selection. Using all modules.")
            return available_modules
    else:
        print("\nInvalid choice. Using all modules.")
        return available_modules

def setup_providers() -> List[str]:
    """Setup which providers to use"""
    clear_screen()
    print_header("Setup Providers")
    
    # Load configuration
    config = load_config()
    
    # Check API keys
    api_keys = check_api_keys()
    
    print("Provider Status:")
    for provider, info in api_keys.items():
        # Get config
        provider_config = config.get("providers", {}).get(provider, {"enabled": False})
        enabled = provider_config.get("enabled", False)
        model = provider_config.get("default_model", "default")
        
        # Get status
        if info["available"]:
            status = "✓ API key found and valid"
        else:
            if provider == "google" and info["missing"]:
                status = f"✗ Missing: {', '.join(info['missing'])}"
            elif provider == "google" and info["status"] == "invalid":
                status = f"✗ {info.get('error', 'Invalid configuration')}"
            else:
                status = "✗ API key missing"
        
        # Display status
        enabled_str = "Enabled" if enabled else "Disabled"
        print(f"  {provider:<10} - [{enabled_str}] {status} (Model: {model})")
    
    print("\nChoose action:")
    print("1. Use providers as configured")
    print("2. Enable/disable specific providers")
    print("3. Use all providers with valid API keys")
    print("4. Use only OpenAI")
    print("5. Use only Anthropic")
    print("6. Use mock provider (no API keys needed)")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    available_providers = [p for p, info in api_keys.items() if info["available"]]
    enabled_providers = [p for p, conf in config.get("providers", {}).items() 
                        if conf.get("enabled", False)]
    
    if choice == '1':
        # Use as configured, but validate that API keys exist
        selected = []
        for provider in enabled_providers:
            if provider == "mock_provider" or provider.startswith("mock_"):
                selected.append(provider)
            elif provider in api_keys and api_keys[provider]["available"]:
                selected.append(provider)
            else:
                print(f"\nWarning: Provider '{provider}' is enabled but has no valid API key.")
                use_anyway = input(f"Do you want to use {provider} anyway? (y/n): ").strip().lower()
                if use_anyway == 'y':
                    selected.append(provider)
        
        if not selected:
            print("No valid providers selected. Defaulting to mock provider.")
            selected = ["mock_provider"]
            
            # Update config
            if "mock_provider" in config.get("providers", {}):
                config["providers"]["mock_provider"]["enabled"] = True
            else:
                if "providers" not in config:
                    config["providers"] = {}
                config["providers"]["mock_provider"] = {"enabled": True, "default_model": "mock-model"}
            save_config(config)
        
        # Initialize provider manager to check for any initialization issues
        if selected and selected != ["mock_provider"]:
            temp_manager = ProviderManager(selected)
            if hasattr(temp_manager, 'initialization_errors') and temp_manager.initialization_errors:
                print("\nWarning: Some providers had initialization issues:")
                for provider, error in temp_manager.initialization_errors.items():
                    if provider in selected:
                        print(f"  - {provider}: {error}")
                        
                print("\nWould you like to continue with these providers? (y/n)")
                continue_anyway = input("> ").strip().lower()
                if continue_anyway != 'y':
                    print("Using mock provider instead.")
                    selected = ["mock_provider"]
                    
                    # Update config
                    if "mock_provider" in config.get("providers", {}):
                        config["providers"]["mock_provider"]["enabled"] = True
                    else:
                        if "providers" not in config:
                            config["providers"] = {}
                        config["providers"]["mock_provider"] = {"enabled": True, "default_model": "mock-model"}
                    save_config(config)
        
        return selected
        
    elif choice == '2':
        # Enable/disable specific providers
        for provider in sorted(config.get("providers", {}).keys()):
            current = "enabled" if config["providers"][provider]["enabled"] else "disabled"
            toggle = input(f"{provider} is currently {current}. Toggle? (y/n): ").strip().lower()
            if toggle == 'y':
                config["providers"][provider]["enabled"] = not config["providers"][provider]["enabled"]
        
        # Save updated config
        save_config(config)
        
        # Return enabled providers
        enabled_providers = [p for p, conf in config.get("providers", {}).items() 
                            if conf.get("enabled", False)]
        
        # Validate that API keys exist
        selected = []
        for provider in enabled_providers:
            if provider == "mock_provider" or provider.startswith("mock_"):
                selected.append(provider)
            elif provider in api_keys and api_keys[provider]["available"]:
                selected.append(provider)
            else:
                print(f"\nWarning: Provider '{provider}' is enabled but has no valid API key.")
                use_anyway = input(f"Do you want to use {provider} anyway? (y/n): ").strip().lower()
                if use_anyway == 'y':
                    selected.append(provider)
        
        if not selected:
            print("No valid providers selected. Defaulting to mock provider.")
            selected = ["mock_provider"]
            
            # Update config
            if "mock_provider" in config.get("providers", {}):
                config["providers"]["mock_provider"]["enabled"] = True
            else:
                if "providers" not in config:
                    config["providers"] = {}
                config["providers"]["mock_provider"] = {"enabled": True, "default_model": "mock-model"}
            save_config(config)
        
        return selected
        
    elif choice == '3':
        # Use all providers with valid API keys
        if not available_providers:
            print("\nNo valid API keys found. Defaulting to mock provider.")
            selected = ["mock_provider"]
        else:
            selected = available_providers
            
        # Update config to match selection
        for provider in config.get("providers", {}):
            config["providers"][provider]["enabled"] = (provider in selected)
        
        # Make sure mock_provider exists in config
        if "mock_provider" not in config.get("providers", {}):
            if "providers" not in config:
                config["providers"] = {}
            config["providers"]["mock_provider"] = {
                "enabled": "mock_provider" in selected,
                "default_model": "mock-model"
            }
            
        save_config(config)
        return selected
        
    elif choice == '4':
        # OpenAI only
        if api_keys["openai"]["available"]:
            selected = ["openai"]
        else:
            print("\nOpenAI API key not available. Using mock instead.")
            selected = ["mock_openai"]
            
        # Update config
        for provider in config.get("providers", {}):
            config["providers"][provider]["enabled"] = (provider in selected)
            
        save_config(config)
        return selected
        
    elif choice == '5':
        # Anthropic only
        if api_keys["anthropic"]["available"]:
            selected = ["anthropic"]
        else:
            print("\nAnthropic API key not available. Using mock instead.")
            selected = ["mock_anthropic"]
            
        # Update config
        for provider in config.get("providers", {}):
            config["providers"][provider]["enabled"] = (provider in selected)
            
        save_config(config)
        return selected
        
    elif choice == '6':
        # Mock provider only
        selected = ["mock_provider"]
        
        # Update config
        for provider in config.get("providers", {}):
            config["providers"][provider]["enabled"] = (provider in selected)
            
        # Make sure mock_provider exists in config
        if "mock_provider" not in config.get("providers", {}):
            if "providers" not in config:
                config["providers"] = {}
            config["providers"]["mock_provider"] = {"enabled": True, "default_model": "mock-model"}
            
        save_config(config)
        return selected
        
    else:
        print("Invalid choice. Using providers as configured.")
        
        # Use as configured, but validate that API keys exist
        selected = []
        for provider in enabled_providers:
            if provider == "mock_provider" or provider.startswith("mock_"):
                selected.append(provider)
            elif provider in api_keys and api_keys[provider]["available"]:
                selected.append(provider)
        
        if not selected:
            print("No valid providers selected. Defaulting to mock provider.")
            selected = ["mock_provider"]
            
            # Update config
            if "mock_provider" in config.get("providers", {}):
                config["providers"]["mock_provider"]["enabled"] = True
            else:
                if "providers" not in config:
                    config["providers"] = {}
                config["providers"]["mock_provider"] = {"enabled": True, "default_model": "mock-model"}
            save_config(config)
        
        return selected

def setup_models(providers: List[str]) -> Dict[str, str]:
    """Setup which models to use for each provider"""
    clear_screen()
    print_header("Setup Models")
    
    # Load configuration
    config = load_config()
    models = {}
    
    print("Current provider models:")
    for provider in providers:
        provider_config = config.get("providers", {}).get(provider, {})
        default_model = provider_config.get("default_model", "default")
        print(f"  {provider:<10} - Current model: {default_model}")
    
    customize = input("\nDo you want to customize the models? (y/n): ").strip().lower()
    
    if customize != 'y':
        # Return models from config
        for provider in providers:
            provider_config = config.get("providers", {}).get(provider, {})
            if "default_model" in provider_config:
                models[provider] = provider_config["default_model"]
        return models
    
    # Update models
    for provider in providers:
        provider_config = config.get("providers", {}).get(provider, {})
        default_model = provider_config.get("default_model", "default")
        
        model = input(f"Enter model for {provider} (default: {default_model}): ").strip()
        
        if model:
            models[provider] = model
            
            # Update config
            if "providers" not in config:
                config["providers"] = {}
            if provider not in config["providers"]:
                config["providers"][provider] = {}
            
            config["providers"][provider]["default_model"] = model
    
    # Save configuration
    save_config(config)
    
    return models

def run_tests(tester: LLMTester, providers: List[str], models: Dict[str, str] = None, optimize: bool = False):
    """Run tests with the given configuration"""
    clear_screen()
    print_header("Running Tests" + (" (Optimized)" if optimize else ""))
    
    # Load configuration
    config = load_config()
    test_settings = config.get("test_settings", {})
    default_output_dir = test_settings.get("output_dir", "test_results")
    
    # Let the user select which modules to test
    selected_modules = select_modules_to_test(tester)
    
    # Ask for output directory
    print("\nWhere would you like to save the test results?")
    print(f"1. Default directory ({default_output_dir})")
    print("2. Custom directory")
    print("3. Don't save results to file")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "2":
        output_dir = input("Enter the output directory path: ").strip()
        if not output_dir:
            output_dir = default_output_dir
    elif choice == "3":
        output_dir = None
    else:
        output_dir = default_output_dir
    
    # Create custom filename
    if output_dir:
        filename = input("\nEnter a custom filename (leave empty for timestamp-based name): ").strip()
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}{'_optimized' if optimize else ''}.md"
    
    # Check if we're using mock providers
    using_mock = any(p.startswith("mock_") for p in providers)
    
    print("\nStarting test run...")
    print(f"Providers: {', '.join(providers)}")
    if models:
        for provider, model in models.items():
            print(f"Using model for {provider}: {model}")
    print(f"Testing modules: {', '.join(selected_modules)}")
    
    # If using mock, we'll use the imported mock_get_response
    if using_mock:
        print("\nUsing mock providers. No API calls will be made.")
        
        # Get save_optimized_prompts setting from config
        config = load_config()
        test_settings = config.get("test_settings", {})
        save_optimized_prompts = test_settings.get("save_optimized_prompts", True)
        
        # Patch the get_response method
        with patch('llm_tester.utils.provider_manager.ProviderManager.get_response', mock_get_response):
            if optimize:
                # Ask if user wants to save optimized prompts
                should_save = input(f"\nSave optimized prompts to files? (y/n) [{'y' if save_optimized_prompts else 'n'}]: ").strip().lower()
                if should_save:
                    save_optimized_prompts = should_save == 'y'
                    
                    # Update config if changed
                    if save_optimized_prompts != test_settings.get("save_optimized_prompts", True):
                        if "test_settings" not in config:
                            config["test_settings"] = {}
                        config["test_settings"]["save_optimized_prompts"] = save_optimized_prompts
                        save_config(config)
                
                def progress_callback(message):
                    print(message)
                    
                results = tester.run_optimized_tests(
                    model_overrides=models,
                    save_optimized_prompts=save_optimized_prompts,
                    modules=selected_modules,
                    progress_callback=progress_callback
                )
                
                # If prompts were saved, show the paths
                if save_optimized_prompts:
                    print("\nOptimized prompts saved to:")
                    for test_id, test_results in results.items():
                        if 'optimized_prompt_path' in test_results:
                            print(f"  {test_id}: {test_results['optimized_prompt_path']}")
            else:
                def progress_callback(message):
                    print(message)
                results = tester.run_tests(
                    model_overrides=models, 
                    modules=selected_modules,
                    progress_callback=progress_callback
                )
    else:
        # Run with real providers
        print("\nSending requests to LLM providers. This may take some time...")
        
        # Get save_optimized_prompts setting from config
        config = load_config()
        test_settings = config.get("test_settings", {})
        save_optimized_prompts = test_settings.get("save_optimized_prompts", True)
        
        if optimize:
            # Ask if user wants to save optimized prompts
            should_save = input(f"\nSave optimized prompts to files? (y/n) [{'y' if save_optimized_prompts else 'n'}]: ").strip().lower()
            if should_save:
                save_optimized_prompts = should_save == 'y'
                
                # Update config if changed
                if save_optimized_prompts != test_settings.get("save_optimized_prompts", True):
                    if "test_settings" not in config:
                        config["test_settings"] = {}
                    config["test_settings"]["save_optimized_prompts"] = save_optimized_prompts
                    save_config(config)
            
            def progress_callback(message):
                print(message)
            
            results = tester.run_optimized_tests(
                model_overrides=models,
                save_optimized_prompts=save_optimized_prompts,
                modules=selected_modules,
                progress_callback=progress_callback
            )
            
            # If prompts were saved, show the paths
            if save_optimized_prompts:
                print("\nOptimized prompts saved to:")
                for test_id, test_results in results.items():
                    if 'optimized_prompt_path' in test_results:
                        print(f"  {test_id}: {test_results['optimized_prompt_path']}")
        else:
            def progress_callback(message):
                print(message)
            
            results = tester.run_tests(
                model_overrides=models, 
                modules=selected_modules,
                progress_callback=progress_callback
            )
    
    print("\nTests completed successfully!")
    
    # Generate report
    print("Generating report...")
    report_dict = tester.generate_report(results, optimized=optimize)
    
    # Extract main report
    if isinstance(report_dict, dict):
        report = report_dict.get('main', '')
    else:
        # If generate_report returned a string directly, use that
        report = report_dict
    
    # Save report to file if requested
    if output_dir and report:
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, filename)
        
        with open(report_path, "w") as f:
            f.write(report)
        
        print(f"\nReport saved to {report_path}")
        
        # Save output directory to config
        if output_dir != default_output_dir:
            if "test_settings" not in config:
                config["test_settings"] = {}
            config["test_settings"]["output_dir"] = output_dir
            save_config(config)
    
    # Print summary
    print("\nTest Summary:")
    for test_name, test_results in results.items():
        print(f"  {test_name}:")
        for provider, provider_result in test_results.items():
            if isinstance(provider_result, dict) and 'validation' in provider_result:
                validation = provider_result.get('validation', {})
                accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                model = provider_result.get('model', 'default')
                print(f"    {provider} ({model}): {accuracy:.2f}%")
            else:
                print(f"    {provider}: Results available in full report")
    
    # Save cost report
    cost_report_path = tester.save_cost_report(output_dir)
    if cost_report_path:
        print(f"\nCost report saved to {cost_report_path}")
    
    # Ask if user wants to view the report
    view_report = input("\nDo you want to view the full report? (y/n): ").strip().lower()
    if view_report == 'y':
        clear_screen()
        print_header("Test Report")
        print(report)
    
    # Ask if user wants to view the cost report
    view_cost = input("\nDo you want to view the cost summary? (y/n): ").strip().lower()
    if view_cost == 'y':
        clear_screen()
        print_header("Cost Summary")
        
        # Get cost summary
        cost_summary = cost_tracker.get_run_summary(tester.run_id)
        if cost_summary:
            print(f"Total cost: ${cost_summary.get('total_cost', 0):.6f}")
            print(f"Total tokens: {cost_summary.get('total_tokens', 0):,}")
            print(f"Prompt tokens: {cost_summary.get('prompt_tokens', 0):,}")
            print(f"Completion tokens: {cost_summary.get('completion_tokens', 0):,}")
            
            # Add model-specific costs
            print("\nModel Costs:")
            for model_name, model_data in cost_summary.get('models', {}).items():
                print(f"- {model_name}: ${model_data.get('total_cost', 0):.6f} "
                    f"({model_data.get('total_tokens', 0):,} tokens, {model_data.get('test_count', 0)} tests)")
        else:
            print("No cost data available")
    
    input("\nPress Enter to return to the main menu...")

# Define run_optimized_tests as a wrapper around run_tests
def run_optimized_tests(tester: LLMTester, providers: List[str], models: Dict[str, str] = None):
    """Run optimized tests (wrapper around run_tests)"""
    return run_tests(tester, providers, models, optimize=True)

def run_default_tests(tester: LLMTester):
    """Run tests with default settings without interactive prompting"""
    from .non_interactive import run_with_defaults
    
    clear_screen()
    print_header("Running Tests with Default Settings")
    
    print("This will run tests using all enabled providers and default settings.")
    print("No further prompts will be shown until the tests are complete.")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    # Run with defaults
    run_with_defaults()
    
    input("\nPress Enter to return to the main menu...")

def edit_configuration():
    """Edit test settings"""
    clear_screen()
    print_header("Edit Configuration")
    
    config = load_config()
    test_settings = config.get("test_settings", {})
    
    print("Current test settings:")
    print(f"  Output directory: {test_settings.get('output_dir', 'test_results')}")
    print(f"  Save optimized prompts: {test_settings.get('save_optimized_prompts', True)}")
    
    module_list = test_settings.get('default_modules', [])
    modules_str = ", ".join(module_list) if module_list else "All"
    print(f"  Default modules to test: {modules_str}")
    
    print("\nEdit settings:")
    
    # Edit output directory
    new_output_dir = input(f"Output directory [{test_settings.get('output_dir', 'test_results')}]: ")
    if new_output_dir:
        if "test_settings" not in config:
            config["test_settings"] = {}
        config["test_settings"]["output_dir"] = new_output_dir
    
    # Edit save optimized prompts
    current_save = test_settings.get('save_optimized_prompts', True)
    save_opt_prompts = input(f"Save optimized prompts (y/n) [{current_save and 'y' or 'n'}]: ")
    if save_opt_prompts and save_opt_prompts.lower() in ['y', 'n']:
        if "test_settings" not in config:
            config["test_settings"] = {}
        config["test_settings"]["save_optimized_prompts"] = (save_opt_prompts.lower() == 'y')
    
    # Edit default modules
    print("\nDefault modules to test:")
    print("Enter a comma-separated list of modules to test by default.")
    print("Leave empty to test all available modules.")
    current_modules = ", ".join(test_settings.get('default_modules', []))
    new_modules = input(f"Modules [{current_modules}]: ")
    
    if new_modules:
        module_list = [m.strip() for m in new_modules.split(',') if m.strip()]
        if "test_settings" not in config:
            config["test_settings"] = {}
        config["test_settings"]["default_modules"] = module_list
    
    # Save configuration
    save_config(config)
    print("\nConfiguration saved.")
    input("\nPress Enter to continue...")

def create_new_model(model_name=None):
    """Create scaffolding for a new model"""
    clear_screen()
    print_header("Create New Model")
    
    # Get base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Get model name if not provided
    if not model_name:
        while True:
            model_name = input("Enter name for the new model (e.g., 'product_reviews'): ").strip()
            if not model_name:
                print("Model name cannot be empty.")
                continue
                
            # Convert to snake_case if needed
            model_name = model_name.lower().replace(' ', '_').replace('-', '_')
            
            # Check if model already exists
            model_dir = os.path.join(base_dir, "models", model_name)
            if os.path.exists(model_dir):
                overwrite = input(f"Model '{model_name}' already exists. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    continue
            
            break
    else:
        # Convert provided name to snake_case
        model_name = model_name.lower().replace(' ', '_').replace('-', '_')
    
    # Get model class name (PascalCase)
    default_class_name = ''.join(word.capitalize() for word in model_name.split('_'))
    class_name = input(f"Enter model class name (default: {default_class_name}): ").strip()
    if not class_name:
        class_name = default_class_name
    
    # Get model description
    description = input("Enter a short description for the model: ").strip()
    if not description:
        description = f"Extract structured information from {model_name.replace('_', ' ')}." 
    
    # Create directory structure
    model_dir = os.path.join(base_dir, "models", model_name)
    os.makedirs(model_dir, exist_ok=True)
    
    # Create test directories
    tests_dir = os.path.join(model_dir, "tests")
    os.makedirs(os.path.join(tests_dir, "sources"), exist_ok=True)
    os.makedirs(os.path.join(tests_dir, "prompts"), exist_ok=True)
    os.makedirs(os.path.join(tests_dir, "expected"), exist_ok=True)
    os.makedirs(os.path.join(model_dir, "reports"), exist_ok=True)
    
    # Create __init__.py files
    with open(os.path.join(model_dir, "__init__.py"), "w") as f:
        f.write(f'''"""{description}"""

from .model import {class_name}

__all__ = ["{class_name}"]
''')
    
    with open(os.path.join(tests_dir, "__init__.py"), "w") as f:
        f.write(f'''"""{model_name} test cases"""
''')
    
    # Create sample model.py file with proper structure
    with open(os.path.join(model_dir, "model.py"), "w") as f:
        f.write(f'''"""
{model_name} model definition
"""

import os
import json
from typing import List, Optional, Dict, Any, ClassVar
from pydantic import BaseModel, Field
from datetime import date


class {class_name}(BaseModel):
    """
    {description}
    """
    
    # Class variables for module configuration
    MODULE_NAME: ClassVar[str] = "{model_name}"
    TEST_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "tests")
    REPORT_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "reports")
    
    # Define model fields
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name or title")
    description: str = Field(..., description="Detailed description")
    
    # Example of optional fields
    # created_at: Optional[date] = Field(None, description="Creation date")
    # tags: List[str] = Field(default_factory=list, description="List of tags")
    
    @classmethod
    def get_test_cases(cls) -> List[Dict[str, Any]]:
        """Discover test cases for this module"""
        test_cases = []
        
        # Check required directories
        sources_dir = os.path.join(cls.TEST_DIR, "sources")
        prompts_dir = os.path.join(cls.TEST_DIR, "prompts")
        expected_dir = os.path.join(cls.TEST_DIR, "expected")
        
        if not all(os.path.exists(d) for d in [sources_dir, prompts_dir, expected_dir]):
            return []
        
        # Get test case base names (from source files without extension)
        for source_file in os.listdir(sources_dir):
            if not source_file.endswith(".txt"):
                continue
                
            base_name = os.path.splitext(source_file)[0]
            prompt_file = f"{base_name}.txt"
            expected_file = f"{base_name}.json"
            
            if not os.path.exists(os.path.join(prompts_dir, prompt_file)):
                continue
                
            if not os.path.exists(os.path.join(expected_dir, expected_file)):
                continue
            
            test_case = {{
                "module": cls.MODULE_NAME,
                "name": base_name,
                "model_class": cls,
                "source_path": os.path.join(sources_dir, source_file),
                "prompt_path": os.path.join(prompts_dir, prompt_file),
                "expected_path": os.path.join(expected_dir, expected_file)
            }}
            
            test_cases.append(test_case)
        
        return test_cases
    
    @classmethod
    def save_module_report(cls, results: Dict[str, Any], run_id: str) -> str:
        """Save a report specifically for this module"""
        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        
        # Create module-specific report
        report_path = os.path.join(cls.REPORT_DIR, f"report_{cls.MODULE_NAME}_{run_id}.md")
        
        with open(report_path, "w") as f:
            f.write(f"# {cls.MODULE_NAME.replace('_', ' ').title()} Module Report\\n\\n")
            f.write(f"Run ID: {run_id}\\n\\n")
            
            # Add test results
            f.write("## Test Results\\n\\n")
            for test_id, test_results in results.items():
                if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                    continue
                    
                test_name = test_id.split("/")[1]
                f.write(f"### Test: {test_name}\\n\\n")
                
                for provider, provider_results in test_results.items():
                    f.write(f"#### Provider: {provider}\\n\\n")
                    
                    if "error" in provider_results:
                        f.write(f"Error: {provider_results['error']}\\n\\n")
                        continue
                    
                    validation = provider_results.get("validation", {{}})
                    accuracy = validation.get("accuracy", 0.0) if validation.get("success", False) else 0.0
                    f.write(f"Accuracy: {accuracy:.2f}%\\n\\n")
                    
                    usage = provider_results.get("usage", {{}})
                    if usage:
                        f.write("Usage:\\n")
                        f.write(f"- Prompt tokens: {usage.get('prompt_tokens', 0)}\\n")
                        f.write(f"- Completion tokens: {usage.get('completion_tokens', 0)}\\n")
                        f.write(f"- Total tokens: {usage.get('total_tokens', 0)}\\n")
                        f.write(f"- Cost: ${usage.get('total_cost', 0):.6f}\\n\\n")
        
        return report_path
    
    @classmethod
    def save_module_cost_report(cls, cost_data: Dict[str, Any], run_id: str) -> str:
        """Save a cost report specifically for this module"""
        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        
        # Create module-specific cost report
        report_path = os.path.join(cls.REPORT_DIR, f"cost_report_{cls.MODULE_NAME}_{run_id}.json")
        
        # Filter cost data for this module only
        module_cost_data = {{
            "run_id": run_id,
            "module": cls.MODULE_NAME,
            "tests": {{}},
            "summary": {{
                "total_cost": 0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "models": {{}}
            }}
        }}
        
        # Collect tests that belong to this module
        for test_id, test_data in cost_data.get("tests", {{}}).items():
            if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                continue
                
            module_cost_data["tests"][test_id] = test_data
            
            # Add to summary
            for provider, provider_data in test_data.items():
                module_cost_data["summary"]["total_cost"] += provider_data.get("total_cost", 0)
                module_cost_data["summary"]["total_tokens"] += provider_data.get("total_tokens", 0)
                module_cost_data["summary"]["prompt_tokens"] += provider_data.get("prompt_tokens", 0)
                module_cost_data["summary"]["completion_tokens"] += provider_data.get("completion_tokens", 0)
                
                # Add to model-specific summary
                model_name = provider_data.get("model", "unknown")
                if model_name not in module_cost_data["summary"]["models"]:
                    module_cost_data["summary"]["models"][model_name] = {{
                        "total_cost": 0,
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "test_count": 0
                    }}
                
                model_summary = module_cost_data["summary"]["models"][model_name]
                model_summary["total_cost"] += provider_data.get("total_cost", 0)
                model_summary["total_tokens"] += provider_data.get("total_tokens", 0)
                model_summary["prompt_tokens"] += provider_data.get("prompt_tokens", 0)
                model_summary["completion_tokens"] += provider_data.get("completion_tokens", 0)
                model_summary["test_count"] += 1
        
        # Write to file
        with open(report_path, "w") as f:
            json.dump(module_cost_data, f, indent=2)
        
        return report_path
''')
    
    # Create example files
    # Example prompt
    with open(os.path.join(tests_dir, "prompts", "example.txt"), "w") as f:
        f.write(f'''Extract and structure the {model_name.replace('_', ' ')} information as a JSON object with the following schema:

{{
  "id": "Unique identifier",
  "name": "Name or title",
  "description": "Detailed description"
}}

Respond only with the JSON object, no additional text.''')
    
    # Example source
    with open(os.path.join(tests_dir, "sources", "example.txt"), "w") as f:
        f.write(f'''EXAMPLE {model_name.upper().replace('_', ' ')}

ID: example-123

NAME: Example {model_name.replace('_', ' ').title()}

DESCRIPTION:
This is an example description for testing the {model_name.replace('_', ' ')} model.
You can replace this with actual content to extract information from.''')
    
    # Example expected output
    with open(os.path.join(tests_dir, "expected", "example.json"), "w") as f:
        f.write(f'''{{
  "id": "example-123",
  "name": "Example {model_name.replace('_', ' ').title()}",
  "description": "This is an example description for testing the {model_name.replace('_', ' ')} model. You can replace this with actual content to extract information from."
}}''')
    
    print(f"\nModel '{model_name}' created successfully!")
    print(f"Model directory: {model_dir}")
    print(f"\nTo use this model:")
    print(f"1. Edit the model definition in {os.path.join(model_dir, 'model.py')}")
    print(f"2. Add real test cases in the tests directory")
    
    input("\nPress Enter to continue...")
    
    return model_name
