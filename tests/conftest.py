import pytest
import os
from unittest.mock import Mock, MagicMock
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
# Use dotenv_values to get a dictionary of loaded variables
from dotenv import dotenv_values
config_values = dotenv_values()

# Explicitly set loaded variables in os.environ
if config_values:
    for key, value in config_values.items():
        os.environ[key] = value

# from src.llm_tester import LLMTester # No longer need to import the actual class for spec
from src.utils.config_manager import ConfigManager
from src.py_models.job_ads.model import JobAd

# Define a mock class that mimics the necessary parts of LLMTester
class MockLLMTester:
    def __init__(self, providers, test_dir):
        self.providers = providers
        self.test_dir = test_dir
        self.prompt_optimizer = MagicMock()
        self.report_generator = MagicMock()
        self.run_id = "mock_run_id" # Add a mock run_id

    def discover_test_cases(self):
        # Return a list of mock test cases
        return [{'module': 'dummy', 'name': 'test', 'model_class': Mock(), 'source_path': 'path/to/source', 'prompt_path': 'path/to/prompt', 'expected_path': 'path/to/expected'}]


    def run_test(self, test_case, model_overrides=None, progress_callback=None):
        # Return a mock result structure
        return {'openai': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}, 'anthropic': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}}

    def run_tests(self, model_overrides=None, modules=None, progress_callback=None):
        # Return a mock result structure
        return {'dummy/test': {'openai': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}, 'anthropic': {'response': '...', 'validation': {'success': True, 'validated_data': {'test': 'data'}, 'accuracy': 90.0}}}}


    def run_optimized_tests(self, model_overrides=None, save_optimized_prompts=True, modules=None, progress_callback=None):
        # Mimic the behavior needed by tests that call this
        self.prompt_optimizer.optimize_prompt("dummy prompt") # Call the mock optimizer
        return {'dummy/test': {'original_results': {}, 'optimized_results': {}, 'original_prompt': '...', 'optimized_prompt': '...'}} # Return dummy results

    def generate_report(self, results, optimized=False):
        # Mimic the behavior needed by tests that call this
        self.report_generator.generate_report(results, optimized) # Call the mock generator
        return {'main': 'Test report'} # Return dummy report

    def _validate_response(self, response, model_class, expected_data):
         # Return a mock validation result
         return {
            'success': True,
            'validated_data': {'test': 'data'},
            'accuracy': 90.0
        }

    def _calculate_accuracy(self, actual, expected, **kwargs):
        # Return a mock accuracy value
        return 100.0


@pytest.fixture
def mock_tester():
    """Fixture that provides a mock LLMTester instance"""
    # Create an instance of the custom mock class
    mock_instance = MockLLMTester(providers=["mock_provider"], test_dir="tests")

    # Create a Mock object that wraps the instance
    mock = Mock(wraps=mock_instance)

    # You can still configure specific return values or side effects on the mock if needed
    # For example, if you need discover_test_cases to return a specific list:
    # mock.discover_test_cases.return_value = [...]

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
