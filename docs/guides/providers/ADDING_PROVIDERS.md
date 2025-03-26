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
      "max_output_tokens": 4000
    }
  ]
}
```

Adjust the values according to your provider's specifications:
- `name`: Identifier used in the code
- `provider_type`: Type identifier
- `env_key`: Environment variable for the API key
- `system_prompt`: Default system prompt
- `models`: List of supported models with their configurations

### 4. Update Provider Initialization

Add your provider to the initialization in `llm_tester/llms/__init__.py`:

```python
try:
    from . import your_provider_name
except ImportError:
    pass
```

### 5. Update Pricing Information

Add your provider's pricing to `models_pricing.json`:

```json
{
  "your_provider_name": {
    "your-model-name": {
      "input": 1.0,
      "output": 2.0
    }
  }
}
```

## Testing Your Provider Integration

### 1. Verify Provider Discovery

Run the verification script to check if your provider is discovered:

```bash
./verify_providers.py
```

### 2. Test with a Simple Request

Run a simple test to verify your provider works:

```bash
./runner.py test -p your_provider_name -m job_ads
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