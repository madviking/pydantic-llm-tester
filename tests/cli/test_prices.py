import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from pydantic_llm_tester.cli import app
from pydantic_llm_tester.cli.core import price_query_logic

runner = CliRunner()

@pytest.fixture
def mock_model_prices():
    """Fixture providing mock model pricing data"""
    return [
        {
            "provider": "openai",
            "name": "gpt-4",
            "cost_input": 30.0,
            "cost_output": 60.0,
            "total_cost": 90.0,
            "context_length": 8192,
            "input_tokens": 4096,
            "output_tokens": 4096,
            "cost_category": "expensive"
        },
        {
            "provider": "anthropic",
            "name": "claude-3",
            "cost_input": 15.0,
            "cost_output": 75.0,
            "total_cost": 90.0,
            "context_length": 100000,
            "input_tokens": 50000,
            "output_tokens": 50000,
            "cost_category": "expensive"
        },
        {
            "provider": "mistral",
            "name": "mistral-small",
            "cost_input": 2.0,
            "cost_output": 6.0,
            "total_cost": 8.0,
            "context_length": 32768,
            "input_tokens": 16384,
            "output_tokens": 16384,
            "cost_category": "standard"
        }
    ]

@pytest.fixture
def mock_providers():
    """Fixture providing mock provider list"""
    return ["openai", "anthropic", "mistral", "openrouter"]

# Test command structure and options
def test_prices_list_command_exists():
    """Test that the 'prices list' command exists and returns help text"""
    result = runner.invoke(app, ["prices", "list", "--help"])
    assert result.exit_code == 0
    assert "List and filter model prices" in result.stdout

def test_prices_refresh_command_exists():
    """Test that the 'prices refresh' command exists and returns help text"""
    result = runner.invoke(app, ["prices", "refresh", "--help"])
    assert result.exit_code == 0
    assert "Refresh model information" in result.stdout

# Test core logic functions
@patch("pydantic_llm_tester.cli.core.price_query_logic.get_all_model_prices")
@patch("pydantic_llm_tester.cli.core.price_query_logic.display_model_prices")
def test_prices_list_basic(mock_display, mock_get_prices, mock_model_prices):
    """Test basic 'prices list' command without filters"""
    mock_get_prices.return_value = mock_model_prices
    
    result = runner.invoke(app, ["prices", "list"])
    
    assert result.exit_code == 0
    mock_get_prices.assert_called_once_with(
        provider_filter=None,
        model_pattern=None,
        max_cost=None,
        min_context_length=None,
        show_all_models=False
    )
    mock_display.assert_called_once_with(
        models=mock_model_prices,
        sort_by="total_cost",
        ascending=True
    )

@patch("pydantic_llm_tester.cli.core.price_query_logic.get_all_model_prices")
@patch("pydantic_llm_tester.cli.core.price_query_logic.display_model_prices")
def test_prices_list_with_filters(mock_display, mock_get_prices, mock_model_prices):
    """Test 'prices list' command with various filters"""
    mock_get_prices.return_value = [mock_model_prices[0]]  # Return filtered result
    
    result = runner.invoke(app, [
        "prices", "list",
        "--providers", "openai",
        "--model", "gpt",
        "--max-cost", "100",
        "--min-context", "4000",
        "--sort-by", "name",
        "--desc"
    ])
    
    assert result.exit_code == 0
    mock_get_prices.assert_called_once_with(
        provider_filter=["openai"],
        model_pattern="gpt",
        max_cost=100.0,
        min_context_length=4000,
        show_all_models=False
    )
    mock_display.assert_called_once_with(
        models=[mock_model_prices[0]],
        sort_by="name",
        ascending=False
    )

@patch("pydantic_llm_tester.cli.core.price_query_logic.refresh_openrouter_models")
def test_prices_refresh_success(mock_refresh):
    """Test successful 'prices refresh' command"""
    mock_refresh.return_value = (True, "Successfully refreshed 50 models from OpenRouter API")
    
    # Simulate user confirming the action
    result = runner.invoke(app, ["prices", "refresh"], input="y\n")
    
    assert result.exit_code == 0
    assert "Successfully refreshed 50 models" in result.stdout
    mock_refresh.assert_called_once()

@patch("pydantic_llm_tester.cli.core.price_query_logic.refresh_openrouter_models")
def test_prices_refresh_failure(mock_refresh):
    """Test failed 'prices refresh' command"""
    mock_refresh.return_value = (False, "Failed to fetch models from OpenRouter API")
    
    # Simulate user confirming the action
    result = runner.invoke(app, ["prices", "refresh"], input="y\n")
    
    assert result.exit_code == 1
    assert "Error: Failed to fetch models" in result.stdout
    mock_refresh.assert_called_once()

@patch("pydantic_llm_tester.cli.core.price_query_logic.refresh_openrouter_models")
def test_prices_refresh_abort(mock_refresh):
    """Test aborting 'prices refresh' command"""
    # Simulate user aborting the action
    result = runner.invoke(app, ["prices", "refresh"], input="n\n")
    
    assert result.exit_code == 1
    assert "Aborted" in result.stdout
    mock_refresh.assert_not_called()

# Test the core logic directly
@pytest.mark.skip(reason="Test needs to be updated to use LLMRegistry instead of provider configs")
def test_get_all_model_prices_filtering():
    """Test filtering in get_all_model_prices function"""
    # This test needs to be updated to use LLMRegistry and get_all_model_details
    # instead of loading provider configs directly
    pass

# Test error handling
@patch("pydantic_llm_tester.cli.core.price_query_logic.get_all_model_prices")
def test_prices_list_empty_results(mock_get_prices):
    """Test 'prices list' command when no models match the filters"""
    mock_get_prices.return_value = []
    
    with patch("pydantic_llm_tester.cli.core.price_query_logic.console.print") as mock_print:
        result = runner.invoke(app, ["prices", "list", "--providers", "nonexistent"])
        
        assert result.exit_code == 0
        mock_print.assert_called_with("[yellow]No models found matching the specified criteria.[/yellow]")

@patch("pydantic_llm_tester.cli.core.price_query_logic.get_available_providers")
def test_get_all_model_prices_invalid_provider_filter(mock_get_providers):
    """Test get_all_model_prices with invalid provider filter"""
    mock_get_providers.return_value = ["openai", "anthropic"]
    
    models = price_query_logic.get_all_model_prices(provider_filter=["nonexistent"])
    assert models == []

def test_get_all_model_prices_invalid_regex():
    """Test get_all_model_prices with invalid regex pattern"""

    models = price_query_logic.get_all_model_prices(model_pattern="[invalid")
    assert models == []

# Test OpenRouter API integration
@patch("pydantic_llm_tester.utils.config_manager.ConfigManager")
def test_refresh_openrouter_models_success(mock_config_manager_cls):
    """Test successful refresh of OpenRouter models"""
    # Setup ConfigManager mock
    mock_config_manager = MagicMock()
    mock_config_manager_cls.return_value = mock_config_manager
    mock_config_manager.is_openrouter_enabled.return_value = True
    mock_config_manager.fetch_and_process_openrouter_models.return_value = [{"id": "model1"}, {"id": "model2"}]
    
    # Call the function under test
    success, message = price_query_logic.refresh_openrouter_models()
    
    # Verify results
    assert success is True
    assert "Successfully refreshed" in message
    mock_config_manager.fetch_and_process_openrouter_models.assert_called_once_with(force=True)

@patch("pydantic_llm_tester.utils.config_manager.ConfigManager")
def test_refresh_openrouter_models_failure(mock_config_manager_cls):
    """Test failed refresh of OpenRouter models"""
    # Setup ConfigManager mock
    mock_config_manager = MagicMock()
    mock_config_manager_cls.return_value = mock_config_manager
    mock_config_manager.is_openrouter_enabled.return_value = True
    mock_config_manager.fetch_and_process_openrouter_models.return_value = None
    
    # Call the function under test
    success, message = price_query_logic.refresh_openrouter_models()
    
    # Verify results
    assert success is False
    assert "OpenRouter API returned no valid model data" in message
    mock_config_manager.fetch_and_process_openrouter_models.assert_called_once_with(force=True)

@patch("pydantic_llm_tester.utils.config_manager.ConfigManager")
def test_refresh_openrouter_models_exception(mock_config_manager_cls):
    """Test exception during refresh of OpenRouter models"""
    # Setup ConfigManager mock
    mock_config_manager = MagicMock()
    mock_config_manager_cls.return_value = mock_config_manager
    mock_config_manager.is_openrouter_enabled.return_value = True
    mock_config_manager.fetch_and_process_openrouter_models.side_effect = Exception("API error")
    
    # Call the function under test
    success, message = price_query_logic.refresh_openrouter_models()
    
    # Verify results
    assert success is False
    assert "Error refreshing OpenRouter models" in message
    mock_config_manager.fetch_and_process_openrouter_models.assert_called_once_with(force=True)
