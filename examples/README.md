# LLM Tester Examples

This directory contains example scripts demonstrating various use cases for the LLM Tester library.

## Available Examples

- `run_mock_test.py`: Run tests with mock responses (no API keys needed)
- `run_mock_test_with_products.py`: Run tests with both job ads and product descriptions models
- `run_with_google.py`: Example of using Google's Gemini model

## Using the Examples

These example scripts are provided for reference. The recommended way to use LLM Tester is through the interactive runner:

```bash
# From the project root directory
./runner.py
```

## Creating Your Own Examples

If you want to create your own usage examples, you can use these scripts as a starting point.

Here's a minimal example:

```python
import sys
from pathlib import Path

# Add the parent directory to the path to import llm_tester
sys.path.append(str(Path(__file__).parent.parent))

from llm_tester import LLMTester

# Initialize the tester with a specific provider
tester = LLMTester(providers=["openai"])

# Run tests and generate a report
results = tester.run_tests()
report = tester.generate_report(results)
print(report)
```