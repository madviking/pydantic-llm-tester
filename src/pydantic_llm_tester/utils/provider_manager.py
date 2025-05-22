"""
Manager for LLM provider connections
"""

import logging
from typing import List, Optional, Tuple, Type # Added Type
from pydantic import BaseModel # Added BaseModel for type hint
from pathlib import Path
from dotenv import load_dotenv

from .common import get_default_dotenv_path
from .cost_manager import UsageData
from pydantic_llm_tester.llms.llm_registry import LLMRegistry # Import LLMRegistry
from pydantic_llm_tester.llms.provider_factory import create_provider # Import create_provider

# Load environment variables from .env file
load_dotenv(dotenv_path=get_default_dotenv_path())


class ProviderManager:
    """
    Manages connections to LLM providers using the pluggable LLM system
    """

    def __init__(self, providers: List[str], llm_models: Optional[List[str]] = None):
        """
        Initialize the provider manager

        Args:
            providers: List of provider names to initialize
            llm_models: Optional list of specific LLM model names to test
        """
        self.providers = providers
        self.llm_models = llm_models # Store the list of desired LLM models
        self.logger = logging.getLogger(__name__)
        self.provider_instances = {}
        self.initialization_errors = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize provider instances from the LLM registry"""
        registry = LLMRegistry() # Get the singleton registry instance

        # Get available providers (filtered by enabled status in ConfigManager)
        # Use discover_providers from the LLMRegistry instance
        available_providers = registry.discover_providers()
        self.logger.info(f"Available providers: {', '.join(available_providers)}")

        for provider_name in self.providers:
            # Check if the provider is in the list of available providers (enabled in config)
            if provider_name not in available_providers:
                 self.initialization_errors[provider_name] = f"Provider {provider_name} is not enabled in the configuration."
                 self.logger.warning(f"Skipping initialization for disabled provider: {provider_name}")
                 continue

            try:
                # Get models for the provider from the registry
                models = registry.get_provider_models(provider_name)

                # Handle mock providers - they might not have models in the registry initially
                if provider_name == "mock" and not models:
                     # Create a default mock model if none exist in the registry
                     from pydantic_llm_tester.llms.base import ModelConfig
                     models = {
                         "mock:default": ModelConfig(
                             name="mock:default",
                             provider="mock",
                             default=True,
                             preferred=False,
                             enabled=True,
                             cost_input=0.0,
                             cost_output=0.0,
                             cost_category="free",
                             max_input_tokens=4096,
                             max_output_tokens=4096
                         )
                     }
                     # Store this default mock model in the registry for consistency
                     registry.store_provider_models("mock", models)
                     self.logger.debug("Created default mock model and stored in registry.")


                if not models:
                    self.initialization_errors[provider_name] = f"No models found in registry for provider {provider_name}."
                    self.logger.warning(f"No models found in registry for provider {provider_name}. Skipping initialization.")
                    continue

                # Filter models based on the llm_models list provided during initialization
                filtered_models = models.values()
                if self.llm_models is not None:
                    filtered_models = [model for model in models.values() if model.name in self.llm_models]
                    if not filtered_models:
                         self.initialization_errors[provider_name] = f"No specified models {self.llm_models} found for provider {provider_name}."
                         self.logger.warning(f"No specified models {self.llm_models} found for provider {provider_name}. Skipping initialization.")
                         continue
                    self.logger.debug(f"Filtered models for {provider_name} based on filter {self.llm_models}: {[m.name for m in filtered_models]}")


                # Get provider instance from registry (which uses create_provider internally)
                # Pass the filtered list of ModelConfig objects to get_llm_provider
                provider_instance = registry.get_llm_provider(provider_name, llm_models=list(filtered_models))

                if not provider_instance:
                    self.initialization_errors[provider_name] = f"Failed to create provider instance for {provider_name}."
                    self.logger.warning(f"Failed to create provider instance for {provider_name}.")
                    continue

                # Store provider instance
                self.provider_instances[provider_name] = provider_instance
                self.logger.info(f"Initialized provider: {provider_name}")

            except Exception as e:
                self.logger.error(f"Failed to initialize {provider_name} provider: {str(e)}")
                self.initialization_errors[provider_name] = str(e)

    def get_response(self, provider: str, prompt: str, source: str, model_class: Type[BaseModel], model_name: Optional[str] = None, files: Optional[List[str]] = None) -> Tuple[str, Optional[UsageData]]:
        """
        Get a response from a provider

        Args:
            provider: Provider name
            prompt: Prompt text
            source: Source text
            model_class: The Pydantic model class for schema guidance.
            model_name: Optional specific model name to use
            files: Optional list of file paths to upload

        Returns:
            Tuple of (response_text, usage_data)
        """
        # Check if the provider is initialized
        if provider not in self.provider_instances:
            # Check if we have a specific initialization error for this provider
            if provider in self.initialization_errors:
                error_msg = self.initialization_errors[provider]
                raise ValueError(f"Provider {provider} not initialized: {error_msg}")
            else:
                raise ValueError(f"Provider {provider} not initialized")

        # Get provider instance
        provider_instance = self.provider_instances[provider]

        # Get response from provider
        try:
            response_text, usage_data = provider_instance.get_response(
                prompt=prompt,
                source=source,
                model_class=model_class, # Pass model_class
                model_name=model_name,
                files=files
            )

            # Log usage info
            if usage_data:
                self.logger.info(f"{provider} usage: {usage_data.prompt_tokens} prompt tokens, "
                               f"{usage_data.completion_tokens} completion tokens, "
                               f"${usage_data.total_cost:.6f} total cost")

            return response_text, usage_data

        except Exception as e:
            self.logger.error(f"Error getting response from {provider}: {str(e)}")
            raise
