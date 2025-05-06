"""Base modules for LLM providers"""

from .base import BaseLLM, ProviderConfig, ModelConfig
from .llm_registry import get_llm_provider, get_available_providers, discover_providers, reset_provider_cache
from .provider_factory import create_provider, reset_caches

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
    'reset_caches'
]