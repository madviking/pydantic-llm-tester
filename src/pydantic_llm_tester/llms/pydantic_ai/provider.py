"""PydanticAI provider implementation"""

import logging
import os
import json # Added json import
from typing import Dict, Any, Tuple, Optional, Union, Type, List 
import inspect

from pydantic import BaseModel # BaseModel is directly from pydantic here

# Define a global variable for pydantic_ai availability
PYDANTIC_AI_AVAILABLE = False

# Try to import pydantic_ai
try:
    import pydantic_ai

    PYDANTIC_AI_AVAILABLE = True
except Exception as e:
    logging.getLogger(__name__).error(f"Error importing pydantic_ai: {e}")
    PYDANTIC_AI_AVAILABLE = False  # Ensure flag is False on import error
    pass


from ..base import BaseLLM, ModelConfig
from pydantic_llm_tester.utils.cost_manager import UsageData


class PydanticAIProvider(BaseLLM):
    """Provider implementation using PydanticAI"""

    def __init__(self, config=None, llm_models: Optional[List[str]] = None): # Added llm_models
        """Initialize the PydanticAI provider"""
        super().__init__(config, llm_models=llm_models) # Pass llm_models to super

        # Check if PydanticAI is available
        if not PYDANTIC_AI_AVAILABLE:
            self.logger.warning("PydanticAI not available. Install with 'pip install pydantic-ai'")
            return

        self.logger.info("PydanticAI provider initialized")

        # Store runners for different providers
        self.provider_configs = {}
        self.logger.info("PydanticAI provider initialized") # Moved from original position for clarity

    def _get_model_instance(self, provider: str, model: str) -> Any:
        """Get or create a model instance for the specified provider and model

        Args:
            provider: The provider to use (openai, anthropic)
            model: The model name

        Returns:
            A PydanticAI model instance
        """
        if not PYDANTIC_AI_AVAILABLE:
            self.logger.error("PydanticAI not available")
            raise ValueError("PydanticAI not available")

        model_key = f"{provider}:{model}"

        # Check if model already exists
        if model_key in self.provider_configs:
            return self.provider_configs[model_key]

        # Create new model instance based on provider
        if provider == "openai":
            # Get API key
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.logger.error("No API key found for OpenAI")
                raise ValueError("No API key found for OpenAI")

            # Import the OpenAI model dynamically
            from pydantic_ai.models.openai import OpenAIModel

            # Create OpenAI model
            model_instance = OpenAIModel(
                model_name=model,
                api_key=api_key
            )

        elif provider == "anthropic":
            # Get API key
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                self.logger.error("No API key found for Anthropic")
                raise ValueError("No API key found for Anthropic")

            # Import the Anthropic model dynamically
            from pydantic_ai.models.anthropic import AnthropicModel

            # Create Anthropic model
            model_instance = AnthropicModel(
                model_name=model,
                api_key=api_key
            )

        else:
            self.logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")

        # Cache the model
        self.provider_configs[model_key] = model_instance
        return model_instance

    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str,
                     model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call using PydanticAI

        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            model_class: The Pydantic model class for schema guidance.
            files: Optional list of file paths. PydanticAI itself doesn't directly
                   handle file uploads; this would depend on the underlying LLM
                   and how PydanticAI is configured to use it.

        Returns:
            Tuple of (response_text, usage_data)
        """
        if not PYDANTIC_AI_AVAILABLE:
            self.logger.error("PydanticAI not available")
            raise ValueError("PydanticAI not available")

        # Parse model name to get provider and model
        # Expected format is pydantic_ai:underlying_provider:model_name
        name_parts = model_name.split(':')
        if len(name_parts) < 3 or name_parts[0] != 'pydantic_ai':
            self.logger.error(f"Invalid model name format for PydanticAI: {model_name}. Expected pydantic_ai:provider:model")
            raise ValueError(f"Invalid model name format for PydanticAI: {model_name}. Expected pydantic_ai:provider:model")

        provider_name = name_parts[1]  # Underlying provider (openai or anthropic)
        underlying_model_name = name_parts[2]  # Underlying model name

        # Ensure we have a valid system prompt
        if not system_prompt:
            # PydanticAI might not use system_prompt in the same way as direct API calls.
            # It's often part of the main prompt or handled by the library.
            # For now, we'll keep it, but its effectiveness depends on pydantic-ai's internals.
            system_prompt = "You are a helpful AI assistant. Your task is to extract information into a structured JSON format."
        
        # model_class is now passed directly as an argument. The inspect logic is removed.
        if not model_class: # Should not happen if BaseLLM.get_response is called correctly
            self.logger.error("PydanticAIProvider._call_llm_api called without model_class.")
            raise ValueError("model_class is required for PydanticAIProvider.")

        # Get or create model instance for the specified provider
        model_instance = self._get_model_instance(provider_name, underlying_model_name)

        if files and self.supports_file_upload:
            # TODO: Investigate how PydanticAI could leverage files with underlying models.
            # This would likely involve passing file content or specific structures
            # to the `pydantic_ai` library methods if it supports multimodal input
            # for the chosen underlying LLM.
            self.logger.info(f"PydanticAI provider received files: {files}. Direct handling by PydanticAI provider not yet implemented; depends on underlying LLM and pydantic-ai library capabilities.")

        # Generate response using PydanticAI
        # Trying a different pattern: calling a method on the model_class itself
        # Common method names might be 'parse_response' or 'from_response'
        # Let's try 'parse_response' first. This assumes pydantic_ai adds this method to BaseModel subclasses.
        if not hasattr(model_class, 'parse_response'):
             self.logger.error(f"Model class {model_class.__name__} does not have a 'parse_response' method.")
             raise AttributeError(f"Model class {model_class.__name__} does not have a 'parse_response' method.")

        # Assuming parse_response takes the model instance, prompt, system prompt, etc.
        # This might not be the correct signature, but it's a starting point based on the error context.
        # The model_instance is needed to make the actual API call.
        # Let's assume the method is on the model_class but takes the model_instance as an argument.
        # This is getting complicated without documentation. Let's rethink the pydantic_ai usage.

        # Reverting to the original approach of calling a method on model_instance,
        # but need to find the correct method name.
        # Let's try the most generic method name: 'process'.

        # Generate response using PydanticAI
        # Trying a different pattern: calling a method on the model_class itself
        # Common method names might be 'parse_response' or 'from_response'
        # Let's try 'from_response' as a less common but possible pattern.
        if not hasattr(model_class, 'from_response'):
             self.logger.error(f"Model class {model_class.__name__} does not have a 'from_response' method.")
             raise AttributeError(f"Model class {model_class.__name__} does not have a 'from_response' method.")

        # Assuming from_response takes the model instance, prompt, system prompt, etc.
        # This is highly speculative without documentation.
        # Let's assume it takes the model instance and the prompt/system prompt.
        result = model_class.from_response(
            model_instance, # Pass the model instance
            prompt=prompt,
            system=system_prompt,
            # response_model is implicit when calling on the model_class
            temperature=model_config.temperature or 0.1,
            max_tokens=model_config.max_output_tokens
        )

        # Get usage stats from result
        usage_data = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        # Try to extract usage data if available
        # Assuming usage data might be attached to the result object
        if hasattr(result, "_usage") and result._usage:
            usage = result._usage
            usage_data = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        # Alternatively, usage might be returned alongside the result
        # The BaseLLM._call_llm_api signature expects a tuple of (response_text, usage_data_dict)
        # The pydantic_ai library might return the Pydantic model instance directly.
        # If so, we need to return the JSON string of the model instance and extract usage separately if possible.

        # Let's assume the pydantic_ai method returns the Pydantic model instance directly.
        # We need to convert this instance to a JSON string.
        try:
            if hasattr(result, "model_dump"):
                # Pydantic v2
                response_text = result.model_dump_json(indent=2)
                # Check for usage data in the result object itself if not in _usage
                if not usage_data['total_tokens'] and hasattr(result, 'usage') and result.usage:
                     usage_data = {
                         "prompt_tokens": result.usage.prompt_tokens or 0,
                         "completion_tokens": result.usage.completion_tokens or 0,
                         "total_tokens": result.usage.total_tokens or 0
                     }
            else:
                # Pydantic v1
                response_text = result.json(indent=2)
                # Check for usage data in the result object itself if not in _usage
                if not usage_data['total_tokens'] and hasattr(result, 'usage') and result.usage:
                     usage_data = {
                         "prompt_tokens": result.usage.prompt_tokens or 0,
                         "completion_tokens": result.usage.completion_tokens or 0,
                         "total_tokens": result.usage.total_tokens or 0
                     }

            self.logger.debug(f"PydanticAI returned model instance, converted to JSON: {response_text[:500]}...")

        except Exception as e:
            self.logger.error(f"Error converting PydanticAI result to JSON or extracting usage: {str(e)}")
            # Fall back to string representation and zero usage
            response_text = str(result)
            usage_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


        return response_text, usage_data

    def get_response(self, prompt: str, source: str, model_class: Type[BaseModel], model_name: Optional[str] = None, files: Optional[List[str]] = None) -> Tuple[str, UsageData]:
        """Override to handle model_class parameter and files.
           The model_class is now part of the base signature, so this override might only be needed
           if PydanticAIProvider has special handling for it before calling super.
           For now, it just passes it through.
        """
        # The inspect logic to inject model_class into frame_locals for _call_llm_api
        # is no longer needed as model_class is passed through the call chain.
        return super().get_response(prompt, source, model_class, model_name, files=files)
