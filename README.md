# LLM Tester

A powerful Python framework for benchmarking, comparing, and optimizing various LLM providers through structured data extraction tasks. It also serves as a bridge to easily integrate LLM functionalities into your applications using Pydantic models for structured data extraction.

## Purpose

LLM Tester helps you:

1.  **Evaluate LLMs**: Objectively measure how accurately different LLMs extract structured data.
2.  **Optimize Prompts**: Refine prompts to improve extraction accuracy.
3.  **Analyze Costs**: Track token usage and costs across providers.
4.  **Integrate LLMs**: Easily add structured data extraction capabilities to your Python applications.

The framework provides a consistent way to interact with various LLM providers and evaluate their performance on your specific data extraction needs.

## Architecture

LLM Tester features a flexible, pluggable architecture for integrating with LLM providers. It supports native API integrations (including OpenAI, Anthropic, Mistral, Google, and OpenRouter), PydanticAI integration, and mock implementations for testing.

For more details on the architecture, see the [documentation](docs/README.md).

## Features

-   Benchmark and compare multiple LLM providers.
-   Validate responses against Pydantic models.
-   Calculate extraction accuracy.
-   Optimize prompts for better results.
-   Generate detailed test reports.
-   Manage configuration centrally.
-   Use mock providers for testing without API keys.
-   Track token usage and costs.
-   Easily integrate structured data extraction into your applications.
-   **Query model prices**: Compare pricing across providers and models to make cost-effective decisions.
-   **Configure models**: Add, edit, and manage LLM models for each provider.
-   **Update cost information**: Keep pricing data current with OpenRouter API integration.
-   **File Upload Support**: Process and test LLMs with file inputs (e.g., images) for multimodal analysis. See the [guide on Using Files](docs/guides/files/USING_FILES.md) for more details.

## A word about *word* models

Unfortunately things can get little confusing with the word *model*, so I've opted to use py_models and llm_models as the terms. 
-   **py_models**: Refers to the Pydantic models used for structured data extraction.
-   **llm_models**: Refers to the LLM models provided by various providers (e.g., OpenAI, Anthropic).

## Example Pydantic Models

LLM Tester includes example models for common extraction tasks:

1.  **Job Advertisements**: Extract structured job information.
2.  **Product Descriptions**: Extract product details.

You can easily add your own custom models for specific tasks. See the [documentation](docs/guides/models/ADDING_MODELS.md) for details.

## Installation

You can install `llm-tester` from PyPI or by cloning the repository.

### Installing from PyPI

```bash
pip install pydantic-llm-tester
```

### Installing from Source

```bash
# Clone the repository
# git clone https://github.com/yourusername/llm-tester.git # Replace with actual repo URL
cd llm-tester

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .
```

### Configuration

After installation, configure your API keys:

```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Configure API Keys (Interactive)
llm-tester configure keys
# This will prompt for missing keys found in provider configs and offer to save them to the default .env path (e.g., src/pydantic_llm_tester/.env or project root).
```
Make sure your API keys are set in the `.env` file (at the default location or specified via `--env`) or as environment variables. The `llm-tester configure keys` command helps manage this.

## Usage

LLM Tester can be used via the command-line interface (CLI) or as a Python library in your applications.

### CLI Usage

The primary way to use the tool is via the `llm-tester` command after activating your virtual environment.

```bash
# Make sure the virtual environment is activated
source venv/bin/activate

# Show help and available commands
llm-tester --help
```

For detailed CLI command references, see the [documentation](docs/guides/cli_commands/).

Key CLI commands:

-   **Scaffolding**: Quickly set up new providers and models.
    ```bash
    llm-tester scaffold --help
    ```
    It is recommended to start by scaffolding a new model or provider.

-   **Model Prices**: Query and display pricing information for LLM models.
    ```bash
    llm-tester prices --help
    ```
    See [Prices Documentation](docs/guides/cli_commands/PRICES.md) for details.

-   **Model Configuration**: Manage LLM models for providers (add, edit, remove, list).
    ```bash
    llm-tester models --help
    ```
    See [Models Documentation](docs/guides/cli_commands/MODELS.md) for details.

-   **Cost Management**: Update and manage model costs from OpenRouter API.
    ```bash
    llm-tester costs --help
    ```
    See [Costs Documentation](docs/guides/cli_commands/COSTS.md) for details.

-   **Running Tests**: Execute tests against configured providers.
    ```bash
    llm-tester run --help
    ```

-   **Example: Run a particular test that uses a file with a full debugging**: Testing specific file
    ```bash
    llm-tester -vv run -p openai -m job_ads -f job_ad_from_image --llm_models openai:gpt-4
    ```

-   **Configuration**: Manage API keys and provider settings.
    ```bash
    llm-tester configure --help
    ```

-   **Listing**: List available models, providers, and test cases.
    ```bash
    llm-tester list --help
    ```

-   **Providers**: Enable/disable providers and manage their models.
    ```bash
    llm-tester providers --help
    ```

-   **Schemas**: List available extraction schemas.
    ```bash
    llm-tester schemas --help
    ```

-   **Recommendations**: Get LLM-assisted model recommendations.
    ```bash
    llm-tester recommend-model --help
    ```

-   **Interactive Mode**: Launch a menu-driven session.
    ```bash
    llm-tester interactive
    ```


### Python API Usage

You can integrate LLM Tester into your Python applications. See the [documentation](docs/guides/USING_THE_API.md) for detailed API usage.

```python
from pydantic_llm_tester import LLMTester # For using the installed package
# Or, if running from source for development:
# from pydantic_llm_tester.llm_tester import LLMTester

# Example: Using LLM Tester as a bridge for structured data extraction
# Initialize tester with providers and your custom py_models directory
tester = LLMTester(providers=["openai"], test_dir="/path/to/your/custom/py_models")

# Assuming you have a model named 'my_task' in your custom py_models directory
# and a test case named 'example' with source and prompt files.

# You can directly run a specific test case by name
# This requires knowing the test case ID (module_name/test_case_name)
# In this example, let's assume a test case 'my_task/example' exists.
# You would typically discover test cases first:
# test_cases = tester.discover_test_cases(modules=["my_task"])
# example_test_case = next((tc for tc in test_cases if tc['name'] == 'example'), None)

# For a simple "Hello World" style example using an external model:
# 1. Scaffold a new model: llm-tester scaffold model --interactive (e.g., name it 'hello_world')
# 2. Update the generated model.py to define a simple schema (e.g., just a 'greeting' field).
# 3. Update the generated tests/sources/example.txt and tests/prompts/example.txt
#    Source: "Hello, world!"
#    Prompt: "Extract the greeting from the text."
#    Expected: {"greeting": "Hello, world!"}
# 4. Run the test using the CLI: llm-tester run --test-dir /path/to/your/custom/py_models --providers mock --py_models mock:mock-model --filter hello_world/example
#    (Using mock provider for simplicity, replace with real provider if configured)

# Programmatic "Hello World" example (assuming the 'hello_world' model is set up as above)
# Define a simple model class directly for demonstration (or import from your external model file)
from pydantic import BaseModel


class HelloWorldModel(BaseModel):
    greeting: str


# Define a simple test case structure
hello_world_test_case = {
    'module': 'hello_world',
    'name': 'example',
    'model_class': HelloWorldModel,
    'source_path': '/path/to/your/custom/py_models/hello_world/tests/sources/example.txt',  # Replace with actual path
    'prompt_path': '/path/to/your/custom/py_models/hello_world/tests/prompts/example.txt',  # Replace with actual path
    'expected_path': '/path/to/your/custom/py_models/hello_world/tests/expected/example.json'  # Replace with actual path
}

# Initialize tester with a provider (e.g., mock for this example) and the directory containing your model
tester = LLMTester(providers=["mock"], test_dir="/path/to/your/custom/py_models")  # Replace path and provider as needed

# Run the specific test case
results = tester.run_test(hello_world_test_case)

# Process and print the result
print("\nHello World Test Result:")
for provider, result in results.items():
    print(f"Provider: {provider}")
    if "error" in result:
        print(f"  Error: {result['error']}")
    else:
        print(f"  Success: {result.get('validation', {}).get('success')}")
        print(f"  Extracted Data: {result.get('extracted_data')}")
        print(f"  Accuracy: {result.get('validation', {}).get('accuracy'):.2f}%")

```

## Testing

LLM Tester includes a test suite using `pytest` to ensure the framework's functionality and stability.

To run the tests:

```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Run all tests
pytest

# Run tests for a specific module (e.g., CLI commands)
pytest tests/cli/
```

For more details on testing, see the [documentation](docs/README.md). (Note: A dedicated testing guide is planned).

## Provider System

LLM Tester uses a pluggable provider system. See the [documentation](docs/architecture/PROVIDER_SYSTEM.md) for architectural details and the [guide](docs/guides/providers/ADDING_PROVIDERS.md) for adding new providers.

## Adding New Models

You can easily add new extraction models using the `llm-tester scaffold model` command or by following the manual steps. See the [documentation](docs/guides/models/ADDING_MODELS.md) for details.

## General implementation notes
This package is written initially using Claude Code, using only minimum manual intervention and edits. Further improvements are made with Cline, using Gemini 2.5 and other models. LLM generated code is reviewed and tested by the author and all of the architectural decisions are mine.

## License
MIT

---

© 2025 Timo Railo
