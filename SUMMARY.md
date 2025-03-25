# LLM Tester Project Summary

## Overview

Python module called `llm_tester` that evaluates how well different Large Language Models (LLMs) perform at extracting structured information from unstructured text. The framework uses pydanticAI to validate responses against predefined data models.

## Project Structure

```
llm_tester/
├── __init__.py          # Package initialization
├── llm_tester.py        # Main tester class
├── cli.py               # Command-line interface
├── models/              # Pydantic model definitions
│   ├── __init__.py
│   ├── job_ads/         # Job advertisement models
│   │   ├── __init__.py
│   │   └── model.py     # JobAd model
│   └── ...              # Other model categories
├── tests/
│   ├── __init__.py
│   └── cases/           # Test cases organized by category
│       ├── job_ads/     # Job advertisement test cases
│       │   ├── expected/   # Expected JSON outputs
│       │   ├── prompts/    # Prompt templates
│       │   └── sources/    # Source text materials
│       └── ...          # Other test case categories
└── utils/               # Utility functions
    ├── __init__.py
    ├── provider_manager.py    # Manages LLM provider connections
    ├── prompt_optimizer.py    # Optimizes prompts based on results
    └── report_generator.py    # Generates test reports
```

## Key Components

1. **LLMTester Class** - The main class that runs tests and generates reports
2. **JobAd Model** - A pydantic model representing structured job advertisement data
3. **Provider Manager** - Handles connections to LLM providers (OpenAI, Anthropic, Mistral)
4. **Prompt Optimizer** - Improves prompts based on test results
5. **Report Generator** - Creates detailed performance reports
6. **Command-line Interface** - Provides easy access to testing functionality

## Sample Test Cases

We've created two sample job advertisement test cases:
1. Senior Machine Learning Engineer - A complex job posting
2. Full Stack Developer - Another job posting

Each test case includes:
- Source text (the job posting)
- Expected JSON output
- Prompt for the LLM

## Running Tests

Tests can be run through the CLI:

```bash
# Run all tests
python -m llm_tester.cli

# List available tests
python -m llm_tester.cli --list

# Run with optimized prompts
python -m llm_tester.cli --optimize
```

## Unit Tests

We've added comprehensive unit tests using pytest:
- Tests for the LLMTester class
- Tests for the CLI
- Mock tests that don't require actual LLM API calls

## Next Steps

From todo.txt:
1. Add more model categories beyond job ads
2. Implement advanced prompt optimization strategies
3. Add support for more LLM providers
4. Create visual reports
5. Implement caching for LLM responses
6. Add support for additional input formats
7. Create a web interface for testing

## Note

The tests running LLM models will require API keys for each provider (OpenAI, Anthropic, Mistral) to be set as environment variables or passed through a configuration file.
