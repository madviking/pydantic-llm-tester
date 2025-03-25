"""Configuration utilities for the interactive runner"""

import os
import logging
from pathlib import Path

# Load environment variables
def load_env_file(env_path: str = None) -> bool:
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        
        if env_path:
            load_dotenv(dotenv_path=env_path)
            return True
        else:
            default_paths = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    load_dotenv(dotenv_path=path)
                    logging.info(f"Loaded environment variables from {path}")
                    return True
            
            logging.warning("No .env file found. Please set up API keys manually.")
            return False
    except ImportError:
        logging.warning("python-dotenv package not installed. Cannot load .env file.")
        return False

# Load configuration
def load_config(config_path: str = None):
    """Load configuration from file"""
    from llm_tester.utils.config_manager import load_config as load_cfg
    if config_path:
        print(f"Note: Custom config path {config_path} will be ignored, using default")
    return load_cfg()

# Save configuration
def save_config(config, config_path: str = None):
    """Save configuration to file"""
    from llm_tester.utils.config_manager import save_config as save_cfg
    if config_path:
        print(f"Note: Custom config path {config_path} will be ignored, using default")
    return save_cfg(config)

# Check API keys
def check_api_keys():
    """Check which API keys are available"""
    results = {
        "openai": {
            "available": bool(os.environ.get("OPENAI_API_KEY")),
            "key_name": "OPENAI_API_KEY",
            "value": os.environ.get("OPENAI_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "anthropic": {
            "available": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "key_name": "ANTHROPIC_API_KEY",
            "value": os.environ.get("ANTHROPIC_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "mistral": {
            "available": bool(os.environ.get("MISTRAL_API_KEY")),
            "key_name": "MISTRAL_API_KEY", 
            "value": os.environ.get("MISTRAL_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "google": {
            "available": False,
            "missing": [],
            "keys": {
                "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
                "GOOGLE_PROJECT_ID": os.environ.get("GOOGLE_PROJECT_ID", "")
            },
            "status": "valid"
        }
    }
    
    # Check Google specifically since it needs multiple keys
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    google_project = os.environ.get("GOOGLE_PROJECT_ID")
    
    if not google_creds:
        results["google"]["missing"].append("GOOGLE_APPLICATION_CREDENTIALS")
    elif not os.path.exists(google_creds):
        results["google"]["status"] = "invalid"
        results["google"]["error"] = f"Credentials file not found: {google_creds}"
    
    if not google_project:
        results["google"]["missing"].append("GOOGLE_PROJECT_ID")
    
    results["google"]["available"] = (
        bool(google_creds) and
        bool(google_project) and
        results["google"]["status"] == "valid"
    )
    
    # Check other providers
    for provider in ["openai", "anthropic", "mistral"]:
        key_name = results[provider]["key_name"]
        if not results[provider]["value"]:
            results[provider]["missing"].append(key_name)
            results[provider]["status"] = "missing"
    
    return results
