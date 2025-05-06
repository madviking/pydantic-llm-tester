# Scaffolding New Providers and Models

The `llm-tester scaffold` command provides a convenient way to quickly set up the basic directory structure and template files for new LLM providers and extraction models. This saves you from manually creating directories and files, allowing you to jump directly into implementing the core logic.

The `scaffold` command has two subcommands: `provider` and `model`.

## Scaffolding Providers

To scaffold a new LLM provider:

```bash
llm-tester scaffold provider [OPTIONS] [PROVIDER_NAME]
```

- `PROVIDER_NAME`: The name of the new provider to scaffold. This is required in non-interactive mode.

Options:

- `--providers-dir TEXT`: Directory to create the provider in (defaults to `llm_tester/llms`).
- `--interactive, -i`: Enable interactive mode. If this flag is used, you will be prompted for the provider name and other details.

### Interactive Provider Scaffolding

Run the command with the `--interactive` flag:

```bash
llm-tester scaffold provider --interactive
```

The CLI will prompt you to enter the provider name:

```
Interactive Provider Scaffolding
Enter the name of the new provider: your_provider_name
```

After you enter the name and press Enter, the command will create the necessary directory structure and template files for your provider in the default or specified providers directory.

### Non-Interactive Provider Scaffolding

Run the command with the provider name as an argument:

```bash
llm-tester scaffold provider your_provider_name
```

This will immediately scaffold the provider with the given name without prompting for input. You can optionally specify a different output directory using the `--providers-dir` option:

```bash
llm-tester scaffold provider your_provider_name --providers-dir /path/to/custom/providers
```

## Scaffolding Models

To scaffold a new extraction model:

```bash
llm-tester scaffold model [OPTIONS] [MODEL_NAME]
```

- `MODEL_NAME`: The name of the new model to scaffold. This is required in non-interactive mode.

Options:

- `--models-dir TEXT`: Directory to create the model in (defaults to `./models`).
- `--interactive, -i`: Enable interactive mode. If this flag is used, you will be prompted for the model name and other details.

### Interactive Model Scaffolding

Run the command with the `--interactive` flag:

```bash
llm-tester scaffold model --interactive
```

The CLI will prompt you to enter the model name:

```
Interactive Model Scaffolding
Enter the name of the new model: your_model_name
```

After you enter the name and press Enter, the command will create the necessary directory structure and template files for your model in the default or specified models directory.

### Non-Interactive Model Scaffolding

Run the command with the model name as an argument:

```bash
llm-tester scaffold model your_model_name
```

This will immediately scaffold the model with the given name without prompting for input. You can optionally specify a different output directory using the `--models-dir` option:

```bash
llm-tester scaffold model your_model_name --models-dir /path/to/custom/models
```

## What gets created?

When you scaffold a provider or model, the command creates the basic directory structure and populates it with template files (`__init__.py`, `provider.py` or `model.py`, `config.json` for providers, and test case templates for models). These files contain placeholder code and comments to help you get started with your implementation.

Refer to the [Adding Providers](guides/providers/ADDING_PROVIDERS.md) and [Adding Models](guides/models/ADDING_MODELS.md) guides for detailed instructions on how to complete the implementation after scaffolding.
