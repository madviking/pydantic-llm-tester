"""Mistral provider implementation"""

import logging
import json
import os
from typing import Dict, Any, Tuple, Optional, List, Union

try:
    import mistralai
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig
from ...utils.cost_manager import UsageData


class MistralProvider(BaseLLM):
    """Provider implementation for Mistral AI"""
    
    def __init__(self, config=None):
        """Initialize the Mistral provider"""
        super().__init__(config)
        
        # Check if Mistral SDK is available
        if not MISTRAL_AVAILABLE:
            self.logger.warning("Mistral SDK not available. Install with 'pip install mistralai'")
            self.client = None
            return
            
        # Get API key
        api_key = self.get_api_key()
        if not api_key:
            self.logger.warning(f"No API key found for Mistral. Set the {self.config.env_key if self.config else 'MISTRAL_API_KEY'} environment variable.")
            self.client = None
            return
            
        # Initialize Mistral client
        self.client = MistralClient(api_key=api_key)
        self.logger.info("Mistral client initialized")
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the Mistral API
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not self.client:
            self.logger.error("Mistral client not initialized")
            raise ValueError("Mistral client not initialized")
            
        # Calculate max tokens based on model config
        max_tokens = min(model_config.max_output_tokens, 4096)  # Default cap at 4096
        
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "Extract the requested information from the provided text as accurate JSON."
        
        # Make the API call
        self.logger.info(f"Sending request to Mistral model {model_name}")
        
        try:
            # Prepare messages
            messages = [
                ChatMessage(role="system", content=system_prompt + " Return the result as valid JSON."),
                ChatMessage(role="user", content=prompt)
            ]
            
            # Send request
            response = self.client.chat(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1  # Lower temperature for more deterministic results
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Process usage data
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.prompt_tokens + response.usage.completion_tokens
            }
            
            return response_text, usage_data
            
        except Exception as e:
            self.logger.error(f"Error calling Mistral API: {str(e)}")
            raise ValueError(f"Error calling Mistral API: {str(e)}")