"""OpenAI provider implementation"""

import base64
import mimetypes
import os
import json # Added json import
from typing import Dict, Any, Tuple, Optional, List, Union, Type # Added Type

try:
    from openai import OpenAI, BadRequestError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig, BaseModel # Added BaseModel for Type hint
from pydantic_llm_tester.utils.cost_manager import UsageData


class OpenAIProvider(BaseLLM):
    """Provider implementation for OpenAI"""
    
    def __init__(self, config=None, llm_models: Optional[List[str]] = None):
        """Initialize the OpenAI provider"""
        super().__init__(config, llm_models=llm_models)
        
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
        self.client = OpenAI(
            api_key=api_key,
            timeout=120.0, # Overall timeout for the request in seconds
            max_retries=2 # Number of retries
        )
        self.logger.info("OpenAI client initialized with timeout and retries")
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the OpenAI API
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            model_class: The Pydantic model class for schema guidance.
            files: Optional list of file paths. Note: Standard OpenAI chat completions
                   don't directly use file paths in this manner. Vision models or
                   assistants handle files differently. This is a placeholder for
                   future, more specific file handling.
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not self.client:
            self.logger.error("OpenAI client not initialized")
            raise ValueError("OpenAI client not initialized")
            
        # Calculate max tokens based on model config
        # GPT-4 supports up to 4096 tokens, others may vary
        max_tokens = min(model_config.max_output_tokens, 4096)  # Default cap at 4096
        
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "You are a helpful AI assistant. Your primary goal is to extract structured data from the user's input." # More generic default
        
        # Enhance system_prompt with Pydantic schema instructions
        try:
            # Pydantic V2
            schema_str = json.dumps(model_class.model_json_schema(), indent=2)
        except AttributeError:
            # Pydantic V1 fallback
            schema_str = model_class.schema_json(indent=2)
            
        schema_instruction = (
            f"\n\nYour output MUST be a JSON object that strictly conforms to the following JSON Schema:\n"
            f"```json\n{schema_str}\n```\n"
            "Ensure that the generated JSON is valid and adheres to this schema. "
            "If certain information is not present in the input, use appropriate null or default values as defined in the schema."
        )
        
        # Prepend schema instruction to the existing system_prompt or use as system_prompt if original is empty
        effective_system_prompt = f"{system_prompt}\n{schema_instruction}" if system_prompt else schema_instruction.strip()


        # Make the API call
        self.logger.info(f"Sending request to OpenAI model {model_name}")

        user_content: Union[str, List[Dict[str, Any]]] = prompt # Default to text prompt

        if files and self.supports_file_upload:
            self.logger.info(f"OpenAI provider processing files: {files}")
            content_parts = [{"type": "text", "text": prompt}]
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
                        image_url_part = {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                        }
                        content_parts.append(image_url_part)
                        processed_image = True
                        self.logger.info(f"Added image {file_path} ({mime_type}) to OpenAI request.")
                    except Exception as e:
                        self.logger.error(f"Error processing image file {file_path}: {e}")
                else:
                    self.logger.warning(f"Unsupported file type '{mime_type}' for OpenAI vision: {file_path}. Skipping. Only common image types are currently supported.")
            
            if processed_image: # Only use multipart content if at least one image was processed
                user_content = content_parts
            else:
                self.logger.info("No supported image files processed, sending text-only prompt to OpenAI.")
        
        messages = [
            {"role": "system", "content": effective_system_prompt},
            {"role": "user", "content": user_content}
        ]

        # Check if model supports response_format (only newer py_models like gpt-4o and gpt-4-turbo support it)
        supports_json_response_format = any(name in model_name for name in ['gpt-4o', 'gpt-4-turbo', 'gpt-4-vision'])
        
        request_params = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1, # Keep temperature low for structured output
        }

        if supports_json_response_format:
            # If the model supports JSON mode, always use it.
            # The schema is now in the system prompt, guiding the JSON structure.
            request_params["response_format"] = {"type": "json_object"}
            self.logger.info("Requesting JSON object response from OpenAI.")
        else:
            # For older models that don't support response_format,
            # the schema instruction in the system_prompt is the primary way to get JSON.
            # The original system_prompt might already ask for JSON.
            # The schema_instruction reinforces this.
            self.logger.info("Model does not explicitly support JSON response_format. Relying on prompt instructions for JSON output.")
            # No need to further modify messages[0]["content"] here as effective_system_prompt already contains schema and JSON instructions.


        try:
            response = self.client.chat.completions.create(**request_params)
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {str(e)}")
            # If it's a BadRequestError and mentions vision, it might be due to model not supporting vision
            if isinstance(e, BadRequestError) and "vision" in str(e).lower():
                 self.logger.error("This model may not support vision/image inputs, or the image format was incorrect.")
            raise ValueError(f"Error code: {getattr(e, 'status_code', 'unknown')} - {str(e)}")
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        # Return usage data as a dictionary
        usage_data = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return response_text, usage_data
