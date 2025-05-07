"""OpenRouter provider implementation"""

import logging
import os
from typing import Dict, Any, Tuple, Union
import importlib # Import importlib

# Import OpenAI library components directly at the top level
# Errors will be caught during initialization check if not installed
try:
    from openai import OpenAI, APIError
    from openai.types.chat import ChatCompletion, ChatCompletionMessage
    from openai.types.chat.chat_completion import Choice
    from openai.types.completion_usage import CompletionUsage
    OPENAI_CLASSES_AVAILABLE = True
except ImportError:
    OPENAI_CLASSES_AVAILABLE = False
    # Define dummy classes if openai is not installed to allow file parsing
    class OpenAI: pass
    class APIError(Exception): pass
    class ChatCompletion: pass
    class Choice: pass
    class ChatCompletionMessage: pass
    class CompletionUsage: pass

# Import base classes from the project
# Assuming standard project structure allows these imports
try:
    from ..base import BaseLLM, ModelConfig
    from pydantic_llm_tester.utils.cost_manager import UsageData # Relative import for UsageData
except ImportError as e:
    # Fallback for potential import issues, log error
    logging.getLogger(__name__).error(f"Failed to import base classes: {e}. Using dummy classes.")
    class BaseModel: # Dummy Pydantic-like base
        def __init__(self, **kwargs): pass
    class BaseLLM: # Dummy BaseLLM
        def __init__(self, config=None): self.config = config; self.logger = logging.getLogger(__name__)
        def get_api_key(self): return os.environ.get(self.config.env_key) if self.config else None
    class ModelConfig(BaseModel): pass
    class UsageData(BaseModel): pass


class OpenRouterProvider(BaseLLM):
    """Provider implementation for OpenRouter using OpenAI-compatible API"""

    def __init__(self, config=None):
        """Initialize the OpenRouter provider"""
        super().__init__(config)
        self.client = None # Initialize client to None

        # Check if OpenAI SDK is available using importlib
        openai_spec = importlib.util.find_spec("openai")
        if openai_spec is None:
            self.logger.warning("OpenAI SDK not available. Install with 'pip install openai'")
            return # Exit initialization if library not found

        # Check if the necessary classes were imported successfully at the top level
        if not OPENAI_CLASSES_AVAILABLE:
             self.logger.error("Required OpenAI classes could not be imported.")
             return # Should not happen if spec check passed, but safety first

        # Get API key from environment variable specified in config
        env_key_name_from_config = self.config.env_key if self.config else None
        self.logger.debug(f"Attempting to get API key using env var name from config: '{env_key_name_from_config}'")
        api_key = self.get_api_key() # This calls os.environ.get(env_key_name_from_config)
        self.logger.debug(f"Value retrieved for key '{env_key_name_from_config}': '{'******' if api_key else api_key}'") # Mask key if found

        # Explicitly check for None to distinguish missing from empty
        if api_key is None:
            env_key_name_for_warning = env_key_name_from_config or "OPENROUTER_API_KEY" # Use config key or default for warning
            self.logger.warning(f"No API key found for OpenRouter. Set the {env_key_name_for_warning} environment variable.")
            return # Exit initialization if key is missing
        elif not api_key: # Handle empty key case
             self.logger.warning(f"API key for OpenRouter ({self.config.env_key}) is empty. Authentication will likely fail.")
             # Proceed for now, let the API call fail if empty key is invalid

        # Headers recommended by OpenRouter for analytics/identification
        headers = {
            "HTTP-Referer": "https://github.com/madviking/pydantic-llm-tester", # Using URL found in file
            "X-Title": "LLM Tester"      # Using app name
        }

        # Initialize OpenAI client pointing to OpenRouter endpoint
        try:
            # Explicitly pass the retrieved api_key
            self.client = OpenAI(
                api_key=api_key, # Pass the key directly
                base_url="https://openrouter.ai/api/v1",
                default_headers=headers # Pass the headers
            )
            self.logger.info("OpenRouter client initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenRouter client: {e}")
            self.client = None # Ensure client is None on error

    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str,
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the OpenRouter API
        using the OpenAI client library.

        Args:
            prompt: The full prompt text to send.
            system_prompt: System prompt from config.
            model_name: Full OpenRouter model name (e.g., "google/gemini-flash-1.5").
            model_config: Model configuration object.

        Returns:
            Tuple of (response_text, usage_data_dict).
            usage_data_dict contains token counts: prompt_tokens, completion_tokens, total_tokens.
        """
        if not self.client:
            self.logger.error("OpenRouter client is not initialized.")
            raise ValueError("OpenRouter client not initialized. Check API key and configuration.")

        # Ensure we have a valid system prompt (provide a default if empty)
        if not system_prompt:
            system_prompt = "You are a helpful assistant." # Basic default

        # Determine max tokens for the response
        # Use model_config.max_output_tokens if available, otherwise a sensible default
        max_tokens = model_config.max_output_tokens if model_config and model_config.max_output_tokens else 2048

        self.logger.info(f"Sending request to OpenRouter model {model_name} with max_tokens={max_tokens}")

        try:
            # Make the API call using the OpenAI client
            response = self.client.chat.completions.create(
                model=model_name, # Pass the full OpenRouter model ID
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1,  # Lower temperature for more deterministic results, adjust if needed
                # Add other parameters like top_p if required
            )

            # Extract response text
            if response.choices and response.choices[0].message:
                response_text = response.choices[0].message.content or ""
            else:
                self.logger.warning("Received empty response choices from OpenRouter.")
                response_text = ""

            # Extract usage data
            if response.usage:
                usage_data = {
                    "prompt_tokens": response.usage.prompt_tokens or 0,
                    "completion_tokens": response.usage.completion_tokens or 0,
                    "total_tokens": response.usage.total_tokens or 0
                }
            else:
                self.logger.warning("No usage information received from OpenRouter.")
                usage_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            return response_text, usage_data

        except APIError as e:
            # Handle specific OpenAI/OpenRouter API errors
            self.logger.error(f"OpenRouter API error: Status={e.status_code}, Message={e.message}")
            # You might want to raise a more specific custom exception here
            raise ValueError(f"OpenRouter API Error ({e.status_code}): {e.message}") from e
        except Exception as e:
            # Handle other potential errors (network issues, etc.)
            self.logger.error(f"Unexpected error calling OpenRouter API: {str(e)}")
            raise ValueError(f"Unexpected error during OpenRouter API call: {str(e)}") from e

# Example of how to potentially export for discovery if needed by factory
# (Depends on the discovery mechanism in provider_factory.py)
# __all__ = ['OpenRouterProvider']
