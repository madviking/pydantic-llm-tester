# LLM Tester

A Python module for testing and comparing different LLM models using PydanticAI to extract structured data from text.

## Features

- Test multiple LLM providers (OpenAI, Anthropic, Mistral, Google)
- Validate responses against Pydantic models
- Calculate accuracy compared to expected results
- Optimize prompts for better performance
- Generate detailed test reports

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

# Install the package
pip install -e .
```

## Environment Setup

Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
MISTRAL_API_KEY=your_mistral_key
GOOGLE_PROJECT_ID=your_google_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
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

## CLI Usage

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

## Mock Testing

For development without API keys, use the mock test examples:

```bash
python examples/run_mock_test.py
python examples/run_mock_test_with_products.py
```

## Adding New Models

1. Create a new directory in `llm_tester/models/your_model_type/`
2. Implement your Pydantic model in `model.py`
3. Add test cases in `llm_tester/tests/cases/your_model_type/`
   - Add source files in `sources/`
   - Add prompts in `prompts/`
   - Add expected outputs in `expected/`

## License

MIT