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
    assert "List and filter model prices from all providers" in result.stdout

def test_prices_refresh_command_exists():
    """Test that the 'prices refresh' command exists and returns help text"""
    result = runner.invoke(app, ["prices", "refresh", "--help"])
    assert result.exit_code == 0
    assert "Refresh model prices from OpenRouter API" in result.stdout

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
        min_context_length=None
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
        min_context_length=4000
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
def test_get_all_model_prices_filtering():
    """Test filtering in get_all_model_prices function"""
    with patch("pydantic_llm_tester.cli.core.price_query_logic.get_available_providers") as mock_get_providers, \
         patch("pydantic_llm_tester.cli.core.price_query_logic.load_provider_config") as mock_load_config:
        
        mock_get_providers.return_value = ["openai", "anthropic"]
        
        # Mock provider configs
        openai_config = MagicMock()
        openai_config.llm_models = [
                MagicMock(
                    enabled=True,
                    cost_input=30.0,
                    cost_output=60.0,
                    max_input_tokens=4096,
                    max_output_tokens=4096,
                    cost_category="expensive"
                ),
                MagicMock(
                    enabled=True,
                    cost_input=2.0,
                    cost_output=2.0,
                    max_input_tokens=4096,
                    max_output_tokens=4096,
                    cost_category="standard"
                ),
                MagicMock(
                    enabled=False,
                    cost_input=1.0,
                    cost_output=1.0,
                    max_input_tokens=4096,
                    max_output_tokens=4096,
                    cost_category="standard"
                )
            ]
        openai_config.llm_models[0].name = "gpt-4"
        openai_config.llm_models[1].name = "gpt-3.5-turbo"
        openai_config.llm_models[2].name = "disabled-model"


        anthropic_config = MagicMock()
        anthropic_config.llm_models = [
            MagicMock(
                enabled=True,
                cost_input=15.0,
                cost_output=75.0,
                max_input_tokens=50000,
                max_output_tokens=50000,
                cost_category="expensive"
            )
        ]
        anthropic_config.llm_models[0].name = "claude-3"
        
        def mock_load_config_side_effect(provider):
            if provider == "openai":
                return openai_config
            elif provider == "anthropic":
                return anthropic_config
            return None
        
        mock_load_config.side_effect = mock_load_config_side_effect
        
        # Test provider filter
        models = price_query_logic.get_all_model_prices(provider_filter=["openai"])
        assert len(models) == 2  # Only enabled OpenAI models
        assert all(m["provider"] == "openai" for m in models)
        
        # Test model pattern filter
        models = price_query_logic.get_all_model_prices(model_pattern="gpt")
        assert len(models) == 2
        assert all("gpt" in m["name"].lower() for m in models)
        
        # Test max cost filter
        models = price_query_logic.get_all_model_prices(max_cost=10.0)
        assert len(models) == 1
        assert models[0]["name"] == "gpt-3.5-turbo"
        
        # Test min context length filter
        models = price_query_logic.get_all_model_prices(min_context_length=90000)
        assert len(models) == 1
        assert models[0]["name"] == "claude-3"

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
@patch("pydantic_llm_tester.cli.core.price_query_logic._fetch_openrouter_models_with_cache")
def test_refresh_openrouter_models_success(mock_fetch):
    """Test successful refresh of OpenRouter models"""
    mock_fetch.return_value = [{"id": "model1"}, {"id": "model2"}]
    
    success, message = price_query_logic.refresh_openrouter_models()
    
    assert success is True
    assert "Successfully refreshed" in message
    mock_fetch.assert_called_once_with()

@patch("pydantic_llm_tester.cli.core.price_query_logic._fetch_openrouter_models_with_cache")
def test_refresh_openrouter_models_failure(mock_fetch):
    """Test failed refresh of OpenRouter models"""
    mock_fetch.return_value = None
    
    success, message = price_query_logic.refresh_openrouter_models()
    
    assert success is False
    assert "Failed to fetch models" in message
    mock_fetch.assert_called_once_with()

@patch("pydantic_llm_tester.cli.core.price_query_logic._fetch_openrouter_models_with_cache")
def test_refresh_openrouter_models_exception(mock_fetch):
    """Test exception during refresh of OpenRouter models"""
    mock_fetch.side_effect = Exception("API error")
    
    success, message = price_query_logic.refresh_openrouter_models()
    
    assert success is False
    assert "Error refreshing OpenRouter models" in message
    mock_fetch.assert_called_once_with()
