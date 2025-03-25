"""
Pytest configuration
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from llm_tester import LLMTester
from llm_tester.models.job_ads import JobAd


@pytest.fixture
def mock_provider_manager():
    """Mock provider manager"""
    # Import mock_get_response
    from llm_tester.utils.mock_responses import mock_get_response
    
    with patch('llm_tester.utils.provider_manager.ProviderManager') as mock:
        manager_instance = MagicMock()
        mock.return_value = manager_instance
        
        # Use the mock_get_response from the module
        manager_instance.get_response.side_effect = mock_get_response
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