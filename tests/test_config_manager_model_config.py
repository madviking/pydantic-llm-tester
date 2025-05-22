"""Tests for ConfigManager model configuration feature"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, Mock, MagicMock

from pydantic_llm_tester.utils.config_manager import ConfigManager, fetch_and_save_openrouter_models
from pydantic_llm_tester.llms.llm_registry import LLMRegistry
from pydantic_llm_tester.llms.base import ModelConfig

class TestConfigManagerModelConfig:
    """Tests for ConfigManager with new model configuration"""
    
    def test_check_openrouter_enabled(self):
        """Test that ConfigManager correctly identifies when OpenRouter is enabled"""
        # Create a temporary config file with OpenRouter enabled
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp:
            config = {
                "providers": {
                    "openrouter": {
                        "enabled": True,
                        "default_model": "openrouter:mistral-large-latest"
                    },
                    "openai": {
                        "enabled": True,
                        "default_model": "gpt-4"
                    }
                }
            }
            temp.write(json.dumps(config).encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Initialize ConfigManager with the temp config
            config_manager = ConfigManager(config_path=temp_path, temp_mode=True)
            
            # Test the new method
            assert config_manager.is_openrouter_enabled() == True
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_check_openrouter_disabled(self):
        """Test that ConfigManager correctly identifies when OpenRouter is disabled"""
        # Create a temporary config file with OpenRouter disabled
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp:
            config = {
                "providers": {
                    "openrouter": {
                        "enabled": False,
                        "default_model": "openrouter:mistral-large-latest"
                    },
                    "openai": {
                        "enabled": True,
                        "default_model": "gpt-4"
                    }
                }
            }
            temp.write(json.dumps(config).encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Initialize ConfigManager with the temp config
            config_manager = ConfigManager(config_path=temp_path, temp_mode=True)
            
            # Test the new method
            assert config_manager.is_openrouter_enabled() == False
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_check_openrouter_not_in_config(self):
        """Test that ConfigManager correctly handles when OpenRouter is not in config"""
        # Create a temporary config file without OpenRouter
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp:
            config = {
                "providers": {
                    "openai": {
                        "enabled": True,
                        "default_model": "gpt-4"
                    }
                }
            }
            temp.write(json.dumps(config).encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Initialize ConfigManager with the temp config
            config_manager = ConfigManager(config_path=temp_path, temp_mode=True)
            
            # Test the new method
            assert config_manager.is_openrouter_enabled() == False
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    @patch('pydantic_llm_tester.utils.config_manager.fetch_and_save_openrouter_models')
    def test_fetch_openrouter_models_during_init(self, mock_fetch):
        """Test that OpenRouter models are fetched during ConfigManager initialization if enabled"""
        # Create a temporary config file with OpenRouter enabled
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp:
            config = {
                "providers": {
                    "openrouter": {
                        "enabled": True,
                        "default_model": "openrouter:mistral-large-latest"
                    }
                }
            }
            temp.write(json.dumps(config).encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Initialize ConfigManager with the temp config
            config_manager = ConfigManager(config_path=temp_path, temp_mode=True)
            
            # Verify that fetch_and_save_openrouter_models was called
            mock_fetch.assert_called_once()
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    @patch('pydantic_llm_tester.llms.llm_registry.LLMRegistry.store_provider_models')
    @patch('pydantic_llm_tester.utils.config_manager.fetch_and_save_openrouter_models')
    @patch('pydantic_llm_tester.utils.config_manager.read_json_file')
    def test_openrouter_models_stored_in_registry(self, mock_read_json, mock_fetch, mock_store_models):
        """Test that fetched OpenRouter models are stored in the central registry"""
        # Mock data returned by read_json_file
        mock_models_data = {
            "data": [
                {
                    "id": "openrouter/mistral-large-latest",
                    "name": "Mistral Large (Latest)",
                    "pricing": {
                        "prompt": 0.000008,
                        "completion": 0.000024
                    },
                    "context_length": 32000
                },
                {
                    "id": "openrouter/anthropic/claude-3-opus",
                    "name": "Claude 3 Opus",
                    "pricing": {
                        "prompt": 0.000015,
                        "completion": 0.000075
                    },
                    "context_length": 200000
                }
            ]
        }
        mock_read_json.return_value = mock_models_data
        
        # Create a temporary config file with OpenRouter enabled
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp:
            config = {
                "providers": {
                    "openrouter": {
                        "enabled": True,
                        "default_model": "openrouter:mistral-large-latest"
                    }
                }
            }
            temp.write(json.dumps(config).encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Initialize ConfigManager with the temp config
            config_manager = ConfigManager(config_path=temp_path, temp_mode=True)
            
            # Call the method that would process and store the models
            config_manager.process_openrouter_models()
            
            # Verify that store_provider_models was called with expected data
            mock_store_models.assert_called_once()
            # Check that the call has 'openrouter' as the first argument
            assert mock_store_models.call_args[0][0] == 'openrouter'
            # Check that the second argument is a dictionary (model details)
            assert isinstance(mock_store_models.call_args[0][1], dict)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    def test_parse_provider_model_string(self):
        """Test that ConfigManager correctly parses 'provider:model-name' format"""
        config_manager = ConfigManager(temp_mode=True)
        
        # Test valid model string
        provider, model = config_manager._parse_model_string("openrouter:mistral-large-latest")
        assert provider == "openrouter"
        assert model == "mistral-large-latest"
        
        # Test invalid model string
        with pytest.raises(ValueError):
            config_manager._parse_model_string("invalid-format")
            
    @patch('pydantic_llm_tester.utils.config_manager.ConfigManager.is_provider_enabled')
    @patch('pydantic_llm_tester.llms.llm_registry.LLMRegistry.get_model_details')
    def test_lookup_model_details_from_registry(self, mock_get_model_details, mock_is_provider_enabled):
        """Test that ConfigManager looks up model details from the central registry"""
        # Mock provider to be enabled
        mock_is_provider_enabled.return_value = True
        
        # Mock the model details returned by get_model_details
        mock_model_config = ModelConfig(
            name="openrouter:mistral-large-latest",
            cost_input=0.000008,
            cost_output=0.000024,
            max_input_tokens=32000,
            max_output_tokens=32000
        )
        mock_get_model_details.return_value = mock_model_config
        
        config_manager = ConfigManager(temp_mode=True)
        
        # Call the method to get model details
        model_details = config_manager.get_model_details_from_registry("openrouter:mistral-large-latest")
        
        # Verify that get_model_details was called with expected arguments
        mock_get_model_details.assert_called_once_with("openrouter", "mistral-large-latest")
        
        # Verify that the returned model details match the mock
        assert model_details == mock_model_config
        
    def test_check_disabled_provider_raises_exception(self):
        """Test that using a disabled provider raises an exception"""
        # Create a temporary config file with OpenRouter disabled
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp:
            config = {
                "providers": {
                    "openrouter": {
                        "enabled": False,
                        "default_model": "openrouter:mistral-large-latest"
                    }
                }
            }
            temp.write(json.dumps(config).encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Initialize ConfigManager with the temp config
            config_manager = ConfigManager(config_path=temp_path, temp_mode=True)
            
            # Test that using a disabled provider raises an exception
            with pytest.raises(ValueError) as excinfo:
                config_manager.check_provider_enabled("openrouter")
            
            # Verify the exception message
            assert "Provider 'openrouter' is not enabled" in str(excinfo.value)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)