# LLM Tester Development Guide

This document provides an overview of the LLM Tester codebase architecture and guidelines for development.

## Project Structure

```
llm_tester/
├── __init__.py           # Package initialization
├── cli.py                # Command-line interface
├── llm_tester.py         # Main tester implementation
├── models/               # Pydantic model definitions
│   ├── job_ads/          # Job advertisement models
│   └── product_descriptions/ # Product description models
├── tests/                # Test cases and expected results
│   └── cases/            # Test cases by model type
└── utils/                # Utility modules
    ├── config_manager.py # Configuration management
    ├── mock_responses.py # Mock response system
    ├── prompt_optimizer.py # Prompt optimization
    ├── provider_manager.py # LLM provider connections
    └── report_generator.py # Report generation
```

## Core Components

### Configuration Management

The `config_manager.py` module centralizes all configuration-related functionality:

- Loading and saving configuration from `config.json`
- Getting enabled providers and their settings
- Accessing and updating test settings
- Retrieving provider-specific model information

```python
from llm_tester.utils.config_manager import load_config, get_enabled_providers, get_test_setting

# Get configuration
config = load_config()

# Get enabled providers
providers = get_enabled_providers()

# Get specific test setting
output_dir = get_test_setting("output_dir", default="test_results")
```

### Provider Manager

The `provider_manager.py` handles connections to different LLM providers:

- Initializing provider clients with appropriate API keys
- Managing provider-specific request formats
- Handling error states when providers are unavailable
- Providing a unified interface for all providers

### Mock Response System

The `mock_responses.py` module provides mock responses for testing without API keys:

- Template-based responses for different model types
- Content customization based on source text
- Intelligent response selection based on context cues
- Compatible interface with the real provider manager

```python
from llm_tester.utils.mock_responses import mock_get_response

# Get a mock response
response = mock_get_response(
    provider="any_provider",
    prompt="Extract job details",
    source="POSITION: Software Engineer\nCOMPANY: Tech Corp"
)
```

### Prompt Optimizer

The `prompt_optimizer.py` module improves prompts based on initial test results:

- Analyzing validation errors and accuracy issues
- Identifying problematic fields in responses
- Adding specific instructions for improvement
- Saving optimized prompts for future use

### LLM Tester Core

The `llm_tester.py` main class integrates all components:

- Discovering and loading test cases
- Finding appropriate model classes
- Running tests across providers
- Validating responses against expected results
- Calculating accuracy metrics
- Managing prompt optimization workflow

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_config_manager.py
pytest tests/test_mock_responses.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=llm_tester
```

## Development Workflow

1. Create or update unit tests for new functionality
2. Implement changes in the codebase
3. Run tests to ensure functionality works as expected
4. Update documentation to reflect changes
5. Submit a pull request with your changes

## Adding New Provider Support

To add a new LLM provider:

1. Update `provider_manager.py` with a new client initialization method
2. Add provider-specific request handling 
3. Update the `get_response` method to support the new provider
4. Add mock responses for the provider in `mock_responses.py`
5. Update configuration defaults in `config_manager.py`

## Adding New Model Types

To add a new model type:

1. Create a new directory in `models/`
2. Implement the Pydantic model in `model.py`
3. Add test cases in `tests/cases/your_model_type/`
4. Add mock response templates in `mock_responses.py`
5. Update the model discovery logic in `_find_model_class()`