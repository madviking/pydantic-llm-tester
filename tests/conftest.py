import pytest
import os
from unittest.mock import Mock, MagicMock
from src.llm_tester import LLMTester
from src.utils.config_manager import ConfigManager
from src.py_models.job_ads.model import JobAd

@pytest.fixture
def mock_tester():
    """Fixture that mocks the LLMTester class"""
    mock = Mock(spec=LLMTester)
    mock.providers = ["mock_provider"]
    mock.test_dir = "tests"

    # Configure mock methods to return values expected by tests
    mock.discover_test_cases.return_value = [{'module': 'dummy', 'name': 'test', 'model_class': Mock(), 'source_path': 'path/to/source', 'prompt_path': 'path/to/prompt', 'expected_path': 'path/to/expected'}]

    # Create a mock object that behaves like a dictionary for _validate_response
    mock_validation_result = MagicMock()
    mock_validation_result.__getitem__.side_effect = lambda key: {
        'success': True,
        'validated_data': {'test': 'data'}, # Add 'validated_data' here
        'accuracy': 90.0
    }[key]
    mock._validate_response.return_value = mock_validation_result

    # Configure run_test to return a dictionary with validated_data
    mock.run_test.return_value = {'openai': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}, 'anthropic': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}}

    # Configure run_tests to return a dictionary with validated_data
    mock.run_tests.return_value = {'dummy/test': {'openai': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}, 'anthropic': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}}}

    # Add mock attributes for prompt_optimizer and report_generator
    mock.prompt_optimizer = MagicMock()
    mock.report_generator = MagicMock()

    # Configure run_optimized_tests to call the mock prompt_optimizer
    def run_optimized_tests_side_effect():
        mock.prompt_optimizer.optimize_prompt("dummy prompt") # Call the mock optimizer
        return {'dummy/test': {'original_results': {}, 'optimized_results': {}, 'original_prompt': '...', 'optimized_prompt': '...'}} # Return dummy results
    mock.run_optimized_tests.side_effect = run_optimized_tests_side_effect

    # Configure generate_report to call the mock report_generator
    def generate_report_side_effect(results, optimized):
        mock.report_generator.generate_report(results, optimized) # Call the mock generator
        return {'main': 'Test report'} # Return dummy report
    mock.generate_report.side_effect = generate_report_side_effect


    return mock

@pytest.fixture 
def temp_config():
    """Fixture that creates a temporary config file"""
    config_path = "temp_config.json"
    config = ConfigManager(config_path)
    yield config
    if os.path.exists(config_path):
        os.remove(config_path)

@pytest.fixture
def job_ad_model():
    """Fixture providing a job ad model instance"""
    return JobAd
