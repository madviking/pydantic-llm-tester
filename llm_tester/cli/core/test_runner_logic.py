import json
import logging
import os
from typing import List, Dict, Optional, Any

# Use absolute imports
from llm_tester import LLMTester # The main class
from llm_tester.cli.core.provider_logic import get_available_providers_from_factory # To get default providers

logger = logging.getLogger(__name__)

def parse_model_overrides(model_args: Optional[List[str]]) -> Dict[str, str]:
    """
    Parse model arguments in the format 'provider:model_name' or 'provider/model_name'.
    Handles potential '/' in model names if provider is specified first.

    Args:
        model_args: List of model specifications (e.g., ["openai:gpt-4o", "openrouter/google/gemini-pro"]).

    Returns:
        Dictionary mapping provider names to model names.
    """
    models = {}
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
            models[provider] = model_name
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
    Lists discovered test cases and configured providers/models without running tests.

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
        # Need to load provider configs to show default/overridden models
        from llm_tester.llms.provider_factory import load_provider_config # Local import
        for provider_name in sorted(providers_list):
            model_to_use = "Default"
            config = load_provider_config(provider_name)
            default_model_name = "N/A"
            if config and config.models:
                 # Find the explicitly enabled default model first
                 default_model_obj = next((m for m in config.models if m.default and m.enabled), None)
                 # Fallback: find the first enabled model if no default is enabled
                 if not default_model_obj:
                     default_model_obj = next((m for m in config.models if m.enabled), None)
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
    model_overrides: Optional[Dict[str, str]] = None,
    test_dir: Optional[str] = None,
    output_file: Optional[str] = None,
    output_json: bool = False,
    optimize: bool = False,
    test_filter: Optional[str] = None # TODO: Implement filtering
) -> bool:
    """
    Runs the main LLM testing suite.

    Args:
        providers: List of providers to test (if None, uses all available).
        model_overrides: Dictionary mapping provider to a specific model to use.
        test_dir: Optional path to the test directory.
        output_file: Optional path to save the report/JSON output.
        output_json: If True, output results as JSON instead of Markdown.
        optimize: If True, run prompt optimization.
        test_filter: Optional pattern to filter test cases (e.g., "module/name").

    Returns:
        True if execution completed successfully (regardless of test results), False on error.
    """
    if model_overrides is None:
        model_overrides = {}
    if providers is None:
        providers = get_available_providers_from_factory()
        logger.info(f"No providers specified, running tests for all available: {', '.join(providers)}")
        if not providers:
             print("Error: No providers are enabled or available. Cannot run tests.")
             print("Use 'llm-tester providers list' and 'llm-tester providers enable <name>'.")
             return False

    try:
        # Initialize tester with the selected providers and test_dir
        tester = LLMTester(
            providers=providers,
            test_dir=test_dir
        )

        # TODO: Implement test filtering logic within LLMTester or here
        if test_filter:
            logger.warning(f"Test filtering ('{test_filter}') is not yet implemented in the refactored CLI.")

        # Run tests
        if optimize:
            print("Running optimized tests...")
            results = tester.run_optimized_tests(model_overrides=model_overrides)
        else:
            print("Running tests...")
            results = tester.run_tests(model_overrides=model_overrides)

        # Generate output
        if output_json:
            # Convert any non-serializable objects (like Pydantic models in errors)
            serializable_results = _make_serializable(results)
            output_content = json.dumps(serializable_results, indent=2)
        else:
            output_content = tester.generate_report(results, optimized=optimize)

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
                print("--- End Results ---") # Corrected indentation
                return False # Indicate failure to write file # Corrected indentation
        else:
            # Ensure output_content is a string before printing
            print("\n" + str(output_content)) # Corrected indentation

        return True # Completed successfully # Corrected indentation relative to the main try block

    except Exception as e:
        logger.error(f"An error occurred during testing: {e}", exc_info=True)
        print(f"\nAn error occurred during testing: {e}")
        return False


def _make_serializable(obj: Any) -> Any:
    """
    Recursively convert non-JSON-serializable objects within results to strings.
    Handles common types like Pydantic models or exceptions often found in error results.
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
        # Attempt to convert other types (like Pydantic models) to string
        try:
            return str(obj)
        except Exception:
             # Fallback if str() fails
             return f"<{type(obj).__name__} object (non-serializable)>"
