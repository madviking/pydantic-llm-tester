import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic_llm_tester.llms import BaseLLM
from pydantic_llm_tester.utils import UsageData


class MockBaseLLM(BaseLLM):
    """Mock implementation of BaseLLM for testing"""
    
    def __init__(self, config=None):
        super().__init__(config)
        # Default response for testing
        self.response_text = "Mock response from BaseLLM"
    
    def _call_llm_api(self, prompt, system_prompt, model_name, model_config):
        """Implement the abstract method with mock behavior"""
        return self.response_text, {"prompt_tokens": 10, "completion_tokens": 20}
        
    def get_response(self, prompt, source, model_name=None):
        """Override get_response for direct testing"""
        return self.response_text, UsageData(
            provider=self.name,
            model="test-model",
            prompt_tokens=100,
            completion_tokens=50
        )


class TestProviderManagerRefactored(unittest.TestCase):
    """Test the refactored ProviderManager that uses the pluggable LLM system"""
    
    def test_provider_manager_initialization(self):
        """Test that the ProviderManager correctly initializes providers from the registry"""
        # Create mock registry functions
        discover_providers_mock = MagicMock(return_value=["test_provider", "another_provider"])
        
        test_provider = MockBaseLLM()
        test_provider.name = "test_provider"
        
        another_provider = MockBaseLLM()
        another_provider.name = "another_provider"
        
        # Configure get_llm_provider to return our mock instances
        get_llm_provider_mock = MagicMock(side_effect=lambda name: 
            test_provider if name == "test_provider" else
            another_provider if name == "another_provider" else None
        )
        
        # Patch both functions in the provider_manager module
        with patch('pydantic_llm_tester.llms.llm_registry.discover_providers', discover_providers_mock), \
             patch('pydantic_llm_tester.llms.llm_registry.get_llm_provider', get_llm_provider_mock):
            
            # Import the ProviderManager class (inside the patch to ensure imports are patched)
            from pydantic_llm_tester.utils import ProviderManager
            
            # Initialize with a list of providers
            manager = ProviderManager(providers=["test_provider", "another_provider"])
            
            # Check that get_llm_provider was called for each provider
            get_llm_provider_mock.assert_has_calls([
                call("test_provider"),
                call("another_provider")
            ], any_order=True)
            
            # Check that provider instances were stored
            self.assertIn("test_provider", manager.provider_instances)
            self.assertIn("another_provider", manager.provider_instances)
            
            # Check that the correct instances were stored
            self.assertEqual(manager.provider_instances["test_provider"], test_provider)
            self.assertEqual(manager.provider_instances["another_provider"], another_provider)
    
    def test_provider_manager_get_response(self):
        """Test that the get_response method correctly delegates to the provider"""
        test_provider = MockBaseLLM()
        test_provider.name = "test_provider"
        
        # Mock the get_response method
        test_provider.get_response = MagicMock(return_value=(
            "Custom test response",
            UsageData(
                provider="test_provider",
                model="custom-model",
                prompt_tokens=200,
                completion_tokens=100
            )
        ))
        
        # Configure our mocks
        discover_providers_mock = MagicMock(return_value=["test_provider"])
        get_llm_provider_mock = MagicMock(return_value=test_provider)
        
        # Patch the registry functions
        with patch('pydantic_llm_tester.llms.llm_registry.discover_providers', discover_providers_mock), \
             patch('pydantic_llm_tester.llms.llm_registry.get_llm_provider', get_llm_provider_mock):
            
            # Import the ProviderManager class
            from pydantic_llm_tester.utils import ProviderManager
            
            # Initialize the manager
            manager = ProviderManager(providers=["test_provider"])
            
            # Call get_response
            response, usage = manager.get_response(
                provider="test_provider",
                prompt="Test prompt",
                source="Test source",
                model_name="custom-model"
            )
            
            # Check that the provider's get_response was called with correct arguments
            test_provider.get_response.assert_called_once_with(
                prompt="Test prompt",
                source="Test source",
                model_name="custom-model"
            )
            
            # Check the response and usage data
            self.assertEqual(response, "Custom test response")
            self.assertEqual(usage.provider, "test_provider")
            self.assertEqual(usage.model, "custom-model")
            self.assertEqual(usage.prompt_tokens, 200)
            self.assertEqual(usage.completion_tokens, 100)
    
    def test_provider_manager_mock_provider_handling(self):
        """Test that the ProviderManager correctly handles mock providers"""
        mock_provider = MockBaseLLM()
        mock_provider.name = "mock"
        
        # Mock the get_response method of the mock provider
        mock_provider.get_response = MagicMock(return_value=(
            "Mock response",
            UsageData(
                provider="mock",
                model="mock-model",
                prompt_tokens=50,
                completion_tokens=25
            )
        ))
        
        # Configure our mocks
        discover_providers_mock = MagicMock(return_value=["mock"])
        get_llm_provider_mock = MagicMock(return_value=mock_provider)
        
        # Patch the registry functions
        with patch('pydantic_llm_tester.llms.llm_registry.discover_providers', discover_providers_mock), \
             patch('pydantic_llm_tester.llms.llm_registry.get_llm_provider', get_llm_provider_mock):
            
            # Import the ProviderManager class
            from pydantic_llm_tester.utils import ProviderManager
            
            # Initialize with a mock provider prefix
            manager = ProviderManager(providers=["mock_test"])
            
            # Check that get_llm_provider was called with "mock"
            get_llm_provider_mock.assert_called_with("mock")
            
            # Check that the mock provider was stored with the requested name
            self.assertIn("mock_test", manager.provider_instances)
            self.assertEqual(manager.provider_instances["mock_test"], mock_provider)
            
            # Call get_response
            response, usage = manager.get_response(
                provider="mock_test",
                prompt="Test prompt",
                source="Test source"
            )
            
            # Check that the mock provider's get_response was called
            mock_provider.get_response.assert_called_once()
            
            # Check the response
            self.assertEqual(response, "Mock response")
            self.assertEqual(usage.provider, "mock")
    
    def test_provider_manager_error_handling(self):
        """Test that the ProviderManager correctly handles errors"""
        # Configure our mocks - return None for unknown provider
        discover_providers_mock = MagicMock(return_value=["test_provider"])
        get_llm_provider_mock = MagicMock(return_value=None)
        
        # Patch the registry functions
        with patch('pydantic_llm_tester.llms.llm_registry.discover_providers', discover_providers_mock), \
             patch('pydantic_llm_tester.llms.llm_registry.get_llm_provider', get_llm_provider_mock):
            
            # Import the ProviderManager class
            from pydantic_llm_tester.utils import ProviderManager
            
            # Initialize with an unknown provider
            manager = ProviderManager(providers=["unknown"])
            
            # Check that there's an initialization error
            self.assertIn("unknown", manager.initialization_errors)
            
            # Test calling get_response with an unknown provider
            with self.assertRaises(ValueError) as context:
                manager.get_response(
                    provider="unknown",
                    prompt="Test prompt",
                    source="Test source"
                )
            
            # Check that the error mentions the provider
            self.assertIn("unknown", str(context.exception))
    
    def test_provider_manager_provider_error(self):
        """Test that the ProviderManager handles errors from providers"""
        test_provider = MockBaseLLM()
        test_provider.name = "test_provider"
        
        # Mock the get_response method to raise an exception
        test_provider.get_response = MagicMock(side_effect=Exception("Provider error"))
        
        # Configure our mocks
        discover_providers_mock = MagicMock(return_value=["test_provider"])
        get_llm_provider_mock = MagicMock(return_value=test_provider)
        
        # Patch the registry functions
        with patch('pydantic_llm_tester.llms.llm_registry.discover_providers', discover_providers_mock), \
             patch('pydantic_llm_tester.llms.llm_registry.get_llm_provider', get_llm_provider_mock):
            
            # Import the ProviderManager class
            from pydantic_llm_tester.utils import ProviderManager
            
            # Initialize the manager
            manager = ProviderManager(providers=["test_provider"])
            
            # Test calling get_response
            with self.assertRaises(Exception) as context:
                manager.get_response(
                    provider="test_provider",
                    prompt="Test prompt",
                    source="Test source"
                )
            
            # Check that the error contains the provider error message
            self.assertIn("Provider error", str(context.exception))


if __name__ == '__main__':
    unittest.main()
