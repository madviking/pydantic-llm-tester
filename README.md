# LLM Tester

A powerful Python framework for benchmarking, comparing, and optimizing various LLM providers through structured data extraction tasks. 
Framwork relies on Pydantic models for data structure definition and gives a percentage accuracy score for each provider and a cost.

## Purpose

LLM Tester solves three key challenges in LLM development and evaluation:

1. **Consistent Evaluation**: Objectively measure how accurately different LLMs extract structured data
2. **Prompt Optimization**: Automatically refine prompts to improve extraction accuracy
3. **Cost Analysis**: Track token usage and costs across providers to optimize for performance/cost ratio

The framework is designed to help you determine which LLM provider and model best suits your specific data extraction needs, while also helping optimize prompts for maximum accuracy.

You will see very quickly, that the accuracy even between runs fluctuates a lot. I'm using this also to see when models are "having a bad day." Multi-pass and sway calculation is also along then way, as well as sway calculation over time. 

## Architecture

LLM Tester features a flexible, pluggable architecture that supports multiple integration methods:

### Pluggable LLM Providers

The system supports three types of provider implementations:

1. **Native Implementations**: Direct integration with provider APIs (OpenAI, Anthropic, Mistral, Google, OpenRouter)
   - Provider-specific code is encapsulated in dedicated classes
   - Each provider has standardized configuration in `config.json` (Note: OpenRouter dynamically fetches model details like cost/limits from its API, overriding static config values).
   - Token usage and costs are automatically tracked

2. **PydanticAI Integration**: Use the PydanticAI library as an abstraction layer
   - Leverage PydanticAI's structured data extraction capabilities
   - Benefit from PydanticAI's optimizations and error handling
   - Use the same Pydantic models across different providers

3. **Mock Implementations**: Test without API keys
   - Simulate provider responses for development and testing
   - Include realistic token counts and timing
   - Great for CI/CD pipelines or offline development

Adding a new provider requires minimal effort - just create a directory under `llm_tester/llms/` with a provider implementation and configuration file.

## Features

- Test multiple LLM providers (OpenAI, Anthropic, Mistral, Google)
- Validate responses against Pydantic models
- Calculate accuracy compared to expected results
- Optimize prompts for better performance
- Generate detailed test reports
- Centralized configuration management
- Enhanced mock response system for testing without API keys
- Track token usage and cost across providers

## Supported Models

1. Job Advertisements
   - Extract structured job information including title, company, skills, etc.

2. Product Descriptions
   - Extract product details including specifications, pricing, etc.

## Installation

```bash
# Clone the repository
# git clone https://github.com/yourusername/llm-tester.git # Replace with actual repo URL
cd llm-tester

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API Keys (Interactive)
python -m llm_tester.cli configure keys
# This will prompt for missing keys found in provider configs and offer to save them to llm_tester/.env
```
Make sure your API keys are set in `llm_tester/.env` or as environment variables. The `configure keys` command helps with this.

## Running via CLI

The primary way to run tests and manage the tool is via the command-line interface.

```bash
# Make sure the virtual environment is activated
source venv/bin/activate

# --- Running Tests (Default Command) ---

# Run tests using all enabled providers and their default models
python -m llm_tester.cli

# Run tests for specific providers
python -m llm_tester.cli --providers openai anthropic

# Run tests using specific models for providers
python -m llm_tester.cli --providers openai openrouter --models openai:gpt-4o openrouter/google/gemini-pro-1.5

# Run tests and save report to a file
python -m llm_tester.cli --output my_report.md

# Run tests with prompt optimization
python -m llm_tester.cli --optimize

# List available test cases and configured providers/models without running
python -m llm_tester.cli --list

# Filter tests by name (e.g., only 'simple' tests in 'job_ads')
python -m llm_tester.cli --filter job_ads/simple

# Increase verbosity for debugging
python -m llm_tester.cli -vv

# --- Configuration & Management ---

# Configure API Keys (Interactive Prompt)
python -m llm_tester.cli configure keys

# Update Model Info (e.g., pricing/limits) from OpenRouter API
python -m llm_tester.cli update-models --provider openrouter

# List all discoverable providers and their enabled/disabled status
python -m llm_tester.cli providers list

# Enable a provider (adds to or creates enabled_providers.json)
python -m llm_tester.cli providers enable openrouter

# Disable a provider (removes from enabled_providers.json)
python -m llm_tester.cli providers disable google

# List models within a specific provider's config and their status
python -m llm_tester.cli models list --provider openrouter

# Enable a specific model within a provider's config
python -m llm_tester.cli models enable openrouter/anthropic/claude-3-haiku

# Disable a specific model within a provider's config
python -m llm_tester.cli models disable openai:gpt-3.5-turbo

# Get LLM-assisted model recommendations for a task (Interactive Prompt)
python -m llm_tester.cli recommend-model
```

## Usage

```python
from llm_tester import LLMTester

# Initialize tester with providers
tester = LLMTester(providers=["openai", "anthropic", "google", "mistral"])

# Run tests
results = tester.run_tests()

# Generate report
report = tester.generate_report(results)
print(report)

# Run optimized tests
optimized_results = tester.run_optimized_tests()
optimized_report = tester.generate_report(optimized_results, optimized=True)
```

## Provider System

LLM Tester uses a pluggable provider system that makes it easy to add and configure different LLM providers:

### Native Provider Integration

To use a native provider integration:

```python
tester = LLMTester(providers=["openai", "anthropic", "google", "mistral"])
```

Native providers directly call the respective provider's API with optimized parameters.

### PydanticAI Integration

To use the PydanticAI integration:

```python
tester = LLMTester(providers=["pydantic_ai"])
```

This will use PydanticAI's extraction capabilities with your specified model.

### Mock Testing

For testing without API keys:

```python
tester = LLMTester(providers=["mock"])
```

Mock providers simulate responses based on the test case structure.

## Adding New Providers

1. Create a new directory in `llm_tester/llms/your_provider/`
2. Implement a provider class that inherits from `BaseLLM` (see `llm_tester/llms/base.py`).
3. Create a `config.json` file with provider settings (`name`, `env_key`, etc.) and a list of `models` with their details (cost, tokens). See existing provider configs for examples.
   *(Note: For OpenRouter, costs and token limits are fetched dynamically via `update-models` or on load, overriding static values in `config.json`)*.
4. Add `from .provider import YourProviderClass` to the provider's `__init__.py` to ensure discovery.
5. Optionally, enable the provider using `python -m llm_tester.cli providers enable your_provider`.

## Adding New Extraction Models

1. Create a new directory in `llm_tester/models/your_model_type/`
2. Implement your Pydantic model in `model.py` with these components:
   - Define your model class extending BaseModel
   - Add class variables for module configuration: MODULE_NAME, TEST_DIR, REPORT_DIR
   - Implement the `get_test_cases()` class method
   - Implement the `save_module_report()` and `save_module_cost_report()` class methods
3. Create the test structure:
   - Create `llm_tester/models/your_model_type/tests/` directory
   - Add `sources/` for input data files
   - Add `prompts/` for prompt templates
   - Add `expected/` for expected output JSON
   - Create `reports/` directory for module-specific reports
4. Add appropriate `__init__.py` files to ensure proper imports

NOTE: you can add new model / module also with the CLI tool.

## Verifying Provider Setup

You can verify your provider setup, check configurations, and see model availability using the CLI:

```bash
# List discovered providers and enabled status
python -m llm_tester.cli providers list

# List models within a specific provider's config
python -m llm_tester.cli models list --provider <provider_name>
```
The old `./verify_providers.py` script may still exist but the CLI commands are the recommended way to check status.


## General implementation notes

This package is written initially using Claude Code, using only minimum manual intervention and edits. Further improvements are made with Cline, using Gemini 2.5. LLM generated code is reviewed and tested by the author and all of the architectural decisions are mine. 


## License

MIT

---

© 2025 Timo Railo
