"""Mistral provider implementation"""

import logging
import json # Added json import
from typing import Dict, Any, Tuple, Optional, List, Union, Type # Added Type

try:
    # Import the client directly
    from mistralai.client import MistralClient
    # Message format is now a list of dicts, no need for UserMessage/ChatMessage classes
    # from mistralai.models.chat_messages import UserMessage, ChatMessage # Not needed anymore
    MISTRAL_AVAILABLE = True
except ImportError as e:
    MISTRAL_AVAILABLE = False
    # Log the import error for debugging
    logging.warning(f"Could not import Mistral SDK: {e}. Install with 'pip install mistralai'")

from ..base import BaseLLM, ModelConfig, BaseModel # Added BaseModel
from pydantic_llm_tester.utils.cost_manager import UsageData


class MistralProvider(BaseLLM):
    """Provider implementation for Mistral AI"""

    def __init__(self, config=None, llm_models: Optional[List[str]] = None): # Added llm_models
        """Initialize the Mistral provider"""
        super().__init__(config, llm_models=llm_models) # Pass llm_models to super

        self.client: Optional[MistralClient] = None # Type hint for clarity

        # Check if Mistral SDK is available
        if not MISTRAL_AVAILABLE:
            # Warning already logged during import
            return

        # Get API key
        # Use the helper method from the base class if available, otherwise check env var directly
        api_key = self.get_api_key() # Assuming BaseLLM has this
        if not api_key:
            env_var_name = self.config.env_key if self.config and self.config.env_key else 'MISTRAL_API_KEY'
            self.logger.warning(f"No API key found for Mistral. Set the {env_var_name} environment variable.")
            return

        try:
            # Initialize Mistral client
            self.client = MistralClient(api_key=api_key)
            # Optional: Check connection or list models to confirm key validity early
            # self.client.list_models() # Uncomment if you want strict early validation
            self.logger.info("Mistral client initialized successfully")
        except Exception as e:
             self.logger.error(f"Failed to initialize Mistral client: {e}")
             self.client = None


    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str,
                     model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the Mistral API

        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            model_class: The Pydantic model class for schema guidance.
            files: Optional list of file paths. Standard Mistral chat models
                   are primarily text-based. File handling might involve
                   inlining text content if applicable.

        Returns:
            Tuple of (response_text, usage_data)
        """
        if not self.client:
            self.logger.error("Mistral client not initialized. Cannot make API call.")
            raise ValueError("Mistral client not initialized")

        # Use max_output_tokens from config directly.
        # The API/SDK will handle None or invalid values.
        max_tokens = model_config.max_output_tokens

        # Prepare messages in the new format (list of dictionaries)
        
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
        effective_system_prompt = f"{system_prompt}\n{schema_instruction}" if system_prompt else schema_instruction.strip()

        messages: List[Dict[str, str]] = []
        if effective_system_prompt: # Use the enhanced system prompt
            messages.append({"role": "system", "content": effective_system_prompt})

        messages.append({"role": "user", "content": prompt})

        # Determine if JSON output is requested.
        # The original code forced JSON by modifying the system prompt and user prompt.
        # The modern way is using the response_format parameter.
        # Assuming you want to keep the intent of forcing JSON output:
        response_format = {"type": "json_object"}
        # Note: Not all Mistral models support JSON mode. Check model documentation.
        # If the model doesn't support it, the API call might fail or return plain text.
        # You might want to add a check based on model_name if needed.

        # Make the API call
        self.logger.info(f"Sending request to Mistral model {model_name}")

        if files and self.supports_file_upload:
            # TODO: Implement actual file handling for Mistral if applicable.
            # For text-based models, this might mean reading text file content
            # and prepending/appending it to the prompt.
            # For now, just log that files were received.
            self.logger.info(f"Mistral provider received files: {files}. Specific handling not yet implemented for this text-centric API.")
        
        try:
            response = self.client.chat(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=model_config.temperature or 0.1, # Use config temp, default to 0.1
                # top_p=model_config.top_p, # Add if you use top_p in ModelConfig
                # random_seed=model_config.seed, # Add if you use seed in ModelConfig
                response_format=response_format, # Request JSON output explicitly
            )

            # Extract response text - this part is usually stable
            response_text = response.choices[0].message.content

            # Process usage data - attribute names updated
            usage_data_dict = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": model_name # Add the model name to usage data
            }
            # You might want to wrap this in your UsageData class if it's not a dict alias
            usage_data = UsageData(**usage_data_dict) if isinstance(UsageData, type) else usage_data_dict


            self.logger.info(f"Mistral API call successful. Usage: {usage_data_dict}")

            return response_text, usage_data

        except Exception as e:
            self.logger.error(f"Error calling Mistral API with model {model_name}: {str(e)}")
            # Re-raise the exception after logging
            raise ValueError(f"Error calling Mistral API: {str(e)}") from e

    # You might need to implement other methods required by BaseLLM
    # e.g., get_available_models, calculate_cost, etc.
    # def get_available_models(self) -> List[str]:
    #     # Example of how you might get models, requires client initialization
    #     if not self.client:
    #          self.logger.warning("Mistral client not initialized. Cannot fetch models.")
    #          return []
    #     try:
    #         models = self.client.list_models().data
    #         # Filter models that support chat if necessary
    #         chat_models = [m.id for m in models if 'chat' in m.id or 'instruct' in m.id] # Simple heuristic
    #         return chat_models
    #     except Exception as e:
    #         self.logger.error(f"Failed to fetch Mistral models: {e}")
    #         return []

    # def calculate_cost(self, model_name: str, usage: UsageData) -> float:
    #     # You would need a mapping of model_name to token costs (per input/output token)
    #     # This data changes, so keeping it updated is important.
    #     # Example (replace with actual current costs):
    #     cost_per_million_input_tokens = {
    #         "mistral-tiny-2312": 0.14,
    #         "mistral-small-2402": 2.00,
    #         "mistral-medium-2312": 2.70,
    #         "mistral-large-2402": 8.00,
    #         "mistral-embed-latest": 0.10, # Embeddings model, not chat
    #         # ... add other models
    #     }.get(model_name, 0) # Default to 0 if model cost not found

    #     cost_per_million_output_tokens = {
    #         "mistral-tiny-2312": 0.42,
    #         "mistral-small-2402": 6.00,
    #         "mistral-medium-2312": 8.10,
    #         "mistral-large-2402": 24.00,
    #         "mistral-embed-latest": 0.10, # Embeddings model, not chat
    #         # ... add other models
    #     }.get(model_name, 0)

    #     input_cost = (usage.prompt_tokens / 1_000_000) * cost_per_million_input_tokens
    #     output_cost = (usage.completion_tokens / 1_000_000) * cost_per_million_output_tokens
    #     return input_cost + output_cost
