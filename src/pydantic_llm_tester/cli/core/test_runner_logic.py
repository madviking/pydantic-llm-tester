import json
import logging
import os
from typing import List, Dict, Optional, Any, Type

# Use absolute imports
from pydantic_llm_tester import LLMTester # The main class
from pydantic_llm_tester.cli.core.provider_logic import get_available_providers_from_factory # To get default providers
from pydantic import BaseModel # Import BaseModel

logger = logging.getLogger(__name__)

def parse_model_overrides(model_args: Optional[List[str]]) -> Dict[str, List[str]]:
    """
    Parse model arguments in the format 'provider:model_name' or 'provider/model_name'.
    Handles potential '/' in model names if provider is specified first.
    Allows specifying multiple models per provider.

    Args:
        model_args: List of model specifications (e.g., ["openai:gpt-4o", "openrouter/google/gemini-pro", "openai:gpt-3.5-turbo"]).

    Returns:
        Dictionary mapping provider names to lists of model names.
    """
    models: Dict[str, List[str]] = {}
    if not model_args:
        return models

    for arg in model_args:
        provider = None
        model_name = None
        if ":" in arg:
            parts = arg.split(":", 1)
            provider = parts[0].strip()
            model_name = parts[1].strip()
        elif "/" in arg:
             # Handle provider/model/name format
             parts = arg.split("/", 1)
             provider = parts[0].strip()
             model_name = parts[1].strip() # Keep the rest as model name
        else:
            logger.warning(f"Ignoring invalid model specification '{arg}'. Format should be 'provider:model_name' or 'provider/model_name'.")
            continue

        if provider and model_name:
            if provider not in models:
                models[provider] = []
            models[provider].append(model_name)
        else:
             logger.warning(f"Could not parse provider and model from '{arg}'. Skipping.")

    logger.debug(f"Parsed model overrides: {models}")
    return models

def list_available_tests_and_providers(
    providers_list: Optional[List[str]] = None,
    model_overrides: Optional[Dict[str, str]] = None,
    test_dir: Optional[str] = None
) -> str:
    """
    Lists discovered test cases and configured providers/py_models without running tests.

    Args:
        providers_list: Specific providers to list (if None, defaults to all available).
        model_overrides: Dictionary mapping provider to a specific model to use.
        test_dir: Optional path to the test directory.

    Returns:
        A formatted string containing the list information.
    """
    output_lines = []
    if model_overrides is None:
        model_overrides = {}

    # Determine providers to check
    if providers_list is None:
        providers_list = get_available_providers_from_factory()
        logger.info(f"--list used without --providers, listing all available: {', '.join(providers_list)}")

    # Initialize LLMTester to discover tests
    try:
        # Pass only the test_dir if specified, let LLMTester handle provider loading later
        tester = LLMTester(providers=[], test_dir=test_dir) # Init with empty providers for discovery
        test_cases = tester.discover_test_cases()
        output_lines.append(f"Found {len(test_cases)} test cases:")
        # Sort test cases for consistent output
        sorted_test_cases = sorted(test_cases, key=lambda tc: (tc.get('module', ''), tc.get('name', '')))
        for test_case in sorted_test_cases:
            output_lines.append(f"  - {test_case.get('module', 'unknown')}/{test_case.get('name', 'unknown')}")
    except Exception as e:
        logger.error(f"Error discovering test cases: {e}", exc_info=True)
        output_lines.append(f"\nError discovering test cases: {e}")
        # Continue to list providers if possible

    output_lines.append("\nConfigured Providers & Models:")
    if not providers_list:
        output_lines.append("  (No providers enabled or specified)")
    else:
        # Need to load provider configs to show default/overridden py_models
        from pydantic_llm_tester.llms.provider_factory import load_provider_config # Local import
        for provider_name in sorted(providers_list):
            model_to_use = "Default"
            config = load_provider_config(provider_name)
            default_model_name = "N/A"
            if config and config.llm_models:
                 # Find the explicitly enabled default model first
                 default_model_obj = next((m for m in config.llm_models if m.default and m.enabled), None)
                 # Fallback: find the first enabled model if no default is enabled
                 if not default_model_obj:
                     default_model_obj = next((m for m in config.llm_models if m.enabled), None)
                 if default_model_obj:
                     default_model_name = default_model_obj.name

            if provider_name in model_overrides:
                model_to_use = f"Specified: {model_overrides[provider_name]}"
            else:
                 model_to_use = f"Default: {default_model_name}"

            output_lines.append(f"  - {provider_name} ({model_to_use})")

    return "\n".join(output_lines)


def run_test_suite(
    providers: Optional[List[str]] = None,
    model_overrides: Optional[Dict[str, List[str]]] = None, # Updated type hint
    llm_models: Optional[List[str]] = None,
    test_dir: Optional[str] = None,
    output_file: Optional[str] = None,
    output_json: bool = False,
    optimize: bool = False,
    py_models: Optional[List[str]] = None,
    test_name_filter: Optional[str] = None
) -> bool:
    """
    Runs the main LLM testing suite.

    Args:
        providers: List of providers to test (if None, uses all available).
        model_overrides: Dictionary mapping provider to a list of specific models to use.
        llm_models: List of model specifications in "provider:model-name" format from CLI.
        test_dir: Optional path to the test directory.
        output_file: Optional path to save the report/JSON output.
        output_json: If True, output results as JSON instead of Markdown.
        optimize: If True, run prompt optimization.
        py_models: Optional list of specific py_models to test.
        test_name_filter: Optional pattern to filter test cases (e.g., "module/name").

    Returns:
        True if execution completed successfully (regardless of test results), False on error.
    """
    # Enforce that llm_models must be specified
    if not llm_models:
        print("Error: You must specify at least one LLM model to test using the --llm-models flag.")
        print("Example: llm-tester run --llm-models openai:gpt-4o openrouter:mistral-large-latest")
        return False

    # Parse the llm_models list into the model_overrides dictionary format
    model_overrides = parse_model_overrides(llm_models)

    # Determine the list of providers to attempt to use based on the specified models
    providers_to_check = list(model_overrides.keys())

    if not providers_to_check:
        # This case should ideally not be reached if llm_models is not empty,
        # but as a safeguard if parse_model_overrides returns an empty dict for some reason.
        print("Error: No valid providers found in the specified --llm-models.")
        return False

    logger.info(f"Providers derived from --llm-models: {', '.join(providers_to_check)}")

    # Check for required API keys and build a list of usable providers
    usable_providers = []
    from pydantic_llm_tester.llms.provider_factory import load_provider_config # Local import

    print("\nChecking provider configurations and API keys...")
    # Iterate through providers derived from model_overrides
    for provider_name in providers_to_check:
        try:
            # Adjust lookup name for mock providers
            config_lookup_name = provider_name
            if provider_name.startswith("mock_") and provider_name != "mock":
                config_lookup_name = "mock"
            
            config = load_provider_config(config_lookup_name)
            if config:
                # Special handling for mock providers - they don't need a real API key check
                is_mock_provider_type = config.provider_type == "mock" # Check provider_type from config
                
                if is_mock_provider_type or not config.env_key:
                    usable_providers.append(provider_name)
                    logger.info(f"Provider '{provider_name}' enabled (mock provider or no API key required).")
                elif config.env_key:
                    # Check if the required environment variable is set and not empty
                    api_key = os.environ.get(config.env_key)
                    if api_key:
                        usable_providers.append(provider_name)
                        logger.info(f"Provider '{provider_name}' enabled (API key found for {config.env_key}).")
                    else:
                        print(f"Skipping provider '{provider_name}': Required environment variable '{config.env_key}' not set.")
                        logger.warning(f"Skipping provider '{provider_name}': Required environment variable '{config.env_key}' not set.")
            else:
                # Config not found
                print(f"Skipping provider '{provider_name}': Configuration not found.")
                logger.warning(f"Skipping provider '{provider_name}': Configuration not found.")

        except Exception as e:
            print(f"Error checking config for provider '{provider_name}': {e}")
            logger.error(f"Error checking config for provider '{provider_name}': {e}", exc_info=True)
            print(f"Skipping provider '{provider_name}' due to configuration error.")


    if not usable_providers:
        print("\nError: No usable providers found with required API keys set from the specified --llm-models.")
        print("Please ensure your API keys are set in your environment or in a .env file.")
        print("Use 'llm-tester configure keys' to help set up keys.")
        return False

    print(f"\nRunning tests with usable providers: {', '.join(usable_providers)}")

    try:
        # Initialize tester with the *usable* providers and test_dir
        # Pass the parsed model_overrides directly to LLMTester
        tester = LLMTester(
            providers=usable_providers,
            model_overrides=model_overrides, # Pass the parsed dictionary
            test_dir=test_dir
        )

        # Run tests
        if optimize:
            print("Running optimized tests...")
            # TODO: Consider if test_name_filter should also apply to run_optimized_tests
            # Pass the parsed model_overrides to run_optimized_tests
            results = tester.run_optimized_tests(model_overrides=model_overrides, modules=py_models)
        else:
            print("Running tests...")
            # Pass the parsed model_overrides to run_tests
            results = tester.run_tests(
                model_overrides=model_overrides,
                modules=py_models,
                test_name_filter=test_name_filter # Pass the filter here
            )

        # Generate output
        if output_json:
            # Convert any non-serializable objects (like Pydantic py_models in errors)
            serializable_results = _make_serializable(results)
            output_content = json.dumps(serializable_results, indent=2)
        else:
            # Generate module-specific reports
            reports = {}
            modules_processed = set()
            for test_id, test_result_data in results.items():
                module_name = test_id.split('/')[0]

                # Skip if already processed or is the test module
                if module_name in modules_processed or module_name == 'test':
                    continue

                if py_models and module_name not in py_models:
                    logger.info(f"Module '{module_name}' not in specified py_models. Skipping.")
                    continue

                modules_processed.add(module_name)

                # Get model class from the results for this module
                model_class: Optional[Type[BaseModel]] = test_result_data.get('model_class')

                if not model_class:
                    logger.warning(f"Could not find model class in results for module {module_name}. Skipping module report.")
                    continue

                # Generate module-specific report if the model class has the method
                if hasattr(model_class, 'save_module_report'):
                    try:
                        # Pass only results relevant to this module to the module's report generator
                        module_results = {tid: data for tid, data in results.items() if tid.startswith(f"{module_name}/")}
                        module_report_path = model_class.save_module_report(module_results, tester.run_id)
                        logger.info(f"Module report for {module_name} saved to {module_report_path}")

                        # Read the report content
                        try:
                            with open(module_report_path, 'r', encoding='utf-8') as f:
                                reports[module_name] = f.read()
                        except Exception as e:
                            logger.error(f"Error reading module report for {module_name}: {str(e)}")

                    except Exception as e:
                        logger.error(f"Error generating module report for {module_name}: {str(e)}")

            # Generate main report including cost summary and module reports
            output_content = tester.report_generator.generate_report(results, optimized=optimize)

            # Append module reports to the main report
            for module_name, report_content in reports.items():
                 output_content += f"\n\n---\n\n## Module Report: {module_name}\n\n"
                 output_content += report_content


        # Write or print output
        if output_file:
            try:
                with open(output_file, "w", encoding='utf-8') as f:
                    f.write(output_content)
                print(f"\nResults written to {output_file}")
            except Exception as e:
                logger.error(f"Failed to write output to {output_file}: {e}", exc_info=True)
                print(f"\nError writing output to file: {e}")
                print("\n--- Results ---")
                print(output_content) # Print to stdout as fallback
                print("--- End Results ---")
                return False # Indicate failure to write file
        else:
            # Ensure output_content is a string before printing
            print("\n" + str(output_content))

        return True # Completed successfully

    except Exception as e:
        logger.error(f"An error occurred during testing: {e}", exc_info=True)
        print(f"\nAn error occurred during testing: {e}")
        return False


def _make_serializable(obj: Any) -> Any:
    """
    Recursively convert non-JSON-serializable objects within results to strings.
    Handles common types like Pydantic py_models or exceptions often found in error results.
    """
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (Exception, BaseException)):
         # Format exceptions nicely
         return f"{type(obj).__name__}: {str(obj)}"
    else:
        # Attempt to convert other types (like Pydantic py_models) to string
        try:
            return str(obj)
        except Exception:
             # Fallback if str() fails
             return f"<{type(obj).__name__} object (non-serializable)>"

    # Check for required API keys and build a list of usable providers
    usable_providers = []
    from pydantic_llm_tester.llms.provider_factory import load_provider_config # Local import

    print("\nChecking provider configurations and API keys...")
    for provider_name in providers_to_check:
        try:
            # Adjust lookup name for mock providers
            config_lookup_name = provider_name
            if provider_name.startswith("mock_") and provider_name != "mock":
                config_lookup_name = "mock"
            
            config = load_provider_config(config_lookup_name)
            if config:
                # Special handling for mock providers - they don't need a real API key check
                is_mock_provider_type = config.provider_type == "mock" # Check provider_type from config
                
                if is_mock_provider_type or not config.env_key:
                    usable_providers.append(provider_name)
                    logger.info(f"Provider '{provider_name}' enabled (mock provider or no API key required).")
                elif config.env_key:
                    # Check if the required environment variable is set and not empty
                    api_key = os.environ.get(config.env_key)
                    if api_key:
                        usable_providers.append(provider_name)
                        logger.info(f"Provider '{provider_name}' enabled (API key found for {config.env_key}).")
                    else:
                        print(f"Skipping provider '{provider_name}': Required environment variable '{config.env_key}' not set.")
                        logger.warning(f"Skipping provider '{provider_name}': Required environment variable '{config.env_key}' not set.")
            else:
                # Config not found
                print(f"Skipping provider '{provider_name}': Configuration not found.")
                logger.warning(f"Skipping provider '{provider_name}': Configuration not found.")

        except Exception as e:
            print(f"Error checking config for provider '{provider_name}': {e}")
            logger.error(f"Error checking config for provider '{provider_name}': {e}", exc_info=True)
            print(f"Skipping provider '{provider_name}' due to configuration error.")


    if not usable_providers:
        print("\nError: No usable providers found with required API keys set.")
        print("Please ensure your API keys are set in your environment or in a .env file.")
        print("Use 'llm-tester configure keys' to help set up keys.")
        return False

    print(f"\nRunning tests with usable providers: {', '.join(usable_providers)}")

    try:
        # Initialize tester with the *usable* providers and test_dir
        tester = LLMTester(
            providers=usable_providers,
            llm_models=llm_models,
            test_dir=test_dir
        )

        # Run tests
        if optimize:
            print("Running optimized tests...")
            # TODO: Consider if test_name_filter should also apply to run_optimized_tests
            results = tester.run_optimized_tests(model_overrides=model_overrides, modules=py_models) 
        else:
            print("Running tests...")
            results = tester.run_tests(
                model_overrides=model_overrides, 
                modules=py_models, 
                test_name_filter=test_name_filter # Pass the filter here
            )

        # Generate output
        if output_json:
            # Convert any non-serializable objects (like Pydantic py_models in errors)
            serializable_results = _make_serializable(results)
            output_content = json.dumps(serializable_results, indent=2)
        else:
            # Generate module-specific reports
            reports = {}
            modules_processed = set()
            for test_id, test_result_data in results.items():
                module_name = test_id.split('/')[0]

                # Skip if already processed or is the test module
                if module_name in modules_processed or module_name == 'test':
                    continue

                if py_models and module_name not in py_models:
                    logger.info(f"Module '{module_name}' not in specified py_models. Skipping.")
                    continue

                modules_processed.add(module_name)

                # Get model class from the results for this module
                model_class: Optional[Type[BaseModel]] = test_result_data.get('model_class')

                if not model_class:
                    logger.warning(f"Could not find model class in results for module {module_name}. Skipping module report.")
                    continue

                # Generate module-specific report if the model class has the method
                if hasattr(model_class, 'save_module_report'):
                    try:
                        # Pass only results relevant to this module to the module's report generator
                        module_results = {tid: data for tid, data in results.items() if tid.startswith(f"{module_name}/")}
                        module_report_path = model_class.save_module_report(module_results, tester.run_id)
                        logger.info(f"Module report for {module_name} saved to {module_report_path}")

                        # Read the report content
                        try:
                            with open(module_report_path, 'r', encoding='utf-8') as f:
                                reports[module_name] = f.read()
                        except Exception as e:
                            logger.error(f"Error reading module report for {module_name}: {str(e)}")

                    except Exception as e:
                        logger.error(f"Error generating module report for {module_name}: {str(e)}")

            # Generate main report including cost summary and module reports
            output_content = tester.report_generator.generate_report(results, optimized=optimize)

            # Append module reports to the main report
            for module_name, report_content in reports.items():
                 output_content += f"\n\n---\n\n## Module Report: {module_name}\n\n"
                 output_content += report_content


        # Write or print output
        if output_file:
            try:
                with open(output_file, "w", encoding='utf-8') as f:
                    f.write(output_content)
                print(f"\nResults written to {output_file}")
            except Exception as e:
                logger.error(f"Failed to write output to {output_file}: {e}", exc_info=True)
                print(f"\nError writing output to file: {e}")
                print("\n--- Results ---")
                print(output_content) # Print to stdout as fallback
                print("--- End Results ---")
                return False # Indicate failure to write file
        else:
            # Ensure output_content is a string before printing
            print("\n" + str(output_content))

        return True # Completed successfully

    except Exception as e:
        logger.error(f"An error occurred during testing: {e}", exc_info=True)
        print(f"\nAn error occurred during testing: {e}")
        return False


def _make_serializable(obj: Any) -> Any:
    """
    Recursively convert non-JSON-serializable objects within results to strings.
    Handles common types like Pydantic py_models or exceptions often found in error results.
    """
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (Exception, BaseException)):
         # Format exceptions nicely
         return f"{type(obj).__name__}: {str(obj)}"
    else:
        # Attempt to convert other types (like Pydantic py_models) to string
        try:
            return str(obj)
        except Exception:
             # Fallback if str() fails
             return f"<{type(obj).__name__} object (non-serializable)>"
