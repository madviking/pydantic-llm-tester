import pytest
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.llms.openrouter.provider import OpenRouterProvider
from src.pydantic_llm_tester.utils.cost_manager import UsageData # Import UsageData

@pytest.fixture
def mock_openrouter_client():
    """Fixture to mock the OpenRouter client."""
    with patch('src.pydantic_llm_tester.llms.openrouter.provider.OpenRouter') as MockOpenRouter:
        mock_client_instance = MagicMock()
        MockOpenRouter.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def openrouter_provider(mock_openrouter_client):
    """Fixture to create an OpenRouterProvider instance with a mocked client."""
    # Mock the config object that the provider expects
    mock_config = MagicMock()
    mock_config.name = "openrouter"
    mock_config.provider_type = "openrouter"
    mock_config.env_key = "OPENROUTER_API_KEY"
    mock_config.system_prompt = "You are a helpful assistant."
    mock_config.llm_models = [ # Provide some mock model configs
        MagicMock(name="openrouter/google/gemini-pro", cost_input=0.1, cost_output=0.15, max_input_tokens=32000, max_output_tokens=4000, default=True, preferred=False, enabled=True),
        MagicMock(name="openrouter/mistral/mistral-large-latest", cost_input=0.8, cost_output=0.24, max_input_tokens=32000, max_output_tokens=4000, default=False, preferred=False, enabled=True),
    ]

    # Mock the LLMRegistry to return the mock model configs
    with patch('src.pydantic_llm_tester.llms.openrouter.provider.LLMRegistry') as MockRegistry:
        mock_registry_instance = MockRegistry.get_instance.return_value = MagicMock()
        def get_model_details_side_effect(provider_name, model_name):
            if provider_name == "openrouter":
                for model_config in mock_config.llm_models:
                    if model_config.name == model_name:
                        return model_config
            return None
        mock_registry_instance.get_model_details.side_effect = get_model_details_side_effect

        # Pass the mock config to the provider
        provider = OpenRouterProvider(config=mock_config)
        yield provider


def test_openrouter_provider_returns_usage_data(openrouter_provider, mock_openrouter_client):
    """
    Test that OpenRouterProvider's get_response method returns UsageData with token counts.
    """
    # Configure the mock OpenRouter client to return a mock response with usage data
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices[0].message.content = "Mock LLM response"
    mock_chat_completion.usage.prompt_tokens = 300
    mock_chat_completion.usage.completion_tokens = 150
    mock_chat_completion.usage.total_tokens = 450
    mock_chat_completion.model = "openrouter/google/gemini-pro" # Ensure the model name is included

    mock_openrouter_client.chat.completions.create.return_value = mock_chat_completion

    # Call the get_response method
    prompt = "Test prompt"
    source = "Test source"
    model_name = "openrouter/google/gemini-pro"
    response_text, usage_data = openrouter_provider.get_response(prompt, source, model_name)

    # Verify the response text
    assert response_text == "Mock LLM response"

    # Verify the returned usage_data is a UsageData object
    assert isinstance(usage_data, UsageData)

    # Verify the token counts in the UsageData object
    assert usage_data.provider == "openrouter"
    assert usage_data.model == "openrouter/google/gemini-pro"
    assert usage_data.prompt_tokens == 300
    assert usage_data.completion_tokens == 150
    assert usage_data.total_tokens == 450

    # Verify that the calculate_cost function within UsageData was implicitly called
    # and calculated costs based on the mocked ModelConfig pricing.
    # We can check the calculated costs in the UsageData object.
    expected_prompt_cost = (300 / 1_000_000) * 0.1
    expected_completion_cost = (150 / 1_000_000) * 0.15
    expected_total_cost = expected_prompt_cost + expected_completion_cost

    assert pytest.approx(usage_data.prompt_cost) == expected_prompt_cost
    assert pytest.approx(usage_data.completion_cost) == expected_completion_cost
    assert pytest.approx(usage_data.total_cost) == expected_total_cost

# Add similar tests for other providers if any are added in the future
