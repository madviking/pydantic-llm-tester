"""
Manager for LLM provider connections
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

from .cost_manager import UsageData

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


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
        # Import here to avoid circular imports
        from ..llms.llm_registry import get_llm_provider, discover_providers
        
        # Get available providers
        available_providers = discover_providers()
        self.logger.info(f"Available providers: {', '.join(available_providers)}")
        
        for provider in self.providers:
            try:
                # Handle mock providers
                if provider.startswith("mock_"):
                    # Get or create mock provider
                    mock_provider = get_llm_provider("mock")
                    if not mock_provider:
                        self.initialization_errors[provider] = "Mock provider not available"
                        self.logger.warning(f"Mock provider not available for {provider}")
                        continue
                    
                    # Store provider instance with the requested name
                    self.provider_instances[provider] = mock_provider
                    self.logger.info(f"Using mock provider for {provider}")
                    continue
                
                # Get provider from registry
                provider_instance = get_llm_provider(provider)
                if not provider_instance:
                    self.initialization_errors[provider] = f"Provider {provider} not found in registry"
                    self.logger.warning(f"Provider {provider} not found in registry")
                    continue
                
                # Store provider instance
                self.provider_instances[provider] = provider_instance
                self.logger.info(f"Initialized provider: {provider}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider} provider: {str(e)}")
                self.initialization_errors[provider] = str(e)
    
    def get_response(self, provider: str, prompt: str, source: str, model_name: Optional[str] = None) -> Tuple[str, Optional[UsageData]]:
        """
        Get a response from a provider
        
        Args:
            provider: Provider name
            prompt: Prompt text
            source: Source text
            model_name: Optional specific model name to use
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        # Check if this is a mock provider but not properly initialized
        if provider.startswith("mock_") and provider not in self.provider_instances:
            # Import here to avoid circular imports
            from .mock_responses import get_mock_response
            
            self.logger.info(f"Falling back to legacy mock provider for {provider}")
            
            # Create mock usage data
            mock_model = "mock-model"
            # Estimate token count for the mock response
            prompt_tokens = len(prompt.split()) + len(source.split())
            completion_tokens = 500  # Rough estimate for mock responses
            
            # Determine which mock to use based on source content
            if "MACHINE LEARNING ENGINEER" in source or "job" in source.lower() or "software engineer" in source.lower() or "developer" in source.lower():
                mock_response = get_mock_response("job_ads", source)
            else:
                mock_response = get_mock_response("product_descriptions", source)
            
            # Create usage data for mock
            usage_data = UsageData(
                provider=provider,
                model=mock_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            return mock_response, usage_data
        
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
                model_name=model_name
            )
            
            # Log usage info
            self.logger.info(f"{provider} usage: {usage_data.prompt_tokens} prompt tokens, "
                           f"{usage_data.completion_tokens} completion tokens, "
                           f"${usage_data.total_cost:.6f} total cost")
            
            return response_text, usage_data
            
        except Exception as e:
            self.logger.error(f"Error getting response from {provider}: {str(e)}")
            raise
