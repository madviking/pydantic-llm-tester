# Adding New Providers to LLM Tester

This guide explains how to add a new LLM provider to the LLM Tester framework. The provider system is designed to be modular and extensible, making it easy to add support for new LLM API providers.

## Provider Integration Options

LLM Tester supports multiple ways to integrate with LLM providers:

1. **Native Integration**: Direct integration with a provider's API
2. **PydanticAI Integration**: Using PydanticAI as an abstraction layer
3. **Mock Integration**: Creating a mock provider for testing

This guide focuses on creating a native integration.

## Steps to Add a New Provider

### 1. Create Provider Directory Structure

Create a new directory for your provider in the `llm_tester/llms/` directory:

```bash
mkdir -p llm_tester/llms/your_provider_name
touch llm_tester/llms/your_provider_name/__init__.py
touch llm_tester/llms/your_provider_name/provider.py
touch llm_tester/llms/your_provider_name/config.json
```

### 2. Implement the Provider Class

Create a provider class in `provider.py` that inherits from `BaseLLM`:

```python
"""Your provider implementation"""

import logging
import json
import os
from typing import Dict, Any, Tuple, Optional, List, Union

# Import provider-specific SDK
try:
    # Import your provider's SDK here
    PROVIDER_AVAILABLE = True
except ImportError:
    PROVIDER_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig
from ...utils.cost_manager import UsageData


class YourProviderProvider(BaseLLM):
    """Provider implementation for Your Provider"""
    
    def __init__(self, config=None):
        """Initialize the provider"""
        super().__init__(config)
        
        # Check if SDK is available
        if not PROVIDER_AVAILABLE:
            self.logger.warning("Provider SDK not available. Install with 'pip install provider-sdk'")
            self.client = None
            return
            
        # Get API key
        api_key = self.get_api_key()
        if not api_key:
            self.logger.warning(f"No API key found. Set the {self.config.env_key if self.config else 'YOUR_PROVIDER_API_KEY'} environment variable.")
            self.client = None
            return
            
        # Initialize client
        self.client = None  # Initialize your client here
        self.logger.info("Provider client initialized")
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not self.client:
            self.logger.error("Provider client not initialized")
            raise ValueError("Provider client not initialized")
            
        # Calculate max tokens based on model config
        max_tokens = min(model_config.max_output_tokens, 4096)  # Default cap 
        
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "Extract the requested information from the provided text as accurate JSON."
        
        # Make the API call
        self.logger.info(f"Sending request to Provider model {model_name}")
        
        try:
            # Implement your API call here
            # ...
            
            # Example:
            # response = self.client.completion.create(
            #     model=model_name,
            #     messages=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": prompt}
            #     ],
            #     max_tokens=max_tokens
            # )
            
            # For this example, we'll use dummy data
            response_text = json.dumps({"example": "response"})
            
            # Create usage data
            usage_data = {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
            
            return response_text, usage_data
            
        except Exception as e:
            self.logger.error(f"Error calling API: {str(e)}")
            raise ValueError(f"Error calling API: {str(e)}")
```

### 3. Create Provider Configuration

Create a `config.json` file with your provider's configuration:

```json
{
  "name": "your_provider_name",
  "provider_type": "your_provider_type",
  "env_key": "YOUR_PROVIDER_API_KEY",
  "env_key_secret": "",
  "system_prompt": "Extract the requested information from the provided text as accurate JSON.",
  "models": [
    {
      "name": "your-model-name",
      "default": true,
      "preferred": true,
      "cost_input": 1.0,
      "cost_output": 2.0,
      "cost_category": "standard",
      "max_input_tokens": 8000,
      "max_output_tokens": 4000,
      "enabled": true // Add this flag to control model availability
    }
  ]
}
```

Adjust the values according to your provider's specifications:
- `name`: Identifier used in the code
- `provider_type`: Type identifier
- `env_key`: Environment variable for the API key
- `system_prompt`: Default system prompt
- `models`: List of supported models with their configurations. Add `"enabled": true` or `"enabled": false` to control if the model is active.

*(Note: For the `openrouter` provider, cost and token limit fields in `config.json` are overridden by values fetched dynamically from the OpenRouter API via the `llm-tester update-models` command or during runtime loading. However, flags like `default`, `preferred`, and `enabled` are still respected from the static config file.)*

### 4. Ensure Provider Discovery

The framework automatically discovers providers by looking for subdirectories within `llm_tester/llms/` that contain an `__init__.py` file. Ensure your `llm_tester/llms/your_provider_name/__init__.py` file exists and imports your provider class:

```python
# llm_tester/llms/your_provider_name/__init__.py
from .provider import YourProviderProvider

# Optional: Define __all__ if you want to be explicit
__all__ = ['YourProviderProvider']
```
No changes are needed in the parent `llm_tester/llms/__init__.py` file.

### 5. Enable the Provider (Optional)

By default, if no `enabled_providers.json` file exists in the project root, all discovered providers are considered enabled. If the file *does* exist, you need to add your new provider's name to it. You can do this manually or use the CLI:

```bash
# Activate virtual environment first
source venv/bin/activate

# Enable your new provider
python -m llm_tester.cli providers enable your_provider_name
```

## Testing Your Provider Integration

### 1. Verify Provider Discovery and Status

Use the CLI to check if your provider is discovered and enabled:

```bash
# Activate virtual environment first
source venv/bin/activate

# List all providers and their status
python -m llm_tester.cli providers list

# List models configured for your provider
python -m llm_tester.cli models list --provider your_provider_name
```

### 2. Test with a Simple Request

Run a simple test using the CLI to verify your provider works:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run tests using only your provider and a specific model (optional)
python -m llm_tester.cli --providers your_provider_name --models your_provider_name:your-model-name

# Or run using the default model for your provider
python -m llm_tester.cli --providers your_provider_name
```

## Best Practices

1. **Error Handling**: Implement robust error handling for API calls
2. **Logging**: Use the logger for meaningful log messages
3. **Validation**: Validate inputs before sending to the API
4. **Documentation**: Document any provider-specific behaviors
5. **Testing**: Create tests for your provider implementation

## Provider Requirements

Your provider implementation must:

1. Inherit from `BaseLLM`
2. Implement the `_call_llm_api` method
3. Return a tuple of (response_text, usage_data)

## Example Implementations

Refer to existing provider implementations as examples:

- `llm_tester/llms/openai/provider.py`
- `llm_tester/llms/anthropic/provider.py`
- `llm_tester/llms/mistral/provider.py`

These implementations show how to handle different API formats, error cases, and usage tracking.
