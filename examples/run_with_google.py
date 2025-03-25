#!/usr/bin/env python3
"""
Example of running LLM Tester with Google's Gemini model
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import llm_tester
sys.path.append(str(Path(__file__).parent.parent))

from llm_tester import LLMTester
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Main function"""
    # List of providers to test
    providers = ["openai", "anthropic", "google", "mistral"]
    
    # Model overrides (optional)
    model_overrides = {
        "openai": "gpt-4-turbo",
        "google": "gemini-pro",  # Using standard gemini model
        "anthropic": "claude-3-haiku-20240307",
        "mistral": "mistral-medium"
    }
    
    # Initialize the tester
    tester = LLMTester(providers=providers)
    
    # Discover test cases
    test_cases = tester.discover_test_cases()
    print(f"Found {len(test_cases)} test cases:")
    for test_case in test_cases:
        print(f"  {test_case['module']}/{test_case['name']}")
    
    # Run tests with model overrides
    print("\nRunning tests...")
    results = tester.run_tests(model_overrides=model_overrides)
    
    # Generate report
    report = tester.generate_report(results)
    print("\nTest Results:\n")
    print(report)
    
    # Save report to file
    report_path = Path(__file__).parent / "test_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to {report_path}")
    
    # Run optimized tests
    print("\nRunning optimized tests...")
    optimized_results = tester.run_optimized_tests(model_overrides=model_overrides)
    
    # Generate optimized report
    optimized_report = tester.generate_report(optimized_results, optimized=True)
    print("\nOptimized Test Results:\n")
    print(optimized_report)
    
    # Save optimized report to file
    optimized_report_path = Path(__file__).parent / "optimized_test_report.md"
    with open(optimized_report_path, "w") as f:
        f.write(optimized_report)
    print(f"\nOptimized report saved to {optimized_report_path}")

if __name__ == "__main__":
    main()