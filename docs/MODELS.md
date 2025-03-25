# Using Different LLM Providers and Models

LLM Tester supports multiple LLM providers and models. This document explains how to configure and use different models.

## Supported Providers

LLM Tester currently supports the following providers:

1. **OpenAI** - GPT models
2. **Anthropic** - Claude models
3. **Mistral AI** - Mistral models
4. **Google** - Gemini models

## API Key Configuration

You need to set up API keys for each provider you want to use. Create a `.env` file in the root directory of the project based on the `.env.example` file:

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Mistral API 
MISTRAL_API_KEY=your_mistral_api_key_here

# Google Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
GOOGLE_PROJECT_ID=your_google_cloud_project_id
GOOGLE_LOCATION=us-central1  # The region where your Vertex AI resources are located
```

### Google Credentials

For Google's Vertex AI (Gemini models), you need to:

1. Create a Google Cloud project
2. Enable the Vertex AI API
3. Create a service account with appropriate permissions
4. Download the JSON key file for that service account
5. Set the path to that file in your `.env` file as `GOOGLE_APPLICATION_CREDENTIALS`

## Using Different Models

You can specify which models to use in several ways:

### Command Line Interface

```bash
# Run tests with specific models
llm-tester --models openai:gpt-4-turbo anthropic:claude-3-haiku-20240307 google:gemini-1.5-pro

# List available test cases and providers
llm-tester --list

# Run only specific providers
llm-tester --providers openai google
```

### Python API

```python
from llm_tester import LLMTester

# Specify providers and model overrides
providers = ["openai", "anthropic", "google"]
model_overrides = {
    "openai": "gpt-4-turbo",
    "anthropic": "claude-3-opus-20240229",
    "google": "gemini-1.5-pro"
}

# Initialize tester with providers
tester = LLMTester(providers=providers)

# Run tests with model overrides
results = tester.run_tests(model_overrides=model_overrides)

# Generate and print report
report = tester.generate_report(results)
print(report)
```

## Available Models

Here are some common models available for each provider:

### OpenAI

- `gpt-4` - Standard GPT-4 model
- `gpt-4-turbo` - Faster GPT-4 model
- `gpt-3.5-turbo` - Less capable but faster and cheaper

### Anthropic

- `claude-3-opus-20240229` - Most capable Claude model
- `claude-3-sonnet-20240229` - Balanced capability and speed
- `claude-3-haiku-20240307` - Fastest Claude model

### Mistral AI

- `mistral-large-latest` - Most capable Mistral model
- `mistral-medium` - Medium capability
- `mistral-small` - Fast, smaller model

### Google (Vertex AI)

- `gemini-pro` - Standard Gemini model
- `gemini-1.5-pro` - Newest Gemini model with enhanced capabilities
- `gemini-1.5-flash` - Faster Gemini model

## Testing Multiple Models

When comparing LLM performance, it's often useful to test multiple models from the same provider to see how they compare. You can do this by running separate tests with different model overrides or by using different provider names to represent different models from the same provider.

Example:

```python
# Creating separate providers for different model variations
providers = ["openai-4", "openai-3.5", "anthropic-opus", "anthropic-haiku", "google-pro"]

# Map each provider to a specific model
model_overrides = {
    "openai-4": "gpt-4-turbo",
    "openai-3.5": "gpt-3.5-turbo",
    "anthropic-opus": "claude-3-opus-20240229",
    "anthropic-haiku": "claude-3-haiku-20240307",
    "google-pro": "gemini-1.5-pro"
}

# Initialize provider manager with custom naming (need to modify code)
# Then run tests as normal
```

## Adding New Providers

To add a new LLM provider, you'll need to:

1. Add a new method to create the client in `ProviderManager`
2. Add a new method to get responses from the provider
3. Update the `_initialize_providers` method to include the new provider
4. Update the default models in the CLI