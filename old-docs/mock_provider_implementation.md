# Mock Provider Implementation Plan

This document outlines the implementation plan for creating a proper Mock Provider within the pluggable LLM system.

## Background

Currently, mock responses are handled in `utils/mock_responses.py` and are used directly in the `ProviderManager`. This approach bypasses the pluggable LLM system and requires special handling in the provider manager.

By implementing a proper `MockProvider` class that follows the `BaseLLM` interface, we can:

1. Standardize the way mocks are handled
2. Remove special-case code from the provider manager
3. Improve testability
4. Make the mock behavior more configurable

## Implementation Steps

### 1. Create Directory Structure

Create the following structure:

```
llm_tester/llms/mock/
│
├── __init__.py
├── config.json
└── provider.py
```

### 2. Implement Configuration

Create `config.json` with:

```json
{
  "name": "mock",
  "provider_type": "mock",
  "env_key": "MOCK_API_KEY",
  "system_prompt": "You are a mock LLM provider for testing purposes.",
  "models": [
    {
      "name": "mock:default",
      "default": true,
      "preferred": false,
      "cost_input": 0.0,
      "cost_output": 0.0,
      "cost_category": "free",
      "max_input_tokens": 16000,
      "max_output_tokens": 16000
    },
    {
      "name": "mock:fast",
      "default": false,
      "preferred": false,
      "cost_input": 0.0,
      "cost_output": 0.0,
      "cost_category": "free",
      "max_input_tokens": 8000,
      "max_output_tokens": 8000
    },
    {
      "name": "mock:large",
      "default": false,
      "preferred": false,
      "cost_input": 0.0,
      "cost_output": 0.0,
      "cost_category": "free",
      "max_input_tokens": 32000,
      "max_output_tokens": 32000
    }
  ]
}
```

### 3. Implement Provider

Create `provider.py` with:

```python
"""Mock provider implementation for testing purposes"""

import logging
import json
import os
import re
from typing import Dict, Any, Tuple, Optional, List, Union
import time
import random

from ..base import BaseLLM, ModelConfig
from ...utils.cost_manager import UsageData

# Import mock response utilities
from ...utils.mock_responses import get_mock_response, register_mock_response

class MockProvider(BaseLLM):
    """Provider implementation for mocked responses"""
    
    def __init__(self, config=None):
        """Initialize the Mock provider"""
        super().__init__(config)
        self.logger.info("Mock provider initialized")
        
        # Set up mock response registry
        self.response_registry = {}
        
    def register_mock_response(self, key: str, response: str) -> None:
        """
        Register a mock response for a specific key
        
        Args:
            key: The key to associate with this response
            response: The mock response text
        """
        self.response_registry[key] = response
        self.logger.debug(f"Registered mock response for key: {key}")
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call for mocked responses
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        self.logger.info(f"Mock provider called with model {model_name}")
        
        # Add simulated delay to mimic real API call
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)
        
        # Determine response type based on content
        source_match = re.search(r'SOURCE:(.*?)(?=$|PROMPT:)', prompt, re.DOTALL | re.IGNORECASE)
        source_text = source_match.group(1).strip() if source_match else ""
        
        # Get mock response based on source content
        if "MACHINE LEARNING ENGINEER" in source_text or "job" in source_text.lower() or "software engineer" in source_text.lower() or "developer" in source_text.lower():
            mock_response = get_mock_response("job_ads", source_text)
        else:
            mock_response = get_mock_response("product_descriptions", source_text)
        
        # Calculate token counts for usage data
        prompt_tokens = len(prompt.split())
        completion_tokens = len(mock_response.split())
        total_tokens = prompt_tokens + completion_tokens
        
        # Create usage data
        usage_data = UsageData(
            provider="mock",
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            prompt_cost=0.0,
            completion_cost=0.0,
            total_cost=0.0,
            elapsed_time=delay
        )
        
        return mock_response, usage_data
```

### 4. Update `__init__.py`

Create an `__init__.py` that exports the provider:

```python
"""Mock provider module"""

from .provider import MockProvider

__all__ = ['MockProvider']
```

### 5. Extend Mock Response Module (Optional)

Enhance the existing `utils/mock_responses.py` to work better with the mock provider:

```python
"""
Mock response generator for testing without API calls
"""

import json
import os
import re
import random
from typing import Dict, Any, List, Optional, Tuple

# Global registry of mock responses
_MOCK_RESPONSES: Dict[str, Dict[str, str]] = {}

def register_mock_response(category: str, key: str, response: str) -> None:
    """
    Register a mock response for a specific category and key
    
    Args:
        category: The category (e.g., 'job_ads', 'product_descriptions')
        key: The key to associate with this response
        response: The mock response text
    """
    if category not in _MOCK_RESPONSES:
        _MOCK_RESPONSES[category] = {}
    
    _MOCK_RESPONSES[category][key] = response

def get_mock_response(category: str, source_text: str) -> str:
    """
    Get a mock response based on category and source text
    
    Args:
        category: The category to get a response for
        source_text: The source text to base the response on
        
    Returns:
        A mock response string
    """
    # Check if we have a specific mock for this source_text
    if category in _MOCK_RESPONSES:
        for key, response in _MOCK_RESPONSES[category].items():
            if key in source_text:
                return response
    
    # If no specific mock found, use the default mock
    if category == "job_ads":
        return _generate_job_ad_response(source_text)
    elif category == "product_descriptions":
        return _generate_product_description_response(source_text)
    else:
        return _generate_generic_response(category, source_text)

# Existing mock generation functions can remain unchanged
def _generate_job_ad_response(source_text: str) -> str:
    # Implementation remains the same...

def _generate_product_description_response(source_text: str) -> str:
    # Implementation remains the same...

def _generate_generic_response(category: str, source_text: str) -> str:
    # Implementation remains the same...
```

### 6. Integration Steps

1. Create and test the Mock Provider implementation
2. Update the provider registry to recognize the mock provider
3. Update the provider manager to use the mock provider through the pluggable system
4. Test with existing test cases to ensure compatibility

## Testing Strategy

1. Unit test the mock provider in isolation
2. Test the mock provider through the pluggable LLM system
3. Ensure the behavior is identical to the previous implementation
4. Test different model configurations within the mock provider

## Benefits

- Standard interface for all providers, including mocks
- Improved testability
- Simplified provider manager implementation
- More configurable mock behavior (e.g., different mock models)
- Removing special cases from the code