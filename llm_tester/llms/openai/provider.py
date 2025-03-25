"""OpenAI provider implementation"""

import logging
import json
import os
from typing import Dict, Any, Tuple, Optional, List, Union

try:
    from openai import OpenAI, BadRequestError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig
from ...utils.cost_manager import UsageData


class OpenAIProvider(BaseLLM):
    """Provider implementation for OpenAI"""
    
    def __init__(self, config=None):
        """Initialize the OpenAI provider"""
        super().__init__(config)
        
        # Check if OpenAI SDK is available
        if not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI SDK not available. Install with 'pip install openai'")
            self.client = None
            return
            
        # Get API key
        api_key = self.get_api_key()
        if not api_key:
            self.logger.warning(f"No API key found for OpenAI. Set the {self.config.env_key if self.config else 'OPENAI_API_KEY'} environment variable.")
            self.client = None
            return
            
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.logger.info("OpenAI client initialized")
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the OpenAI API
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not self.client:
            self.logger.error("OpenAI client not initialized")
            raise ValueError("OpenAI client not initialized")
            
        # Calculate max tokens based on model config
        max_tokens = min(model_config.max_output_tokens, 8192)  # Default cap at 8192
        
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "Extract the requested information from the provided text as accurate JSON."
        
        # Make the API call
        self.logger.info(f"Sending request to OpenAI model {model_name}")
        
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.1,  # Lower temperature for more deterministic results
            response_format={"type": "json_object"}  # Request JSON response
        )
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        # Return usage data as a dictionary
        usage_data = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return response_text, usage_data