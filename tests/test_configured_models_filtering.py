"""
Tests for the configured models filtering functionality.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.utils.config_manager import ConfigManager
from src.pydantic_llm_tester.llms.llm_registry import LLMRegistry, get_all_model_details
from src.pydantic_llm_tester.llms.base import ModelConfig

# Sample test configuration
TEST_CONFIG = {
    "providers": {
        "openai": {
            "enabled": True,
            "default_model": "gpt-4"
        },
        "anthropic": {
            "enabled": True,
            "default_model": "claude-3-opus"
        },
        "disabled-provider": {
            "enabled": False,
            "default_model": "disabled-model"
        }
    },
    "bridge": {
        "default_provider": "openai",
        "default_model": "gpt-4",
        "secondary_provider": "anthropic",
        "secondary_model": "claude-3-opus"
    },
    "py_models": {
        "job_ads": {
            "enabled": True,
            "llm_models": [
                "openai:gpt-4o",
                "anthropic:claude-3-haiku"
            ]
        },
        "disabled_model": {
            "enabled": False,
            "llm_models": [
                "openai:disabled-model"
            ]
        }
    }
}

@pytest.fixture
def mock_config_manager():
    """Create a ConfigManager with test configuration."""
    with patch('src.pydantic_llm_tester.utils.config_manager.ConfigManager._load_config') as mock_load:
        mock_load.return_value = TEST_CONFIG
        config_manager = ConfigManager()
        yield config_manager

def test_get_configured_models(mock_config_manager):
    """Test that get_configured_models correctly identifies configured models."""
    configured_models = mock_config_manager.get_configured_models()
    
    # Check that all expected models are in the result
    expected_models = {
        "openai:gpt-4",            # Default model for openai
        "anthropic:claude-3-opus",  # Default model for anthropic and secondary model in bridge
        "openai:gpt-4o",           # From py_models.job_ads.llm_models
        "anthropic:claude-3-haiku"  # From py_models.job_ads.llm_models
    }
    
    # Convert configured_models to a set for easier comparison
    configured_models_set = set(configured_models)
    
    # Check that all expected models are in the result
    for model in expected_models:
        assert model in configured_models_set, f"Expected model {model} not found in configured models"
    
    # Check that no unexpected models are in the result
    assert len(configured_models) == len(expected_models), \
        f"Expected {len(expected_models)} models, got {len(configured_models)}"
    
    # Disabled provider's model should not be included
    assert "disabled-provider:disabled-model" not in configured_models_set, \
        "Model from disabled provider should not be included"
    
    # Disabled py_model's models should not be included
    assert "openai:disabled-model" not in configured_models_set, \
        "Model from disabled py_model should not be included"

@pytest.fixture
def mock_registry_with_models():
    """Create a mock LLMRegistry with test models."""
    registry = LLMRegistry()
    
    # Create model data for testing
    provider1_models = {
        "model1": ModelConfig(
            name="model1",
            provider="provider1",
            cost_input=1.0,
            cost_output=2.0,
            enabled=True,
            default=True,
            preferred=False,
            cost_category="standard",
            max_input_tokens=1000,
            max_output_tokens=2000
        ),
        "model2": ModelConfig(
            name="model2",
            provider="provider1",
            cost_input=3.0,
            cost_output=4.0,
            enabled=True,
            default=False,
            preferred=True,
            cost_category="premium",
            max_input_tokens=3000,
            max_output_tokens=4000
        ),
        "model3": ModelConfig(
            name="model3",
            provider="provider1",
            cost_input=5.0,
            cost_output=6.0,
            enabled=False,  # Disabled model
            default=False,
            preferred=False,
            cost_category="economy",
            max_input_tokens=5000,
            max_output_tokens=6000
        )
    }
    
    provider2_models = {
        "model4": ModelConfig(
            name="model4",
            provider="provider2",
            cost_input=7.0,
            cost_output=8.0,
            enabled=True,
            default=True,
            preferred=False,
            cost_category="standard",
            max_input_tokens=7000,
            max_output_tokens=8000
        )
    }
    
    # Store model data in the registry
    registry.store_provider_models("provider1", provider1_models)
    registry.store_provider_models("provider2", provider2_models)
    
    return registry

@patch('src.pydantic_llm_tester.utils.config_manager.ConfigManager')
def test_get_all_model_details_with_configured_filter(mock_config_manager_class, mock_registry_with_models):
    """Test that get_all_model_details filters to configured models when requested."""
    # Setup
    mock_config_manager = MagicMock()
    mock_config_manager_class.return_value = mock_config_manager
    
    # Configure mock to return a list of configured models
    mock_config_manager.get_configured_models.return_value = ["provider1:model1"]
    
    # Get only configured models
    with patch('src.pydantic_llm_tester.llms.llm_registry.LLMRegistry.get_instance', return_value=mock_registry_with_models):
        configured_models = get_all_model_details(only_configured=True)
    
    # Should only return the one configured model
    assert len(configured_models) == 1
    assert configured_models[0].name == "model1"
    assert configured_models[0].provider == "provider1"
    
    # Verify the config manager was called to get configured models
    mock_config_manager.get_configured_models.assert_called_once()

@patch('src.pydantic_llm_tester.utils.config_manager.ConfigManager')
def test_get_all_model_details_without_filter(mock_config_manager_class, mock_registry_with_models):
    """Test that get_all_model_details returns all enabled models when not filtering."""
    # Setup mock (shouldn't be called)
    mock_config_manager = MagicMock()
    mock_config_manager_class.return_value = mock_config_manager
    
    # Get all enabled models (regardless of configuration)
    with patch('src.pydantic_llm_tester.llms.llm_registry.LLMRegistry.get_instance', return_value=mock_registry_with_models):
        all_models = get_all_model_details(only_configured=False)
    
    # Should return all 3 enabled models (model1, model2, model4)
    assert len(all_models) == 3
    model_names = {model.name for model in all_models}
    assert model_names == {"model1", "model2", "model4"}
    
    # Config manager should not have been called to get configured models
    mock_config_manager.get_configured_models.assert_not_called()