# Provider System Architecture

This document describes the architecture of the LLM provider system in the LLM Tester framework.

## Overview

The provider system is responsible for:
- Managing communication with LLM providers
- Handling authentication and API keys
- Standardizing prompts and responses
- Tracking token usage and costs

## Key Components

### Base Provider Class

`BaseLLM` (`llm_tester/llms/base.py`): Defines the interface that all providers must implement:

```python
class BaseLLM(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config=None):
        """Initialize provider with optional config"""
        
    def get_response(self, prompt: str, source: str, model_name: Optional[str] = None) -> Tuple[str, UsageData]:
        """Get response from LLM for the given prompt and source"""
        
    @abstractmethod
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the LLM"""
        
    def get_default_model(self) -> Optional[str]:
        """Get the default model name for this provider"""
        
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable"""
        
    def get_model_config(self, model_name: Optional[str] = None) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
```

### Provider Factory

`provider_factory.py`: Creates provider instances based on name:

```python
def create_provider(provider_name: str) -> Optional[BaseLLM]:
    """Create a provider instance by name"""
```

Key functions:
- `discover_provider_classes()`: Discovers available provider classes
- `load_provider_config()`: Loads provider configuration
- `validate_provider_implementation()`: Validates provider implementations

### Provider Registry

`llm_registry.py`: Manages provider instances:

```python
def get_llm_provider(provider_name: str) -> Optional[BaseLLM]:
    """Get an LLM provider instance by name, creating it if needed"""
    
def discover_providers() -> List[str]:
    """Discover all available LLM providers"""
    
def reset_provider_cache() -> None:
    """Reset the provider instance cache"""
```

### Provider Manager

`provider_manager.py`: High-level manager for provider interactions:

```python
class ProviderManager:
    """Manages connections to LLM providers"""
    
    def __init__(self, providers: List[str]):
        """Initialize with list of provider names"""
        
    def get_response(self, provider: str, prompt: str, source: str, model_name: Optional[str] = None) -> Tuple[str, Optional[UsageData]]:
        """Get a response from a provider"""
```

## Configuration System

Provider configuration consists of:

1. **Global Configuration** (`config.json`): 
   - Which providers are enabled
   - Default models for each provider

2. **Provider Configuration** (`llm_tester/llms/provider_name/config.json`):
   - Provider-specific information
   - Available models and their configurations

3. **Environment Variables**:
   - API keys and credentials

## Provider Types

The system supports several types of providers:

1. **Native Providers**: Direct integration with LLM APIs
   - OpenAI
   - Anthropic
   - Mistral
   - Google

2. **Abstraction Layer Providers**:
   - PydanticAI: Uses PydanticAI for extraction

3. **Mock Providers**:
   - Mock: Simulates responses for testing

## Provider Development

Developing a new provider involves:

1. Creating a new directory in `llm_tester/llms/`
2. Implementing a provider class that inherits from `BaseLLM`
3. Creating a provider configuration file

The provider must implement the `_call_llm_api` method, which handles the actual API call.

## Provider Architecture Flow

The flow for a provider request:

1. `LLMTester` calls `provider_manager.get_response()`
2. `ProviderManager` looks up the provider instance in its cache
3. If not found, it requests a new instance from `llm_registry.get_llm_provider()`
4. `llm_registry` checks its cache for an existing instance
5. If not found, it calls `provider_factory.create_provider()`
6. `provider_factory` creates a new provider instance
7. The provider's `get_response()` method is called
8. The provider handles authentication and API communication
9. The response is returned to the caller

## Provider Integration Strategies

The framework supports different integration strategies:

1. **Provider SDK Integration**: Using the provider's official SDK
2. **Direct API Integration**: Making HTTP requests directly
3. **PydanticAI Integration**: Using PydanticAI's abstraction layer

## Error Handling

Provider errors are handled at multiple levels:

1. **Provider Level**: The provider handles API-specific errors
2. **Provider Manager Level**: The manager handles provider initialization errors
3. **LLM Tester Level**: The tester handles general provider errors

## Cost Management

Provider costs are tracked using the `cost_manager`:

1. `UsageData` objects track token usage
2. Costs are calculated based on model pricing information
3. Reports are generated for cost analysis

## External Provider Support

The system supports loading providers from external modules:

1. External providers are defined in `external_providers.json`
2. The factory loads and initializes these providers
3. External providers must still implement the `BaseLLM` interface