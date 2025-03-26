#!/usr/bin/env python3
"""
Script to verify LLM provider setup and configuration
"""

import os
import sys
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_providers")

def main():
    """Main verification function"""
    print("LLM Tester Provider Verification")
    print("================================\n")
    
    # Ensure provider caches are reset
    try:
        from llm_tester.llms.provider_factory import reset_caches
        from llm_tester.llms.llm_registry import reset_provider_cache
        
        reset_caches()
        reset_provider_cache()
        print("✓ Reset provider caches successfully\n")
    except ImportError as e:
        print(f"❌ Error importing provider modules: {e}")
        return False
    
    # Discover available providers
    try:
        from llm_tester.llms.llm_registry import discover_providers
        providers = discover_providers()
        
        if providers:
            print(f"✓ Discovered {len(providers)} providers: {', '.join(providers)}\n")
        else:
            print("❌ No providers discovered\n")
            return False
    except Exception as e:
        print(f"❌ Error discovering providers: {e}")
        return False
    
    # Check each provider's configuration
    try:
        from llm_tester.llms.llm_registry import get_provider_info
        
        print("Provider Configurations:")
        print("-----------------------")
        
        for provider_name in providers:
            provider_info = get_provider_info(provider_name)
            
            if not provider_info.get('available', False):
                print(f"❌ {provider_name}: Not available")
                continue
                
            # Check if configuration is loaded
            if provider_info.get('config') is None:
                print(f"⚠️ {provider_name}: Available but missing configuration")
                continue
                
            # Check for API key
            env_key = provider_info.get('config', {}).get('env_key', '')
            has_api_key = bool(os.environ.get(env_key, ''))
            
            # Get model count
            models = provider_info.get('models', [])
            
            if has_api_key:
                print(f"✓ {provider_name}: Configured with {len(models)} models and API key")
            else:
                print(f"⚠️ {provider_name}: Configured with {len(models)} models but missing API key ({env_key})")
                
            # List models
            for model in models:
                default_marker = " (default)" if model.get('default', False) else ""
                preferred_marker = " (preferred)" if model.get('preferred', False) else ""
                print(f"  - {model.get('name')}{default_marker}{preferred_marker}")
                
            print("")
            
        print("\nProvider verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying providers: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)