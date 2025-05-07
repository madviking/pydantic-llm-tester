"""
Tests for the provider factory
"""

import unittest
from unittest.mock import patch
import os
import sys
import json
import tempfile
import shutil

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic_llm_tester.llms import BaseLLM, ProviderConfig, ModelConfig


class MockValidProvider(BaseLLM):
    """Valid mock provider implementation for testing"""
    
    def __init__(self, config=None):
        super().__init__(config)
    
    def _call_llm_api(self, prompt, system_prompt, model_name, model_config):
        """Implement the abstract method"""
        return "Mock response", {"prompt_tokens": 10, "completion_tokens": 20}


class MockInvalidProvider:
    """Invalid provider implementation missing required interface"""
    
    def __init__(self, config=None):
        self.config = config
    
    # Missing _call_llm_api method


class TestProviderFactory(unittest.TestCase):
    """Test the provider factory functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock provider directory
        self.provider_dir = os.path.join(self.temp_dir, "mock_provider")
        os.makedirs(self.provider_dir, exist_ok=True)
        
        # Create an __init__.py file
        with open(os.path.join(self.provider_dir, "__init__.py"), "w") as f:
            f.write("from .provider import MockProvider\n\n__all__ = ['MockProvider']")
        
        # Create a provider.py file
        with open(os.path.join(self.provider_dir, "provider.py"), "w") as f:
            f.write("""
from src.llms.base import BaseLLM

class MockProvider(BaseLLM):
    def __init__(self, config=None):
        super().__init__(config)
    
    def _call_llm_api(self, prompt, system_prompt, model_name, model_config):
        return "Mock response", {"prompt_tokens": 10, "completion_tokens": 20}
""")
        
        # Create an invalid provider directory
        self.invalid_provider_dir = os.path.join(self.temp_dir, "invalid_provider")
        os.makedirs(self.invalid_provider_dir, exist_ok=True)
        
        # Create an __init__.py file for invalid provider
        with open(os.path.join(self.invalid_provider_dir, "__init__.py"), "w") as f:
            f.write("from .provider import InvalidProvider\n\n__all__ = ['InvalidProvider']")
        
        # Create a provider.py file for invalid provider that doesn't implement required methods
        with open(os.path.join(self.invalid_provider_dir, "provider.py"), "w") as f:
            f.write("""
# Note this doesn't inherit from BaseLLM
class InvalidProvider:
    def __init__(self, config=None):
        self.config = config
    
    # Missing _call_llm_api method
""")
        
        # Create a config.json file for invalid provider
        invalid_config = {
            "name": "invalid_provider",
            "provider_type": "invalid",
            "env_key": "INVALID_API_KEY",
            "system_prompt": "You are an invalid provider",
            "llm_models": [
                {
                    "name": "invalid:model1",
                    "default": True,
                    "preferred": False,
                    "cost_input": 0.01,
                    "cost_output": 0.02,
                    "cost_category": "cheap"
                }
            ]
        }
        
        with open(os.path.join(self.invalid_provider_dir, "config.json"), "w") as f:
            json.dump(invalid_config, f, indent=2)
            
        # Create an external module directory
        self.external_dir = os.path.join(self.temp_dir, "external_module")
        os.makedirs(self.external_dir, exist_ok=True)
        
        # Create an __init__.py file for external module
        with open(os.path.join(self.external_dir, "__init__.py"), "w") as f:
            f.write("from .external_provider import ExternalProvider\n\n__all__ = ['ExternalProvider']")
        
        # Create a provider.py file for external provider
        with open(os.path.join(self.external_dir, "external_provider.py"), "w") as f:
            f.write("""
from src.llms.base import BaseLLM

class ExternalProvider(BaseLLM):
    def __init__(self, config=None):
        super().__init__(config)
    
    def _call_llm_api(self, prompt, system_prompt, model_name, model_config):
        return "External response", {"prompt_tokens": 15, "completion_tokens": 25}
""")
        
        # Create a config.json file for external provider
        external_config = {
            "name": "external",
            "provider_type": "external",
            "env_key": "EXTERNAL_API_KEY",
            "system_prompt": "You are an external provider",
            "llm_models": [
                {
                    "name": "external:model1",
                    "default": True,
                    "preferred": False,
                    "cost_input": 0.03,
                    "cost_output": 0.04,
                    "cost_category": "standard"
                }
            ]
        }
        
        with open(os.path.join(self.external_dir, "config.json"), "w") as f:
            json.dump(external_config, f, indent=2)
        
        # Create a config.json file for valid mock provider
        config = {
            "name": "mock_provider",
            "provider_type": "mock",
            "env_key": "MOCK_API_KEY",
            "system_prompt": "You are a mock provider",
            "llm_models": [
                {
                    "name": "mock:model1",
                    "default": True,
                    "preferred": False,
                    "cost_input": 0.01,
                    "cost_output": 0.02,
                    "cost_category": "cheap"
                }
            ]
        }
        
        with open(os.path.join(self.provider_dir, "config.json"), "w") as f:
            json.dump(config, f, indent=2)
        
        # Patch the llms directory
        self.llms_dir_patcher = patch('src.llms.provider_factory.os.path.dirname')
        self.mock_dirname = self.llms_dir_patcher.start()
        self.mock_dirname.return_value = self.temp_dir
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.llms_dir_patcher.stop()
        
        # Clean up temp directory
        shutil.rmtree(self.temp_dir)
    
    def test_load_provider_config(self):
        """Test loading provider configuration"""
        from pydantic_llm_tester.llms import load_provider_config
        
        # Call the function
        config = load_provider_config("mock_provider")


        
        # Check that the config was loaded correctly
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "mock_provider")
        self.assertEqual(config.provider_type, "mock")
        self.assertEqual(config.env_key, "MOCK_API_KEY")
        self.assertEqual(config.system_prompt, "You are a mock provider")
        self.assertEqual(len(config.llm_models), 1)
        self.assertEqual(config.llm_models[0].name, "mock:model1")
        self.assertEqual(config.llm_models[0].default, True)
    
    def test_discover_provider_classes(self):
        """Test discovering provider classes"""
        from pydantic_llm_tester.llms import discover_provider_classes, register_provider_class
        
        # Register a mock provider directly for testing
        register_provider_class("mock_provider", MockValidProvider)
        
        # Call the function
        provider_classes = discover_provider_classes()
        
        # Check that the provider class was discovered
        self.assertIn("mock_provider", provider_classes)
        self.assertEqual(provider_classes["mock_provider"].__name__, "MockValidProvider")
    
    def test_get_available_providers(self):
        """Test getting available providers"""
        from pydantic_llm_tester.llms import get_available_providers, register_provider_class
        
        # Register a mock provider directly for testing
        register_provider_class("mock_provider", MockValidProvider)
        
        # Call the function
        providers = get_available_providers()
        
        # Check that the provider was found
        self.assertIn("mock_provider", providers)
    
    def test_create_provider(self):
        """Test creating a provider instance"""
        from pydantic_llm_tester.llms import create_provider, register_provider_class
        
        # Register a mock provider directly for testing
        register_provider_class("mock_provider", MockValidProvider)
        
        # Patch the load_provider_config function to return a mock config
        with patch('src.llms.provider_factory.load_provider_config') as mock_load_config:
            # Create a mock config
            mock_config = ProviderConfig(
                name="mock_provider",
                provider_type="mock",
                env_key="MOCK_API_KEY",
                system_prompt="You are a mock provider",
                llm_models=[
                    ModelConfig(
                        name="mock:model1",
                        default=True,
                        preferred=False,
                        cost_input=0.01,
                        cost_output=0.02,
                        cost_category="cheap"
                    )
                ]
            )
            mock_load_config.return_value = mock_config
            
            # Call the function
            provider = create_provider("mock_provider")
            
            # Check that the provider was created
            self.assertIsNotNone(provider)
            self.assertEqual(provider.__class__.__name__, "MockValidProvider")
            # In MockValidProvider the name is set from the config
            self.assertEqual(provider.name, "mock_provider")
    
    def test_validate_provider_implementation(self):
        """Test validating a provider implementation"""
        # This test requires the new validate_provider_implementation function
        # that we'll implement in the provider_factory.py
        from pydantic_llm_tester.llms import validate_provider_implementation
        
        # Test with valid provider
        valid_result = validate_provider_implementation(MockValidProvider)
        self.assertTrue(valid_result)
        
        # Test with invalid provider
        invalid_result = validate_provider_implementation(MockInvalidProvider)
        self.assertFalse(invalid_result)
    
    def test_invalid_provider_creation(self):
        """Test creating an invalid provider"""
        # This test expects the create_provider function to check validity
        from pydantic_llm_tester.llms import create_provider
        
        # Try to create an invalid provider
        provider = create_provider("invalid_provider")
        
        # Should return None because it's invalid
        self.assertIsNone(provider)
    
    def test_external_provider_loading(self):
        """Test loading a provider from an external module"""
        # This test requires implementing external module loading support
        
        # Set up the sys.path to include the external directory
        sys.path.insert(0, self.temp_dir)
        
        try:
            # Create an external_providers.json file that points to the external module
            external_providers_path = os.path.join(self.temp_dir, "external_providers.json")
            external_providers_config = {
                "external": {
                    "module": "external_module",
                    "class": "ExternalProvider"
                }
            }
            
            with open(external_providers_path, "w") as f:
                json.dump(external_providers_config, f, indent=2)
            
            # Patch the function that loads external provider configs
            with patch('src.llms.provider_factory.load_external_providers') as mock_load:
                mock_load.return_value = external_providers_config
                
                # Import and test the new register_external_provider function
                from pydantic_llm_tester.llms import register_external_provider, create_provider
                
                # Register the external provider
                success = register_external_provider("external", "external_module", "ExternalProvider")
                self.assertTrue(success)
                
                # Try to create the external provider
                provider = create_provider("external")
                
                # Check that the provider was created correctly
                self.assertIsNotNone(provider)
                self.assertEqual(provider.__class__.__name__, "ExternalProvider")
                self.assertEqual(provider.name, "external")
        finally:
            # Clean up
            sys.path.remove(self.temp_dir)
            
            # Remove external providers file if it exists
            external_providers_path = os.path.join(self.temp_dir, "external_providers.json")
            if os.path.exists(external_providers_path):
                os.remove(external_providers_path)


if __name__ == '__main__':
    unittest.main()
