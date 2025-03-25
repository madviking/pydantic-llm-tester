#!/bin/bash
# Script to run LLM tester tests with specific module
# Must be run inside an activated virtual environment

# Default values
MODULE="job_ads"
OUTPUT_DIR="test_results"
MODEL_OVERRIDE=""
MOCK=1  # Default to mock mode

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -m, --module MODULE     Module to test (default: job_ads)"
    echo "  -o, --output DIR        Output directory for test results (default: test_results)"
    echo "  -r, --real              Use real API calls instead of mock calls"
    echo "  -p, --provider PROVIDER Use a specific provider (openai, anthropic, mistral, google)"
    echo "  --model PROVIDER:MODEL  Override model for provider (e.g. openai:gpt-4-turbo)"
    echo "  -h, --help              Show this help message"
    echo
    echo "Example:"
    echo "  $0 -m job_ads -o results --model openai:gpt-4 --model anthropic:claude-3-opus-20240229"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--module)
            MODULE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -r|--real)
            MOCK=0
            shift
            ;;
        -p|--provider)
            PROVIDERS="${PROVIDERS} $2"
            shift 2
            ;;
        --model)
            MODEL_OVERRIDE="${MODEL_OVERRIDE} $2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Choose which script to run based on mock/real mode
if [ $MOCK -eq 1 ]; then
    echo "Running in MOCK mode (no real API calls)"
    
    # Create a temporary mock test script
    TMP_SCRIPT="$OUTPUT_DIR/mock_test_$MODULE.py"
    cat > "$TMP_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Mock test that doesn't make real API calls
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from unittest.mock import patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mock_test")

# Import LLMTester
from llm_tester import LLMTester

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run LLM tester with mock responses")
    parser.add_argument("--module", default="job_ads", help="Module to test")
    parser.add_argument("--output", default="test_results", help="Output directory")
    parser.add_argument("--models", nargs="+", help="Model overrides in format provider:model")
    parser.add_argument("--providers", nargs="+", default=["openai", "anthropic", "mistral", "google"], 
                        help="Providers to test")
    return parser.parse_args()

# Parse model overrides
def parse_model_overrides(model_args):
    """Parse model override arguments"""
    models = {}
    if not model_args:
        return models
    
    for arg in model_args:
        if ":" not in arg:
            logger.warning(f"Ignoring invalid model specification '{arg}'. Format should be 'provider:model_name'")
            continue
        
        provider, model_name = arg.split(":", 1)
        models[provider] = model_name
    
    return models

# Mock the provider manager's get_response method
def mock_get_response(self, provider, prompt, source, model_name=None):
    """Mock the get_response method to return the expected response"""
    logger.info(f"Mock call to {provider} (model: {model_name})")
    
    # Find the expected response for this test
    module = args.module
    test_name = "complex"  # Default to complex
    
    # Try to determine the test name from the source text
    if "FULL STACK DEVELOPER" in source:
        test_name = "simple"
    
    # Load the expected response
    expected_file = Path(f"llm_tester/tests/cases/{module}/expected/{test_name}.json")
    if expected_file.exists():
        with open(expected_file, "r") as f:
            response_data = json.load(f)
        return json.dumps(response_data, indent=2)
    else:
        logger.warning(f"Expected file not found: {expected_file}")
        return "{}"

# Run a mock test
def run_mock_test(args):
    """Run a test with mocked API calls"""
    logger.info(f"Running mock test for module: {args.module}")
    
    # Parse model overrides
    model_overrides = parse_model_overrides(args.models)
    
    # Patch the get_response method
    with patch("llm_tester.utils.provider_manager.ProviderManager.get_response", 
               mock_get_response):
        # Initialize tester with all providers
        providers = args.providers
        
        tester = LLMTester(providers=providers)
        
        # Run tests with model overrides
        logger.info("Running tests with mock responses...")
        results = tester.run_tests(model_overrides=model_overrides)
        
        # Generate and save report
        report = tester.generate_report(results)
        report_path = Path(args.output) / f"{args.module}_test_report.md"
        with open(report_path, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {report_path}")
        
        # Run optimized tests
        logger.info("Running optimized tests with mock responses...")
        optimized_results = tester.run_optimized_tests(
            model_overrides=model_overrides)
        
        # Generate and save optimized report
        optimized_report = tester.generate_report(optimized_results, optimized=True)
        optimized_report_path = Path(args.output) / f"{args.module}_optimized_test_report.md"
        with open(optimized_report_path, "w") as f:
            f.write(optimized_report)
        logger.info(f"Optimized report saved to {optimized_report_path}")
        
        print("\nTest Summary:")
        for test_name, test_results in results.items():
            print(f"  {test_name}:")
            for provider, provider_result in test_results.items():
                validation = provider_result.get('validation', {})
                accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                model = provider_result.get('model', 'default')
                print(f"    {provider} ({model}): {accuracy:.2f}%")

if __name__ == "__main__":
    args = parse_args()
    run_mock_test(args)
EOF

    # Make the script executable
    chmod +x "$TMP_SCRIPT"
    
    # Run the mock test script
    MODEL_ARGS=""
    if [ -n "$MODEL_OVERRIDE" ]; then
        MODEL_ARGS="--models $MODEL_OVERRIDE"
    fi
    
    PROVIDER_ARGS=""
    if [ -n "$PROVIDERS" ]; then
        PROVIDER_ARGS="--providers $PROVIDERS"
    fi
    
    echo "Running: python $TMP_SCRIPT --module $MODULE --output $OUTPUT_DIR $MODEL_ARGS $PROVIDER_ARGS"
    python "$TMP_SCRIPT" --module "$MODULE" --output "$OUTPUT_DIR" $MODEL_ARGS $PROVIDER_ARGS
    
else
    echo "Running with REAL API calls"
    # Check if API keys are set up
    if [ ! -f ".env" ]; then
        echo "Warning: .env file not found. Creating from template..."
        cp llm_tester/.env.example .env
        echo "Please edit the .env file with your API keys before running with real API calls."
        exit 1
    fi
    
    # Build command for real API calls
    CMD="python -m llm_tester.cli"
    
    # Add model overrides if specified
    if [ -n "$MODEL_OVERRIDE" ]; then
        CMD="$CMD --models $MODEL_OVERRIDE"
    fi
    
    # Add providers if specified
    if [ -n "$PROVIDERS" ]; then
        CMD="$CMD --providers $PROVIDERS"
    fi
    
    # Add output file
    CMD="$CMD --output $OUTPUT_DIR/${MODULE}_test_report.md"
    
    # Run the command
    echo "Running: $CMD"
    eval "$CMD"
    
    # Run with optimization
    CMD="$CMD --optimize --output $OUTPUT_DIR/${MODULE}_optimized_test_report.md"
    echo "Running: $CMD"
    eval "$CMD"
fi

echo "Testing completed. Reports are in the $OUTPUT_DIR directory."