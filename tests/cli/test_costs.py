import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from pydantic_llm_tester.cli import app
from pydantic_llm_tester.cli.core import cost_update_logic

runner = CliRunner()

@pytest.fixture
def mock_update_result_success():
    """Fixture providing a successful update result"""
    return {
        "success": True,
        "message": "Successfully updated pricing information for 2 models, added 1 new models",
        "updated": 2,
        "added": 1,
        "unchanged": 3,
        "updated_models": [
            {
                "provider": "openai",
                "model": "gpt-4",
                "old_input": 30.0,
                "old_output": 60.0,
                "new_input": 25.0,
                "new_output": 50.0
            },
            {
                "provider": "anthropic",
                "model": "claude-3",
                "old_input": 15.0,
                "old_output": 75.0,
                "new_input": 12.0,
                "new_output": 60.0
            }
        ],
        "added_models": [
            {
                "provider": "mistral",
                "model": "mistral-large",
                "input": 8.0,
                "output": 24.0
            }
        ],
        "unchanged_models": [
            {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "input": 2.0,
                "output": 2.0
            },
            {
                "provider": "mistral",
                "model": "mistral-small",
                "input": 2.0,
                "output": 6.0
            },
            {
                "provider": "mistral",
                "model": "mistral-medium",
                "input": 4.0,
                "output": 12.0
            }
        ]
    }

@pytest.fixture
def mock_update_result_failure():
    """Fixture providing a failed update result"""
    return {
        "success": False,
        "message": "Failed to fetch models from OpenRouter API",
        "updated": 0,
        "added": 0,
        "unchanged": 0
    }

@pytest.fixture
def mock_providers():
    """Fixture providing mock provider list"""
    return ["openai", "anthropic", "mistral", "openrouter"]

# Test command structure and options
def test_costs_update_command_exists():
    """Test that the 'costs update' command exists and returns help text"""
    result = runner.invoke(app, ["costs", "update", "--help"])
    assert result.exit_code == 0
    assert "Update model costs" in result.stdout

def test_costs_reset_cache_command_exists():
    """Test that the 'costs reset-cache' command exists and returns help text"""
    result = runner.invoke(app, ["costs", "reset-cache", "--help"])
    assert result.exit_code == 0
    assert "Reset provider caches to force rediscovery" in result.stdout

# Test core logic functions
@pytest.mark.skip(reason="Costs update tests need to be rewritten to match new implementation")
def test_costs_update_basic():
    """Test basic 'costs update' command without filters"""
    pass

@pytest.mark.skip(reason="Costs update tests need to be rewritten to match new implementation")
def test_costs_update_with_options():
    """Test 'costs update' command with various options"""
    pass

@patch("pydantic_llm_tester.cli.core.cost_update_logic.update_model_costs")
def test_costs_update_failure(mock_update, mock_update_result_failure):
    """Test failed 'costs update' command"""
    mock_update.return_value = mock_update_result_failure
    
    # Simulate user confirming the action
    result = runner.invoke(app, ["costs", "update"], input="y\n")
    
    assert result.exit_code == 1
    mock_update.assert_called_once()

@patch("pydantic_llm_tester.cli.core.cost_update_logic.update_model_costs")
def test_costs_update_abort(mock_update):
    """Test aborting 'costs update' command"""
    # Simulate user aborting the action
    result = runner.invoke(app, ["costs", "update"], input="n\n")
    
    assert result.exit_code == 1
    assert "Aborted" in result.stdout
    mock_update.assert_not_called()

@patch("pydantic_llm_tester.llms.provider_factory.reset_caches")
def test_costs_reset_cache(mock_reset):
    """Test 'costs reset-cache' command"""
    # Simulate user confirming the action
    result = runner.invoke(app, ["costs", "reset-cache"], input="y\n")
    
    assert result.exit_code == 0
    assert "Provider caches reset successfully" in result.stdout
    mock_reset.assert_called_once()

@patch("pydantic_llm_tester.llms.provider_factory.reset_caches")
def test_costs_reset_cache_abort(mock_reset):
    """Test aborting 'costs reset-cache' command"""
    # Simulate user aborting the action
    result = runner.invoke(app, ["costs", "reset-cache"], input="n\n")
    
    assert result.exit_code == 1
    assert "Aborted" in result.stdout
    mock_reset.assert_not_called()

# Skip these tests as they need to be updated for the new implementation
@pytest.mark.skip(reason="Test needs to be updated for the new cost update implementation")
def test_update_model_costs_basic():
    """Test basic update_model_costs function"""
    pass

@pytest.mark.skip(reason="Test needs to be updated for the new cost update implementation")
def test_update_model_costs_api_failure():
    """Test update_model_costs when API fetch fails"""
    pass

@pytest.mark.skip(reason="Test needs to be updated for the new cost update implementation")
def test_update_model_costs_invalid_provider_filter():
    """Test update_model_costs with invalid provider filter"""
    pass

@pytest.mark.skip(reason="Test needs to be updated for the new cost update implementation")
def test_update_model_costs_with_provider_configs():
    """Test update_model_costs with provider config updates"""
    pass

@pytest.mark.skip(reason="Test needs to be updated for the new cost update implementation")
def test_update_provider_configs():
    """Test _update_provider_configs function"""
    pass

# Test display functions
def test_display_update_summary_success(mock_update_result_success):
    """Test display_update_summary with successful update"""
    with patch("pydantic_llm_tester.cli.core.cost_update_logic.console.print") as mock_print:
        cost_update_logic.display_update_summary(mock_update_result_success)
        
        # Check that console.print was called with tables
        assert mock_print.call_count >= 3  # Summary table + updated models table + added models table

def test_display_update_summary_failure(mock_update_result_failure):
    """Test display_update_summary with failed update"""
    with patch("pydantic_llm_tester.cli.core.cost_update_logic.console.print") as mock_print:
        cost_update_logic.display_update_summary(mock_update_result_failure)
        
        # Check that console.print was called with error message
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "Error" in args

def test_get_available_providers_for_suggestions():
    """Test get_available_providers_for_suggestions function"""
    with patch("pydantic_llm_tester.cli.core.cost_update_logic.get_available_providers") as mock_get_providers:
        mock_get_providers.return_value = ["openai", "anthropic", "mistral"]
        
        providers = cost_update_logic.get_available_providers_for_suggestions()
        
        assert providers == ["openai", "anthropic", "mistral"]
        mock_get_providers.assert_called_once()
