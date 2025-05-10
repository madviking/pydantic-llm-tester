"""Anthropic provider implementation"""

from typing import Dict, Any, Tuple, Union, Optional, List

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig
from pydantic_llm_tester.utils.cost_manager import UsageData


class AnthropicProvider(BaseLLM):
    """Provider implementation for Anthropic"""
    
    def __init__(self, config=None, llm_models=None): # Added llm_models
        """Initialize the Anthropic provider"""
        super().__init__(config, llm_models=llm_models) # Pass llm_models to super
        
        # Check if Anthropic SDK is available
        if not ANTHROPIC_AVAILABLE:
            self.logger.warning("Anthropic SDK not available. Install with 'pip install anthropic'")
            self.client = None
            return
            
        # Get API key
        api_key = self.get_api_key()
        if not api_key:
            self.logger.warning(f"No API key found for Anthropic. Set the {self.config.env_key if self.config else 'ANTHROPIC_API_KEY'} environment variable.")
            self.client = None
            return
            
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=api_key)
        self.logger.info("Anthropic client initialized")
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig, files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the Anthropic API
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            files: Optional list of file paths. Anthropic models like Claude 3
                   support image inputs, which would require specific handling of these files.
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not self.client:
            self.logger.error("Anthropic client not initialized")
            raise ValueError("Anthropic client not initialized")
            
        # Calculate max tokens based on model config
        max_tokens = min(model_config.max_output_tokens, 4096)  # Default cap at 4096
        
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "Extract the requested information from the provided text as accurate JSON."
        
        # Make the API call
        self.logger.info(f"Sending request to Anthropic model {model_name}")

        if files and self.supports_file_upload:
            # TODO: Implement actual file handling for Anthropic.
            # This would involve reading file content (e.g., for images),
            # encoding it (e.g., base64), and constructing the message
            # payload according to Anthropic's API for multimodal inputs.
            self.logger.info(f"Anthropic provider received files: {files}. Specific handling not yet implemented.")
        
        try:
            # Attempt to use response_format (for newer Anthropic SDK versions)
            response = self.client.messages.create(
                model=model_name,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1,  # Lower temperature for more deterministic results
                response_format={"type": "json_object"}  # Request JSON response
            )
        except TypeError:
            # Fall back to not using response_format for older versions
            self.logger.info("Falling back to older Anthropic API format without response_format")
            response = self.client.messages.create(
                model=model_name,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1  # Lower temperature for more deterministic results
            )
        
        # Extract response text
        response_text = response.content[0].text
        
        # Return usage data as a dictionary
        usage_data = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }
        
        return response_text, usage_data
