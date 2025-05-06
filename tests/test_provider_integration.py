import pytest
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Configure logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load .env file ---
# Load environment variables for API keys needed by providers
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_dotenv_path = os.path.join(_project_root, '.env')
if os.path.exists(_dotenv_path):
    load_dotenv(dotenv_path=_dotenv_path, override=True)
    logger.info(f"Integration test loaded environment variables from: {_dotenv_path}")
else:
    logger.warning(f"Integration test: Default .env file not found at {_dotenv_path}. API keys might be missing.")

# --- Imports for the Test ---
try:
    from src.llms.provider_factory import create_provider, get_available_providers
    from src.py_models.integration_test.model import IntegrationTestModel
    from openai import APIError # Import specific error for catching potential issues
    PROVIDER_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import provider components for integration test: {e}")
    PROVIDER_COMPONENTS_AVAILABLE = False
    pytest.skip(f"Failed to import required components: {e}", allow_module_level=True)


# --- Test Setup ---

# Define cheap/fast py_models for each provider (adjust as needed)
# These are just suggestions; actual availability/cost may vary.
# Ensure the corresponding provider config.json includes these py_models.
INTEGRATION_TEST_MODELS = {
    "openai": "gpt-3.5-turbo",
    "anthropic": "claude-3-haiku-20240307",
    "openrouter": "mistralai/mistral-7b-instruct:free", # Use the free tier
    "google": "gemini-1.0-pro", # Or another available Gemini model
    "mistral": "mistral-tiny", # Or another available Mistral model
    # Add other providers and their cheap/fast py_models here
}

# Discover available providers (excluding mock, pydantic_ai, and external providers for now)
# Load external provider definitions to filter them out
external_providers_config = {}
try:
    from src.llms.provider_factory import load_external_providers
    external_providers_config = load_external_providers()
except ImportError:
    logger.warning("Could not import load_external_providers to filter external providers.")

available_providers = [
    p for p in get_available_providers()
    if p != 'mock' and p != 'pydantic_ai' and p not in external_providers_config
]
logger.info(f"Running integration tests for providers: {available_providers}")


# --- Test Function ---

@pytest.mark.integration # Mark as integration test
@pytest.mark.parametrize("provider_name", available_providers)
def test_provider_live_api_call(provider_name: str):
    """
    Performs a small, live API call for each available provider to verify
    basic connectivity, authentication, and response structure.
    """
    # .env loading is now handled by conftest.py

    logger.info(f"--- Starting live integration test for provider: {provider_name} ---")

    # 1. Get the simple test case
    test_cases = IntegrationTestModel.get_test_cases()
    assert len(test_cases) > 0, "Could not find the integration test case."
    test_case = test_cases[0]

    # 2. Instantiate Provider
    logger.info(f"Instantiating provider: {provider_name}")
    provider = create_provider(provider_name)
    assert provider is not None, f"Failed to create provider instance for {provider_name}."
    assert provider.client is not None, f"Provider client for {provider_name} failed to initialize. Check API key and config."
    logger.info(f"Provider {provider_name} instantiated successfully.")

    # 3. Prepare Test Call Data
    with open(test_case['prompt_path'], 'r') as f:
        test_prompt = f.read()
    with open(test_case['source_path'], 'r') as f:
        test_source = f.read() # Although not used by prompt, load it for completeness

    # Use a specific cheap/fast model for this integration test if defined,
    # otherwise let the provider use its default.
    test_model_name = INTEGRATION_TEST_MODELS.get(provider_name)
    if not test_model_name:
        test_model_name = provider.get_default_model()
        logger.warning(f"No specific integration test model defined for {provider_name}, using provider default: {test_model_name}")

    assert test_model_name is not None, f"Could not determine a model to use for provider {provider_name}"

    # Get the model config (needed for _call_llm_api)
    # Note: This assumes the test model is defined in the provider's config
    model_config = provider.get_model_config(test_model_name)
    if not model_config:
         # If using provider default, it should exist. If using specific test model,
         # it MUST be added to the provider's config.json.
         pytest.fail(f"Model config for '{test_model_name}' not found in {provider_name}'s config.json.")

    logger.info(f"Attempting API call to provider '{provider_name}' using model: {test_model_name}")

    # 4. Make Live API Call
    response_text = None
    usage_data = None
    error = None
    try:
        # Directly call _call_llm_api for this basic test
        response_text, usage_data = provider._call_llm_api(
            prompt=test_prompt,
            system_prompt=provider.config.system_prompt if provider.config else "You are a test assistant.",
            model_name=test_model_name, # Use the actual model name from config
            model_config=model_config
        )
        logger.info(f"API call to {provider_name} successful.")
        logger.info(f"Response Text (excerpt): {response_text[:100]}...")
        logger.info(f"Usage Data: {usage_data}")

    except (APIError, ValueError) as e:
        logger.error(f"API call to {provider_name} failed: {e}", exc_info=True)
        error = e

    # 5. Assert Basic Success Criteria
    assert error is None, f"API call to {provider_name} raised an exception: {error}"
    assert isinstance(response_text, str), f"Response text from {provider_name} should be a string."
    # Allow empty string as some py_models might just return {} which stringifies
    # assert len(response_text) > 0, f"Response text from {provider_name} should not be empty."
    assert isinstance(usage_data, dict), f"Usage data from {provider_name} should be a dictionary."
    # Optional: Check for token keys, but some APIs might not return them reliably
    # assert "prompt_tokens" in usage_data, f"Usage data from {provider_name} missing 'prompt_tokens'."
    # assert "completion_tokens" in usage_data, f"Usage data from {provider_name} missing 'completion_tokens'."
    # assert "total_tokens" in usage_data, f"Usage data from {provider_name} missing 'total_tokens'."

    # Basic check if the response looks like the expected JSON structure
    assert '"animal":' in response_text.lower(), f"Response from {provider_name} doesn't contain expected JSON key 'animal'."

    logger.info(f"--- Live integration test for provider: {provider_name} completed successfully. ---")
