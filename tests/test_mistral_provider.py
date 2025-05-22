import pytest
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.llms.mistral.provider import MistralProvider
from src.pydantic_llm_tester.utils.cost_manager import UsageData # Import UsageData

@pytest.fixture
def mock_mistral_client():
    """Fixture to mock the Mistral client."""
    with patch('src.pydantic_llm_tester.llms.mistral.provider.MistralClient') as MockMistralClient:
        mock_client_instance = MagicMock()
        MockMistralClient.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def mistral_provider(mock_mistral_client):
    """Fixture to create a MistralProvider instance with a mocked client."""
    # Mock the config object that the provider expects
    mock_config = MagicMock()
    mock_config.name = "mistral"
    mock_config.provider_type = "mistral"
    mock_config.env_key = "MISTRAL_API_KEY"
    mock_config.system_prompt = "You are a helpful assistant."
    mock_config.llm_models = [ # Provide some mock model configs
        MagicMock(name="mistral-large-latest", cost_input=8.0, cost_output=24.0, max_input_tokens=32000, max_output_tokens=4000, default=True, preferred=False, enabled=True),
        MagicMock(name="mistral-small", cost_input=2.0, cost_output=6.0, max_input_tokens=32000, max_output_tokens=4000, default=False, preferred=False, enabled=True),
    ]

    # Mock the LLMRegistry to return the mock model configs
    with patch('src.pydantic_llm_tester.llms.mistral.provider.LLMRegistry') as MockRegistry:
        mock_registry_instance = MockRegistry.get_instance.return_value = MagicMock()
        def get_model_details_side_effect(provider_name, model_name):
            if provider_name == "mistral":
                for model_config in mock_config.llm_models:
                    if model_config.name == model_name:
                        return model_config
            return None
        mock_registry_instance.get_model_details.side_effect = get_model_details_side_effect

        # Pass the mock config to the provider
        provider = MistralProvider(config=mock_config)
        yield provider


def test_mistral_provider_returns_usage_data(mistral_provider, mock_mistral_client):
    """
    Test that MistralProvider's get_response method returns UsageData with token counts.
    """
    # Configure the mock Mistral client to return a mock response with usage data
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices[0].message.content = "Mock LLM response"
    mock_chat_completion.usage.prompt_tokens = 200
    mock_chat_completion.usage.completion_tokens = 100
    mock_chat_completion.usage.total_tokens = 300
    mock_chat_completion.model = "mistral-large-latest" # Ensure the model name is included

    mock_mistral_client.chat.completions.create.return_value = mock_chat_completion

    # Call the get_response method
    prompt = "Test prompt"
    source = "Test source"
    model_name = "mistral-large-latest"
    response_text, usage_data = mistral_provider.get_response(prompt, source, model_name)

    # Verify the response text
    assert response_text == "Mock LLM response"

    # Verify the returned usage_data is a UsageData object
    assert isinstance(usage_data, UsageData)

    # Verify the token counts in the UsageData object
    assert usage_data.provider == "mistral"
    assert usage_data.model == "mistral-large-latest"
    assert usage_data.prompt_tokens == 200
    assert usage_data.completion_tokens == 100
    assert usage_data.total_tokens == 300

    # Verify that the calculate_cost function within UsageData was implicitly called
    # and calculated costs based on the mocked ModelConfig pricing.
    # We can check the calculated costs in the UsageData object.
    expected_prompt_cost = (200 / 1_000_000) * 8.0
    expected_completion_cost = (100 / 1_000_000) * 24.0
    expected_total_cost = expected_prompt_cost + expected_completion_cost

    assert pytest.approx(usage_data.prompt_cost) == expected_prompt_cost
    assert pytest.approx(usage_data.completion_cost) == expected_completion_cost
    assert pytest.approx(usage_data.total_cost) == expected_total_cost

# Add similar tests for other providers (Google, OpenRouter)
