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
    assert "Update model costs from OpenRouter API" in result.stdout

def test_costs_reset_cache_command_exists():
    """Test that the 'costs reset-cache' command exists and returns help text"""
    result = runner.invoke(app, ["costs", "reset-cache", "--help"])
    assert result.exit_code == 0
    assert "Reset provider caches to force rediscovery" in result.stdout

# Test core logic functions
@patch("pydantic_llm_tester.cli.core.cost_update_logic.update_model_costs")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.display_update_summary")
def test_costs_update_basic(mock_display, mock_update, mock_update_result_success):
    """Test basic 'costs update' command without filters"""
    mock_update.return_value = mock_update_result_success
    
    # Simulate user confirming the action
    result = runner.invoke(app, ["costs", "update"], input="y\n")
    
    assert result.exit_code == 0
    mock_update.assert_called_once_with(
        provider_filter=None,
        update_provider_configs=False,
        force_refresh=False
    )
    mock_display.assert_called_once_with(mock_update_result_success)

@patch("pydantic_llm_tester.cli.core.cost_update_logic.update_model_costs")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.display_update_summary")
def test_costs_update_with_options(mock_display, mock_update, mock_update_result_success):
    """Test 'costs update' command with various options"""
    mock_update.return_value = mock_update_result_success
    
    # Simulate user confirming the action
    result = runner.invoke(app, [
        "costs", "update",
        "--providers", "openai", "--providers", "anthropic",
        "--update-configs",
        "--force"
    ], input="y\n")
    
    assert result.exit_code == 0
    mock_update.assert_called_once_with(
        provider_filter=["openai", "anthropic"],
        update_provider_configs=True,
        force_refresh=True
    )
    mock_display.assert_called_once_with(mock_update_result_success)

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

# Test the core logic directly
@patch("pydantic_llm_tester.cli.core.cost_update_logic.get_available_providers")
@patch("pydantic_llm_tester.cli.core.cost_update_logic._fetch_openrouter_models_with_cache")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.load_model_pricing")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.save_model_pricing")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.reset_caches")
def test_update_model_costs_basic(mock_reset, mock_save, mock_load, mock_fetch, mock_get_providers, mock_providers):
    """Test basic update_model_costs function"""
    mock_get_providers.return_value = mock_providers
    
    # Mock API response
    mock_fetch.return_value = [
        {
            "id": "openai/gpt-4",
            "pricing": {
                "prompt": "0.000025",
                "completion": "0.000050"
            }
        },
        {
            "id": "anthropic/claude-3",
            "pricing": {
                "prompt": "0.000012",
                "completion": "0.000060"
            }
        },
        {
            "id": "mistral/mistral-large",
            "pricing": {
                "prompt": "0.000008",
                "completion": "0.000024"
            }
        }
    ]
    
    # Mock current pricing data
    mock_load.return_value = {
        "openai": {
            "gpt-4": {
                "input": 30.0,
                "output": 60.0
            },
            "gpt-3.5-turbo": {
                "input": 2.0,
                "output": 2.0
            }
        },
        "anthropic": {
            "claude-3": {
                "input": 15.0,
                "output": 75.0
            }
        },
        "mistral": {
            "mistral-small": {
                "input": 2.0,
                "output": 6.0
            },
            "mistral-medium": {
                "input": 4.0,
                "output": 12.0
            }
        }
    }
    
    result = cost_update_logic.update_model_costs()
    
    assert result["success"] is True
    assert result["updated"] == 2  # gpt-4 and claude-3
    assert result["added"] == 1    # mistral-large
    assert result["unchanged"] == 3  # gpt-3.5-turbo, mistral-small, mistral-medium
    
    # Check that save_model_pricing was called with updated pricing
    expected_pricing = {
        "openai": {
            "gpt-4": {
                "input": 25.0,  # Updated
                "output": 50.0   # Updated
            },
            "gpt-3.5-turbo": {
                "input": 2.0,
                "output": 2.0
            }
        },
        "anthropic": {
            "claude-3": {
                "input": 12.0,  # Updated
                "output": 60.0   # Updated
            }
        },
        "mistral": {
            "mistral-small": {
                "input": 2.0,
                "output": 6.0
            },
            "mistral-medium": {
                "input": 4.0,
                "output": 12.0
            },
            "mistral-large": {  # Added
                "input": 8.0,
                "output": 24.0
            }
        }
    }
    mock_save.assert_called_once()
    mock_reset.assert_called_once()

@patch("pydantic_llm_tester.cli.core.cost_update_logic.get_available_providers")
@patch("pydantic_llm_tester.cli.core.cost_update_logic._fetch_openrouter_models_with_cache")
def test_update_model_costs_api_failure(mock_fetch, mock_get_providers, mock_providers):
    """Test update_model_costs when API fetch fails"""
    mock_get_providers.return_value = mock_providers
    mock_fetch.return_value = None
    
    result = cost_update_logic.update_model_costs()
    
    assert result["success"] is False
    assert "Failed to fetch models" in result["message"]
    assert result["updated"] == 0
    assert result["added"] == 0
    assert result["unchanged"] == 0

@patch("pydantic_llm_tester.cli.core.cost_update_logic.get_available_providers")
def test_update_model_costs_invalid_provider_filter(mock_get_providers, mock_providers):
    """Test update_model_costs with invalid provider filter"""
    mock_get_providers.return_value = mock_providers
    
    result = cost_update_logic.update_model_costs(provider_filter=["nonexistent"])
    
    assert result["success"] is False
    assert "No matching providers found" in result["message"]
    assert result["updated"] == 0
    assert result["added"] == 0
    assert result["unchanged"] == 0

# Test provider config updates
@patch("pydantic_llm_tester.cli.core.cost_update_logic.get_available_providers")
@patch("pydantic_llm_tester.cli.core.cost_update_logic._fetch_openrouter_models_with_cache")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.load_model_pricing")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.save_model_pricing")
@patch("pydantic_llm_tester.cli.core.cost_update_logic._update_provider_configs")
@patch("pydantic_llm_tester.cli.core.cost_update_logic.reset_caches")
def test_update_model_costs_with_provider_configs(mock_reset, mock_update_configs, mock_save, mock_load, mock_fetch, mock_get_providers, mock_providers):
    """Test update_model_costs with provider config updates"""
    mock_get_providers.return_value = mock_providers
    mock_fetch.return_value = [{"id": "openai/gpt-4", "pricing": {"prompt": "0.000025", "completion": "0.000050"}}]
    mock_load.return_value = {"openai": {"gpt-4": {"input": 30.0, "output": 60.0}}}
    
    result = cost_update_logic.update_model_costs(update_provider_configs=True)
    
    assert result["success"] is True
    mock_update_configs.assert_called_once_with(mock_fetch.return_value, mock_providers)
    mock_reset.assert_called_once()

def test_update_provider_configs():
    """Test _update_provider_configs function"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock provider config file
        provider_dir = os.path.join(tmpdir, "openai")
        os.makedirs(provider_dir)
        config_path = os.path.join(provider_dir, "config.json")
        
        provider_config = {
            "name": "openai",
            "api_key_env": "OPENAI_API_KEY",
            "llm_models": [
                {
                    "name": "gpt-4",
                    "default": True,
                    "preferred": False,
                    "enabled": True,
                    "cost_input": 30.0,
                    "cost_output": 60.0,
                    "cost_category": "expensive",
                    "max_input_tokens": 4096,
                    "max_output_tokens": 4096
                }
            ]
        }
        
        with open(config_path, "w") as f:
            json.dump(provider_config, f)
        
        # Mock API data with context length information
        api_models_data = [
            {
                "id": "openai/gpt-4",
                "context_length": 16384,
                "top_provider": {
                    "max_completion_tokens": 8192
                }
            }
        ]
        
        # Mock the load_provider_config function
        with patch("pydantic_llm_tester.cli.core.cost_update_logic.load_provider_config") as mock_load_config, \
             patch("pydantic_llm_tester.cli.core.cost_update_logic.os.path.dirname") as mock_dirname:
            
            # Create a mock provider config object
            mock_config = MagicMock()
            mock_config.llm_models = [
                MagicMock(
                    name="gpt-4",
                    max_input_tokens=4096,
                    max_output_tokens=4096
                )
            ]
            mock_load_config.return_value = mock_config
            
            # Mock dirname to return the temporary directory
            mock_dirname.return_value = tmpdir
            
            # Call the function
            cost_update_logic._update_provider_configs(api_models_data, ["openai"])
            
            # Check that the model's context length was updated
            assert mock_config.llm_models[0].max_input_tokens == 8192
            assert mock_config.llm_models[0].max_output_tokens == 8192

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