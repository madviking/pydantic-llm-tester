"""Anthropic provider implementation"""

import base64
import mimetypes
import os
import json # Added json import
from typing import Dict, Any, Tuple, Union, Optional, List, Type # Added Type

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig, BaseModel # Added BaseModel for Type hint
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
                     model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the Anthropic API
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            model_class: The Pydantic model class for schema guidance.
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
            system_prompt = "You are a helpful AI assistant. Your primary goal is to extract structured data from the user's input." # More generic default

        # Enhance system_prompt with Pydantic schema instructions
        try:
            schema_str = json.dumps(model_class.model_json_schema(), indent=2)
        except AttributeError:
            schema_str = model_class.schema_json(indent=2)
            
        schema_instruction = (
            f"\n\nYour output MUST be a JSON object that strictly conforms to the following JSON Schema:\n"
            f"```json\n{schema_str}\n```\n"
            "Ensure that the generated JSON is valid and adheres to this schema. "
            "If certain information is not present in the input, use appropriate null or default values as defined in the schema."
        )
        effective_system_prompt = f"{system_prompt}\n{schema_instruction}" if system_prompt else schema_instruction.strip()

        # Make the API call
        self.logger.info(f"Sending request to Anthropic model {model_name}")

        user_message_content: Union[str, List[Dict[str, Any]]]

        if files and self.supports_file_upload:
            self.logger.info(f"Anthropic provider processing files: {files}")
            content_blocks: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
            processed_image = False
            for file_path in files:
                if not os.path.exists(file_path):
                    self.logger.warning(f"File not found: {file_path}. Skipping.")
                    continue

                mime_type, _ = mimetypes.guess_type(file_path)
                supported_image_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]

                if mime_type in supported_image_types:
                    try:
                        with open(file_path, "rb") as image_file:
                            image_bytes = image_file.read()
                        base64_image = base64.b64encode(image_bytes).decode('utf-8')
                        image_block = {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image,
                            },
                        }
                        content_blocks.append(image_block)
                        processed_image = True
                        self.logger.info(f"Added image {file_path} ({mime_type}) to Anthropic request.")
                    except Exception as e:
                        self.logger.error(f"Error processing image file {file_path}: {e}")
                else:
                    self.logger.warning(f"Unsupported file type '{mime_type}' for Anthropic: {file_path}. Skipping. Only common image types are currently supported.")
            
            if processed_image:
                user_message_content = content_blocks
            else:
                self.logger.info("No supported image files processed, sending text-only prompt to Anthropic.")
                user_message_content = prompt # Fallback to simple string prompt
        else:
            user_message_content = prompt

        messages_payload = [{"role": "user", "content": user_message_content}]
        
        request_params = {
            "model": model_name,
            "system": effective_system_prompt, # Use the enhanced system prompt
            "messages": messages_payload,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        # Anthropic's JSON mode is usually implicitly handled by good prompting.
        # Claude 3 models are good at following system prompt instructions for JSON.
        # The response_format parameter is newer and might not be supported by all SDK versions or models.
        # Forcing JSON via prompt is generally robust for Claude.
        # We will attempt to use response_format if available, but the primary mechanism is the system prompt.
        
        try:
            # Try with response_format first if the SDK version supports it
            # This is a bit of a guess; official docs should be checked for exact SDK version compatibility
            if hasattr(self.client.messages, "create") and "response_format" in anthropic.types.MessageCreateParams.__annotations__:
                 self.logger.info("Attempting to use response_format with Anthropic.")
                 response = self.client.messages.create(
                     **request_params,
                     response_format={"type": "json_object"} 
                 )
            else:
                 self.logger.info("Anthropic SDK version does not seem to support 'response_format' parameter directly, or it's not type-hinted. Relying on system prompt for JSON.")
                 response = self.client.messages.create(**request_params)

        except TypeError as te: # Handles cases where response_format is not a valid param for the SDK version
            self.logger.warning(f"TypeError when calling Anthropic, possibly due to 'response_format': {te}. Retrying without it.")
            # Remove response_format if it caused TypeError and retry
            if "response_format" in request_params: # Should not be needed if check above is perfect
                del request_params["response_format"] 
            
            # The effective_system_prompt already contains strong instructions for JSON.
            response = self.client.messages.create(**request_params)
        except Exception as e:
            self.logger.error(f"Error calling Anthropic API: {str(e)}")
            raise ValueError(f"Error calling Anthropic API: {str(e)}")
        
        # Extract response text
        response_text = response.content[0].text
        
        # Return usage data as a dictionary
        usage_data = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }
        
        return response_text, usage_data
