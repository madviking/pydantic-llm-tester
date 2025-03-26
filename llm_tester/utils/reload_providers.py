"""
Utility to manually force provider reloading and discovery
"""

import logging
import sys
import os

# Setup basic logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def reload_providers():
    """
    Force reload and discovery of all providers
    """
    logger.info("Reloading all LLM providers...")
    
    # Import and reset caches in provider_factory and llm_registry
    try:
        from ..llms.provider_factory import reset_caches
        from ..llms.llm_registry import reset_provider_cache
        
        # Reset all caches
        reset_caches()
        reset_provider_cache()
        
        logger.info("Provider caches reset")
        
        # Import all provider modules to ensure they're loaded
        try:
            from ..llms import anthropic
            from ..llms import openai
            from ..llms import mistral
            from ..llms import google
            from ..llms import mock
            from ..llms import pydantic_ai
            
            # Get available providers
            from ..llms.llm_registry import discover_providers
            providers = discover_providers()
            
            logger.info(f"Successfully discovered providers: {', '.join(providers)}")
            return True
            
        except ImportError as e:
            logger.warning(f"Some provider modules could not be imported: {e}")
            
    except ImportError as e:
        logger.error(f"Error importing provider modules: {e}")
        return False

    return True

if __name__ == "__main__":
    # Allow directly running this script to reload providers
    success = reload_providers()
    
    # Get available providers after reload
    try:
        from ..llms.llm_registry import discover_providers
        providers = discover_providers()
        logger.info(f"Available providers: {', '.join(providers)}")
    except:
        logger.error("Could not list available providers")
    
    sys.exit(0 if success else 1)