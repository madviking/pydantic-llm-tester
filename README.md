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

1. **Native Implementations**: Direct integration with provider APIs (OpenAI, Anthropic, Mistral, Google)
   - Provider-specific code is encapsulated in dedicated classes
   - Each provider has standardized configuration in `config.json`
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
git clone https://github.com/yourusername/llm-tester.git
cd llm-tester

# Run the installation script
chmod +x install.sh
./install.sh
```

The installation script will:
- Create a virtual environment
- Install required dependencies
- Create a template .env file for your API keys

## Running the Tool

### Interactive Mode

```bash
# Make sure the virtual environment is activated
source venv/bin/activate

# Run the interactive tool
./runner.py
```

The interactive runner provides a menu-driven interface to:
- Check your setup and API keys
- List available test cases
- Configure which providers and models to use
- Run tests with or without prompt optimization
- View and save test results

### Non-Interactive Mode

You can also run tests directly using default settings without any prompts:

```bash
# Run with default settings (providers from config)
./runner.py --non-interactive

# Run with specific providers
./runner.py -n -p openai -p anthropic

# Run optimized tests
./runner.py -n --optimize

# Run specific modules
./runner.py -n -m job_ads -m product_descriptions

# Specify output directory
./runner.py -n --output-dir ./my_results
```

Command line options for non-interactive mode:
- `-n, --non-interactive`: Run in non-interactive mode using defaults
- `-o, --optimize`: Run with prompt optimization
- `-p, --provider`: Provider to use (can be specified multiple times)
- `-m, --module`: Module to test (can be specified multiple times)
- `--output-dir`: Directory to save results
- `--debug`: Enable debug logging

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
2. Implement a provider class that inherits from `BaseLLM`
3. Create a `config.json` file with model configurations
4. Add initialization code in the provider's `__init__.py`

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

You can verify your provider setup by running:

```bash
./verify_providers.py
```

This will check all discovered providers, their configurations, and available models.


## General implementation note

This package is written from the ground up using Claude Code, using only minimum manual intervention. Claude
written code is reviewed and tested by the author. Test coverage is good, but not 100%.

## License

MIT

---

*Built with the help of Claude Code - A demonstration of AI-assisted software development using Claude 3.5 Sonnet*
© 2025 Timo Railo
