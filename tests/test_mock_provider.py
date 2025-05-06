import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llms.base import BaseLLM, ModelConfig, ProviderConfig
from src.utils.cost_manager import UsageData


class TestMockProvider(unittest.TestCase):
    """Test the MockProvider implementation"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a basic test config for the mock provider
        self.config = ProviderConfig(
            name="mock",
            provider_type="mock",
            env_key="MOCK_API_KEY",
            system_prompt="Test system prompt",
            llm_models=[
                ModelConfig(
                    name="mock:default",
                    default=True,
                    preferred=False,
                    cost_input=0.0,
                    cost_output=0.0,
                    cost_category="free",
                    max_input_tokens=16000,
                    max_output_tokens=16000
                ),
                ModelConfig(
                    name="mock:fast",
                    default=False,
                    preferred=False,
                    cost_input=0.0,
                    cost_output=0.0,
                    cost_category="free",
                    max_input_tokens=8000,
                    max_output_tokens=8000
                )
            ]
        )

    def test_mock_provider_initialization(self):
        """Test that the MockProvider can be initialized"""
        # Import the MockProvider
        from src.llms.mock.provider import MockProvider
        
        # Initialize the provider
        provider = MockProvider(self.config)
        
        # Check basic properties
        self.assertEqual(provider.name, "mock")
        self.assertEqual(provider.config, self.config)
        
    def test_mock_provider_get_response(self):
        """Test that the MockProvider.get_response works correctly"""
        # Import the MockProvider
        from src.llms.mock.provider import MockProvider
        
        # Initialize the provider
        provider = MockProvider(self.config)
        
        # Prepare a test prompt with a job-related source
        prompt = "Analyze this job posting"
        source = "MACHINE LEARNING ENGINEER with 5+ years of experience required"
        
        # Call get_response
        response_text, usage_data = provider.get_response(prompt, source)
        
        # Check that we got a response
        self.assertIsNotNone(response_text)
        self.assertIsInstance(response_text, str)
        self.assertTrue(len(response_text) > 0)
        
        # Check usage data
        self.assertIsInstance(usage_data, UsageData)
        self.assertEqual(usage_data.provider, "mock")
        self.assertGreater(usage_data.prompt_tokens, 0)
        self.assertGreater(usage_data.completion_tokens, 0)
        # The total cost may not be exactly 0.0 due to pricing calculation
        self.assertAlmostEqual(usage_data.total_cost, 0.0, places=3)
        
    def test_mock_provider_with_product_source(self):
        """Test that the MockProvider works with product description sources"""
        # Import the MockProvider
        from src.llms.mock.provider import MockProvider
        
        # Initialize the provider
        provider = MockProvider(self.config)
        
        # Prepare a test prompt with a product-related source
        prompt = "Analyze this product description"
        source = "The latest smartphone with 6GB RAM and 128GB storage"
        
        # Call get_response
        response_text, usage_data = provider.get_response(prompt, source)
        
        # Check that we got a response
        self.assertIsNotNone(response_text)
        self.assertIsInstance(response_text, str)
        self.assertTrue(len(response_text) > 0)
        
        # The response should contain product-related JSON
        self.assertIn("{", response_text)
        self.assertIn("}", response_text)
        
    def test_mock_provider_different_models(self):
        """Test that the MockProvider works with different model names"""
        # Import the MockProvider
        from src.llms.mock.provider import MockProvider
        
        # Initialize the provider
        provider = MockProvider(self.config)
        
        # Prepare a test prompt
        prompt = "Analyze this text"
        source = "Sample source text for testing"
        
        # Call get_response with different model names
        response1, usage1 = provider.get_response(prompt, source, model_name="mock:default")
        response2, usage2 = provider.get_response(prompt, source, model_name="mock:fast")
        
        # Check that model names are correctly reflected in usage data
        self.assertEqual(usage1.model, "mock:default")
        self.assertEqual(usage2.model, "mock:fast")
        
    def test_mock_provider_in_registry(self):
        """Test that the MockProvider can be loaded from the registry"""
        # Import the registry
        from src.llms.llm_registry import get_llm_provider, reset_provider_cache
        
        # Reset the cache to ensure a clean test
        reset_provider_cache()
        
        # Get the mock provider from the registry
        provider = get_llm_provider("mock")
        
        # Check that we got a provider
        self.assertIsNotNone(provider)
        self.assertEqual(provider.name, "mock")


if __name__ == '__main__':
    unittest.main()
