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
    
import unittest
from unittest.mock import patch, MagicMock, call # Import MagicMock and call
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic_llm_tester.llms import BaseLLM, ProviderConfig, ModelConfig # Import ModelConfig


class MockProvider(BaseLLM):
    """Mock provider for testing the registry"""

    def __init__(self, config=None, llm_models=None): # Added llm_models
        super().__init__(config)
        self.llm_models_filter = llm_models # Store the filter

    def _call_llm_api(self, prompt, system_prompt, model_name, model_config):
        """Implement the abstract method"""
        return "Mock response", {"prompt_tokens": 10, "completion_tokens": 20}


class TestLLMRegistry(unittest.TestCase):
    """Test the LLM registry functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Patch create_provider where it is used in llm_registry
        # This is necessary because llm_registry imports it locally within methods.
        self.create_patcher = patch('pydantic_llm_tester.llms.llm_registry.create_provider')
        self.mock_create_provider = self.create_patcher.start()

        # Create mock provider instances
        self.test_provider = MockProvider()
        self.another_provider = MockProvider()

        # Configure create_provider to return the mock instance
        def create_provider_side_effect(provider_name, llm_models=None):
            if provider_name == "test_provider":
                # Return a new MockProvider instance with the filter
                return MockProvider(llm_models=llm_models)
            elif provider_name == "another_provider":
                 # Return a new MockProvider instance with the filter
                return MockProvider(llm_models=llm_models)
            return None

        self.mock_create_provider.side_effect = create_provider_side_effect

        # Reset the singleton instance and caches before each test
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry
        LLMRegistry._instance = None
        LLMRegistry._provider_instances = {}
        LLMRegistry._model_data = {}
        LLMRegistry._cache_timestamps = {}


    def tearDown(self):
        """Tear down test fixtures"""
        self.discover_patcher.stop()
        self.create_patcher.stop()

        # Ensure the singleton instance and caches are reset after each test
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry
        LLMRegistry._instance = None
        LLMRegistry._provider_instances = {}
        LLMRegistry._model_data = {}
        LLMRegistry._cache_timestamps = {}


    def test_discover_providers(self):
        """Test discovering available providers"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry

        # Get the registry instance
        model_registry = LLMRegistry()

        # Patch get_available_providers after getting the registry instance
        with patch('pydantic_llm_tester.llms.llm_registry.get_available_providers') as mock_get_available_providers:
            # Configure get_available_providers to return our test providers
            mock_get_available_providers.return_value = ["test_provider", "another_provider"]

            # Call discover_providers
            providers = model_registry.discover_providers()

            # Check that get_available_providers was called
            mock_get_available_providers.assert_called_once()

            # Check that the correct providers were returned
            self.assertEqual(set(providers), {"test_provider", "another_provider"})

    def test_get_llm_provider(self):
        """Test getting a provider instance"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry

        # Get the registry instance
        model_registry = LLMRegistry()

        # Call get_llm_provider
        provider = model_registry.get_llm_provider("test_provider")

        # Check that create_provider was called
        self.mock_create_provider.assert_called_once_with("test_provider", llm_models=None)

        # Check that the correct provider was returned (it should be a MockProvider instance)
        self.assertIsInstance(provider, MockProvider)
        self.assertEqual(provider.name, "test_provider")
        self.assertIsNone(provider.llm_models_filter) # Check that filter was passed correctly

    def test_get_llm_provider_with_models_filter(self):
        """Test getting a provider instance with a models filter"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry

        # Get the registry instance
        model_registry = LLMRegistry()

        # Define a models filter
        models_filter = ["model1", "model2"]

        # Call get_llm_provider with the filter
        provider = model_registry.get_llm_provider("test_provider", llm_models=models_filter)

        # Check that create_provider was called with the filter
        self.mock_create_provider.assert_called_once_with("test_provider", llm_models=models_filter)

        # Check that the returned provider instance has the correct filter
        self.assertIsInstance(provider, MockProvider)
        self.assertEqual(provider.name, "test_provider")
        self.assertEqual(provider.llm_models_filter, models_filter) # Check that filter was passed correctly


    def test_get_llm_provider_caching(self):
        """Test that provider instances are cached"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry

        # Get the registry instance
        model_registry = LLMRegistry()

        # Call get_llm_provider twice for the same provider and filter
        provider1 = model_registry.get_llm_provider("test_provider", llm_models=["modelA"])
        provider2 = model_registry.get_llm_provider("test_provider", llm_models=["modelA"])

        # Check that create_provider was called only once
        self.mock_create_provider.assert_called_once_with("test_provider", llm_models=["modelA"])

        # Check that the same instance was returned both times
        self.assertIs(provider1, provider2)

    def test_get_llm_provider_caching_different_filters(self):
        """Test that different filters result in different cached instances"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry

        # Get the registry instance
        model_registry = LLMRegistry()

        # Call get_llm_provider with different filters
        provider1 = model_registry.get_llm_provider("test_provider", llm_models=["modelA"])
        provider2 = model_registry.get_llm_provider("test_provider", llm_models=["modelB"])
        provider3 = model_registry.get_llm_provider("test_provider", llm_models=["modelA"]) # Call again with first filter

        # Check that create_provider was called for each unique filter
        self.assertEqual(self.mock_create_provider.call_count, 2)
        self.mock_create_provider.assert_has_calls([
            call("test_provider", llm_models=["modelA"]),
            call("test_provider", llm_models=["modelB"])
        ], any_order=True)

        # Check that the first and third calls returned the same instance
        self.assertIs(provider1, provider3)
        # Check that the second call returned a different instance
        self.assertIsNot(provider1, provider2)


    def test_reset_provider_cache(self):
        """Test resetting the provider cache"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry

        # Get the registry instance
        model_registry = LLMRegistry()

        # Call get_llm_provider to cache a provider
        provider1 = model_registry.get_llm_provider("test_provider")

        # Reset the cache
        model_registry.reset_provider_cache()

        # Call get_llm_provider again
        provider2 = model_registry.get_llm_provider("test_provider")

        # Check that create_provider was called twice (once before reset, once after)
        self.assertEqual(self.mock_create_provider.call_count, 2)

        # Check that different instances were returned
        self.assertIsNot(provider1, provider2)

    def test_store_and_retrieve_models(self):
        """Test storing and retrieving model details from the registry"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry, ModelConfig

        model_registry = LLMRegistry()

        # Create mock model configs
        model_configs = {
            "test:model1": ModelConfig(
                name="test:model1",
                provider="test_provider",
                default=True,
                preferred=False,
                enabled=True,
                cost_input=0.001,
                cost_output=0.002,
                cost_category="test",
                max_input_tokens=4096, # Added max_input_tokens
                max_output_tokens=1000 # Added max_output_tokens
            ),
            "test:model2": ModelConfig(
                name="test:model2",
                provider="test_provider",
                default=False,
                preferred=True,
                enabled=True,
                cost_input=0.003,
                cost_output=0.004,
                cost_category="test",
                max_input_tokens=8192, # Added max_input_tokens
                max_output_tokens=2000 # Added max_output_tokens
            )
        }

        # Store the models
        model_registry.store_provider_models("test_provider", model_configs)

        # Retrieve models for the provider
        retrieved_models = model_registry.get_provider_models("test_provider")

        # Check that the retrieved models match the stored models
        self.assertEqual(len(retrieved_models), 2)
        self.assertEqual(retrieved_models["test:model1"].name, "test:model1")
        self.assertEqual(retrieved_models["test:model2"].name, "test:model2")
        self.assertEqual(retrieved_models["test:model1"].cost_input, 0.001)
        self.assertEqual(retrieved_models["test:model1"].max_input_tokens, 4096) # Check max_input_tokens
        self.assertEqual(retrieved_models["test:model1"].max_output_tokens, 1000) # Check max_output_tokens


        # Retrieve a specific model
        retrieved_model1 = model_registry.get_model_details("test_provider", "test:model1")
        self.assertEqual(retrieved_model1.name, "test:model1")
        self.assertEqual(retrieved_model1.cost_input, 0.001)
        self.assertEqual(retrieved_model1.max_input_tokens, 4096) # Check max_input_tokens
        self.assertEqual(retrieved_model1.max_output_tokens, 1000) # Check max_output_tokens


        retrieved_model2 = model_registry.get_model_details("test_provider", "test:model2")
        self.assertEqual(retrieved_model2.name, "test:model2")
        self.assertEqual(retrieved_model2.max_input_tokens, 8192) # Check max_input_tokens
        self.assertEqual(retrieved_model2.max_output_tokens, 2000) # Check max_output_tokens


        # Test retrieving non-existent provider or model
        self.assertEqual(model_registry.get_provider_models("non_existent_provider"), {}) # Expect empty dict
        with self.assertRaises(ValueError, msg="Model 'non_existent_model' not found for provider 'test_provider'."): # Expect ValueError
            model_registry.get_model_details("test_provider", "non_existent_model")
        with self.assertRaises(ValueError, msg="Model 'test:model1' not found for provider 'non_existent_provider'."): # Expect ValueError
            model_registry.get_model_details("non_existent_provider", "test:model1")


    def test_get_provider_info(self):
        """Test getting provider information"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry, ModelConfig

        # Get the LLMRegistry instance
        model_registry = LLMRegistry()

        # Create a config for the test provider (without llm_models)
        config = ProviderConfig(
            name="test_provider",
            provider_type="test",
            env_key="TEST_API_KEY",
            llm_models=[] # llm_models should be empty in config.json now
        )

        # Set the config on the test provider (still needed for get_llm_provider fallback in get_provider_info)
        self.test_provider.config = config

        # Create mock model configs to store in the registry
        model_configs = {
            "test:model1": ModelConfig(
                name="test:model1",
                provider="test_provider",
                default=True,
                preferred=False,
                enabled=True,
                cost_input=0.001,
                cost_output=0.002,
                cost_category="test",
                max_input_tokens=4096,
                max_output_tokens=1000
            )
        }

        # Store the model data in the registry
        model_registry.store_provider_models("test_provider", model_configs)

        # Get the provider info
        info = model_registry.get_provider_info("test_provider")

        # Check that the correct info was returned
        self.assertEqual(info["name"], "test_provider")
        self.assertEqual(info["available"], True)
        self.assertEqual(info["config"]["provider_type"], "test")
        self.assertEqual(info["config"]["env_key"], "TEST_API_KEY")
        self.assertEqual(len(info["llm_models"]), 1)
        self.assertEqual(info["llm_models"][0]["name"], "test:model1")
        self.assertEqual(info["llm_models"][0]["default"], True)
        self.assertEqual(info["llm_models"][0]["preferred"], False)
        self.assertEqual(info["llm_models"][0]["enabled"], True)
        self.assertEqual(info["llm_models"][0]["cost_input"], 0.001)
        self.assertEqual(info["llm_models"][0]["cost_output"], 0.002)
        self.assertEqual(info["llm_models"][0]["cost_category"], "test")
        self.assertEqual(info["llm_models"][0]["max_input_tokens"], 4096)
        self.assertEqual(info["llm_models"][0]["max_output_tokens"], 1000)
        self.assertEqual(info["llm_models"][0]["provider"], "test_provider")


    def test_get_provider_info_unavailable(self):
        """Test getting info for an unavailable provider"""
        from pydantic_llm_tester.llms.llm_registry import LLMRegistry

        # Get the LLMRegistry instance
        model_registry = LLMRegistry()

        # Ensure the provider is NOT in the discovered providers list for this test
        self.mock_get_available_providers.return_value = ["another_provider"]

        # Get info for an unavailable provider (one not in discovered list and not stored)
        info = model_registry.get_provider_info("unavailable_provider")

        # Check that the correct info was returned
        self.assertEqual(info["name"], "unavailable_provider")
        self.assertEqual(info["available"], False)
        self.assertIsNone(info.get("config")) # Config should not be available
        self.assertIsNone(info.get("llm_models")) # Check that llm_models key is not present


if __name__ == '__main__':
    unittest.main()
