# LLM Tester Examples

This directory contains example scripts that demonstrate how to use the LLM Tester framework.

## Prerequisites

Before running any examples, make sure you:

1. Install the required dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

2. Set up your API keys in the `.env` file in the root directory (copy from `../llm_tester/.env.example`).

## Examples

### `run_with_google.py`

This script shows how to use LLM Tester with Google's Gemini models alongside other LLM providers.

Features demonstrated:
- Using multiple providers (OpenAI, Anthropic, Google, Mistral) 
- Setting model overrides for each provider
- Running both regular and optimized tests
- Generating and saving reports

To run:
```bash
python run_with_google.py
```

### Running CLI Examples

You can run the CLI tool directly:

```bash
# List available test cases
python -m llm_tester.cli --list

# Run tests with specific providers
python -m llm_tester.cli --providers openai anthropic

# Run tests with specific models
python -m llm_tester.cli --models openai:gpt-4-turbo anthropic:claude-3-haiku-20240307

# Run optimized tests and save report
python -m llm_tester.cli --optimize --output test_report.md
```

## Generated Reports

When running the examples, reports will be generated and saved in this directory:

- `test_report.md`: Standard test results
- `optimized_test_report.md`: Results with optimized prompts

These reports show how different LLM models perform on the test cases and how prompt optimization improves their performance.