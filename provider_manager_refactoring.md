# ProviderManager Refactoring Implementation Guide

This document provides a detailed implementation plan for refactoring the `ProviderManager` class to fully utilize the pluggable LLM system in the `llms/` directory.

## Current Issues

The current `ProviderManager` implementation has several issues:

1. Provider-specific code is duplicated in multiple methods (`_get_openai_response`, `_get_anthropic_response`, etc.)
2. Adding a new provider requires modifying this class in multiple places
3. The same API client creation logic exists here and in the provider classes in `llms/`
4. There's a parallel code path for mocked providers that's handled differently

## Refactoring Strategy

The refactored `ProviderManager` will:

1. Utilize the LLM registry system to load providers
2. Delegate all API interactions to the provider instances
3. Standardize the interface for all providers, including mocks
4. Remove all provider-specific code

## Implementation Details

### Updated Class Structure

```python
class ProviderManager:
    """
    Manages LLM provider interfaces using the pluggable LLM system
    """
    
    def __init__(self, providers: List[str]):
        """
        Initialize the provider manager with specified providers
        
        Args:
            providers: List of provider names to initialize
        """
        self.providers = providers
        self.logger = logging.getLogger(__name__)
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize provider instances from the LLM registry"""
        self.provider_instances = {}
        self.initialization_errors = {}
        
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
```

### Migration Steps

1. Create the new implementation as shown above
2. Update imports to include the LLM registry
3. Test with various providers to ensure it works correctly
4. Remove the old provider-specific methods
5. Update any code that directly used those methods

## Testing Strategy

1. Unit test with mock LLM providers to verify correct delegation
2. Test with real providers using small prompts
3. Test with mock providers to ensure they still work
4. Test error handling with invalid provider names
5. Verify usage tracking still works correctly

## Integration Points

- The `LLMTester` class interfaces with `ProviderManager` directly
- The CLI uses `ProviderManager` indirectly through `LLMTester`
- The runner and UI interact with `ProviderManager` through wrappers

All of these should continue to work without modification once the refactoring is complete, as the external interface of `ProviderManager` remains unchanged.