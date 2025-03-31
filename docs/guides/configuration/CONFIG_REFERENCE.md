# Configuration Reference

This document provides a comprehensive reference for configuring the LLM Tester framework, including configuration files and environment variables.

## Configuration Files

LLM Tester uses several configuration files:

1. **Provider Enablement**: `enabled_providers.json` (Project Root)
2. **Provider Configurations**: `llm_tester/llms/<provider_name>/config.json`
3. **Environment Variables**: `llm_tester/.env` (or system environment)

*(Note: Older global `config.json` and `models_pricing.json` files may exist but are likely deprecated or unused by the current core logic.)*

### Provider Enablement (`enabled_providers.json`)

This optional file, located in the project root directory (where `README.md` is), explicitly lists which providers should be considered active by the framework.

```json
[
  "openai",
  "anthropic",
  "openrouter"
]
```

- If this file **does not exist**, all discovered providers (in `llm_tester/llms/`) are considered enabled.
- If this file **exists**, only the providers listed in the array will be loaded and used by commands like `run` or `recommend-model`.
- This file is managed by the `llm-tester providers enable <name>` and `llm-tester providers disable <name>` CLI commands.

### Provider Configuration (`llm_tester/llms/provider_name/config.json`)

Each provider has its own configuration file:

```json
{
  "name": "provider_name",
  "provider_type": "provider_type",
  "env_key": "PROVIDER_API_KEY",
  "env_key_secret": "",
  "system_prompt": "Extract the requested information from the provided text as accurate JSON.",
  "models": [
    {
      "name": "model-name",
      "default": true,
      "preferred": true,
      "cost_input": 15.0,
      "cost_output": 75.0,
      "cost_category": "expensive",
      "max_input_tokens": 200000,
      "max_output_tokens": 4096,
      "enabled": true
    }
    // ... other models
  ]
}
```

Key settings:
- `name`: Provider identifier
- `provider_type`: Type identifier
- `env_key`: Environment variable for API key
- `system_prompt`: Default system prompt
- `models`: List of supported models

Model settings:
- `name`: Model identifier
- `default`: (boolean) Whether this is the default model for the provider (only one should be true).
- `preferred`: (boolean) Whether this model is preferred (e.g., for production use, informational only).
- `enabled`: (boolean) Whether this specific model is enabled for use (defaults to `true` if missing). Managed by `llm-tester models enable/disable`.
- `cost_input`/`cost_output`: (float) Cost per 1M tokens (in USD). *Note: For OpenRouter, these values are dynamically updated.*
- `max_input_tokens`/`max_output_tokens`: (integer) Token limits. *Note: For OpenRouter, these values are dynamically updated.*

## Environment Variables (`llm_tester/.env`)

LLM Tester uses environment variables primarily for API keys. These are typically stored in a `.env` file located within the `llm_tester` directory (`llm_tester/.env`). The `llm-tester configure keys` command helps manage this file.

Required keys depend on the providers you intend to use:

```dotenv
# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# Mistral
MISTRAL_API_KEY=your_mistral_key

# Google (Vertex AI)
GOOGLE_API_KEY=your_google_key # Or configure via gcloud CLI authentication
# GOOGLE_PROJECT_ID=your_google_project_id # Often needed for Vertex AI
# GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json # Alternative auth

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_key

# Add keys for other providers based on their 'env_key' in config.json
# YOUR_PROVIDER_API_KEY=your_key
```

You can also set these variables directly in your system environment. The `.env` file takes precedence if it exists and contains the key.

## Command-Line Interface (`llm_tester.cli`)

The primary interface is through the command line: `python -m llm_tester.cli <command> [options]`

### Global Options

These apply to all commands:
- `-v`, `--verbose`: Increase verbosity (use `-vv` for debug level).
- `--env <path>`: Specify a custom `.env` file path to load API keys from.

### Commands

**1. Run Tests (Default)**
   - Usage: `python -m llm_tester.cli [run_options]` (no command needed)
   - Options:
     - `--providers <name> [<name>...]`: Specify providers to test (default: all enabled).
     - `--models <provider/model> [<provider/model>...]`: Specify exact models to use.
     - `--test-dir <path>`: Path to test cases directory.
     - `--output <file>`: Save report to a file (default: print to stdout).
     - `--json`: Output results in JSON format instead of Markdown.
     - `--optimize`: Run prompt optimization before final tests.
     - `--list`: List discovered test cases and configured providers/models without running.
     - `--filter <pattern>`: Filter test cases by name (e.g., `job_ads/simple`).

**2. Configure**
   - Usage: `python -m llm_tester.cli configure <subcommand>`
   - Subcommands:
     - `keys`: Interactively prompts for missing API keys (based on provider configs) and offers to save them to `llm_tester/.env`.

**3. Update Models**
   - Usage: `python -m llm_tester.cli update-models [options]`
   - Options:
     - `--provider <name>`: Provider to update (default/currently only: `openrouter`). Fetches latest model details (cost, limits) from the provider API and updates the local `config.json`.

**4. Providers**
   - Usage: `python -m llm_tester.cli providers <subcommand> [args]`
   - Subcommands:
     - `list`: Shows all discoverable providers and whether they are enabled (based on `enabled_providers.json`).
     - `enable <name>`: Enables a provider by adding it to `enabled_providers.json`. Creates the file if it doesn't exist.
     - `disable <name>`: Disables a provider by removing it from `enabled_providers.json`.

**5. Models**
   - Usage: `python -m llm_tester.cli models <subcommand> [args]`
   - Subcommands:
     - `list --provider <name>`: Lists models within a provider's `config.json` and their enabled status.
     - `enable <model_id> [--provider <name>]`: Enables a model within its provider's `config.json` by setting `"enabled": true`. Use format `provider/model_name` or specify `--provider`.
     - `disable <model_id> [--provider <name>]`: Disables a model within its provider's `config.json` by setting `"enabled": false`.

**6. Recommend Model**
   - Usage: `python -m llm_tester.cli recommend-model`
   - Interactively prompts for a task description.
   - Uses an available LLM (prioritizing cheap ones like OpenRouter's Haiku if configured) to recommend suitable models from the currently enabled providers and models based on their configuration (cost, limits).

## Configuration Precedence

Configuration values are determined in the following order (highest precedence first):

1. Command-line arguments
2. Environment variables
3. Configuration files
4. Default values

## Editing Configuration

Configuration can be edited in several ways:

1. **Provider/Model Enablement**: Use the `llm-tester providers enable/disable` and `llm-tester models enable/disable` CLI commands.
2. **API Keys**: Use the `llm-tester configure keys` CLI command or manually edit `llm_tester/.env`.
3. **Provider Settings**: Manually edit the specific `llm_tester/llms/<provider_name>/config.json` file for things like the default system prompt or manually adding/removing models (though `update-models` is preferred for OpenRouter).
4. **Directly edit files**: Modify the JSON files (`enabled_providers.json`, provider `config.json`) directly if needed.

## Provider Verification

Use the CLI commands to check your setup:

```bash
# Check discovered providers and enabled status
python -m llm_tester.cli providers list

# Check models within a specific provider
python -m llm_tester.cli models list --provider <provider_name>

# Check API keys (will prompt if missing)
python -m llm_tester.cli configure keys
```

## Configuration Best Practices

1. **API Keys**: Use `llm-tester configure keys` or manage `llm_tester/.env` carefully. Keep this file out of version control (it should be in `.gitignore`).
2. **Provider Enablement**: Use `enabled_providers.json` (via `llm-tester providers enable/disable`) to control which providers are active, especially if you don't have keys for all of them.
3. **Model Enablement**: Use `llm-tester models enable/disable` to fine-tune which specific models within a provider are used for testing or recommendations.
4. **OpenRouter Updates**: Regularly use `llm-tester update-models --provider openrouter` to keep pricing and token limits accurate.
