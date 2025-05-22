import pytest
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.llms.openai.provider import OpenAIProvider
from src.pydantic_llm_tester.utils.cost_manager import UsageData # Import UsageData

@pytest.fixture
def mock_openai_client():
    """Fixture to mock the OpenAI client."""
    with patch('src.pydantic_llm_tester.llms.openai.provider.OpenAI') as MockOpenAI:
        mock_client_instance = MagicMock()
        MockOpenAI.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def openai_provider(mock_openai_client):
    """Fixture to create an OpenAIProvider instance with a mocked client."""
    # Mock the config object that the provider expects
    mock_config = MagicMock()
    mock_config.name = "openai"
    mock_config.provider_type = "openai"
    mock_config.env_key = "OPENAI_API_KEY"
    mock_config.system_prompt = "You are a helpful assistant."
    mock_config.llm_models = [ # Provide some mock model configs
        MagicMock(name="gpt-4o", cost_input=5.0, cost_output=15.0, max_input_tokens=128000, max_output_tokens=4096, default=True, preferred=False, enabled=True),
        MagicMock(name="gpt-3.5-turbo", cost_input=0.5, cost_output=1.5, max_input_tokens=16385, max_output_tokens=4096, default=False, preferred=False, enabled=True),
    ]

    # Mock the LLMRegistry to return the mock model configs
    with patch('src.pydantic_llm_tester.llms.openai.provider.LLMRegistry') as MockRegistry:
        mock_registry_instance = MockRegistry.get_instance.return_value = MagicMock()
        def get_model_details_side_effect(provider_name, model_name):
            if provider_name == "openai":
                for model_config in mock_config.llm_models:
                    if model_config.name == model_name:
                        return model_config
            return None
        mock_registry_instance.get_model_details.side_effect = get_model_details_side_effect
        
        # Pass the mock config to the provider
        provider = OpenAIProvider(config=mock_config)
        yield provider


def test_openai_provider_returns_usage_data(openai_provider, mock_openai_client):
    """
    Test that OpenAIProvider's get_response method returns UsageData with token counts.
    """
    # Configure the mock OpenAI client to return a mock response with usage data
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices[0].message.content = "Mock LLM response"
    mock_chat_completion.usage.prompt_tokens = 100
    mock_chat_completion.usage.completion_tokens = 50
    mock_chat_completion.usage.total_tokens = 150
    mock_chat_completion.model = "gpt-4o" # Ensure the model name is included

    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Call the get_response method
    prompt = "Test prompt"
    source = "Test source"
    model_name = "gpt-4o"
    response_text, usage_data = openai_provider.get_response(prompt, source, model_name)

    # Verify the response text
    assert response_text == "Mock LLM response"

    # Verify the returned usage_data is a UsageData object
    assert isinstance(usage_data, UsageData)

    # Verify the token counts in the UsageData object
    assert usage_data.provider == "openai"
    assert usage_data.model == "gpt-4o"
    assert usage_data.prompt_tokens == 100
    assert usage_data.completion_tokens == 50
    assert usage_data.total_tokens == 150

    # Verify that the calculate_cost function within UsageData was implicitly called
    # and calculated costs based on the mocked ModelConfig pricing.
    # We can check the calculated costs in the UsageData object.
    expected_prompt_cost = (100 / 1_000_000) * 5.0
    expected_completion_cost = (50 / 1_000_000) * 15.0
    expected_total_cost = expected_prompt_cost + expected_completion_cost

    assert pytest.approx(usage_data.prompt_cost) == expected_prompt_cost
    assert pytest.approx(usage_data.completion_cost) == expected_completion_cost
    assert pytest.approx(usage_data.total_cost) == expected_total_cost

# Add similar tests for other providers (Anthropic, Mistral, Google, OpenRouter)
# to ensure they also return UsageData with correct token counts.
