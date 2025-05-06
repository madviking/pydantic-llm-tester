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
        
        # Extract source text
        source_match = re.search(r'Source Text:\n(.*?)$', prompt, re.DOTALL)
        source_text = source_match.group(1).strip() if source_match else ""
        
        # Check for registered mock responses first
        for key, response in self.response_registry.items():
            if key in prompt or key in source_text:
                self.logger.info(f"Using registered mock response for key: {key}")
                mock_response = response
                break
        else:
            # If no registered response matches, generate a generic one
            self.logger.info("No registered mock response found, generating generic response")
            # Import here to avoid circular imports
            from ...utils.mock_responses import get_mock_response
            
            # Determine response type based on content
            if "Extract the animal" in prompt: # Check for the integration_tests/simple case
                mock_response = get_mock_response("integration_tests", source_text)
            elif "MACHINE LEARNING ENGINEER" in source_text or "job" in source_text.lower() or "software engineer" in source_text.lower() or "developer" in source_text.lower():
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
            total_tokens=total_tokens
        )
        
        # Add elapsed time manually since it's not part of the standard UsageData fields
        usage_data.elapsed_time = delay
        
        return mock_response, usage_data
