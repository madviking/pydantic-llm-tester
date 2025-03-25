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
        help="Path to .env file with API keys (default: .env in project root)"
    )

    args = parser.parse_args()
    
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
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results written to {args.output}")
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