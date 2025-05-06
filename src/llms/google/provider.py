"""Google provider implementation"""

import logging
import json
import os
from typing import Dict, Any, Tuple, Optional, List, Union

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    import google.auth # Import google.auth
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig
from ...utils.cost_manager import UsageData


class GoogleProvider(BaseLLM):
    """Provider implementation for Google Gemini API"""
    
    def __init__(self, config=None):
        """Initialize the Google provider"""
        super().__init__(config)
        
        # Check if Google Generative AI SDK is available
        if not GOOGLE_AVAILABLE:
            self.logger.warning("Google Generative AI SDK not available. Install with 'pip install google-generativeai google-auth'") # Add google-auth to install instructions
            self.client = None
            return
            
        # Attempt to load credentials using google.auth
        credentials, project = google.auth.default()
        
        if credentials is None or not credentials.valid:
             # Fallback to checking for GOOGLE_API_KEY if default auth fails
             api_key = self.get_api_key() # This still checks the env_key from config
             if not api_key:
                 self.logger.warning(f"No Google credentials found. Set GOOGLE_APPLICATION_CREDENTIALS or {self.config.env_key if self.config else 'GOOGLE_API_KEY'} environment variable.")
                 self.client = None
                 return
             else:
                 # Initialize with API key if found
                 genai.configure(api_key=api_key)
                 self.logger.info("Google Generative AI client initialized with API Key")
        else:
            # Initialize with loaded credentials
            # Note: genai.configure doesn't directly take credentials,
            # but the underlying google-generativeai library should use
            # the credentials loaded by google.auth.default() automatically
            # if no api_key is explicitly configured.
            # We can add a check here to ensure the API is accessible with these credentials if needed,
            # but for now, rely on the library's default behavior.
            self.logger.info("Google Generative AI client initialized with default credentials")
            # No explicit genai.configure(credentials=...) needed here,
            # the library should pick them up from the environment/defaults.
            # We can optionally set a dummy api_key if the library requires genai.configure to be called,
            # but it's better to rely on the default credential loading.
            # Let's just ensure the client is not None if credentials were found.
            self.client = True # Indicate client is ready, even if no explicit client object

        # The actual client object might be implicitly managed by the genai library
        # when using default credentials. We'll rely on the library handling the API calls.
        # The _call_llm_api method will use genai.GenerativeModel which should
        # pick up the credentials automatically.
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the Google Gemini API
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not GOOGLE_AVAILABLE:
            self.logger.error("Google Generative AI SDK not initialized")
            raise ValueError("Google Generative AI SDK not initialized")
            
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "Extract the requested information from the provided text as accurate JSON."
        
        # Make the API call
        self.logger.info(f"Sending request to Google model {model_name}")
        
        try:
            # Get model
            # This should automatically use the credentials loaded by google.auth.default()
            model = genai.GenerativeModel(model_name)
            
            # Configure safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
            }
            
            # Create generation config
            generation_config = {
                "temperature": 0.1,  # Low temperature for more deterministic results
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": model_config.max_output_tokens
            }
            
            # Create combined prompt with system prompt
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Send request
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Extract response text
            response_text = response.text
            
            # Create usage data
            # Note: Google API may not provide token usage, so we estimate
            prompt_tokens = len(full_prompt.split())  # Rough estimate
            completion_tokens = len(response_text.split())  # Rough estimate
            
            usage_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
            
            return response_text, usage_data
            
        except Exception as e:
            self.logger.error(f"Error calling Google API: {str(e)}")
            raise ValueError(f"Error calling Google API: {str(e)}")
