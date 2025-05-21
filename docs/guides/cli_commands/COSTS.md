# Updating Cost Information

The `llm-tester costs` command provides tools for updating and managing model cost information from the OpenRouter API. This command helps you keep your pricing data up-to-date and ensures accurate cost tracking when running tests.

## Command Overview

The `costs` command has two subcommands:

1. `update`: Update model costs from OpenRouter API
2. `reset-cache`: Reset provider caches to force rediscovery of models and pricing

## Updating Model Costs

To update model costs from OpenRouter API:

```bash
llm-tester costs update [OPTIONS]
```

### Options

- `--providers`, `-p`: Filter by provider names (e.g., openrouter, openai)
- `--update-configs`, `-u`: Update provider config files with context length and other metadata (flag)
- `--force`, `-f`: Force refresh of OpenRouter API cache (flag)

### What This Command Does

The `costs update` command:

1. Fetches the latest model information from OpenRouter API
2. Updates the pricing information in `models_pricing.json`
3. Optionally updates provider config files with context length and other metadata
4. Displays a summary of changes (models updated, added, and unchanged)

### Examples

Update costs for all providers:

```bash
llm-tester costs update
```

Update costs for specific providers:

```bash
llm-tester costs update --providers openai anthropic
```

Update costs and provider config files:

```bash
llm-tester costs update --update-configs
```

Force refresh of OpenRouter API cache:

```bash
llm-tester costs update --force
```

## Resetting Provider Caches

To reset provider caches:

```bash
llm-tester costs reset-cache
```

This command will clear all provider caches, forcing rediscovery of models and pricing information. This is useful if you've made manual changes to config files or if you're experiencing issues with cached data.

## How Cost Information is Used

Cost information is used by the LLM Tester framework to:

1. Track token usage and costs when running tests
2. Generate cost reports for test runs
3. Help you make informed decisions about which models to use

The cost data is stored in two places:

1. `models_pricing.json`: Central repository for all model pricing information
2. Provider config files: Each provider's `config.json` file contains cost information for its models

## Common Use Cases

### Keeping Costs Up-to-Date

Regularly update cost information to ensure accurate cost tracking:

```bash
llm-tester costs update
```

### Updating After Provider Changes

When providers add new models or change pricing:

```bash
llm-tester costs update --update-configs --force
```

### Troubleshooting Cost Tracking

If you notice issues with cost tracking:

```bash
llm-tester costs reset-cache
llm-tester costs update --update-configs
```

### Updating Context Lengths

Update model context length information:

```bash
llm-tester costs update --update-configs
```

## Understanding the Update Summary

After running `costs update`, you'll see a summary of changes:

1. **Models Updated**: Models that already existed but had their pricing information updated
2. **Models Added**: New models that were added to the pricing information
3. **Models Unchanged**: Models whose pricing information remained the same

For updated models, you'll see a comparison of old and new prices. For added models, you'll see their initial pricing information.

## Troubleshooting

### API Connection Issues

If you encounter connection issues with the OpenRouter API:

1. Check your internet connection
2. Verify your OpenRouter API key is correctly configured
3. Try again later, as the API might be temporarily unavailable

### Configuration File Issues

If you encounter errors saving the configuration:

1. Check that you have write permissions to the pricing and provider configuration files
2. Verify that the configuration files are valid JSON

### Cache Issues

If you're experiencing issues with cached data:

1. Run `llm-tester costs reset-cache` to clear all provider caches
2. Run `llm-tester costs update --force` to force a refresh of the OpenRouter API cache

### Missing or Incorrect Cost Information

If you notice missing or incorrect cost information:

1. Run `llm-tester costs update --update-configs --force` to fetch the latest data
2. If the issue persists, you may need to manually edit the provider's config file or the `models_pricing.json` file