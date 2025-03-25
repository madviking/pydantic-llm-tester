# LLM Tester

A Python module for testing and comparing different LLM models using PydanticAI to extract structured data from text. 

## Features

- Test multiple LLM providers (OpenAI, Anthropic, Mistral, Google)
- Validate responses against Pydantic models
- Calculate accuracy compared to expected results
- Optimize prompts for better performance
- Generate detailed test reports
- Centralized configuration management
- Enhanced mock response system for testing without API keys

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

## Mock Testing

The interactive runner includes a mock mode for testing without API keys. When configuring providers, select the "Mock" option to use the built-in mock responses.

## Advanced CLI Usage

While the interactive runner is recommended, you can also use the CLI directly:

```bash
# Run basic tests
python -m llm_tester.cli --providers openai anthropic

# List available test cases
python -m llm_tester.cli --list

# Run with specific models
python -m llm_tester.cli --models openai:gpt-4 anthropic:claude-3-opus

# Generate JSON output
python -m llm_tester.cli --json --output results.json
```

## Adding New Models

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

## License

MIT
