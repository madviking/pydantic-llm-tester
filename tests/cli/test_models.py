import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from pydantic_llm_tester.cli import app
from pydantic_llm_tester.cli.core import model_config_logic
from pydantic_llm_tester.cli.core import provider_logic

runner = CliRunner()

@pytest.fixture
def mock_provider_config():
    """Fixture providing a mock provider configuration"""
    return {
        "name": "test_provider",
        "api_key_env": "TEST_PROVIDER_API_KEY",
        "base_url": "https://api.test-provider.com",
        "llm_models": [
            {
                "name": "test-model-1",
                "default": True,
                "preferred": False,
                "enabled": True,
                "cost_input": 10.0,
                "cost_output": 20.0,
                "cost_category": "standard",
                "max_input_tokens": 4096,
                "max_output_tokens": 4096
            },
            {
                "name": "test-model-2",
                "default": False,
                "preferred": True,
                "enabled": True,
                "cost_input": 5.0,
                "cost_output": 15.0,
                "cost_category": "cheap",
                "max_input_tokens": 8192,
                "max_output_tokens": 8192
            }
        ]
    }

@pytest.fixture
def mock_model_template():
    """Fixture providing a mock model template"""
    return {
        "name": "",
        "default": False,
        "preferred": False,
        "enabled": True,
        "cost_input": 0.0,
        "cost_output": 0.0,
        "cost_category": "standard",
        "max_input_tokens": 4096,
        "max_output_tokens": 4096
    }

# Test command structure and options
def test_models_list_command_exists():
    """Test that the 'models list' command exists and returns help text"""
    result = runner.invoke(app, ["models", "list", "--help"])
    assert result.exit_code == 0
    assert "List all models for a specific provider" in result.stdout

def test_models_add_command_exists():
    """Test that the 'models add' command exists and returns help text"""
    result = runner.invoke(app, ["models", "add", "--help"])
    assert result.exit_code == 0
    assert "Add a new model to a provider's configuration" in result.stdout

def test_models_edit_command_exists():
    """Test that the 'models edit' command exists and returns help text"""
    result = runner.invoke(app, ["models", "edit", "--help"])
    assert result.exit_code == 0
    assert "Edit an existing model in a provider's configuration" in result.stdout

def test_models_remove_command_exists():
    """Test that the 'models remove' command exists and returns help text"""
    result = runner.invoke(app, ["models", "remove", "--help"])
    assert result.exit_code == 0
    assert "Remove a model from a provider's configuration" in result.stdout

def test_models_set_default_command_exists():
    """Test that the 'models set-default' command exists and returns help text"""
    result = runner.invoke(app, ["models", "set-default", "--help"])
    assert result.exit_code == 0
    assert "Set a model as the default for a provider" in result.stdout

# Test core logic functions
@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.get_provider_config")
def test_models_list(mock_get_config, mock_get_providers, mock_provider_config):
    """Test 'models list' command"""
    mock_get_providers.return_value = ["test_provider"]
    mock_get_config.return_value = mock_provider_config
    
    result = runner.invoke(app, ["models", "list", "test_provider"])
    
    assert result.exit_code == 0
    assert "Models for provider 'test_provider':" in result.stdout
    assert "test-model-1" in result.stdout
    assert "test-model-2" in result.stdout
    assert "Default" in result.stdout
    assert "Preferred" in result.stdout
    mock_get_providers.assert_called_once()
    mock_get_config.assert_called_once_with("test_provider")

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.get_provider_config")
def test_models_list_no_models(mock_get_config, mock_get_providers):
    """Test 'models list' command when provider has no models"""
    mock_get_providers.return_value = ["empty_provider"]
    mock_get_config.return_value = {"name": "empty_provider", "llm_models": []}
    
    result = runner.invoke(app, ["models", "list", "empty_provider"])
    
    assert result.exit_code == 0
    assert "No models found for provider 'empty_provider'" in result.stdout

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
def test_models_list_provider_not_found(mock_get_providers):
    """Test 'models list' command with non-existent provider"""
    mock_get_providers.return_value = ["test_provider"]
    
    result = runner.invoke(app, ["models", "list", "nonexistent"])
    
    assert result.exit_code == 1
    assert "Error: Provider 'nonexistent' not found" in result.stdout

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.add_model_to_provider")
def test_models_add(mock_add_model, mock_get_providers):
    """Test 'models add' command"""
    mock_get_providers.return_value = ["test_provider"]
    mock_add_model.return_value = (True, "Model 'new-model' added to provider 'test_provider' successfully.")
    
    result = runner.invoke(app, [
        "models", "add", "test_provider",
        "--name", "new-model",
        "--cost-input", "5.0",
        "--cost-output", "10.0",
        "--cost-category", "cheap",
        "--max-input", "8192",
        "--max-output", "8192"
    ])
    
    assert result.exit_code == 0
    assert "Model 'new-model' added to provider 'test_provider' successfully" in result.stdout
    mock_get_providers.assert_called_once()
    mock_add_model.assert_called_once_with(
        "test_provider", 
        "new-model", 
        {
            "name": "new-model",
            "default": False,
            "preferred": False,
            "enabled": True,
            "cost_input": 5.0,
            "cost_output": 10.0,
            "cost_category": "cheap",
            "max_input_tokens": 8192,
            "max_output_tokens": 8192
        }
    )

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.add_model_to_provider")
@patch("pydantic_llm_tester.cli.core.model_config_logic.set_default_model")
def test_models_add_as_default(mock_set_default, mock_add_model, mock_get_providers):
    """Test 'models add' command with default flag"""
    mock_get_providers.return_value = ["test_provider"]
    mock_add_model.return_value = (True, "Model 'new-model' added to provider 'test_provider' successfully.")
    mock_set_default.return_value = (True, "Model 'new-model' set as default for provider 'test_provider' successfully.")
    
    result = runner.invoke(app, [
        "models", "add", "test_provider",
        "--name", "new-model",
        "--default",
        "--cost-input", "5.0",
        "--cost-output", "10.0"
    ])
    
    assert result.exit_code == 0
    assert "Model 'new-model' added to provider 'test_provider' successfully" in result.stdout
    mock_add_model.assert_called_once()
    mock_set_default.assert_called_once_with("test_provider", "new-model")

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.get_model_from_provider")
@patch("pydantic_llm_tester.cli.core.model_config_logic.edit_model_in_provider")
def test_models_edit(mock_edit_model, mock_get_model, mock_get_providers):
    """Test 'models edit' command"""
    mock_get_providers.return_value = ["test_provider"]
    mock_get_model.return_value = {
        "name": "test-model",
        "default": False,
        "preferred": False,
        "enabled": True,
        "cost_input": 10.0,
        "cost_output": 20.0,
        "cost_category": "standard",
        "max_input_tokens": 4096,
        "max_output_tokens": 4096
    }
    mock_edit_model.return_value = (True, "Model 'test-model' updated in provider 'test_provider' successfully.")
    
    result = runner.invoke(app, [
        "models", "edit", "test_provider", "test-model",
        "--cost-input", "15.0",
        "--cost-category", "expensive"
    ])
    
    assert result.exit_code == 0
    assert "Model 'test-model' updated in provider 'test_provider' successfully" in result.stdout
    mock_get_providers.assert_called_once()
    mock_get_model.assert_called_once_with("test_provider", "test-model")
    
    # Check that only the specified fields were updated
    expected_config = {
        "name": "test-model",
        "default": False,
        "preferred": False,
        "enabled": True,
        "cost_input": 15.0,  # Updated
        "cost_output": 20.0,
        "cost_category": "expensive",  # Updated
        "max_input_tokens": 4096,
        "max_output_tokens": 4096
    }
    mock_edit_model.assert_called_once_with("test_provider", "test-model", expected_config)

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.remove_model_from_provider")
def test_models_remove(mock_remove_model, mock_get_providers):
    """Test 'models remove' command"""
    mock_get_providers.return_value = ["test_provider"]
    mock_remove_model.return_value = (True, "Model 'test-model' removed from provider 'test_provider' successfully.")
    
    # Simulate user confirming the action
    result = runner.invoke(app, ["models", "remove", "test_provider", "test-model"], input="y\n")
    
    assert result.exit_code == 0
    assert "Model 'test-model' removed from provider 'test_provider' successfully" in result.stdout
    mock_get_providers.assert_called_once()
    mock_remove_model.assert_called_once_with("test_provider", "test-model")

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.remove_model_from_provider")
def test_models_remove_abort(mock_remove_model, mock_get_providers):
    """Test aborting 'models remove' command"""
    mock_get_providers.return_value = ["test_provider"]
    
    # Simulate user aborting the action
    result = runner.invoke(app, ["models", "remove", "test_provider", "test-model"], input="n\n")
    
    assert result.exit_code == 0
    assert "Operation cancelled" in result.stdout
    mock_remove_model.assert_not_called()

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.set_default_model")
def test_models_set_default(mock_set_default, mock_get_providers):
    """Test 'models set-default' command"""
    mock_get_providers.return_value = ["test_provider"]
    mock_set_default.return_value = (True, "Model 'test-model' set as default for provider 'test_provider' successfully.")
    
    result = runner.invoke(app, ["models", "set-default", "test_provider", "test-model"])
    
    assert result.exit_code == 0
    assert "Model 'test-model' set as default for provider 'test_provider' successfully" in result.stdout
    mock_get_providers.assert_called_once()
    mock_set_default.assert_called_once_with("test_provider", "test-model")

# Test the core logic directly
def test_validate_model_config():
    """Test model configuration validation"""
    # Valid model config
    valid_config = {
        "name": "test-model",
        "default": False,
        "preferred": False,
        "enabled": True,
        "cost_input": 10.0,
        "cost_output": 20.0,
        "cost_category": "standard",
        "max_input_tokens": 4096,
        "max_output_tokens": 4096
    }
    
    success, message = model_config_logic.validate_model_config(valid_config)
    assert success is True
    assert "valid" in message.lower()
    
    # Invalid model config (missing required field)
    invalid_config = {
        "name": "test-model",
        "default": False,
        "preferred": False,
        "enabled": True,
        # Missing cost_input
        "cost_output": 20.0,
        "cost_category": "standard",
        "max_input_tokens": 4096,
        "max_output_tokens": 4096
    }
    
    with patch("pydantic_llm_tester.cli.core.model_config_logic.ModelConfig") as mock_model_config:
        mock_model_config.side_effect = Exception("Missing required field")
        success, message = model_config_logic.validate_model_config(invalid_config)
        assert success is False
        assert "invalid" in message.lower()

def test_add_model_to_provider():
    """Test adding a model to a provider"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock provider config file
        config_path = os.path.join(tmpdir, "config.json")
        provider_config = {
            "name": "test_provider",
            "api_key_env": "TEST_PROVIDER_API_KEY",
            "llm_models": []
        }
        
        with open(config_path, "w") as f:
            json.dump(provider_config, f)
        
        # Mock the get_provider_config_path function
        with patch("pydantic_llm_tester.cli.core.model_config_logic.get_provider_config_path") as mock_get_path, \
             patch("pydantic_llm_tester.cli.core.model_config_logic.validate_model_config") as mock_validate, \
             patch("pydantic_llm_tester.cli.core.model_config_logic.reset_caches") as mock_reset:
            
            mock_get_path.return_value = config_path
            mock_validate.return_value = (True, "Model configuration is valid.")
            
            # Add a new model
            model_config = {
                "name": "new-model",
                "default": False,
                "preferred": False,
                "enabled": True,
                "cost_input": 5.0,
                "cost_output": 10.0,
                "cost_category": "cheap",
                "max_input_tokens": 8192,
                "max_output_tokens": 8192
            }
            
            success, message = model_config_logic.add_model_to_provider("test_provider", "new-model", model_config)
            
            assert success is True
            assert "added" in message.lower()
            mock_reset.assert_called_once()
            
            # Verify the model was added to the config file
            with open(config_path, "r") as f:
                updated_config = json.load(f)
                
            assert len(updated_config["llm_models"]) == 1
            assert updated_config["llm_models"][0]["name"] == "new-model"
            assert updated_config["llm_models"][0]["cost_input"] == 5.0

def test_edit_model_in_provider():
    """Test editing a model in a provider"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock provider config file with an existing model
        config_path = os.path.join(tmpdir, "config.json")
        provider_config = {
            "name": "test_provider",
            "api_key_env": "TEST_PROVIDER_API_KEY",
            "llm_models": [
                {
                    "name": "existing-model",
                    "default": False,
                    "preferred": False,
                    "enabled": True,
                    "cost_input": 10.0,
                    "cost_output": 20.0,
                    "cost_category": "standard",
                    "max_input_tokens": 4096,
                    "max_output_tokens": 4096
                }
            ]
        }
        
        with open(config_path, "w") as f:
            json.dump(provider_config, f)
        
        # Mock the get_provider_config_path function
        with patch("pydantic_llm_tester.cli.core.model_config_logic.get_provider_config_path") as mock_get_path, \
             patch("pydantic_llm_tester.cli.core.model_config_logic.validate_model_config") as mock_validate, \
             patch("pydantic_llm_tester.cli.core.model_config_logic.reset_caches") as mock_reset:
            
            mock_get_path.return_value = config_path
            mock_validate.return_value = (True, "Model configuration is valid.")
            
            # Edit the existing model
            updated_config = {
                "name": "existing-model",
                "default": True,
                "preferred": True,
                "enabled": True,
                "cost_input": 15.0,
                "cost_output": 25.0,
                "cost_category": "expensive",
                "max_input_tokens": 8192,
                "max_output_tokens": 8192
            }
            
            success, message = model_config_logic.edit_model_in_provider("test_provider", "existing-model", updated_config)
            
            assert success is True
            assert "updated" in message.lower()
            mock_reset.assert_called_once()
            
            # Verify the model was updated in the config file
            with open(config_path, "r") as f:
                updated_config = json.load(f)
                
            assert len(updated_config["llm_models"]) == 1
            assert updated_config["llm_models"][0]["cost_input"] == 15.0
            assert updated_config["llm_models"][0]["cost_category"] == "expensive"
            assert updated_config["llm_models"][0]["default"] is True

# Test error handling
@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.get_provider_config")
def test_models_list_config_not_found(mock_get_config, mock_get_providers):
    """Test 'models list' command when provider config cannot be loaded"""
    mock_get_providers.return_value = ["test_provider"]
    mock_get_config.return_value = None
    
    result = runner.invoke(app, ["models", "list", "test_provider"])
    
    assert result.exit_code == 1
    assert "Error: Could not load configuration for provider 'test_provider'" in result.stdout

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.add_model_to_provider")
def test_models_add_failure(mock_add_model, mock_get_providers):
    """Test 'models add' command failure"""
    mock_get_providers.return_value = ["test_provider"]
    mock_add_model.return_value = (False, "Model 'new-model' already exists for provider 'test_provider'.")
    
    result = runner.invoke(app, [
        "models", "add", "test_provider",
        "--name", "new-model",
        "--cost-input", "5.0",
        "--cost-output", "10.0"
    ])
    
    assert result.exit_code == 1
    assert "Model 'new-model' already exists for provider 'test_provider'" in result.stdout

@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.get_model_from_provider")
def test_models_edit_model_not_found(mock_get_model, mock_get_providers):
    """Test 'models edit' command when model is not found"""
    mock_get_providers.return_value = ["test_provider"]
    mock_get_model.return_value = None
    
    result = runner.invoke(app, [
        "models", "edit", "test_provider", "nonexistent-model",
        "--cost-input", "15.0"
    ])
    
    assert result.exit_code == 1
    assert "Error: Model 'nonexistent-model' not found in provider 'test_provider'" in result.stdout

# Test interactive mode
@patch("pydantic_llm_tester.cli.core.provider_logic.get_discovered_providers")
@patch("pydantic_llm_tester.cli.core.model_config_logic.get_model_template")
@patch("pydantic_llm_tester.cli.core.model_config_logic.add_model_to_provider")
def test_models_add_interactive(mock_add_model, mock_get_template, mock_get_providers, mock_model_template):
    """Test 'models add' command in interactive mode"""
    mock_get_providers.return_value = ["test_provider"]
    mock_get_template.return_value = mock_model_template
    mock_add_model.return_value = (True, "Model 'interactive-model' added to provider 'test_provider' successfully.")
    
    # Simulate user input for interactive mode
    input_values = [
        "interactive-model",  # Model name
        "n",                  # Set as default? (no)
        "y",                  # Mark as preferred? (yes)
        "y",                  # Enable model? (yes)
        "7.5",                # Cost per 1M input tokens
        "12.5",               # Cost per 1M output tokens
        "2",                  # Cost category (standard)
        "16384",              # Maximum input tokens
        "16384"               # Maximum output tokens
    ]
    
    result = runner.invoke(app, ["models", "add", "test_provider", "--interactive"], input="\n".join(input_values))
    
    assert result.exit_code == 0
    assert "Model 'interactive-model' added to provider 'test_provider' successfully" in result.stdout
    mock_get_providers.assert_called_once()
    mock_get_template.assert_called_once()
    
    # Check that the model config was created correctly from interactive input
    expected_config = {
        "name": "interactive-model",
        "default": False,
        "preferred": True,
        "enabled": True,
        "cost_input": 7.5,
        "cost_output": 12.5,
        "cost_category": "standard",
        "max_input_tokens": 16384,
        "max_output_tokens": 16384
    }
    mock_add_model.assert_called_once_with("test_provider", "interactive-model", expected_config)