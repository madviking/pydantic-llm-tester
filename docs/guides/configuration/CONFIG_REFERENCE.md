# Configuration Reference

This document provides a comprehensive reference for configuring the LLM Tester framework, including configuration files and environment variables.

## Configuration Files

LLM Tester uses several configuration files:

1. **Global Configuration**: `config.json`
2. **Provider Configurations**: `llm_tester/llms/provider_name/config.json`
3. **Model Pricing**: `models_pricing.json`

### Global Configuration (`config.json`)

The global configuration file contains settings for providers and testing:

```json
{
  "providers": {
    "openai": {
      "enabled": true,
      "default_model": "gpt-4"
    },
    "anthropic": {
      "enabled": true,
      "default_model": "claude-3-opus-20240229"
    },
    "mistral": {
      "enabled": false,
      "default_model": "mistral-large-latest"
    },
    "google": {
      "enabled": false,
      "default_model": "gemini-1.5-pro"
    },
    "mock_provider": {
      "enabled": false,
      "default_model": "mock-model"
    }
  },
  "test_settings": {
    "output_dir": "test_results",
    "save_optimized_prompts": true,
    "default_modules": ["job_ads", "product_descriptions"]
  }
}
```

Key settings:
- `providers`: Configuration for enabled providers and default models
- `test_settings`: Global test settings

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
      "cost_input": 15,
      "cost_output": 75,
      "cost_category": "expensive",
      "max_input_tokens": 200000,
      "max_output_tokens": 4096
    }
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
- `default`: Whether this is the default model
- `preferred`: Whether this model is preferred for production
- `cost_input`/`cost_output`: Cost per 1M tokens (in USD)
- `max_input_tokens`/`max_output_tokens`: Token limits

### Model Pricing (`models_pricing.json`)

This file defines pricing for providers and models:

```json
{
  "openai": {
    "gpt-4": {
      "input": 30.0,
      "output": 60.0
    }
  },
  "anthropic": {
    "claude-3-opus-20240229": {
      "input": 15.0,
      "output": 75.0
    }
  }
}
```

This information is used to calculate costs for API calls.

## Environment Variables

LLM Tester uses environment variables for API keys and configuration. These can be set in a `.env` file or directly in the environment.

### API Keys

```
# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# Mistral
MISTRAL_API_KEY=your_mistral_key

# Google
GOOGLE_API_KEY=your_google_key
GOOGLE_PROJECT_ID=your_google_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Logging Configuration

```
# Set log level
LOG_LEVEL=DEBUG
```

## Command-Line Arguments

The `runner.py` script accepts several command-line arguments:

### Test Command

```
./runner.py test [options]
```

Options:
- `-p, --provider`: Provider to use (can be specified multiple times)
- `-m, --module`: Module to test (can be specified multiple times)
- `-o, --optimize`: Run optimized tests
- `--output`: Directory to save results
- `--model`: Specify model as provider:model (can be specified multiple times)

### Verify Command

```
./runner.py verify
```

### Interactive Command

```
./runner.py interactive [options]
```

Options:
- `--env`: Path to .env file with API keys

### Global Options

```
./runner.py [options]
```

Options:
- `--debug`: Enable debug logging
- `-n, --non-interactive`: Run in non-interactive mode

## Configuration Precedence

Configuration values are determined in the following order (highest precedence first):

1. Command-line arguments
2. Environment variables
3. Configuration files
4. Default values

## Editing Configuration

Configuration can be edited in several ways:

1. **Directly edit files**: Modify the JSON files directly
2. **Interactive interface**: Use the "Edit Configuration" option in the menu
3. **Command-line**: Some settings can be overridden with command-line arguments

## Provider Verification

You can verify your provider setup with:

```bash
./verify_providers.py
```

This checks:
- Which providers are discovered
- Whether API keys are configured
- Available models

## Configuration Best Practices

1. **Environment Variables**: Use environment variables for sensitive information like API keys
2. **Default Models**: Set default models for each provider in global configuration
3. **Cost Categories**: Use cost categories to manage expensive models
4. **Default Modules**: Configure frequently used modules as defaults
5. **Output Directory**: Set a dedicated output directory for test results