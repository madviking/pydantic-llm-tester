"""
Pytest configuration
"""

import os
import pytest
import shutil
from unittest.mock import MagicMock, patch
import logging
from dotenv import load_dotenv # Import load_dotenv

from src import LLMTester
from src.py_models.job_ads import JobAd


# --- Command Line Option ---
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration", action="store_true", default=False,
        help="Run integration tests that make live API calls"
    )

def pytest_configure(config):
    """Load .env file at the start of the test session."""
    config.addinivalue_line("markers", "integration: mark test as integration test")

    # Load .env file from src directory
    project_root = os.path.dirname(os.path.abspath(__file__)) # tests directory
    project_root = os.path.dirname(project_root) # Project root
    # Point to src/.env instead of project_root/.env
    dotenv_path = os.path.join(project_root, 'src', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path, override=True)
        print(f"\nLoaded .env file from {dotenv_path} for test session.")
    else:
        print(f"\nWarning: .env file not found at {dotenv_path}. Integration tests might fail.")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        # --run-integration given in cli: do not skip integration tests
        return
    skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
# --- End Command Line Option ---


@pytest.fixture
def mock_provider_manager():
    """Mock provider manager"""
    # Import mock_get_response
    from src.utils.mock_responses import mock_get_response
    from src.utils.cost_manager import UsageData

    with patch('src.utils.provider_manager.ProviderManager') as mock:
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
    # Get the path to the src directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(base_dir, "src", "tests")

    tester = LLMTester(providers=["openai", "anthropic"], test_dir=test_dir) # Example providers

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
        os.path.join(base_dir, "src", "py_models", "job_ads", "tests", "prompts", "optimized"),
        os.path.join(base_dir, "src", "py_models", "product_descriptions", "tests", "prompts", "optimized")
    ]

    for directory in dirs_to_create:
        os.makedirs(directory, exist_ok=True)

    # This runs after the test session
    yield

    # Cleanup is optional - we'll leave the directories in place for now
