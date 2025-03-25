# LLM Tester Test Cases

This directory contains test cases for the LLM Tester module.

## Directory Structure

```
tests/
├── __init__.py
├── cases/
│   ├── job_ads/
│   │   ├── expected/
│   │   ├── prompts/
│   │   └── sources/
│   └── product_descriptions/
│       ├── expected/
│       ├── prompts/
│       └── sources/
├── expected/
├── prompts/
└── sources/
```

## Test Case Organization

Each test domain (like job_ads or product_descriptions) has the following components:

1. **sources/**: Text files containing the raw input data to be processed by the LLM
2. **prompts/**: Prompt templates used to instruct the LLM on how to extract data
3. **expected/**: Expected JSON output to validate LLM extraction accuracy

## Adding New Test Cases

1. Create a new file in the appropriate `sources/` directory
2. Add a corresponding prompt in the `prompts/` directory (with the same base name)
3. Create an expected output JSON file in the `expected/` directory (with the same base name)

For example, to add a new job ad test case:
- Create `cases/job_ads/sources/new_example.txt`
- Create `cases/job_ads/prompts/new_example.txt`
- Create `cases/job_ads/expected/new_example.json`

## Running Tests

To run tests on all available test cases:

```bash
python -m llm_tester.cli --list  # List available test cases
python -m llm_tester.cli  # Run all tests
```

For development without API keys, use the mock testing scripts:

```bash
python examples/run_mock_test.py
python examples/run_mock_test_with_products.py
```