#!/bin/bash
# Script to run the pytest tests

# Exit on any error
set -e

echo "Running LLM Tester Tests"
echo "========================"

# If venv exists, activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. You may need to run setup_venv.sh first."
fi

# Run the tests
echo "Running pytest tests..."
python -m pytest -v "$@"

echo "Tests completed."