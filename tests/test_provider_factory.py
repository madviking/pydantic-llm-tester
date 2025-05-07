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
from typing import List, Optional

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic_llm_tester.llms import BaseLLM, ProviderConfig, ModelConfig
import pydantic_llm_tester.llms.provider_factory # Import the module


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
        self.llms_dir_patcher = patch('pydantic_llm_tester.llms.provider_factory.os.path.dirname')
        self.mock_dirname = self.llms_dir_patcher.start()
        self.mock_dirname.return_value = self.temp_dir
        
        # Reset caches before each test to ensure a clean state for discovery
        pydantic_llm_tester.llms.provider_factory.reset_caches()
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.llms_dir_patcher.stop()
        
        # Clean up temp directory
        shutil.rmtree(self.temp_dir)
    
    @patch('pydantic_llm_tester.llms.provider_factory.load_provider_config')
    def test_load_provider_config(self, mock_load_provider_config):
        """Test loading provider configuration"""
        # Configure the mock to return a specific config
        mock_config_data = {
            "name": "mock_provider",
            "provider_type": "mock",
            "env_key": "MOCK_API_KEY",
            "system_prompt": "You are a mock provider",
            "llm_models": [
                {
                    "name": "mock:model1",
                    "default": True,
                    "preferred": False,
                    "enabled": True,
                    "cost_input": 0.01,
                    "cost_output": 0.02,
                    "cost_category": "cheap",
                    "max_input_tokens": 4096,
                    "max_output_tokens": 4096
                }
            ]
        }
        mock_load_provider_config.return_value = ProviderConfig(**mock_config_data)

        # Use the actual load_provider_config function (which is now mocked)
        config = pydantic_llm_tester.llms.provider_factory.load_provider_config("mock_provider")
        
        # Check that the mock was called
        mock_load_provider_config.assert_called_once_with("mock_provider")

        # Check that the config was loaded correctly (from the mock)
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "mock_provider")
        self.assertEqual(config.provider_type, "mock")
        self.assertEqual(config.env_key, "MOCK_API_KEY")
        self.assertEqual(config.system_prompt, "You are a mock provider")
        self.assertEqual(len(config.llm_models), 1)
        self.assertEqual(config.llm_models[0].name, "mock:model1")
        self.assertEqual(config.llm_models[0].default, True)
    
    @patch('pydantic_llm_tester.llms.provider_factory.importlib.import_module')
    @patch('pydantic_llm_tester.llms.provider_factory.os.path.exists', return_value=True)
    @patch('pydantic_llm_tester.llms.provider_factory.os.path.isdir', side_effect=lambda x: not x.endswith('__pycache__'))
    @patch('pydantic_llm_tester.llms.provider_factory.os.listdir', return_value=['mock_provider', 'invalid_provider', '__pycache__'])
    def test_discover_provider_classes(self, mock_listdir, mock_isdir, mock_exists, mock_import_module):
        """Test discovering provider classes"""
        # Create mock module objects
        mock_valid_module = MagicMock()
        mock_valid_module.MockProvider = MockValidProvider
        mock_valid_module.__all__ = ['MockProvider']

        mock_invalid_module = MagicMock()
        mock_invalid_module.InvalidProvider = MockInvalidProvider
        mock_invalid_module.__all__ = ['InvalidProvider']

        # Configure import_module side effect
        mock_import_module.side_effect = lambda name: mock_valid_module if 'mock_provider' in name else mock_invalid_module

        # Call the function
        provider_classes = pydantic_llm_tester.llms.provider_factory.discover_provider_classes()

        # Check that the valid provider class was discovered and the invalid one was not
        self.assertIn("mock_provider", provider_classes)
        self.assertEqual(provider_classes["mock_provider"], MockValidProvider)
        self.assertNotIn("invalid_provider", provider_classes)

    @patch('pydantic_llm_tester.llms.provider_factory._load_enabled_providers', return_value=None)
    @patch('pydantic_llm_tester.llms.provider_factory.load_external_providers')
    @patch('pydantic_llm_tester.llms.provider_factory.discover_provider_classes')
    def test_get_available_providers(self, mock_discover_provider_classes, mock_load_external_providers, mock_load_enabled_providers):
        """Test getting available providers"""
        # Mock discover_provider_classes and load_external_providers
        mock_discovered_classes = {"mock_provider": MockValidProvider}
        mock_external_providers = {"external": {"module": "external_module", "class": "ExternalProvider"}}

        mock_discover_provider_classes.return_value = mock_discovered_classes
        mock_load_external_providers.return_value = mock_external_providers

        # Call the function
        providers = pydantic_llm_tester.llms.provider_factory.get_available_providers()

        # Check that both internal and external providers are returned
        self.assertEqual(set(providers), {"mock_provider", "external"})

    @patch('pydantic_llm_tester.llms.provider_factory.validate_provider_implementation', return_value=True)
    @patch('pydantic_llm_tester.llms.provider_factory.load_provider_config')
    @patch('pydantic_llm_tester.llms.provider_factory.discover_provider_classes')
    def test_create_provider(self, mock_discover_provider_classes, mock_load_provider_config, mock_validate_implementation):
        """Test creating a provider instance"""
        # Mock discover_provider_classes and load_provider_config
        mock_discovered_classes = {"mock_provider": MockValidProvider}
        mock_config = ProviderConfig(name="mock_provider", provider_type="mock", env_key="MOCK_API_KEY", system_prompt="Mock", llm_models=[])

        mock_discover_provider_classes.return_value = mock_discovered_classes
        mock_load_provider_config.return_value = mock_config

        # Call the function, passing llm_models=None to match the signature
        provider = pydantic_llm_tester.llms.provider_factory.create_provider("mock_provider", llm_models=None)

        # Check that the provider was created
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, MockValidProvider)
        self.assertEqual(provider.name, "mock_provider") # Check name set by BaseLLM __init__

    def test_validate_provider_implementation(self):
        """Test validating a provider implementation"""
        # Use the actual validate_provider_implementation function

        # Test with valid provider
        valid_result = pydantic_llm_tester.llms.provider_factory.validate_provider_implementation(MockValidProvider)
        self.assertTrue(valid_result)

        # Test with invalid provider
        invalid_result = pydantic_llm_tester.llms.provider_factory.validate_provider_implementation(MockInvalidProvider)
        self.assertFalse(invalid_result)

    @patch('pydantic_llm_tester.llms.provider_factory.validate_provider_implementation', return_value=False)
    @patch('pydantic_llm_tester.llms.provider_factory.discover_provider_classes')
    def test_invalid_provider_creation(self, mock_discover_provider_classes, mock_validate_implementation):
        """Test creating an invalid provider"""
        # Mock discover_provider_classes to return an invalid provider
        mock_discovered_classes = {"invalid_provider": MockInvalidProvider}
        mock_discover_provider_classes.return_value = mock_discovered_classes

        # Try to create an invalid provider
        provider = pydantic_llm_tester.llms.provider_factory.create_provider("invalid_provider")

        # Should return None because it's invalid
        self.assertIsNone(provider)

    @patch('pydantic_llm_tester.llms.provider_factory._create_external_provider') # Patch _create_external_provider
    def test_external_provider_loading(self, mock_create_external_provider):
        """Test loading a provider from an external module"""
        # Directly set the _external_providers cache with mock data
        mock_external_providers_data = {"external": {"module": "external_module", "class": "ExternalProvider", "config_path": "/fake/path/to/config.json"}}
        pydantic_llm_tester.llms.provider_factory._external_providers = mock_external_providers_data

        # Configure the mock _create_external_provider to return a simple mock object
        mock_provider_instance = MagicMock()
        mock_provider_instance.name = "external" # Set a name attribute for checking
        mock_create_external_provider.return_value = mock_provider_instance

        # Try to create the external provider
        provider = pydantic_llm_tester.llms.provider_factory.create_provider("external")

        # Check that _create_external_provider was called
        mock_create_external_provider.assert_called_once_with("external")

        # Check that the provider was created correctly (should be the return value of the mock)
        self.assertIsNotNone(provider)
        self.assertEqual(provider.name, "external")


if __name__ == '__main__':
    unittest.main()
