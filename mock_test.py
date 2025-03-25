#!/usr/bin/env python3
"""
Mock test that doesn't make real API calls
"""
import os
import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_test")

# Import LLMTester
from llm_tester import LLMTester

# Sample response to use for mocking
with open("llm_tester/tests/cases/job_ads/expected/complex.json", "r") as f:
    MOCK_RESPONSE = json.load(f)

# Mock the provider manager's get_response method
def mock_get_response(self, provider, prompt, source, model_name=None):
    """Mock the get_response method to return the sample response"""
    logger.info(f"Mock call to {provider} (model: {model_name})")
    return json.dumps(MOCK_RESPONSE, indent=2)

# Run a mock test
def run_mock_test():
    """Run a test with mocked API calls"""
    logger.info("Running mock test with patched API calls")
    
    # Patch the get_response method
    with patch("llm_tester.utils.provider_manager.ProviderManager.get_response", 
               mock_get_response):
        # Initialize tester with all providers
        providers = ["openai", "anthropic", "mistral", "google"]
        model_overrides = {
            "openai": "gpt-4-mock",
            "anthropic": "claude-3-mock",
            "mistral": "mistral-mock",
            "google": "gemini-mock"
        }
        
        tester = LLMTester(providers=providers)
        
        # Run tests with model overrides
        logger.info("Running tests with mock responses...")
        results = tester.run_tests(model_overrides=model_overrides)
        
        # Generate and print report
        report = tester.generate_report(results)
        print("\nTest Report:")
        print(report)
        
        # Save report to file
        report_path = Path("mock_test_report.md")
        with open(report_path, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {report_path}")
        
        # Run optimized tests
        logger.info("Running optimized tests with mock responses...")
        optimized_results = tester.run_optimized_tests(
            model_overrides=model_overrides)
        
        # Generate and print optimized report
        optimized_report = tester.generate_report(optimized_results, optimized=True)
        print("\nOptimized Test Report:")
        print(optimized_report)
        
        # Save optimized report to file
        optimized_report_path = Path("mock_optimized_test_report.md")
        with open(optimized_report_path, "w") as f:
            f.write(optimized_report)
        logger.info(f"Optimized report saved to {optimized_report_path}")

if __name__ == "__main__":
    run_mock_test()
