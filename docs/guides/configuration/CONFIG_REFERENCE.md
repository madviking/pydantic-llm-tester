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
- `enabled`: (boolean) Whether this specific LLM model is enabled for use (defaults to `true` if missing). Managed by `llm-tester providers manage enable/disable`.
- `cost_input`/`cost_output`: (float) Cost per 1M tokens (in USD). *Note: For OpenRouter, these values are dynamically updated via `llm-tester providers manage update openrouter`.*
- `max_input_tokens`/`max_output_tokens`: (integer) Token limits. *Note: For OpenRouter, these values are dynamically updated via `llm-tester providers manage update openrouter`.*

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

## Command-Line Interface (`llm-tester`)

The primary interface is through the `llm-tester` command after installation (`pip install -e .`): `llm-tester <command> [options]`

### Global Options

These apply to all commands:
- `-v`, `--verbose`: Increase verbosity (use `-vv` for debug level).
- `--env <path>`: Specify a custom `.env` file path to load API keys from.

### Commands

**1. `run`**
   - Usage: `llm-tester run [options]`
   - Description: Runs the LLM test suite.
   - Options:
     - `--providers <name> [<name>...]` or `-p <name>`: Specify providers to test (default: all enabled).
     - `--models <provider:model> [<provider:model>...]` or `-m <provider:model>`: Specify exact LLM models to use (e.g., `openai:gpt-4o`). Can be used multiple times.
     - `--test-dir <path>`: Path to test cases directory (default: uses LLMTester default).
     - `--output <file>` or `-o <file>`: Save report to a file (default: print to stdout).
     - `--json`: Output results in JSON format instead of Markdown.
     - `--optimize`: Run prompt optimization before final tests.
     - `--filter <pattern>` or `-f <pattern>`: Filter test cases by name (e.g., `job_ads/simple`). *Note: Filtering not fully implemented yet.*

**2. `list`**
   - Usage: `llm-tester list [options]`
   - Description: Lists discovered test cases and configured providers/models without running tests.
   - Options:
     - `--providers <name> [<name>...]` or `-p <name>`: Specify providers to list (default: all enabled).
     - `--models <provider:model> [<provider:model>...]` or `-m <provider:model>`: Specify LLM models to consider for provider listing.
     - `--test-dir <path>`: Path to test cases directory to list.

**3. `providers`**
   - Usage: `llm-tester providers <subcommand> [args]`
   - Description: Manage LLM providers and their specific LLM models.
   - Subcommands:
     - `list`: Shows all discoverable providers and whether they are enabled (based on `enabled_providers.json`).
     - `enable <name>`: Enables a provider by adding it to `enabled_providers.json`. Creates the file if it doesn't exist.
     - `disable <name>`: Disables a provider by removing it from `enabled_providers.json`.
     - `manage list <provider>`: Lists LLM models within a provider's `config.json` and their enabled status.
     - `manage enable <provider> <model_name>`: Enables a specific LLM model within a provider's `config.json`.
     - `manage disable <provider> <model_name>`: Disables a specific LLM model within a provider's `config.json`.
     - `manage update <provider>`: Updates LLM model details (cost, limits) from the provider API (currently only `openrouter`).

**4. `schemas`**
   - Usage: `llm-tester schemas <subcommand> [args]`
   - Description: Manage Extraction Schemas (Pydantic models and test modules).
   - Subcommands:
     - `list`: Lists all discoverable extraction schemas based on directories in `llm_tester/models/`.

**5. `configure`**
   - Usage: `llm-tester configure <subcommand>`
   - Description: Configure llm-tester settings.
   - Subcommands:
     - `keys`: Interactively prompts for missing API keys (based on provider configs) and offers to save them to `llm_tester/.env`.

**6. `recommend-model`**
   - Usage: `llm-tester recommend-model`
   - Description: Interactively prompts for a task description and uses an available LLM to recommend suitable, enabled LLM models.

**7. `interactive`**
   - Usage: `llm-tester interactive`
   - Description: Launches the interactive menu-driven session.

## Configuration Precedence

Configuration values are determined in the following order (highest precedence first):

1. Command-line arguments
2. Environment variables
3. Configuration files
4. Default values

## Editing Configuration

Configuration can be edited in several ways:

1. **Provider Enablement**: Use `llm-tester providers enable <name>` and `llm-tester providers disable <name>`.
2. **LLM Model Enablement**: Use `llm-tester providers manage enable <provider> <model>` and `llm-tester providers manage disable <provider> <model>`.
3. **API Keys**: Use the `llm-tester configure keys` command or manually edit `llm_tester/.env`.
4. **Provider Settings**: Manually edit the specific `llm_tester/llms/<provider_name>/config.json` file for things like the default system prompt or manually adding/removing models (though `llm-tester providers manage update openrouter` is preferred for OpenRouter).
5. **Directly edit files**: Modify the JSON files (`enabled_providers.json`, provider `config.json`) directly if needed.

## Provider Verification

Use the CLI commands to check your setup:

```bash
# Check discovered providers and enabled status
llm-tester providers list

# Check LLM models within a specific provider
llm-tester providers manage list <provider_name>

# Check API keys (will prompt if missing)
llm-tester configure keys
```

## Configuration Best Practices

1. **API Keys**: Use `llm-tester configure keys` or manage `llm_tester/.env` carefully. Keep this file out of version control (it should be in `.gitignore`).
2. **Provider Enablement**: Use `enabled_providers.json` (via `llm-tester providers enable/disable`) to control which providers are active, especially if you don't have keys for all of them.
3. **LLM Model Enablement**: Use `llm-tester providers manage enable/disable` to fine-tune which specific LLM models within a provider are used for testing or recommendations.
4. **OpenRouter Updates**: Regularly use `llm-tester providers manage update openrouter` to keep pricing and token limits accurate.
