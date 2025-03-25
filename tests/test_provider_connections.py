"""
Tests for LLM provider connections
"""

import os
import pytest
from unittest import mock
from pathlib import Path

# Add the parent directory to sys.path to import llm_tester
import sys
sys.path.append(str(Path(__file__).parent.parent))

from llm_tester.utils.provider_manager import ProviderManager
from llm_tester.utils.mock_responses import mock_get_response

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
        
    @mock.patch('llm_tester.utils.provider_manager.ProviderManager.get_response', side_effect=mock_get_response)
    def test_mock_responses(self, mock_get_response):
        """Test getting mock responses from providers"""
        # Initialize manager with mock provider
        manager = ProviderManager(["mock_provider"])
        
        # Test job ad
        response = manager.get_response(
            provider="mock_provider",
            prompt="Extract information from this job post.",
            source="SENIOR MACHINE LEARNING ENGINEER position at DataVision Analytics"
        )
        
        # Check response has job ad content
        assert "SENIOR MACHINE LEARNING ENGINEER" in response
        assert "DataVision Analytics" in response
        
        # Test product description
        response = manager.get_response(
            provider="mock_provider",
            prompt="Extract information from this product description.",
            source="Wireless Earbuds X1 by TechGear"
        )
        
        # Check response has product description content
        assert "Wireless Earbuds X1" in response
        assert "TechGear" in response
    
    @api_key_required
    def test_available_providers(self):
        """Test which providers have available API keys"""
        # Get providers with API keys
        available_providers = []
        
        if os.environ.get("OPENAI_API_KEY"):
            available_providers.append("openai")
        
        if os.environ.get("ANTHROPIC_API_KEY"):
            available_providers.append("anthropic")
        
        if os.environ.get("MISTRAL_API_KEY"):
            available_providers.append("mistral")
        
        if (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and 
            os.environ.get("GOOGLE_PROJECT_ID")):
            available_providers.append("google")
        
        # Skip the test if no providers are available
        if not available_providers:
            pytest.skip("No API keys available for testing providers")
        
        # Initialize manager with available providers
        manager = ProviderManager(available_providers)
        
        # Test connection by getting a simple response
        for provider in available_providers:
            try:
                response = manager.get_response(
                    provider=provider,
                    prompt="Hello, please respond with a simple 'Hello World'",
                    source="This is a test."
                )
                
                # Check that response isn't empty
                assert response and len(response) > 0
                print(f"✓ {provider} connection successful")
            except Exception as e:
                pytest.fail(f"Error connecting to {provider}: {str(e)}")


@api_key_required
def test_openai_connection():
    """Test connection to OpenAI"""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")
    
    manager = ProviderManager(["openai"])
    
    # Test getting a response
    try:
        response = manager.get_response(
            provider="openai",
            prompt="Say hello",
            source="This is a test",
            model_name="gpt-3.5-turbo"  # Use smaller model for testing
        )
        assert response and len(response) > 0
    except Exception as e:
        pytest.fail(f"OpenAI connection failed: {str(e)}")


@api_key_required
def test_anthropic_connection():
    """Test connection to Anthropic"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("Anthropic API key not available")
    
    manager = ProviderManager(["anthropic"])
    
    # Test getting a response
    try:
        response = manager.get_response(
            provider="anthropic",
            prompt="Say hello",
            source="This is a test",
            model_name="claude-3-haiku-20240307"  # Use smaller model for testing
        )
        assert response and len(response) > 0
    except Exception as e:
        pytest.fail(f"Anthropic connection failed: {str(e)}")


@api_key_required
def test_mistral_connection():
    """Test connection to Mistral"""
    if not os.environ.get("MISTRAL_API_KEY"):
        pytest.skip("Mistral API key not available")
    
    manager = ProviderManager(["mistral"])
    
    # Test getting a response
    try:
        response = manager.get_response(
            provider="mistral",
            prompt="Say hello",
            source="This is a test",
            model_name="mistral-small-latest"  # Use smaller model for testing
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
    
    manager = ProviderManager(["google"])
    
    # Test getting a response
    try:
        response = manager.get_response(
            provider="google",
            prompt="Say hello",
            source="This is a test",
            model_name="gemini-pro"
        )
        assert response and len(response) > 0
    except Exception as e:
        pytest.fail(f"Google connection failed: {str(e)}")