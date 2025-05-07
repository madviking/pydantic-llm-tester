import pytest
import os
from dotenv import load_dotenv
import logging

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
    from pydantic_llm_tester.llms import create_provider, get_available_providers
    from pydantic_llm_tester.py_models.integration_tests import IntegrationTest
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
    "google": "gemini-1.5-flash-latest", # Changed to a potentially more available model
    "mistral": "mistral-tiny", # Or another available Mistral model
    # Add other providers and their cheap/fast py_models here
}

# Discover available providers (excluding mock, pydantic_ai, and external providers for now)
# Load external provider definitions to filter them out
external_providers_config = {}
try:
    from pydantic_llm_tester.llms import load_external_providers
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
    test_cases = IntegrationTest.get_test_cases()
    assert len(test_cases) > 0, "Could not find the integration test case."
    test_case = test_cases[0]

    # 2. Check for required environment variables and instantiate Provider
    logger.info(f"Checking environment variables and instantiating provider: {provider_name}")

    # Check for specific environment variables based on provider
    if provider_name == "google":
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_creds and not google_api_key:
            pytest.skip("Google credentials (GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_API_KEY) not found in environment.")
    elif provider_name == "mistral":
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            pytest.skip("Mistral API key (MISTRAL_API_KEY) not found in environment.")
    # Add checks for other providers if needed (Anthropic, OpenAI, OpenRouter are passing, so likely not needed)


    # Load the provider config
    from pydantic_llm_tester.llms import load_provider_config, reset_caches # Import load_provider_config and reset_caches

    # Reset caches to ensure the latest config is loaded
    reset_caches()

    config = load_provider_config(provider_name)
    assert config is not None, f"Failed to load config for provider {provider_name}."

    # Instantiate the provider, passing the loaded config
    provider = create_provider(provider_name, config=config)
    assert provider is not None, f"Failed to create provider instance for {provider_name}."
    # Instead of checking provider.client, check if a default model can be retrieved
    try:
        default_model = provider.get_default_model()
        assert default_model is not None, f"Could not retrieve default model for {provider_name}. Check config and initialization."
        logger.info(f"Provider {provider_name} instantiated and default model '{default_model}' retrieved successfully.")
    except Exception as e:
        pytest.fail(f"Provider {provider_name} failed to initialize or retrieve default model: {e}")

    # 3. Prepare Test Call Data
    with open(test_case['prompt_path'], 'r') as f:
        test_prompt = f.read()
    with open(test_case['source_path'], 'r') as f:
        test_source = f.read() # Although not used by prompt, load it for completeness

    # Use a specific cheap/fast model for this integration test if defined,
    # otherwise let the provider use its default.
    test_model_name = INTEGRATION_TEST_MODELS.get(provider_name)

    # Explicitly set model name for Google to troubleshoot
    if provider_name == "google":
         test_model_name = "gemini-1.5-flash-latest"
         logger.info(f"Explicitly setting Google model to: {test_model_name}")


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
