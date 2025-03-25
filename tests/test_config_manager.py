"""
Tests for configuration manager
"""

import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path

from llm_tester.utils.config_manager import (
    load_config, save_config, get_enabled_providers, 
    get_provider_model, get_test_setting, update_test_setting,
    DEFAULT_CONFIG, get_config_path
)


@pytest.fixture
def mock_config_path(monkeypatch):
    """Create a temporary config file"""
    temp_dir = tempfile.mkdtemp()
    temp_config = os.path.join(temp_dir, 'config.json')
    
    # Mock the config path function to use our temp file
    def mock_get_config_path():
        return temp_config
    
    monkeypatch.setattr('llm_tester.utils.config_manager.get_config_path', mock_get_config_path)
    
    yield temp_config
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_load_config_default(mock_config_path):
    """Test loading default config when no file exists"""
    # Make sure config file doesn't exist
    if os.path.exists(mock_config_path):
        os.remove(mock_config_path)
        
    config = load_config()
    assert config == DEFAULT_CONFIG
    assert os.path.exists(mock_config_path)


def test_save_and_load_config(mock_config_path):
    """Test saving and loading a config"""
    test_config = {
        "test": "value",
        "nested": {
            "key": "value"
        }
    }
    
    save_config(test_config)
    assert os.path.exists(mock_config_path)
    
    loaded_config = load_config()
    assert loaded_config == test_config


def test_get_enabled_providers(mock_config_path):
    """Test getting enabled providers"""
    test_config = {
        "providers": {
            "openai": {
                "enabled": True,
                "default_model": "test-model"
            },
            "anthropic": {
                "enabled": False,
                "default_model": "test-model"
            },
            "mock": {
                "enabled": True
            }
        }
    }
    
    save_config(test_config)
    enabled = get_enabled_providers()
    
    assert "openai" in enabled
    assert "anthropic" not in enabled
    assert "mock" in enabled
    assert enabled["openai"]["default_model"] == "test-model"


def test_get_provider_model(mock_config_path):
    """Test getting a provider's model"""
    test_config = {
        "providers": {
            "openai": {
                "enabled": True,
                "default_model": "gpt-4"
            },
            "anthropic": {
                "enabled": True,
                "default_model": "claude-3"
            }
        }
    }
    
    save_config(test_config)
    
    assert get_provider_model("openai") == "gpt-4"
    assert get_provider_model("anthropic") == "claude-3"
    assert get_provider_model("nonexistent") is None


def test_get_test_setting(mock_config_path):
    """Test getting a test setting"""
    test_config = {
        "test_settings": {
            "output_dir": "test_output",
            "save_optimized_prompts": True
        }
    }
    
    save_config(test_config)
    
    assert get_test_setting("output_dir") == "test_output"
    assert get_test_setting("save_optimized_prompts") is True
    assert get_test_setting("nonexistent") is None
    assert get_test_setting("nonexistent", "default") == "default"


def test_update_test_setting(mock_config_path):
    """Test updating a test setting"""
    test_config = {
        "test_settings": {
            "output_dir": "test_output"
        }
    }
    
    save_config(test_config)
    
    # Update existing setting
    update_test_setting("output_dir", "new_output")
    assert get_test_setting("output_dir") == "new_output"
    
    # Add new setting
    update_test_setting("new_setting", "value")
    assert get_test_setting("new_setting") == "value"
    
    # Create test_settings if it doesn't exist
    save_config({})  # Empty config
    update_test_setting("output_dir", "test_output")
    assert get_test_setting("output_dir") == "test_output"