import pytest
import os
from unittest.mock import patch, MagicMock, ANY
from typing import Any # Import Any
import importlib

# Mock base classes from the project if they are not directly importable in tests
# This avoids complex path manipulation in the test file itself
try:
    from src.llms.base import BaseLLM, ProviderConfig, ModelConfig
    from src.utils.cost_manager import UsageData
except ImportError:
    # Define dummy base classes if imports fail (e.g., running tests standalone)
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class BaseLLM:
        def __init__(self, config=None):
            self.config = config
            self.name = config.name if config else 'mock'
            self.logger = MagicMock()
        def get_api_key(self):
            return os.environ.get(self.config.env_key) if self.config else None
    class ProviderConfig(BaseModel): pass
    class ModelConfig(BaseModel): pass
    class UsageData(BaseModel): pass

# Import the actual provider
try:
    from src.llms.openrouter.provider import OpenRouterProvider
except ImportError as e:
    # If the provider itself can't be imported, skip all tests in this file
    pytest.skip(f"Could not import OpenRouterProvider: {e}", allow_module_level=True)


# --- Test Setup ---

# Use importlib to check for openai library availability directly in skipif
openai_spec = importlib.util.find_spec("openai")
pytestmark = pytest.mark.skipif(openai_spec is None, reason="openai library not installed")

# Import openai components only if available (needed for dummy class definitions later)
if openai_spec:
    from openai import OpenAI, APIError
    from openai.types.chat import ChatCompletion, ChatCompletionMessage # Use ChatCompletionMessage
    from openai.types.chat.chat_completion import Choice # Choice is still here
    from openai.types.completion_usage import CompletionUsage
else:
    # Define dummy classes if openai is not installed
    class OpenAI: pass
    class APIError(Exception): pass
    class ChatCompletion: pass
    class Choice: pass
    class ChatCompletionMessage: pass # Adjusted dummy class name
    class CompletionUsage: pass

# (Dummy OpenRouterProvider class removed)

# --- Fixtures ---

@pytest.fixture
def mock_provider_config():
    """Provides a mock ProviderConfig for OpenRouter."""
    return ProviderConfig(
        name="openrouter",
        provider_type="openrouter",
        env_key="TEST_OPENROUTER_API_KEY",
        env_key_secret=None,
        system_prompt="Test system prompt",
        llm_models=[
            ModelConfig(
                name="openrouter/test-model",
                default=True,
                preferred=True,
                cost_input=1.0,
                cost_output=2.0,
                max_input_tokens=4000,
                max_output_tokens=1000
            )
        ]
    )

@pytest.fixture
def mock_model_config():
    """Provides a mock ModelConfig."""
    return ModelConfig(
        name="openrouter/test-model",
        default=True,
        preferred=True,
        cost_input=1.0,
        cost_output=2.0,
        max_input_tokens=4000,
        max_output_tokens=1000
    )

# --- Test Cases ---

@patch.dict(os.environ, {"TEST_OPENROUTER_API_KEY": "fake-key"}, clear=True)
@patch('src.llms.openrouter.provider.OpenAI') # Patch OpenAI within the provider module
@patch('src.llms.openrouter.provider.logging.getLogger') # Patch getLogger for this test too
def test_openrouter_provider_init_success(mock_get_logger, mock_openai_class, mock_provider_config):
    """Test successful initialization of OpenRouterProvider."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger # Make getLogger return our mock
    mock_client_instance = MagicMock()
    mock_openai_class.return_value = mock_client_instance # Return mock instance when OpenAI() is called

    provider = OpenRouterProvider(config=mock_provider_config)

    assert provider.client is not None
    mock_openai_class.assert_called_once_with(
        api_key="fake-key",
        base_url="https://openrouter.ai/api/v1",
        default_headers=ANY # Check that headers are passed, specific values checked elsewhere if needed
    )
    # Assert on the mocked logger instance
    mock_logger.info.assert_called_with("OpenRouter client initialized successfully.")


@patch.dict(os.environ, {}, clear=True) # No API key
@patch('src.llms.openrouter.provider.OpenAI') # Patch OpenAI within the provider module
@patch('src.llms.openrouter.provider.logging.getLogger') # Patch getLogger
def test_openrouter_provider_init_no_api_key(mock_get_logger, mock_openai_class, mock_provider_config):
    """Test initialization failure when API key is missing."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger # Make getLogger return our mock

    provider = OpenRouterProvider(config=mock_provider_config)

    assert provider.client is None
    mock_openai_class.assert_not_called()
    # Assert on the mocked logger instance
    mock_logger.warning.assert_called_with(
        f"No API key found for OpenRouter. Set the {mock_provider_config.env_key} environment variable."
    )


@patch.dict(os.environ, {"TEST_OPENROUTER_API_KEY": "fake-key"}, clear=True)
@patch('src.llms.openrouter.provider.OpenAI') # Patch OpenAI within the provider module
def test_openrouter_provider_call_llm_api_success(mock_openai_class, mock_provider_config, mock_model_config):
    """Test successful _call_llm_api call."""
    # Mock the response structure from openai.chat.completions.create
    mock_completion = ChatCompletion(
        id='chatcmpl-test',
        choices=[
            Choice(
                finish_reason='stop',
                index=0,
                # Use ChatCompletionMessage for the mock structure
                message=ChatCompletionMessage(content='Test response', role='assistant', function_call=None, tool_calls=None),
                logprobs=None
            )
        ],
        created=1677652288,
        model=mock_model_config.name,
        object='chat.completion',
        system_fingerprint='fp_test',
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=10, total_tokens=15)
    )

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_openai_class.return_value = mock_client_instance

    provider = OpenRouterProvider(config=mock_provider_config)
    assert provider.client is not None # Ensure client was initialized

    prompt = "User prompt"
    system_prompt = "System instruction"

    response_text, usage_data = provider._call_llm_api(
        prompt=prompt,
        system_prompt=system_prompt,
        model_name=mock_model_config.name,
        model_config=mock_model_config
    )

    assert response_text == "Test response"
    assert usage_data == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
    mock_client_instance.chat.completions.create.assert_called_once_with(
        model=mock_model_config.name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=mock_model_config.max_output_tokens,
        temperature=0.1
    )


@patch.dict(os.environ, {"TEST_OPENROUTER_API_KEY": "fake-key"}, clear=True)
@patch('src.llms.openrouter.provider.OpenAI') # Patch OpenAI within the provider module
@patch('src.llms.openrouter.provider.logging.getLogger') # Patch getLogger here too
def test_openrouter_provider_call_llm_api_error(mock_get_logger, mock_openai_class, mock_provider_config, mock_model_config):
    """Test error handling during _call_llm_api call."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger # Make getLogger return our mock
    mock_client_instance = MagicMock()
    # Simulate an API error - Provide required arguments for APIError, including status_code
    mock_error = APIError(
        "API Error Message",
        request=MagicMock(), # Mock the request object
        body={"error": {"message": "API Error Message", "code": 401}} # Provide a mock body
    )
    # Add status_code attribute to the mock error instance
    mock_error.status_code = 401
    mock_client_instance.chat.completions.create.side_effect = mock_error
    mock_openai_class.return_value = mock_client_instance

    provider = OpenRouterProvider(config=mock_provider_config)
    assert provider.client is not None

    prompt = "User prompt"
    system_prompt = "System instruction"

    # Adjust the expected error message to match what the provider raises
    expected_error_msg = r"OpenRouter API Error \(401\): API Error Message" # Use regex for status code
    with pytest.raises(ValueError, match=expected_error_msg):
        provider._call_llm_api(
            prompt=prompt,
            system_prompt=system_prompt,
            model_name=mock_model_config.name,
            model_config=mock_model_config
        )
    # Assert the logger call on the mocked logger instance
    mock_logger.error.assert_called_with("OpenRouter API error: Status=401, Message=API Error Message")


@patch.dict(os.environ, {}, clear=True) # No API key
@patch('src.llms.openrouter.provider.OpenAI') # Patch OpenAI within the provider module
def test_openrouter_provider_call_llm_api_no_client(mock_openai_class, mock_provider_config, mock_model_config):
    """Test calling _call_llm_api when client is not initialized."""
    provider = OpenRouterProvider(config=mock_provider_config)
    assert provider.client is None # Ensure client is None

    prompt = "User prompt"
    system_prompt = "System instruction"

    with pytest.raises(ValueError, match="OpenRouter client not initialized"):
        provider._call_llm_api(
            prompt=prompt,
            system_prompt=system_prompt,
            model_name=mock_model_config.name,
            model_config=mock_model_config
        )
    mock_openai_class.assert_not_called() # OpenAI client should not have been created
