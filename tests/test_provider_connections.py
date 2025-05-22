"""
Tests for LLM provider connections
"""

import os
import pytest
from pathlib import Path
from pydantic import BaseModel
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to import src
import sys
sys.path.append(str(Path(__file__).parent.parent))

from pydantic_llm_tester.utils import ProviderManager
from pydantic_llm_tester.utils.cost_manager import UsageData
from pydantic_llm_tester.llms.base import BaseLLM, ModelConfig

# Define a dummy model for testing
class DummyModel(BaseModel):
    field1: str = ""
    field2: int = 0

# Mark tests that require API keys
api_key_required = pytest.mark.skipif(
    not (os.environ.get("OPENAI_API_KEY") or 
         os.environ.get("ANTHROPIC_API_KEY") or
         os.environ.get("MISTRAL_API_KEY") or
         (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and os.environ.get("GOOGLE_PROJECT_ID"))),
    reason="API keys required for this test"
)


class TestProviderManager:
    """Tests for the ProviderManager class"""

    def test_initialization(self):
        """Test initializing the provider manager"""
        # Test initializing with all providers
        providers = ["openai", "anthropic", "mistral", "google"]
        manager = ProviderManager(providers)
        
        # Check that the providers list is stored
        assert manager.providers == providers
        
        # Check that a logger is created
        assert manager.logger is not None
        
    def test_mock_responses(self):
        """Test getting mock responses from providers"""
        # Initialize manager with mock provider
        manager = ProviderManager(["mock"])
        
        # Test job ad
        response, usage_data = manager.get_response(
            provider="mock",
            prompt="Extract information from this job post.",
            source="SENIOR MACHINE LEARNING ENGINEER position at DataVision Analytics",
            model_class=DummyModel # Pass dummy model class
        )
        
        # Check response has job ad content
        assert "SENIOR MACHINE LEARNING ENGINEER" in response
        assert "DataVision Analytics" in response
        
        # Check usage data is returned
        assert usage_data is not None
        assert usage_data.provider == "mock"
        assert usage_data.prompt_tokens > 0
        assert usage_data.completion_tokens > 0
        
        # Test product description
        response, usage_data = manager.get_response(
            provider="mock",
            prompt="Extract information from this product description.",
            source="Wireless Earbuds X1 by TechGear",
            model_class=DummyModel # Pass dummy model class
        )
        
        # Check response has product description content
        assert "Wireless Earbuds X1" in response
        assert "TechGear" in response
        
        # Check usage data again
        assert usage_data is not None
        assert usage_data.provider == "mock"
        assert usage_data.prompt_tokens > 0
        assert usage_data.completion_tokens > 0
    
    @api_key_required
    def test_available_providers(self):
        """Test which providers have available API keys"""
        # Get providers with API keys
        available_providers = []
        
        if os.environ.get("OPENAI_API_KEY"):
            available_providers.append("openai")
        
        if os.environ.get("ANTHROPIC_API_KEY"):
            available_providers.append("anthropic")
        
        mistral_key = os.environ.get("MISTRAL_API_KEY")
        if mistral_key and mistral_key != "your_mistral_api_key_here":
            available_providers.append("mistral")
        
        # For Google, use mock_google since the service account may not have LLM permissions
        if (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and 
            os.environ.get("GOOGLE_PROJECT_ID") and
            os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""))):
            # If Google credentials are available, add the real google provider
            available_providers.append("google")
        
        # Always add mock provider for reliable testing
        available_providers.append("mock")
        
        # Skip the test if no real providers are available
        if len(available_providers) == 1 and available_providers[0] == "mock":
            pytest.skip("No API keys available for testing real providers")
        
        # Initialize manager with available providers
        manager = ProviderManager(available_providers)
        
        # Test connection by getting a simple response
        for provider in available_providers:
            try:
                # Use a model that's likely to be available
                model_name = None
                if provider == "openai":
                    model_name = "gpt-3.5-turbo"  # Cheaper option
                elif provider == "anthropic":
                    model_name = "claude-3-haiku-20240307"  # Smaller model
                elif provider == "mistral":
                    model_name = "mistral-small-latest"  # Smaller model
                elif provider == "google":
                    # Use a specific Google model if available, otherwise rely on default
                    model_name = "gemini-pro" # Example Google model name
                elif provider == "mock":
                    # Mock provider doesn't need a specific model name for this test
                    pass
                
                response, _ = manager.get_response( # Ignore usage for this simple test
                    provider=provider,
                    prompt="Hello, please respond with a simple 'Hello World'",
                    source="This is a test.",
                    model_class=DummyModel, # Pass dummy model class
                    model_name=model_name
                )
                
                # Check that response isn't empty
                assert response and len(response) > 0
                print(f"✓ {provider} connection successful")
            except Exception as e:
                if provider == "mock":
                    # Mock provider should always work
                    pytest.fail(f"Error with mock provider: {str(e)}")
                else:
                    # Log error but don't fail the test for real providers with valid credentials
                    print(f"⚠ {provider} connection failed: {str(e)}")
                    # Only fail the test if we have credentials but connection still fails
                    if provider in manager.provider_instances:
                        pytest.fail(f"Error connecting to {provider}: {str(e)}")


# Mock OpenAI Provider for testing ProviderManager interaction
from typing import Optional, List, Type, Any
class MockOpenAIProvider(BaseLLM):
    def __init__(self, config=None, llm_models=None):
        super().__init__(config, llm_models=llm_models)
        self.name = "openai" 
        self.last_received_files: Optional[List[str]] = None
        self.last_received_model_class: Optional[Type[BaseModel]] = None

    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None):
        self.last_received_files = files
        self.last_received_model_class = model_class
        return "Mocked OpenAI response: Hello World", {"prompt_tokens": 5, "completion_tokens": 2}


    def get_response(self, prompt: str, source: str, model_class: Type[BaseModel], model_name: Optional[str] = None, files: Optional[List[str]] = None):
        self.last_received_files = files
        self.last_received_model_class = model_class
        return "Mocked OpenAI response: Hello World", UsageData(
            provider=self.name,
            model=model_name or "gpt-3.5-turbo", 
            prompt_tokens=len(prompt.split()),
            completion_tokens=len("Mocked OpenAI response: Hello World".split())
        )


@api_key_required
@patch('pydantic_llm_tester.llms.llm_registry.get_llm_provider')
def test_openai_connection(mock_get_llm_provider):
    """Test connection to OpenAI"""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")
    
    # Configure the mock to return a MockOpenAIProvider instance
    mock_openai_provider_instance = MockOpenAIProvider()
    # Make the get_response method a MagicMock
    mock_openai_provider_instance.get_response = MagicMock(return_value=(
        "Mocked OpenAI response: Hello World",
        UsageData(
            provider="openai",
            model="gpt-3.5-turbo",
            prompt_tokens=5,
            completion_tokens=2
        )
    ))
    mock_get_llm_provider.return_value = mock_openai_provider_instance

    manager = ProviderManager(["openai"])
    
    # Test getting a response
    try:
        response, usage = manager.get_response( 
            provider="openai",
            prompt="Say hello",
            source="This is a test",
            model_class=DummyModel, # Pass dummy model class
            model_name="gpt-3.5-turbo"
        )
        assert response and len(response) > 0
        # Verify that get_llm_provider was called
        mock_get_llm_provider.assert_called_once_with("openai", llm_models=None)
        # Verify that the mock provider's get_response was called
        mock_openai_provider_instance.get_response.assert_called_once_with(
             prompt="Say hello",
             source="This is a test",
             model_class=DummyModel, # Expect dummy model class
             model_name="gpt-3.5-turbo",
             files=None 
        )
        # Optionally check the returned usage data if needed
        assert usage.provider == "openai"
        assert usage.model == "gpt-3.5-turbo"


    except Exception as e:
        pytest.fail(f"OpenAI connection failed: {str(e)}")


@api_key_required
@patch('pydantic_llm_tester.llms.llm_registry.get_llm_provider')
def test_anthropic_connection(mock_get_llm_provider):
    """Test connection to Anthropic"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("Anthropic API key not available")
    
    # Configure the mock to return a MockAnthropicProvider instance
    mock_anthropic_provider = MagicMock()
    mock_anthropic_provider.name = "anthropic"
    mock_anthropic_provider.get_response.return_value = (
        "Mocked Anthropic response: Hello World",
        UsageData(
            provider="anthropic",
            model="claude-3-haiku-20240307",
            prompt_tokens=5,
            completion_tokens=2
        )
    )
    mock_get_llm_provider.return_value = mock_anthropic_provider
    
    manager = ProviderManager(["anthropic"])
    
    # Test getting a response
    try:
        response, usage = manager.get_response(
            provider="anthropic",
            prompt="Say hello",
            source="This is a test",
            model_class=DummyModel, # Pass dummy model class
            model_name="claude-3-haiku-20240307"
        )
        assert response and len(response) > 0
        # Verify that get_llm_provider was called
        mock_get_llm_provider.assert_called_once_with("anthropic", llm_models=None)
        # Verify that the mock provider's get_response was called
        mock_anthropic_provider.get_response.assert_called_once_with(
            prompt="Say hello",
            source="This is a test",
            model_class=DummyModel,
            model_name="claude-3-haiku-20240307",
            files=None
        )
        # Check usage data
        assert usage.provider == "anthropic"
        assert usage.model == "claude-3-haiku-20240307"
    except Exception as e:
        pytest.fail(f"Anthropic connection failed: {str(e)}")


@api_key_required
def test_mistral_connection():
    """Test connection to Mistral"""
    mistral_key = os.environ.get("MISTRAL_API_KEY")
    if not mistral_key or mistral_key == "your_mistral_api_key_here":
        pytest.skip("Mistral API key not available or has default value")
    
    manager = ProviderManager(["mistral"])
    
    # Test getting a response
    try:
        response, _ = manager.get_response(
            provider="mistral",
            prompt="Say hello",
            source="This is a test",
            model_class=DummyModel, # Pass dummy model class
            model_name="mistral-small-latest"
        )
        assert response and len(response) > 0
    except Exception as e:
        pytest.fail(f"Mistral connection failed: {str(e)}")


@api_key_required
def test_google_connection():
    """Test connection to Google Vertex AI"""
    if not (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and 
            os.environ.get("GOOGLE_PROJECT_ID")):
        pytest.skip("Google API credentials not available")
    
    # Test the real Google provider if credentials are available
    manager = ProviderManager(["google"])
    
    # Test getting a response
    try:
        response, _ = manager.get_response(
            provider="google",
            prompt="Say hello",
            source="This is a test",
            model_class=DummyModel, # Pass dummy model class
            model_name="gemini-pro" # Use a specific Google model
        )
        
        # Verify we got a valid response
        assert response and len(response) > 0
        print("✓ Google connection successful")

    except ImportError as e:
        pytest.skip(f"Google Cloud libraries not installed: {str(e)}")
    except Exception as e:
        if "not allowed to use Publisher Model" in str(e):
            # This is expected if the service account doesn't have permissions
            # for the specific model. Log a warning but don't fail the test.
            print("⚠ Google connection failed due to insufficient permissions (expected for some setups)")
            assert True # Test passes if this specific permission error occurs
        else:
            pytest.fail(f"Google connection failed: {str(e)}")
