#!/usr/bin/env python3
"""
Main entry point for the interactive runner
"""

import argparse
import logging
import sys

from .ui import setup_logging, clear_screen, print_header, print_menu, get_user_choice
from .config import load_env_file, load_config
from .menu_handlers import (
    check_setup,
    list_test_cases,
    run_default_tests,
    run_tests,
    run_optimized_tests,
    setup_providers,
    setup_models,
    edit_configuration,
    create_new_model
)
from .non_interactive import run_with_defaults

from llm_tester import LLMTester

def main(args=None):
    """Main function for the interactive runner"""
    # Setup logging
    logger = setup_logging()    
    
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
        action="store",
        metavar="MODEL_NAME",
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
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
    # Load environment variables
    if parsed_args.env:
        load_env_file(parsed_args.env)
    else:
        load_env_file()
    
    # Create new model if requested
    if parsed_args.create_model:
        create_new_model(parsed_args.create_model)
        return 0
        
    # Only check setup if requested
    if parsed_args.check_only:
        check_setup()
        return 0
    
    # Non-interactive mode
    if parsed_args.non_interactive:
        return run_with_defaults(
            providers=parsed_args.provider,
            modules=parsed_args.module,
            optimize=parsed_args.optimize,
            output_dir=parsed_args.output_dir
        )
    
    # Load configuration
    config = load_config()
    
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
            ("Run Default Tests", "Run tests with default settings"),
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
                
            run_optimized_tests(tester, providers, models)
        elif choice == 5:
            # Run default tests without prompting
            run_default_tests(tester)
        elif choice == 6:
            providers = setup_providers()
            tester = LLMTester(providers=providers)
        elif choice == 7:
            providers = getattr(tester, 'providers', [])
            if not providers:
                providers = setup_providers()
                tester = LLMTester(providers=providers)
            setup_models(providers)
        elif choice == 8:
            # Edit configuration
            edit_configuration()
        elif choice == 9:
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
