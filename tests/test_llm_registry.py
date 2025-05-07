import unittest
from unittest.mock import patch
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic_llm_tester.llms import BaseLLM, ProviderConfig


class MockProvider(BaseLLM):
    """Mock provider for testing the registry"""
    
    def __init__(self, config=None):
        super().__init__(config)
    
    def _call_llm_api(self, prompt, system_prompt, model_name, model_config):
        """Implement the abstract method"""
        return "Mock response", {"prompt_tokens": 10, "completion_tokens": 20}


class TestLLMRegistry(unittest.TestCase):
    """Test the LLM registry functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # We need to patch module imports at the location they're used
        self.factory_patcher = patch('pydantic_llm_tester.llms.llm_registry.get_available_providers')
        self.mock_get_available_providers = self.factory_patcher.start()
        self.mock_get_available_providers.return_value = ["test_provider", "another_provider"]
        
        # Patch create_provider separately
        self.create_provider_patcher = patch('pydantic_llm_tester.llms.llm_registry.create_provider')
        self.mock_create_provider = self.create_provider_patcher.start()
        
        # Create a mock provider instance
        self.test_provider = MockProvider()
        self.another_provider = MockProvider()
        
        # Configure create_provider to return the mock instance
        def create_provider_side_effect(provider_name, llm_models=None): # Added llm_models
            if provider_name == "test_provider":
                return self.test_provider
            elif provider_name == "another_provider":
                return self.another_provider
            return None
        
        self.mock_create_provider.side_effect = create_provider_side_effect
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.factory_patcher.stop()
        self.create_provider_patcher.stop()
        
        # Reset the provider cache to ensure clean tests
        from pydantic_llm_tester.llms import reset_provider_cache
        reset_provider_cache()
    
    def test_discover_providers(self):
        """Test discovering available providers"""
        from pydantic_llm_tester.llms import discover_providers
        
        # Configure get_available_providers to return our test providers
        self.mock_get_available_providers.return_value = ["test_provider", "another_provider"]
        
        # Call discover_providers
        providers = discover_providers()
        
        # Check that get_available_providers was called
        self.mock_get_available_providers.assert_called_once()
        
        # Check that the correct providers were returned
        self.assertEqual(set(providers), {"test_provider", "another_provider"})
    
    def test_get_llm_provider(self):
        """Test getting a provider instance"""
        from pydantic_llm_tester.llms import get_llm_provider
        
        # Call get_llm_provider
        provider = get_llm_provider("test_provider")
        
        # Check that create_provider was called
        self.mock_create_provider.assert_called_once_with("test_provider", llm_models=None)
        
        # Check that the correct provider was returned
        self.assertEqual(provider, self.test_provider)
    
    def test_get_llm_provider_caching(self):
        """Test that provider instances are cached"""
        from pydantic_llm_tester.llms import get_llm_provider
        
        # Call get_llm_provider twice for the same provider
        provider1 = get_llm_provider("test_provider")
        provider2 = get_llm_provider("test_provider")
        
        # Check that create_provider was called only once
        self.mock_create_provider.assert_called_once_with("test_provider", llm_models=None)
        
        # Check that the same instance was returned both times
        self.assertIs(provider1, provider2)
    
    def test_reset_provider_cache(self):
        """Test resetting the provider cache"""
        from pydantic_llm_tester.llms import get_llm_provider, reset_provider_cache
        
        # Create two different provider instances for the test
        provider_instance1 = MockProvider()
        provider_instance2 = MockProvider()
        
        # Setup the mock to return different instances after reset_provider_cache is called
        self.mock_create_provider.side_effect = [provider_instance1, provider_instance2]
        
        # Call get_llm_provider to cache the first provider
        provider1 = get_llm_provider("test_provider") # This will be called with llm_models=None
        
        # Reset the cache
        reset_provider_cache()
        
        # Call get_llm_provider again to get the second instance
        provider2 = get_llm_provider("test_provider") # This will also be called with llm_models=None
        
        # Check that create_provider was called twice
        self.assertEqual(self.mock_create_provider.call_count, 2)
        # Check the calls were as expected
        self.mock_create_provider.assert_any_call("test_provider", llm_models=None)
        
        # Check that different instances were returned
        self.assertIsNot(provider1, provider2)
    
    def test_get_provider_info(self):
        """Test getting provider information"""
        from pydantic_llm_tester.llms import get_provider_info

        # Create a config for the test provider
        config = ProviderConfig(
            name="test_provider",
            provider_type="test",
            env_key="TEST_API_KEY",
            llm_models=[
                {
                    "name": "test:model1",
                    "default": True,
                    "preferred": False,
                    "cost_input": 0.0,
                    "cost_output": 0.0,
                    "cost_category": "test"
                }
            ]
        )
        
        # Set the config on the test provider
        self.test_provider.config = config
        
        # Get the provider info
        info = get_provider_info("test_provider")
        
        # Check that the correct info was returned
        self.assertEqual(info["name"], "test_provider")
        self.assertEqual(info["available"], True)
        self.assertEqual(info["config"]["provider_type"], "test")
        self.assertEqual(info["config"]["env_key"], "TEST_API_KEY")
        self.assertEqual(len(info["py_models"]), 1)
        self.assertEqual(info["py_models"][0]["name"], "test:model1")
        self.assertEqual(info["py_models"][0]["default"], True)
    
    def test_get_provider_info_unavailable(self):
        """Test getting info for an unavailable provider"""
        from pydantic_llm_tester.llms import get_provider_info
        
        # Get info for an unavailable provider
        info = get_provider_info("unavailable_provider")
        
        # Check that the correct info was returned
        self.assertEqual(info["name"], "unavailable_provider")
        self.assertEqual(info["available"], False)


if __name__ == '__main__':
    unittest.main()
