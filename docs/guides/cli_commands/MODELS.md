# Configuring LLM Models

The `llm-tester models` command provides a comprehensive interface for managing LLM models within provider configurations. This command allows you to list, add, edit, remove, and set default models for each provider.

## Command Overview

The `models` command includes the following subcommands:

1. `list`: List all models for a specific provider
2. `add`: Add a new model to a provider's configuration
3. `edit`: Edit an existing model in a provider's configuration
4. `remove`: Remove a model from a provider's configuration
5. `set-default`: Set a model as the default for a provider

## Listing Models

To list all models for a specific provider:

```bash
llm-tester models list <PROVIDER>
```

Where `<PROVIDER>` is the name of the provider (e.g., openai, anthropic, mistral).

Example:

```bash
llm-tester models list openai
```

This will display a list of all models configured for the specified provider, including their status (default, preferred, enabled/disabled) and cost information.

## Adding Models

To add a new model to a provider's configuration:

```bash
llm-tester models add <PROVIDER> [OPTIONS]
```

### Options

- `--name`, `-n`: Name of the model (required)
- `--default`, `-d`: Set as default model for the provider (flag)
- `--preferred`, `-p`: Mark as preferred model (flag)
- `--enabled`, `-e`: Enable the model (flag, enabled by default)
- `--cost-input`, `-i`: Cost per 1M input tokens in USD (required)
- `--cost-output`, `-o`: Cost per 1M output tokens in USD (required)
- `--cost-category`, `-c`: Cost category (cheap, standard, expensive)
- `--max-input`: Maximum input tokens supported (default: 4096)
- `--max-output`: Maximum output tokens supported (default: 4096)
- `--interactive`: Use interactive mode with prompts (flag)

### Examples

Add a new model using command-line options:

```bash
llm-tester models add openai --name gpt-4-turbo --cost-input 10.0 --cost-output 30.0 --max-input 128000 --max-output 4096 --preferred
```

Add a new model using interactive mode:

```bash
llm-tester models add openai --interactive
```

## Editing Models

To edit an existing model in a provider's configuration:

```bash
llm-tester models edit <PROVIDER> <MODEL_NAME> [OPTIONS]
```

### Options

The options are the same as for the `add` command, but all are optional. Only the specified options will be updated.

### Examples

Update the cost of an existing model:

```bash
llm-tester models edit openai gpt-4 --cost-input 8.0 --cost-output 24.0
```

Enable or disable a model:

```bash
llm-tester models edit openai gpt-3.5-turbo --enabled false
```

Edit a model using interactive mode:

```bash
llm-tester models edit openai gpt-4 --interactive
```

## Removing Models

To remove a model from a provider's configuration:

```bash
llm-tester models remove <PROVIDER> <MODEL_NAME>
```

This command will prompt for confirmation before removing the model.

Example:

```bash
llm-tester models remove openai gpt-3.5-turbo
```

## Setting Default Models

To set a model as the default for a provider:

```bash
llm-tester models set-default <PROVIDER> <MODEL_NAME>
```

This will set the specified model as the default and ensure all other models for the provider are not marked as default.

Example:

```bash
llm-tester models set-default openai gpt-4
```

## Common Use Cases

### Managing Model Costs

Keep your model costs up-to-date by editing models when providers change their pricing:

```bash
llm-tester models edit openai gpt-4 --cost-input 10.0 --cost-output 30.0
```

### Disabling Expensive Models

Temporarily disable expensive models to prevent accidental usage:

```bash
llm-tester models edit openai gpt-4 --enabled false
```

### Adding New Provider Models

When a provider releases a new model, add it to your configuration:

```bash
llm-tester models add anthropic --name claude-3-opus --cost-input 15.0 --cost-output 75.0 --max-input 100000 --max-output 4096 --cost-category expensive
```

### Setting Preferred Models for Testing

Mark certain models as preferred for testing:

```bash
llm-tester models edit openai gpt-4 --preferred true
```

## Model Configuration Fields

Each model configuration includes the following fields:

- `name`: The name of the model
- `default`: Whether this is the default model for the provider
- `preferred`: Whether this model is preferred for testing
- `enabled`: Whether the model is enabled
- `cost_input`: Cost per 1M input tokens in USD
- `cost_output`: Cost per 1M output tokens in USD
- `cost_category`: Cost category (cheap, standard, expensive)
- `max_input_tokens`: Maximum input tokens supported
- `max_output_tokens`: Maximum output tokens supported

## Troubleshooting

### Provider Not Found

If you get an error that the provider is not found:

1. Check that you've spelled the provider name correctly
2. Verify that the provider is properly installed and configured
3. Use `llm-tester providers list` to see available providers

### Model Not Found

If you get an error that the model is not found when editing or removing:

1. Check that you've spelled the model name correctly
2. Use `llm-tester models list <PROVIDER>` to see available models

### Configuration File Issues

If you encounter errors saving the configuration:

1. Check that you have write permissions to the provider's configuration file
2. Verify that the configuration file is valid JSON
3. Try resetting the provider cache: `llm-tester costs reset-cache`