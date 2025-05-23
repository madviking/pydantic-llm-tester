import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.cli.main import app
from tests.conftest import mock_llm_tester_run_tests
from src.pydantic_llm_tester.llms.base import ModelConfig # Import ModelConfig

runner = CliRunner()

def test_run_command_handles_provider_model_format(mock_llm_tester_run_tests):
    """
    Test that the run command correctly handles the 'provider:model-name' format
    for specifying models.
    """
    # Mock the LLMTester.run_tests method to check the arguments it receives
    mock_llm_tester_run_tests.return_value = {} # Return an empty dict for simplicity

    result = runner.invoke(app, ["run", "--llm-models", "mock:mock-model-1", "openai:gpt-4o"])

    assert result.exit_code == 0
    # Verify that LLMTester.run_tests was called with the correct model_overrides
    mock_llm_tester_run_tests.assert_called_once()
    called_args, called_kwargs = mock_llm_tester_run_tests.call_args
    
    # Check if model_overrides is in kwargs and has the expected structure
    assert "model_overrides" in called_kwargs
    model_overrides = called_kwargs["model_overrides"]
    assert isinstance(model_overrides, dict)
    assert model_overrides == {"mock": ["mock-model-1"], "openai": ["gpt-4o"]}

    # Add assertions to check for expected output or behavior if needed
    # assert "Report generated" in result.stdout # Example assertion

@patch('src.pydantic_llm_tester.cli.core.test_runner_logic.LLMTester')
@patch('src.pydantic_llm_tester.cli.core.test_runner_logic.load_provider_config')
@patch('src.pydantic_llm_tester.cli.core.test_runner_logic.get_available_providers_from_factory')
def test_run_command_uses_dynamic_model_info(
    mock_get_available_providers,
    mock_load_provider_config,
    mock_llm_tester
):
    """
    Test that the run command uses dynamic model information from the central registry.
    """
    # Mock available providers
    mock_get_available_providers.return_value = ["mock", "openai"]

    # Mock provider config loading
    mock_mock_config = MagicMock()
    mock_mock_config.provider_type = "mock"
    mock_mock_config.env_key = None # Mock doesn't need API key
    mock_openai_config = MagicMock()
    mock_openai_config.provider_type = "openai"
    mock_openai_config.env_key = "OPENAI_API_KEY" # OpenAI needs API key

    def side_effect_load_config(provider_name):
        if provider_name == "mock":
            return mock_mock_config
        elif provider_name == "openai":
            return mock_openai_config
        return None

    mock_load_provider_config.side_effect = side_effect_load_config

    # Mock LLMTester initialization
    mock_tester_instance = MagicMock()
    mock_llm_tester.return_value = mock_tester_instance

    # Set a dummy API key for the test
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'dummy_key'}):
        result = runner.invoke(app, ["run", "--llm-models", "mock:mock-model-1", "openai:gpt-4o"])

    assert result.exit_code == 0

    # Verify LLMTester was initialized with the correct providers and model overrides
    mock_llm_tester.assert_called_once()
    called_args, called_kwargs = mock_llm_tester.call_args

    assert "providers" in called_kwargs
    assert sorted(called_kwargs["providers"]) == sorted(["mock", "openai"]) # Check usable providers

    assert "llm_models" in called_kwargs
    # The llm_models argument passed to LLMTester should be the parsed dictionary
    assert called_kwargs["llm_models"] == {"mock": ["mock-model-1"], "openai": ["gpt-4o"]}

    # Verify run_tests was called on the LLMTester instance with the correct arguments
    mock_tester_instance.run_tests.assert_called_once()
    run_tests_args, run_tests_kwargs = mock_tester_instance.run_tests.call_args

    # Check that model_overrides passed to run_tests is the parsed dictionary
    assert "model_overrides" in run_tests_kwargs
    assert run_tests_kwargs["model_overrides"] == {"mock": ["mock-model-1"], "openai": ["gpt-4o"]}

    # Add more specific assertions if needed, e.g., checking if LLMTester
    # internally accessed model details from a mocked registry. This would
    # require deeper mocking of LLMTester's internal dependencies.
    # For now, verifying the correct initialization arguments is sufficient
    # to test the CLI's interaction with LLMTester regarding model overrides.
