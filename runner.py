#!/usr/bin/env python3
"""
Interactive Runner for LLM Tester

This script provides an interactive interface for running LLM tests,
managing test cases, and viewing results.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from unittest.mock import patch
import importlib

# Add the parent directory to the path to import llm_tester
sys.path.append(str(Path(__file__).parent))

from llm_tester import LLMTester
from llm_tester.utils.config_manager import load_config, save_config, get_enabled_providers, get_test_setting, update_test_setting
from llm_tester.utils.provider_manager import ProviderManager

# Import mock responses
from llm_tester.utils.mock_responses import mock_get_response

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header"""
    width = 80
    print("=" * width)
    print(f"{title.center(width)}")
    print("=" * width)
    print()

def print_menu(options: List[Tuple[str, str]]):
    """Print a menu with options and descriptions"""
    for i, (key, desc) in enumerate(options, 1):
        print(f"{i}. {key:<25} - {desc}")
    print("q. Quit")
    print()

def get_user_choice(max_option: int) -> str:
    """Get user choice from input"""
    while True:
        choice = input("Enter your choice: ").strip().lower()
        if choice == 'q':
            return choice
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= max_option:
                return choice_num
        except ValueError:
            pass
        
        print(f"Invalid choice. Please enter a number between 1 and {max_option} or 'q' to quit.")

def load_env_file(env_path: str = None):
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            default_paths = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    load_dotenv(dotenv_path=path)
                    print(f"Loaded environment variables from {path}")
                    return True
            
            print("No .env file found. Please set up API keys manually.")
            return False
    except ImportError:
        print("python-dotenv package not installed. Cannot load .env file.")
        return False

def check_api_keys() -> Dict[str, Dict[str, Any]]:
    """Check which API keys are available"""
    results = {
        "openai": {
            "available": bool(os.environ.get("OPENAI_API_KEY")),
            "key_name": "OPENAI_API_KEY",
            "value": os.environ.get("OPENAI_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "anthropic": {
            "available": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "key_name": "ANTHROPIC_API_KEY",
            "value": os.environ.get("ANTHROPIC_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "mistral": {
            "available": bool(os.environ.get("MISTRAL_API_KEY")),
            "key_name": "MISTRAL_API_KEY", 
            "value": os.environ.get("MISTRAL_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "google": {
            "available": False,
            "missing": [],
            "keys": {
                "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
                "GOOGLE_PROJECT_ID": os.environ.get("GOOGLE_PROJECT_ID", "")
            },
            "status": "valid"
        }
    }
    
    # Check Google specifically since it needs multiple keys
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    google_project = os.environ.get("GOOGLE_PROJECT_ID")
    
    if not google_creds:
        results["google"]["missing"].append("GOOGLE_APPLICATION_CREDENTIALS")
    elif not os.path.exists(google_creds):
        results["google"]["status"] = "invalid"
        results["google"]["error"] = f"Credentials file not found: {google_creds}"
    
    if not google_project:
        results["google"]["missing"].append("GOOGLE_PROJECT_ID")
    
    results["google"]["available"] = (
        bool(google_creds) and
        bool(google_project) and
        results["google"]["status"] == "valid"
    )
    
    # Check other providers
    for provider in ["openai", "anthropic", "mistral"]:
        key_name = results[provider]["key_name"]
        if not results[provider]["value"]:
            results[provider]["missing"].append(key_name)
            results[provider]["status"] = "missing"
    
    return results

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
    """
    Allow the user to select which modules to test
    
    Args:
        tester: LLMTester instance
        
    Returns:
        List of selected module names
    """
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
                results = tester.run_tests(model_overrides=models, modules=selected_modules)
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
            
            results = tester.run_optimized_tests(
                model_overrides=models,
                save_optimized_prompts=save_optimized_prompts,
                modules=selected_modules
            )
            
            # If prompts were saved, show the paths
            if save_optimized_prompts:
                print("\nOptimized prompts saved to:")
                for test_id, test_results in results.items():
                    if 'optimized_prompt_path' in test_results:
                        print(f"  {test_id}: {test_results['optimized_prompt_path']}")
        else:
            results = tester.run_tests(model_overrides=models, modules=selected_modules)
    
    print("\nTests completed successfully!")
    
    # Generate report
    print("Generating report...")
    report = tester.generate_report(results, optimized=optimize)
    
    # Save report to file if requested
    if output_dir:
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
            if 'validation' in provider_result:
                validation = provider_result.get('validation', {})
                accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                model = provider_result.get('model', 'default')
                print(f"    {provider} ({model}): {accuracy:.2f}%")
            else:
                print(f"    {provider}: Results available in full report")
    
    # Ask if user wants to view the report
    view_report = input("\nDo you want to view the full report? (y/n): ").strip().lower()
    if view_report == 'y':
        clear_screen()
        print_header("Test Report")
        print(report)
    
    input("\nPress Enter to return to the main menu...")

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

def create_new_model():
    """Create scaffolding for a new model"""
    clear_screen()
    print_header("Create New Model")
    
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get model name
    while True:
        model_name = input("Enter name for the new model (e.g., 'product_reviews'): ").strip()
        if not model_name:
            print("Model name cannot be empty.")
            continue
            
        # Convert to snake_case if needed
        model_name = model_name.lower().replace(' ', '_').replace('-', '_')
        
        # Check if model already exists
        model_dir = os.path.join(base_dir, "llm_tester", "models", model_name)
        if os.path.exists(model_dir):
            overwrite = input(f"Model '{model_name}' already exists. Overwrite? (y/n): ").strip().lower()
            if overwrite != 'y':
                continue
        
        break
    
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
    model_dir = os.path.join(base_dir, "llm_tester", "models", model_name)
    os.makedirs(model_dir, exist_ok=True)
    
    # Create __init__.py
    init_content = f"""\"\"\"
{description}
\"\"\"

from .model import {class_name}

__all__ = ["{class_name}"]
"""
    with open(os.path.join(model_dir, "__init__.py"), 'w') as f:
        f.write(init_content)
    
    # Create model.py
    model_content = f"""\"\"\"
Model definition for {model_name}
\"\"\"

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import date, datetime


class {class_name}(BaseModel):
    \"\"\"
    {description}
    \"\"\"
    
    # TODO: Define your model fields here
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name or title")
    description: str = Field(..., description="Detailed description")
    
    # Example of optional fields with different types
    # tags: Optional[List[str]] = Field(None, description="List of tags")
    # created_at: Optional[date] = Field(None, description="Creation date")
    # metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
"""
    with open(os.path.join(model_dir, "model.py"), 'w') as f:
        f.write(model_content)
    
    # Create README.md
    readme_content = f"""# {class_name} Model

{description}

## Structure

The model includes:

- Basic identification fields (id, name)
- Descriptive content

## Example Usage

```python
from llm_tester.models.{model_name} import {class_name}

# Parse data
data = {{
    "id": "example-id",
    "name": "Example Name",
    "description": "This is an example description."
}}

# Validate with model
instance = {class_name}(**data)
```

## Test Cases

Test cases should be added to `/llm_tester/tests/cases/{model_name}/` with:
- Source files in `sources/`
- Prompt templates in `prompts/`
- Expected outputs in `expected/`
"""
    with open(os.path.join(model_dir, "README.md"), 'w') as f:
        f.write(readme_content)
    
    # Create test case directories
    test_cases_dir = os.path.join(base_dir, "llm_tester", "tests", "cases", model_name)
    os.makedirs(os.path.join(test_cases_dir, "sources"), exist_ok=True)
    os.makedirs(os.path.join(test_cases_dir, "prompts"), exist_ok=True)
    os.makedirs(os.path.join(test_cases_dir, "expected"), exist_ok=True)
    
    # Create test case __init__.py
    test_init_content = f"""\"\"\"
Test cases for {model_name}
\"\"\"
"""
    with open(os.path.join(test_cases_dir, "__init__.py"), 'w') as f:
        f.write(test_init_content)
    
    # Create example prompt template
    prompt_content = f"""Extract structured information from the provided {model_name.replace('_', ' ')}. Parse the text and extract all the relevant information. Return the result as a JSON object with the following structure:

{{
  "id": "Unique identifier",
  "name": "Name or title",
  "description": "Detailed description"
  // Add additional fields based on your model
}}

Provide all the information you can find in the source text. If some information is not available, you can omit those fields from the response.
"""
    with open(os.path.join(test_cases_dir, "prompts", "example.txt"), 'w') as f:
        f.write(prompt_content)
    
    # Create example source template
    source_content = f"""EXAMPLE {model_name.upper().replace('_', ' ')}

ID: example-123

NAME: Example {model_name.replace('_', ' ').title()}

DESCRIPTION:
This is an example description for testing the {model_name.replace('_', ' ')} model. 
You can replace this with actual content to extract information from.
"""
    with open(os.path.join(test_cases_dir, "sources", "example.txt"), 'w') as f:
        f.write(source_content)
    
    # Create example expected output
    expected_content = f"""{{
  "id": "example-123",
  "name": "Example {model_name.replace('_', ' ').title()}",
  "description": "This is an example description for testing the {model_name.replace('_', ' ')} model. You can replace this with actual content to extract information from."
}}
"""
    with open(os.path.join(test_cases_dir, "expected", "example.json"), 'w') as f:
        f.write(expected_content)
    
    print(f"\nModel '{model_name}' created successfully!")
    print(f"Model directory: {model_dir}")
    print(f"Test cases directory: {test_cases_dir}")
    print("\nTo use this model:")
    print(f"1. Edit the model definition in {os.path.join(model_dir, 'model.py')}")
    print(f"2. Add real test cases in {test_cases_dir}")
    print("3. Update the model in the LLMTester class if needed")
    
    input("\nPress Enter to continue...")
    
    return model_name

def run_with_defaults(providers=None, models=None, modules=None, optimize=False, output_dir=None):
    """
    Run tests with default settings without interactive prompts
    
    Args:
        providers: List of provider names to use. If None, uses enabled providers from config.
        models: Dictionary mapping providers to models. If None, uses defaults from config.
        modules: List of module names to test. If None, uses all available modules.
        optimize: Whether to run optimized tests
        output_dir: Directory to save results. If None, uses default from config.
        
    Returns:
        Exit code (0 for success)
    """
    logger = logging.getLogger(__name__)
    logger.info("Running with default settings (non-interactive mode)")
    
    # Load configuration
    config = load_config()
    
    # Get providers if not specified
    if providers is None:
        providers = [p for p, conf in config.get("providers", {}).items() 
                    if conf.get("enabled", False)]
        
        if not providers:
            logger.warning("No providers enabled in config, defaulting to mock_provider")
            providers = ["mock_provider"]
            
    # Initialize tester
    tester = LLMTester(providers=providers)
    
    # Get models if not specified
    if models is None:
        models = {}
        for provider in providers:
            provider_config = config.get("providers", {}).get(provider, {})
            if "default_model" in provider_config:
                models[provider] = provider_config["default_model"]
    
    # Get output directory if not specified
    if output_dir is None:
        test_settings = config.get("test_settings", {})
        output_dir = test_settings.get("output_dir", "test_results")
    
    # Create timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}{'_optimized' if optimize else ''}.md"
    
    # Run tests
    logger.info(f"Starting test run with {'optimized' if optimize else 'standard'} prompts")
    logger.info(f"Providers: {', '.join(providers)}")
    
    for provider, model in models.items():
        logger.info(f"Using model for {provider}: {model}")
    
    if modules:
        logger.info(f"Testing modules: {', '.join(modules)}")
    else:
        logger.info("Testing all available modules")
    
    # Prepare progress callback
    def progress_callback(message):
        logger.info(message)
    
    # Run tests
    if optimize:
        # Get save_optimized_prompts setting from config
        test_settings = config.get("test_settings", {})
        save_optimized_prompts = test_settings.get("save_optimized_prompts", True)
        
        results = tester.run_optimized_tests(
            model_overrides=models,
            save_optimized_prompts=save_optimized_prompts,
            modules=modules,
            progress_callback=progress_callback
        )
    else:
        results = tester.run_tests(
            model_overrides=models, 
            modules=modules,
            progress_callback=progress_callback
        )
    
    # Generate report
    logger.info("Generating report...")
    report = tester.generate_report(results, optimized=optimize)
    
    # Save report
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, filename)
    
    with open(report_path, "w") as f:
        f.write(report)
    
    logger.info(f"Report saved to {report_path}")
    
    # Print summary
    logger.info("Test Summary:")
    for test_name, test_results in results.items():
        logger.info(f"  {test_name}:")
        for provider, provider_result in test_results.items():
            if isinstance(provider_result, dict) and 'validation' in provider_result:
                validation = provider_result.get('validation', {})
                accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                model = provider_result.get('model', 'default')
                logger.info(f"    {provider} ({model}): {accuracy:.2f}%")
            else:
                logger.info(f"    {provider}: Results available in full report")
    
    return 0


def main(args=None):
    """Main function for the interactive runner"""
    # Setup logging
    import logging
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Create console handler and set level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # Default level is INFO

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    
    parser = argparse.ArgumentParser(description="Interactive LLM Tester Runner")
    parser.add_argument(
        "--env", 
        type=str, 
        help="Path to .env file with API keys"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check setup and exit"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--create-model",
        type=str,
        help="Create a new model with the given name"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--non-interactive", "-n",
        action="store_true",
        help="Run tests with default settings without interactive prompts"
    )
    parser.add_argument(
        "--optimize", "-o",
        action="store_true",
        help="Run optimized tests (only used with --non-interactive)"
    )
    parser.add_argument(
        "--provider", "-p",
        action="append",
        help="Provider to use (can be specified multiple times, only used with --non-interactive)"
    )
    parser.add_argument(
        "--module", "-m",
        action="append",
        help="Module to test (can be specified multiple times, only used with --non-interactive)"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save results (only used with --non-interactive)"
    )
    
    parsed_args = parser.parse_args(args)
    
    # Configure debug logging if requested
    if parsed_args.debug:
        ch.setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
    # Load environment variables
    if parsed_args.env:
        load_env_file(parsed_args.env)
    else:
        load_env_file()
    
    # Create new model if requested
    if parsed_args.create_model:
        model_name = parsed_args.create_model
        create_new_model(model_name)
        return 0
        
    # Only check setup if requested
    if parsed_args.check_only:
        check_setup()
        return 0
    
    # Load configuration
    config = load_config()
    
    # Non-interactive mode
    if parsed_args.non_interactive:
        return run_with_defaults(
            providers=parsed_args.provider,
            modules=parsed_args.module,
            optimize=parsed_args.optimize,
            output_dir=parsed_args.output_dir
        )
    
    # Get initially enabled providers from config
    enabled_providers = [p for p, conf in config.get("providers", {}).items() 
                        if conf.get("enabled", False)]
    
    # Initialize tester
    tester = LLMTester(providers=[])
    
    # Main menu loop
    while True:
        clear_screen()
        print_header("LLM Tester Interactive Runner")
        
        # Show current configuration
        if hasattr(tester, 'providers') and tester.providers:
            providers_str = ", ".join(tester.providers)
            print(f"Active Providers: {providers_str}")
        else:
            print("No active providers configured. Use 'Setup Providers' to configure.")
        
        print("")  # Empty line for spacing
        
        options = [
            ("Check Setup", "Verify environment and dependencies"),
            ("List Test Cases", "Show all available test cases"),
            ("Run Tests", "Run tests with current settings"),
            ("Run Optimized Tests", "Run tests with prompt optimization"),
            ("Setup Providers", "Choose which LLM providers to use"),
            ("Setup Models", "Configure which models to use for each provider"),
            ("Edit Configuration", "Edit test settings"),
            ("Create New Model", "Generate scaffolding for a new model")
        ]
        
        print_menu(options)
        
        choice = get_user_choice(len(options))
        
        if choice == 'q':
            print("Exiting LLM Tester.")
            break
        
        if choice == 1:
            check_setup()
        elif choice == 2:
            list_test_cases(tester)
        elif choice == 3:
            providers = getattr(tester, 'providers', [])
            if not providers:
                providers = setup_providers()
                tester = LLMTester(providers=providers)
            
            # Get models from config
            models = {}
            for provider in providers:
                provider_config = config.get("providers", {}).get(provider, {})
                if "default_model" in provider_config:
                    models[provider] = provider_config["default_model"]
            
            # Ask if user wants to customize models
            customize_models = input("\nDo you want to customize the models? (y/n): ").strip().lower()
            if customize_models == 'y':
                models = setup_models(providers)
                
            run_tests(tester, providers, models)
        elif choice == 4:
            providers = getattr(tester, 'providers', [])
            if not providers:
                providers = setup_providers()
                tester = LLMTester(providers=providers)
            
            # Get models from config
            models = {}
            for provider in providers:
                provider_config = config.get("providers", {}).get(provider, {})
                if "default_model" in provider_config:
                    models[provider] = provider_config["default_model"]
            
            # Ask if user wants to customize models
            customize_models = input("\nDo you want to customize the models? (y/n): ").strip().lower()
            if customize_models == 'y':
                models = setup_models(providers)
                
            run_tests(tester, providers, models, optimize=True)
        elif choice == 5:
            providers = setup_providers()
            tester = LLMTester(providers=providers)
        elif choice == 6:
            providers = getattr(tester, 'providers', [])
            if not providers:
                providers = setup_providers()
                tester = LLMTester(providers=providers)
            setup_models(providers)
        elif choice == 7:
            # Edit configuration
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
        elif choice == 8:
            # Create new model
            new_model_name = create_new_model()
            
            # Ask if user wants to add the new model to default modules
            add_to_defaults = input(f"Add {new_model_name} to default modules? (y/n): ").strip().lower()
            if add_to_defaults == 'y':
                config = load_config()
                if "test_settings" not in config:
                    config["test_settings"] = {}
                
                default_modules = config["test_settings"].get("default_modules", [])
                if new_model_name not in default_modules:
                    default_modules.append(new_model_name)
                    config["test_settings"]["default_modules"] = default_modules
                    save_config(config)
                    print(f"Added {new_model_name} to default modules.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())