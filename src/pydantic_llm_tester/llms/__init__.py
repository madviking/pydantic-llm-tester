"""Base modules for LLM providers"""

from .base import BaseLLM, ProviderConfig, ModelConfig
from .llm_registry import get_llm_provider, get_available_providers, discover_providers, reset_provider_cache, get_provider_info
from .provider_factory import create_provider, reset_caches, register_provider_class, discover_provider_classes, register_external_provider, load_provider_config, validate_provider_implementation
from .mock.provider import MockProvider

# Import provider modules to ensure they're available
try:
    from . import anthropic
    from . import openai
    from . import mistral
    from . import google
    from . import mock
    from . import pydantic_ai
except ImportError as e:
    # Log but don't fail if a provider module is missing
    import logging
    logging.getLogger(__name__).warning(f"Some provider modules couldn't be imported: {e}")

# Reset caches on import to ensure all providers are discovered
reset_caches()
reset_provider_cache()

__all__ = [
    'BaseLLM',
    'ProviderConfig',
    'ModelConfig',
    'get_llm_provider',
    'get_available_providers',
    'discover_providers',
    'create_provider',
    'reset_provider_cache',
    'reset_caches',
    'MockProvider',
    'register_provider_class',
    'discover_provider_classes',
    'register_external_provider',
    'load_provider_config',
    'validate_provider_implementation',
    'get_provider_info'
]
