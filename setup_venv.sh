#!/bin/bash
# Script to set up a virtual environment for LLM Tester

# Exit on any error
set -e

echo "Setting up Virtual Environment for LLM Tester"
echo "============================================="

# Check if venv is installed
if ! command -v python3 -m venv &> /dev/null; then
    echo "python3 venv is not installed or not in PATH"
    echo "Please install it with: python3 -m pip install virtualenv"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp llm_tester/.env.example .env
    echo "Please edit the .env file with your API keys."
fi

# Activate the virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
echo "Activate on your own using:"
echo "source venv/bin/activate"
echo "Then install dependencies with:"
echo "pip install -r requirements.txt"
echo "pip install -e ."

# Instructions for testing
echo ""
echo "Once dependencies are installed, you can run tests with:"
echo "./run_test.sh --module job_ads"
echo ""
echo "Options:"
echo "  -m, --module MODULE     Module to test (default: job_ads)"
echo "  -o, --output DIR        Output directory for test results (default: test_results)"
echo "  -r, --real              Use real API calls instead of mock calls"
echo "  -p, --provider PROVIDER Use specific providers (can be used multiple times)"
echo "  --model PROVIDER:MODEL  Override model for provider (can be used multiple times)"
echo ""
echo "Example:"
echo "./run_test.sh -m job_ads --model openai:gpt-4-turbo --model anthropic:claude-3-sonnet-20240229"
echo ""
echo "For real API calls (requires API keys in .env):"
echo "./run_test.sh -m job_ads -r"