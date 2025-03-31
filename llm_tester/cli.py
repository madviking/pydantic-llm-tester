#!/usr/bin/env python3
"""
Command-line interface for LLM Tester
"""

import argparse
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv # Import load_dotenv
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


# Default model configurations for each provider
DEFAULT_MODELS = {
    "openai": "gpt-4",
    "anthropic": "claude-3-opus-20240229",
    "mistral": "mistral-large-latest",
    "google": "gemini-pro"
}


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Test LLM performance with pydanticAI models")
    # Add a verbosity argument
    parser.add_argument(
        '-v', '--verbose',
        action='count', default=0,
        help="Increase verbosity level (e.g., -v for INFO, -vv for DEBUG)"
    )
    parser.add_argument(
        "--providers",
        type=str, 
        nargs="+", 
        default=["openai", "anthropic", "mistral", "google"],
        help="LLM providers to test (default: openai anthropic mistral google)"
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
        help="List available test cases without running tests"
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
    parser.add_argument(
        "--env",
        type=str,
        help="Path to .env file with API keys (will override default loading if specified)"
    )

    # Parse arguments fully now
    args = parser.parse_args()

    # --- Setup Logging Level based on verbosity ---
    if args.verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('llm_tester').setLevel(logging.INFO)
        logger.info("Logging level set to INFO")
    elif args.verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('llm_tester').setLevel(logging.DEBUG)
        logger.info("Logging level set to DEBUG")
    else:
        # Default level (can be INFO or WARNING depending on basicConfig)
        pass
    # --- End Logging Setup ---

    # --- Handle explicit --env argument (overrides module-level load) ---
    if args.env:
        if os.path.exists(args.env):
            load_dotenv(dotenv_path=args.env, override=True)
            logger.info(f"Loaded/Overridden environment variables from specified --env file: {args.env}")
        else:
            logger.warning(f"Specified --env file not found: {args.env}. Using previously loaded environment.")
    # --- End explicit --env handling ---


    # Handle model specifications
    models = parse_model_args(args.models)
    
    # Initialize tester
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
        for provider in args.providers:
            if provider in models:
                print(f"  {provider} (using model: {models[provider]})")
            else:
                print(f"  {provider} (using default model: {DEFAULT_MODELS.get(provider, 'default')})")
        
        return 0
    
    # Run tests with specific models if provided
    if args.optimize:
        print("Running optimized tests...")
        results = tester.run_optimized_tests(model_overrides=models)
    else:
        print("Running tests...")
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
        print("\n" + output)
    
    return 0


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
        models[provider] = model_name
    
    return models


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
