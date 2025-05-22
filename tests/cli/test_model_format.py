import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.cli.main import app
from src.pydantic_llm_tester.utils.config_manager import ConfigManager

runner = CliRunner()

@pytest.fixture
def mock_config_manager():
    """Fixture to mock ConfigManager and its methods."""
    with patch('src.pydantic_llm_tester.cli.commands.run.ConfigManager') as MockConfigManager:
        mock_instance = MockConfigManager.return_value
        # Mock methods that might be called during CLI command execution
        mock_instance.load_config.return_value = {} # Return empty config for simplicity
        mock_instance.get_setting.side_effect = lambda key, default=None: default # Mock getting settings
        mock_instance.is_provider_enabled.return_value = True # Assume provider is enabled
        mock_instance.get_model_details_from_registry.return_value = MagicMock() # Return a mock ModelConfig
        yield mock_instance

@pytest.fixture
def mock_llm_tester():
    """Fixture to mock LLMTester and its run_tests method."""
    with patch('src.pydantic_llm_tester.cli.commands.run.LLMTester') as MockLLMTester:
        mock_instance = MockLLMTester.return_value
        mock_instance.run_tests.return_value = {} # Mock run_tests return value
        mock_instance.generate_report.return_value = {"main": "Mock Report"} # Mock report generation
        mock_instance.save_cost_report.return_value = {} # Mock saving cost report
        yield mock_instance

def test_run_command_handles_provider_model_format(mock_config_manager, mock_llm_tester):
    """
    Test that the 'run' command correctly handles the 'provider:model-name' format
    for the --llm_models option.
    """
    # Simulate calling the run command with the new format
    result = runner.invoke(app, ["run", "--llm_models", "openai:gpt-4o", "--py_models", "job_ads"])

    # Check that the command executed successfully
    assert result.exit_code == 0, f"CLI command failed with output: {result.stdout}"

    # Verify that LLMTester.run_tests was called with the correct model_overrides
    # The model_overrides should be a dictionary mapping provider names to model names
    mock_llm_tester.run_tests.assert_called_once()
    call_args, call_kwargs = mock_llm_tester.run_tests.call_args
    assert 'model_overrides' in call_kwargs
    assert call_kwargs['model_overrides'] == {"openai": "gpt-4o"}
    assert 'modules' in call_kwargs
    assert call_kwargs['modules'] == ["job_ads"]

    # Verify that ConfigManager.get_model_details_from_registry was called
    # This confirms that the parsing logic in ConfigManager is being used
    mock_config_manager.get_model_details_from_registry.assert_called_once_with("openai:gpt-4o")

def test_run_command_handles_multiple_provider_model_formats(mock_config_manager, mock_llm_tester):
    """
    Test that the 'run' command correctly handles multiple 'provider:model-name' formats
    for the --llm_models option.
    """
    # Simulate calling the run command with multiple models in the new format
    result = runner.invoke(app, ["run", "--llm_models", "openai:gpt-4o", "--llm_models", "anthropic:claude-3-sonnet-20240229", "--py_models", "job_ads"])

    # Check that the command executed successfully
    assert result.exit_code == 0, f"CLI command failed with output: {result.stdout}"

    # Verify that LLMTester.run_tests was called with the correct model_overrides
    mock_llm_tester.run_tests.assert_called_once()
    call_args, call_kwargs = mock_llm_tester.run_tests.call_args
    assert 'model_overrides' in call_kwargs
    # Note: Typer handles multiple --llm_models flags by creating a list.
    # The CLI logic needs to convert this list into the expected dictionary format.
    # This test verifies the end result passed to run_tests.
    assert call_kwargs['model_overrides'] == {"openai": "gpt-4o", "anthropic": "claude-3-sonnet-20240229"}
    assert 'modules' in call_kwargs
    assert call_kwargs['modules'] == ["job_ads"]

    # Verify that ConfigManager.get_model_details_from_registry was called for each model
    mock_config_manager.get_model_details_from_registry.assert_any_call("openai:gpt-4o")
    mock_config_manager.get_model_details_from_registry.assert_any_call("anthropic:claude-3-sonnet-20240229")
    assert mock_config_manager.get_model_details_from_registry.call_count == 2

def test_llm_tester_initialized_with_correct_model_overrides(mock_llm_tester):
    """
    Test that LLMTester is initialized with the correct model_overrides dictionary
    when the run command is executed with --llm_models.
    """
    # Simulate calling the run command with multiple models
    result = runner.invoke(app, ["run", "--llm_models", "openai:gpt-4o", "--llm_models", "anthropic:claude-3-sonnet-20240229", "--py_models", "job_ads"])

    # Check that the command executed successfully
    assert result.exit_code == 0, f"CLI command failed with output: {result.stdout}"

    # Verify that LLMTester was initialized with the correct model_overrides
    mock_llm_tester.assert_called_once()
    call_args, call_kwargs = mock_llm_tester.call_args
    assert 'model_overrides' in call_kwargs
    assert call_kwargs['model_overrides'] == {"openai": "gpt-4o", "anthropic": "claude-3-sonnet-20240229"}
    assert 'providers' in call_kwargs
    # The providers list should be derived from the keys of model_overrides
    assert sorted(call_kwargs['providers']) == sorted(["openai", "anthropic"])
    assert 'test_dir' in call_kwargs
    assert call_kwargs['test_dir'] is None # Assuming default test_dir for this test

# TODO: Add tests for other CLI commands that might use model names (e.g., prices, costs)
# TODO: Add tests for error handling (e.g., invalid format, provider not enabled)

@pytest.fixture
def mock_cost_manager_summary():
    """Fixture to mock CostManager.get_run_summary."""
    with patch('src.pydantic_llm_tester.utils.cost_manager.cost_tracker') as MockCostTracker:
        mock_instance = MockCostTracker.get_run_summary.return_value = {
            "total_cost": 0.001234,
            "total_tokens": 150,
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "model_costs": {
                "openai:gpt-4o": {
                    "total_cost": 0.001234,
                    "total_tokens": 150,
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "test_count": 1
                }
            }
        }
        yield MockCostTracker

def test_run_command_displays_cost_summary(mock_llm_tester, mock_cost_manager_summary):
    """
    Test that the 'run' command output includes the cost summary from CostManager.
    """
    # Configure mock_llm_tester.generate_report to return a report string
    # that includes a placeholder for the cost summary.
    mock_llm_tester.return_value.report_generator.generate_report.return_value = "Mock Report Content\n## Cost Summary\n{COST_SUMMARY_PLACEHOLDER}"

    # Configure mock_cost_manager_summary to return a specific summary
    mock_cost_manager_summary.get_run_summary.return_value = {
        "total_cost": 0.001234,
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "model_costs": {
            "openai:gpt-4o": {
                "total_cost": 0.001234,
                "total_tokens": 150,
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "test_count": 1
            }
        }
    }

    # Simulate calling the run command
    result = runner.invoke(app, ["run", "--llm_models", "openai:gpt-4o", "--py_models", "job_ads"])

    # Check that the command executed successfully
    assert result.exit_code == 0, f"CLI command failed with output: {result.stdout}"

    # Check that the output contains the expected cost summary information
    # The exact formatting might vary, so check for key elements.
    assert "## Cost Summary" in result.stdout
    assert "Total cost: $0.001234" in result.stdout
    assert "Total tokens: 150" in result.stdout
    assert "Prompt tokens: 100" in result.stdout
    assert "Completion tokens: 50" in result.stdout
    assert "openai:gpt-4o" in result.stdout
    assert "0.001234" in result.stdout # Check for model cost

    # Verify that CostManager.get_run_summary was called
    mock_cost_manager_summary.get_run_summary.assert_called_once()

    # Verify that LLMTester.generate_report was called
    mock_llm_tester.return_value.report_generator.generate_report.assert_called_once()
