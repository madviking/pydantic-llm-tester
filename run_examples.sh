#!/bin/bash
# Script to run examples showing LLM tester usage

echo "LLM Tester Examples"
echo "==================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp llm_tester/.env.example .env
    echo "Please edit the .env file with your API keys before running examples."
    exit 1
fi

# Create examples directory if it doesn't exist
mkdir -p examples

echo "Running CLI example..."
echo "---------------------"
python -m llm_tester.cli --list

echo ""
echo "Running Google Gemini example (requires Google Cloud credentials)..."
echo "------------------------------------------------------------------"
python examples/run_with_google.py 

echo ""
echo "Examples completed. Check report files in the examples directory."