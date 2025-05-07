"""
Tests for the provider factory
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import tempfile
import shutil
import inspect
import importlib.util
from typing import List, Optional # Import List and Optional

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic_llm_tester.llms import BaseLLM, ProviderConfig, ModelConfig
from pydantic_llm_tester.llms.provider_factory import discover_provider_classes, register_provider_class, validate_provider_implementation, create_provider, load_provider_config, load_external_providers, register_external_provider, reset_caches # Import functions directly for testing


class MockValidProvider(BaseLLM):
    """Valid mock provider implementation for testing"""
    
    def __init__(self, config=None, llm_models: Optional[List[str]] = None): # Accept llm_models
        super().__init__(config)
        self.llm_models = llm_models # Store llm_models
    
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
from src.pydantic_llm_tester.llms.base import BaseLLM

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
        self.llms_dir_patcher = patch('src.pydantic_llm_tester.llms.provider_factory.os.path.dirname')
        self.mock_dirname = self.llms_dir_patcher.start()
        self.mock_dirname.return_value = self.temp_dir
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.llms_dir_patcher.stop()
        
        # Clean up temp directory
        shutil.rmtree(self.temp_dir)
    
    def test_load_provider_config(self):
        """Test loading provider configuration"""
        # Use the actual load_provider_config function
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
        # Create mock module objects
        mock_valid_module = MagicMock()
        mock_valid_module.MockProvider = MockValidProvider
        mock_valid_module.__all__ = ['MockProvider']

        mock_invalid_module = MagicMock()
        mock_invalid_module.InvalidProvider = MockInvalidProvider
        mock_invalid_module.__all__ = ['InvalidProvider']

        # Patch os.listdir and importlib.import_module
        with patch('src.pydantic_llm_tester.llms.provider_factory.os.listdir', return_value=['mock_provider', 'invalid_provider', '__pycache__']), \
             patch('src.pydantic_llm_tester.llms.provider_factory.os.path.isdir', side_effect=lambda x: not x.endswith('__pycache__')), \
             patch('src.pydantic_llm_tester.llms.provider_factory.os.path.exists', return_value=True), \
             patch('src.pydantic_llm_tester.llms.provider_factory.importlib.import_module', side_effect=lambda name: mock_valid_module if 'mock_provider' in name else mock_invalid_module):

            # Call the function
            provider_classes = discover_provider_classes()

            # Check that the valid provider class was discovered and the invalid one was not
            self.assertIn("mock_provider", provider_classes)
            self.assertEqual(provider_classes["mock_provider"], MockValidProvider)
            self.assertNotIn("invalid_provider", provider_classes)

    def test_get_available_providers(self):
        """Test getting available providers"""
        # Mock discover_provider_classes and load_external_providers
        mock_discovered_classes = {"mock_provider": MockValidProvider}
        mock_external_providers = {"external": {"module": "external_module", "class": "ExternalProvider"}}

        with patch('src.pydantic_llm_tester.llms.provider_factory.discover_provider_classes', return_value=mock_discovered_classes), \
             patch('src.pydantic_llm_tester.llms.provider_factory.load_external_providers', return_value=mock_external_providers), \
             patch('src.pydantic_llm_tester.llms.provider_factory._load_enabled_providers', return_value=None): # Assume all enabled

            # Call the function
            providers = get_available_providers()

            # Check that both internal and external providers are returned
            self.assertEqual(set(providers), {"mock_provider", "external"})

    def test_create_provider(self):
        """Test creating a provider instance"""
        # Mock discover_provider_classes and load_provider_config
        mock_discovered_classes = {"mock_provider": MockValidProvider}
        mock_config = ProviderConfig(name="mock_provider", provider_type="mock", env_key="MOCK_API_KEY", system_prompt="Mock", llm_models=[])

        with patch('src.pydantic_llm_tester.llms.provider_factory.discover_provider_classes', return_value=mock_discovered_classes), \
             patch('src.pydantic_llm_tester.llms.provider_factory.load_provider_config', return_value=mock_config), \
             patch('src.pydantic_llm_tester.llms.provider_factory.validate_provider_implementation', return_value=True): # Assume validation passes

            # Call the function
            provider = create_provider("mock_provider")

            # Check that the provider was created
            self.assertIsNotNone(provider)
            self.assertIsInstance(provider, MockValidProvider)
            self.assertEqual(provider.name, "mock_provider") # Check name set by BaseLLM __init__

    def test_validate_provider_implementation(self):
        """Test validating a provider implementation"""
        # Use the actual validate_provider_implementation function

        # Test with valid provider
        valid_result = validate_provider_implementation(MockValidProvider)
        self.assertTrue(valid_result)

        # Test with invalid provider
        invalid_result = validate_provider_implementation(MockInvalidProvider)
        self.assertFalse(invalid_result)

    def test_invalid_provider_creation(self):
        """Test creating an invalid provider"""
        # Mock discover_provider_classes to return an invalid provider
        mock_discovered_classes = {"invalid_provider": MockInvalidProvider}

        with patch('src.pydantic_llm_tester.llms.provider_factory.discover_provider_classes', return_value=mock_discovered_classes), \
             patch('src.pydantic_llm_tester.llms.provider_factory.validate_provider_implementation', return_value=False): # Ensure validation fails

            # Try to create an invalid provider
            provider = create_provider("invalid_provider")

            # Should return None because it's invalid
            self.assertIsNone(provider)

    def test_external_provider_loading(self):
        """Test loading a provider from an external module"""
        # Create a mock external module
        mock_external_module = MagicMock()
        mock_external_module.ExternalProvider = MockValidProvider # Use MockValidProvider for simplicity

        # Mock load_external_providers and importlib.import_module
        mock_external_providers_config = {
            "external": {
                "module": "external_module",
                "class": "ExternalProvider",
                "config_path": "/fake/config.json" # Add a fake config path
            }
        }
        mock_config_data = {"name": "external", "provider_type": "external", "env_key": "EXTERNAL_API_KEY", "system_prompt": "External", "llm_models": []}
        mock_config = ProviderConfig(**mock_config_data)


        with patch('src.pydantic_llm_tester.llms.provider_factory.load_external_providers', return_value=mock_external_providers_config), \
             patch('src.pydantic_llm_tester.llms.provider_factory.importlib.import_module', return_value=mock_external_module), \
             patch('src.pydantic_llm_tester.llms.provider_factory.validate_provider_implementation', return_value=True), \
             patch('src.pydantic_llm_tester.llms.provider_factory.os.path.exists', return_value=True), \
             patch('src.pydantic_llm_tester.llms.provider_factory.json.load', return_value=mock_config_data): # Mock json.load to return config data

            # Try to create the external provider
            provider = create_provider("external")

            # Check that the provider was created correctly
            self.assertIsNotNone(provider)
            self.assertIsInstance(provider, MockValidProvider) # Check against MockValidProvider
            self.assertEqual(provider.name, "external") # Check name set by BaseLLM __init__


if __name__ == '__main__':
    unittest.main()
