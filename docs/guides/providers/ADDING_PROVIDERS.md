# Adding New Providers to LLM Tester

This guide explains how to add a new LLM provider to the LLM Tester framework. The provider system is designed to be modular and extensible, making it easy to add support for new LLM API providers.

## Provider Integration Options

LLM Tester supports multiple ways to integrate with LLM providers:

1. **Native Integration**: Direct integration with a provider's API
2. **PydanticAI Integration**: Using PydanticAI as an abstraction layer
3. **Mock Integration**: Creating a mock provider for testing

This guide focuses on creating a native integration.

## Steps to Add a New Provider

You can manually create the necessary files and directories, or use the `llm-tester scaffold provider` command to generate the basic structure and template files automatically.

**Using the `llm-tester scaffold provider` command:**

```bash
# Scaffold a new provider interactively
llm-tester scaffold provider --interactive

# Scaffold a new provider non-interactively
llm-tester scaffold provider <provider_name>
```

This will create the directory structure and template files described in step 1 and partially complete steps 2 and 3.

**Manual Steps:**

### 1. Create Provider Directory Structure

Create a new directory for your provider in the `src/pydantic_llm_tester/llms/` directory:

```bash
# Ensure you are in the project root directory
mkdir -p src/pydantic_llm_tester/llms/your_provider_name
touch src/pydantic_llm_tester/llms/your_provider_name/__init__.py
touch src/pydantic_llm_tester/llms/your_provider_name/provider.py
touch src/pydantic_llm_tester/llms/your_provider_name/config.json
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
    
from pydantic_llm_tester.llms.base import BaseLLM, ModelConfig
from pydantic_llm_tester.utils.cost_manager import UsageData


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
  "llm_models": [
    {
      "name": "your-model-name",
      "default": true,
      "preferred": true,
      "cost_input": 1.0,
      "cost_output": 2.0,
      "cost_category": "standard",
      "max_input_tokens": 8000,
      "max_output_tokens": 4000,
      "enabled": true
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

The framework automatically discovers providers by looking for subdirectories within `src/pydantic_llm_tester/llms/` that contain an `__init__.py` file. Ensure your `src/pydantic_llm_tester/llms/your_provider_name/__init__.py` file exists and imports your provider class:

```python
# src/pydantic_llm_tester/llms/your_provider_name/__init__.py
from .provider import YourProviderProvider

# Optional: Define __all__ if you want to be explicit
__all__ = ['YourProviderProvider']
```
No changes are needed in the parent `src/pydantic_llm_tester/llms/__init__.py` file.

### 5. Enable the Provider (Optional)

By default, if no `enabled_providers.json` file exists in the project root, all discovered providers are considered enabled. If the file *does* exist, you need to add your new provider's name to it. You can do this manually or use the CLI:

```bash
# Activate virtual environment first
source venv/bin/activate

# Enable your new provider
llm-tester providers enable your_provider_name
```

## Testing Your Provider Integration

### 1. Verify Provider Discovery and Status

Use the CLI to check if your provider is discovered and enabled:

```bash
# Activate virtual environment first
# source venv/bin/activate # If in a virtual environment

# List all providers and their status
llm-tester providers list

# List py_models configured for your provider (Note: This command might be `llm-tester providers manage list your_provider_name` or similar based on current CLI structure)
# llm-tester py_models list --provider your_provider_name # Check current CLI for exact command
llm-tester providers manage list your_provider_name
```

### 2. Test with a Simple Request

Run a simple test using the CLI to verify your provider works:

```bash
# Activate virtual environment first
# source venv/bin/activate # If in a virtual environment

# Run tests using only your provider and a specific model (optional)
llm-tester run --providers your_provider_name --py_models your_provider_name:your-model-name

# Or run using the default model for your provider
llm-tester run --providers your_provider_name
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

## Adding External Providers

Developers using the installed `pydantic-llm-tester` package may want to add custom providers without modifying the installed package files. This can be done by placing your provider implementation outside the `pydantic_llm_tester` package directory (typically `site-packages/pydantic_llm_tester`) and configuring the tool to discover it.

**Steps to Add an External Provider:**

1.  **Create Provider Directory:** Create a directory for your external provider anywhere on your system. For example:
    ```bash
    mkdir -p /path/to/your/custom_providers/your_provider_name
    touch /path/to/your/custom_providers/your_provider_name/__init__.py
    touch /path/to/your/custom_providers/your_provider_name/provider.py
    touch /path/to/your/custom_providers/your_provider_name/config.json
    ```
2.  **Implement Provider and Config:** Implement your provider class in `provider.py` and create the `config.json` file, following the same structure and requirements as described in steps 2 and 3 of the "Steps to Add a New Provider" section above.
3.  **Configure LLM Tester to Discover External Providers:** You need to tell `llm_tester` where to look for external providers. This can be done by creating or modifying the `external_providers.json` file in the root of your project where you are using `llm_tester`. This file should contain a list of paths to your external provider directories.

    ```json
    [
      "/path/to/your/custom_providers"
    ]
    ```
    The `pydantic-llm-tester` tool will recursively search the directories listed in `external_providers.json` for valid provider implementations.

4.  **Ensure Provider Discovery:** Similar to internal providers, ensure your external provider directory has an `__init__.py` file that imports your provider class.

    ```python
    # /path/to/your/custom_providers/your_provider_name/__init__.py
    from .provider import YourProviderProvider

    # Optional: Define __all__ if you want to be explicit
    __all__ = ['YourProviderProvider']
    ```

5.  **Enable the Provider (Optional):** If you are using an `enabled_providers.json` file, you will need to add your external provider's name to it.

    ```bash
    # Activate virtual environment first
    source venv/bin/activate

    # Enable your new provider
    llm-tester providers enable your_provider_name
    ```

## Testing Your Provider Integration

### 1. Verify Provider Discovery and Status

Use the CLI to check if your provider is discovered and enabled:

```bash
# Activate virtual environment first
source venv/bin/activate

# List all providers and their status
llm-tester providers list

# List py_models configured for your provider (Note: This command might be `llm-tester providers manage list your_provider_name` or similar)
# llm-tester py_models list --provider your_provider_name # Check current CLI for exact command
llm-tester providers manage list your_provider_name
```

### 2. Test with a Simple Request

Run a simple test using the CLI to verify your provider works:

```bash
# Activate virtual environment first
# source venv/bin/activate # If in a virtual environment

# Run tests using only your provider and a specific model (optional)
llm-tester run --providers your_provider_name --py_models your_provider_name:your-model-name

# Or run using the default model for your provider
llm-tester run --providers your_provider_name
```

## Best Practices

1. **Error Handling**: Implement robust error handling for API calls
2. **Logging**: Use the logger for meaningful log messages
3. **Validation**: Validate inputs before sending to the API
4. **Documentation**: Document any provider-specific behaviors
5. **Testing**: Create tests for your provider implementation

## Example Implementations

Refer to existing provider implementations in `src/pydantic_llm_tester/llms/` as examples:

- `src/pydantic_llm_tester/llms/openai/provider.py`
- `src/pydantic_llm_tester/llms/anthropic/provider.py`
- `src/pydantic_llm_tester/llms/mistral/provider.py`

These implementations show how to handle different API formats, error cases, and usage tracking.
