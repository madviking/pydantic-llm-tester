"""
Pytest configuration
"""

import os
import pytest
import shutil
from unittest.mock import MagicMock, patch

from llm_tester import LLMTester
from llm_tester.models.job_ads import JobAd


@pytest.fixture
def mock_provider_manager():
    """Mock provider manager"""
    # Import mock_get_response
    from llm_tester.utils.mock_responses import mock_get_response
    from llm_tester.utils.cost_manager import UsageData
    
    with patch('llm_tester.utils.provider_manager.ProviderManager') as mock:
        manager_instance = MagicMock()
        mock.return_value = manager_instance
        
        # Use a wrapper that returns both the response and usage data
        def mock_response_with_usage(provider, prompt, source, model_name=None):
            response = mock_get_response(provider, prompt, source, model_name)
            # Create mock usage data
            usage_data = UsageData(
                provider=provider,
                model=model_name or "mock-model",
                prompt_tokens=len(prompt.split()) + len(source.split()),
                completion_tokens=500  # Rough estimate
            )
            return response, usage_data
            
        # Use our wrapped version
        manager_instance.get_response.side_effect = mock_response_with_usage
        yield manager_instance


@pytest.fixture
def mock_tester(mock_provider_manager):
    """Mock LLM tester"""
    # Get the path to the llm_tester directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(base_dir, "llm_tester", "tests")
    
    tester = LLMTester(providers=["openai", "anthropic"], test_dir=test_dir)
    
    # Replace provider manager with mock
    tester.provider_manager = mock_provider_manager
    
    return tester


@pytest.fixture
def job_ad_model():
    """Job ad model"""
    return JobAd


@pytest.fixture(scope="session", autouse=True)
def ensure_optimized_dirs():
    """Ensure optimized prompt directories exist for tests"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    dirs_to_create = [
        os.path.join(base_dir, "llm_tester", "tests", "cases", "job_ads", "prompts", "optimized"),
        os.path.join(base_dir, "llm_tester", "tests", "cases", "product_descriptions", "prompts", "optimized")
    ]
    
    for directory in dirs_to_create:
        os.makedirs(directory, exist_ok=True)
    
    # This runs after the test session
    yield
    
    # Cleanup is optional - we'll leave the directories in place for now