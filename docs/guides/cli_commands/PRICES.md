# Querying Model Prices

The `llm-tester prices` command provides a convenient way to query and display pricing information for LLM models across different providers. This helps you make informed decisions about which models to use based on their cost and capabilities.

## Command Overview

The `prices` command has two subcommands:

1. `list`: List and filter model prices from all providers
2. `refresh`: Refresh model prices from OpenRouter API

## Listing Model Prices

To list model prices:

```bash
llm-tester prices list [OPTIONS]
```

### Options

- `--providers`, `-p`: Filter by provider names (e.g., openrouter, openai)
- `--model`, `-m`: Filter by model name pattern (regex)
- `--max-cost`: Filter by maximum cost per 1M tokens (input + output combined)
- `--min-context`: Filter by minimum context length (input + output tokens)
- `--sort-by`, `-s`: Field to sort results by. Available options:
  - `total_cost`: Total cost per 1M tokens (default)
  - `name`: Model name
  - `provider`: Provider name
  - `context_length`: Total context length
  - `cost_input`: Input cost per 1M tokens
  - `cost_output`: Output cost per 1M tokens
- `--asc/--desc`: Sort in ascending (`--asc`, default) or descending (`--desc`) order

### Examples

List all model prices sorted by total cost (cheapest first):

```bash
llm-tester prices list
```

List only OpenAI models:

```bash
llm-tester prices list --providers openai
```

List models with "gpt" in their name:

```bash
llm-tester prices list --model gpt
```

List models with at least 16K context length:

```bash
llm-tester prices list --min-context 16000
```

List models with a maximum cost of $10 per 1M tokens:

```bash
llm-tester prices list --max-cost 10
```

List models sorted by context length (highest first):

```bash
llm-tester prices list --sort-by context_length --desc
```

## Refreshing Model Prices

To refresh model prices from OpenRouter API:

```bash
llm-tester prices refresh
```

This command will:

1. Prompt for confirmation before proceeding
2. Fetch the latest pricing data from OpenRouter API
3. Update the local cache with the new data

Use this command when you want to ensure you have the most up-to-date pricing information, especially after OpenRouter adds new models or updates existing ones.

## Common Use Cases

### Cost Comparison

Compare the cost of different models to find the most cost-effective option for your use case:

```bash
llm-tester prices list --sort-by total_cost --asc
```

### Finding High-Context Models

Find models with large context windows for processing lengthy documents:

```bash
llm-tester prices list --min-context 32000 --sort-by context_length --desc
```

### Provider-Specific Analysis

Compare models from a specific provider:

```bash
llm-tester prices list --providers anthropic --sort-by total_cost
```

### Budget Planning

Find models within a specific budget constraint:

```bash
llm-tester prices list --max-cost 5 --sort-by total_cost
```

## Troubleshooting

### No Models Found

If no models are displayed:

1. Check if your filter criteria are too restrictive
2. Try refreshing the price data: `llm-tester prices refresh`
3. Verify that provider configurations are correctly set up

### Outdated Pricing Information

If you suspect the pricing information is outdated:

1. Run `llm-tester prices refresh` to fetch the latest data
2. Confirm the operation was successful by checking the output message

### API Connection Issues

If you encounter connection issues with the OpenRouter API:

1. Check your internet connection
2. Verify your OpenRouter API key is correctly configured
3. Try again later, as the API might be temporarily unavailable