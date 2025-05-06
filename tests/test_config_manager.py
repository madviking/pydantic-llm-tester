import os
import json
import pytest
from unittest.mock import patch
from src.utils.config_manager import ConfigManager

def test_load_config_creates_default_if_not_exists(temp_config):
    """Test that ConfigManager creates default config if file doesn't exist"""
    assert os.path.exists(temp_config.config_path)
    assert temp_config.config == {
        "providers": {
            "openai": {
                "enabled": True,
                "default_model": "gpt-4",
                "api_key": None
            },
            "anthropic": {
                "enabled": True,
                "default_model": "claude-3-opus",
                "api_key": None
            },
            "mock": {
                "enabled": False,
                "default_model": "mock-model"
            }
        },
        "test_settings": {
            "output_dir": "test_results",
            "save_optimized_prompts": True,
            "default_modules": ["job_ads"]
        },
        "py_models": {}
    }

def test_save_config_writes_to_file(tmp_path):
    """Test that save_config writes config to file"""
    config_path = os.path.join(tmp_path, "config.json")
    config = ConfigManager(config_path)
    test_config = {"test": "value"}
    config.config = test_config
    config.save_config()
    with open(config_path) as f:
        assert json.load(f) == test_config

def test_get_enabled_providers_returns_only_enabled():
    """Test get_enabled_providers returns only enabled providers"""
    config = ConfigManager()
    config.config = {
        "providers": {
            "enabled": {"enabled": True},
            "disabled": {"enabled": False}
        }
    }
    providers = config.get_enabled_providers()
    assert "enabled" in providers
    assert "disabled" not in providers

def test_get_provider_model_returns_model():
    """Test get_provider_model returns model for provider"""
    config = ConfigManager()
    config.config = {
        "providers": {
            "test_provider": {"default_model": "test_model"}
        }
    }
    assert config.get_provider_model("test_provider") == "test_model"

def test_get_test_setting_returns_value():
    """Test get_test_setting returns setting value"""
    config = ConfigManager()
    config.config = {
        "test_settings": {"test_setting": "value"}
    }
    assert config.get_test_setting("test_setting") == "value"

def test_update_test_setting_updates_config():
    """Test update_test_setting updates test settings"""
    config = ConfigManager()
    config.update_test_setting("new_setting", "value")
    assert config.config["test_settings"]["new_setting"] == "value"
