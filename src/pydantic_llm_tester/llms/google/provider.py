"""Google provider implementation"""

import base64
import mimetypes
import os
import json # Added json import
from typing import Dict, Any, Tuple, Union, Optional, List, Type # Added Type

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold, Part # Added Part
    import google.auth # Import google.auth
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    # Define Part for type hinting if import fails, though it won't be used.
    class Part: pass 
    
from ..base import BaseLLM, ModelConfig, BaseModel # Added BaseModel for Type hint
from pydantic_llm_tester.utils.cost_manager import UsageData


class GoogleProvider(BaseLLM):
    """Provider implementation for Google Gemini API"""
    
    def __init__(self, config=None, llm_models: Optional[List[str]] = None): # Added llm_models
        """Initialize the Google provider"""
        super().__init__(config, llm_models=llm_models) # Pass llm_models to super
        
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
                     model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the Google Gemini API
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            model_class: The Pydantic model class for schema guidance.
            files: Optional list of file paths. Gemini models support multimodal input.
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not GOOGLE_AVAILABLE:
            self.logger.error("Google Generative AI SDK not initialized")
            raise ValueError("Google Generative AI SDK not initialized")
            
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "You are a helpful AI assistant. Your primary goal is to extract structured data from the user's input."

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
        # For Gemini, system instructions are typically part of the main prompt content.
        effective_system_prompt = f"{system_prompt}\n{schema_instruction}" if system_prompt else schema_instruction.strip()
        
        # Make the API call
        self.logger.info(f"Sending request to Google model {model_name}")
        
        # Create combined prompt with system prompt first, as it's always text
        # The user prompt (from the 'prompt' arg) is the main instruction.
        # The 'source' text is already part of the 'prompt' arg by BaseLLM.get_response.
        # So, full_prompt_text will be: original_system_prompt + schema_instruction + original_user_prompt_and_source
        full_prompt_text = f"{effective_system_prompt}\n\n{prompt}"
        
        content_payload: List[Any] = [full_prompt_text] # Start with the text prompt

        if files and self.supports_file_upload:
            self.logger.info(f"Google provider processing files: {files}")
            processed_file = False
            for file_path in files:
                if not os.path.exists(file_path):
                    self.logger.warning(f"File not found: {file_path}. Skipping.")
                    continue

                mime_type, _ = mimetypes.guess_type(file_path)
                # Gemini supports various image types, and also PDF, video, audio.
                # For now, focusing on common image types for consistency.
                supported_image_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]

                if mime_type in supported_image_types:
                    try:
                        with open(file_path, "rb") as f:
                            image_bytes = f.read()
                        # For Gemini, Part.from_data takes raw bytes directly
                        image_part = Part.from_data(data=image_bytes, mime_type=mime_type)
                        content_payload.append(image_part)
                        processed_file = True
                        self.logger.info(f"Added image {file_path} ({mime_type}) to Google Gemini request.")
                    except Exception as e:
                        self.logger.error(f"Error processing image file {file_path} for Gemini: {e}")
                else:
                    self.logger.warning(f"Unsupported file type '{mime_type}' for Google Gemini in this implementation: {file_path}. Skipping. Only common image types are currently handled.")
            
            if not processed_file:
                self.logger.info("No supported files processed, sending text-only prompt to Google Gemini.")
                # content_payload already contains full_prompt_text
        
        try:
            # Get model
            # This should automatically use the credentials loaded by google.auth.default()
            # For models like 'gemini-pro-vision', system_prompt is not directly supported in the same way.
            # It's usually part of the user's first text prompt.
            # The model name itself implies vision capabilities.
            effective_model_name = model_name
            if "vision" not in model_name and any(isinstance(item, Part) and item.inline_data and "image" in item.inline_data.mime_type for item in content_payload):
                # If images are present but model name doesn't explicitly say vision,
                # try appending -vision or using a known vision model if available.
                # This is a heuristic. Better to use explicit vision model names.
                self.logger.warning(f"Images provided for non-vision model name '{model_name}'. Attempting to use with vision capabilities if supported by the model.")
                # For example, 'gemini-1.5-pro' can handle vision. 'gemini-pro' needs 'gemini-pro-vision'.
                # This logic might need refinement based on actual model naming and capabilities.
                if model_name == "gemini-pro" and not any(isinstance(item, str) and "vision" in item for item in content_payload): # Simple check
                     # Heuristic: if it's gemini-pro and we have images, try gemini-pro-vision
                     # This is very basic and might need to be removed or made more robust.
                     # For now, we rely on the user specifying a vision-capable model name.
                     pass


            model = genai.GenerativeModel(effective_model_name)
            
            # Configure safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
            }
            
            # Create generation config
            generation_config_dict: Dict[str, Any] = {
                "temperature": 0.1,  # Low temperature for more deterministic results
                "top_p": 0.95, # Default from original code
                "top_k": 40,   # Default from original code
                "max_output_tokens": model_config.max_output_tokens,
                "response_mime_type": "application/json" # Always request JSON for structured extraction
            }
            self.logger.info("Requesting JSON response (application/json) from Google Gemini.")

            # Send request
            response = model.generate_content(
                contents=content_payload, # Use 'contents' for list of parts
                generation_config=genai.types.GenerationConfig(**generation_config_dict),
                safety_settings=safety_settings
            )
            
            # Extract response text
            # If JSON was requested, response.text might already be a JSON string.
            # If not, it's plain text.
            response_text = response.text
            
            # Create usage data
            # Google API (genai) for generate_content doesn't directly return token counts in the response object.
            # model.count_tokens(content_payload) can be used *before* the call for an estimate.
            # For now, we continue with a rough estimate post-call.
            # This is a known limitation/difference in the Gemini API client.
            
            # Estimate tokens for the input payload
            estimated_prompt_tokens = 0
            for part in content_payload:
                if isinstance(part, str):
                    estimated_prompt_tokens += len(part.split())
                elif isinstance(part, Part) and part.text: # Check if Part has text
                    estimated_prompt_tokens += len(part.text.split())
                # Image token counting is complex and not done here.

            completion_tokens = len(response_text.split()) # Rough estimate
            
            usage_data = {
                "prompt_tokens": estimated_prompt_tokens, # Very rough estimate
                "completion_tokens": completion_tokens,
                "total_tokens": estimated_prompt_tokens + completion_tokens
            }
            
            return response_text, usage_data
            
        except Exception as e:
            self.logger.error(f"Error calling Google API with model {model_name}: {str(e)}")
            # Check for specific errors related to content types if possible
            if " candidats" in str(e).lower() and "finish reason" in str(e).lower(): # French error for no candidates
                 self.logger.error("Google API returned no candidates. This might be due to safety filters or an issue with the prompt/image content.")
            raise ValueError(f"Error calling Google API with model {model_name}: {str(e)}")
