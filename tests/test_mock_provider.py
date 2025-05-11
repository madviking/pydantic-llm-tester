import unittest
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Type, Optional, List # Added Type, Optional, List
from pydantic import BaseModel as PydanticBaseModel # Added BaseModel
from pydantic_llm_tester.llms import ModelConfig, ProviderConfig
from pydantic_llm_tester.llms.mock.provider import MockProvider 
from pydantic_llm_tester.utils import UsageData

# Dummy Pydantic model for testing
class DummyModel(PydanticBaseModel):
    field: str

class TestMockProvider(unittest.TestCase):
    """Test the MockProvider implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.default_llm_models = [
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
        self.config_no_file_support = ProviderConfig(
            name="mock",
            provider_type="mock",
            env_key="MOCK_API_KEY",
            system_prompt="Test system prompt",
            llm_models=self.default_llm_models,
            supports_file_upload=False # Explicitly False
        )
        self.config_with_file_support = ProviderConfig(
            name="mock_files", # Changed name to distinguish in tests
            provider_type="mock",
            env_key="MOCK_API_KEY",
            system_prompt="Test system prompt for file upload",
            llm_models=self.default_llm_models,
            supports_file_upload=True
        )

    def test_mock_provider_initialization(self):
        """Test that the MockProvider can be initialized"""
        provider = MockProvider(self.config_no_file_support)
        self.assertEqual(provider.name, "mock")
        self.assertEqual(provider.config, self.config_no_file_support)
        self.assertFalse(provider.supports_file_upload)

        provider_files = MockProvider(self.config_with_file_support)
        self.assertEqual(provider_files.name, "mock_files")
        self.assertEqual(provider_files.config, self.config_with_file_support)
        self.assertTrue(provider_files.supports_file_upload)
        
    def test_mock_provider_get_response(self):
        """Test that the MockProvider.get_response works correctly"""
        provider = MockProvider(self.config_no_file_support)
        prompt = "Analyze this job posting"
        source = "MACHINE LEARNING ENGINEER with 5+ years of experience required"
        
        response_text, usage_data = provider.get_response(prompt, source, model_class=DummyModel)
        
        self.assertIsNotNone(response_text)
        self.assertIsInstance(response_text, str)
        self.assertTrue(len(response_text) > 0)
        
        self.assertIsInstance(usage_data, UsageData)
        self.assertEqual(usage_data.provider, "mock")
        self.assertGreater(usage_data.prompt_tokens, 0)
        self.assertGreater(usage_data.completion_tokens, 0)
        self.assertAlmostEqual(usage_data.total_cost, 0.0, places=3)
        self.assertEqual(provider.last_received_model_class, DummyModel)
        
    def test_mock_provider_with_product_source(self):
        """Test that the MockProvider works with product description sources"""
        provider = MockProvider(self.config_no_file_support)
        prompt = "Analyze this product description"
        source = "The latest smartphone with 6GB RAM and 128GB storage"
        
        response_text, usage_data = provider.get_response(prompt, source, model_class=DummyModel)
        
        self.assertIsNotNone(response_text)
        self.assertIsInstance(response_text, str)
        self.assertTrue(len(response_text) > 0)
        self.assertIn("{", response_text) 
        self.assertIn("}", response_text)
        self.assertEqual(provider.last_received_model_class, DummyModel)
        
    def test_mock_provider_different_models(self):
        """Test that the MockProvider works with different model names"""
        provider = MockProvider(self.config_no_file_support)
        prompt = "Analyze this text"
        source = "Sample source text for testing"
        
        response1, usage1 = provider.get_response(prompt, source, model_class=DummyModel, model_name="mock:default")
        self.assertEqual(provider.last_received_model_class, DummyModel)
        response2, usage2 = provider.get_response(prompt, source, model_class=DummyModel, model_name="mock:fast")
        self.assertEqual(provider.last_received_model_class, DummyModel)
        
        self.assertEqual(usage1.model, "mock:default")
        self.assertEqual(usage2.model, "mock:fast")
        
    def test_mock_provider_in_registry(self):
        """Test that the MockProvider can be loaded from the registry"""
        from pydantic_llm_tester.llms import get_llm_provider, reset_provider_cache
        
        reset_provider_cache()
        provider_from_registry = get_llm_provider("mock") 
        
        self.assertIsNotNone(provider_from_registry)
        self.assertEqual(provider_from_registry.name, "mock")

    def test_mock_provider_file_upload_supported(self):
        """Test file upload when provider supports it."""
        provider = MockProvider(self.config_with_file_support)
        self.assertTrue(provider.supports_file_upload)

        dummy_files = ["/path/to/file1.txt", "another/file.pdf"]
        prompt = "Analyze these files"
        source = "Some source text."

        response_text, usage_data = provider.get_response(prompt, source, model_class=DummyModel, files=dummy_files)

        self.assertIsNotNone(response_text)
        self.assertEqual(provider.last_received_files, dummy_files)
        self.assertEqual(provider.last_received_model_class, DummyModel)

    def test_mock_provider_file_upload_not_supported_by_provider_config(self):
        """Test file upload when provider config says it's not supported."""
        provider = MockProvider(self.config_no_file_support) 
        self.assertFalse(provider.supports_file_upload)

        dummy_files = ["/path/to/file1.txt"]
        prompt = "Analyze this file"
        source = "Some source text."

        with self.assertRaisesRegex(NotImplementedError, "Provider mock does not support file uploads."):
            provider.get_response(prompt, source, model_class=DummyModel, files=dummy_files)
        
        self.assertIsNone(provider.last_received_files)
        self.assertIsNone(provider.last_received_model_class)


    def test_mock_provider_file_upload_no_files_passed(self):
        """Test behavior when no files are passed, even if supported."""
        provider = MockProvider(self.config_with_file_support) 
        self.assertTrue(provider.supports_file_upload)

        prompt = "Analyze this"
        source = "Some source text."

        response_text, usage_data = provider.get_response(prompt, source, model_class=DummyModel) 
        self.assertIsNotNone(response_text)
        self.assertIsNone(provider.last_received_files)
        self.assertEqual(provider.last_received_model_class, DummyModel)


        provider.last_received_model_class = None # Reset for next call
        response_text_none, usage_data_none = provider.get_response(prompt, source, model_class=DummyModel, files=None) 
        self.assertIsNotNone(response_text_none)
        self.assertIsNone(provider.last_received_files)
        self.assertEqual(provider.last_received_model_class, DummyModel)


    def test_mock_provider_file_upload_not_supported_by_default_config(self):
        """Test file upload when provider config is minimal (relies on BaseLLM/ProviderConfig defaults)."""
        minimal_config = ProviderConfig(
            name="mock_minimal", 
            provider_type="mock",
            env_key="MOCK_API_KEY",
            llm_models=self.default_llm_models
        )
        provider = MockProvider(minimal_config)
        self.assertFalse(provider.supports_file_upload, 
                         f"Provider supports_file_upload was {provider.supports_file_upload}, expected False")

        dummy_files = ["/path/to/file1.txt"]
        prompt = "Analyze this file"
        source = "Some source text."

        with self.assertRaisesRegex(NotImplementedError, "Provider mock_minimal does not support file uploads."):
            provider.get_response(prompt, source, model_class=DummyModel, files=dummy_files)
        
        self.assertIsNone(provider.last_received_files)
        self.assertIsNone(provider.last_received_model_class)


if __name__ == '__main__':
    unittest.main()
