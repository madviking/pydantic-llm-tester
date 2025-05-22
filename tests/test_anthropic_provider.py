import pytest
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.llms.anthropic.provider import AnthropicProvider
from src.pydantic_llm_tester.utils.cost_manager import UsageData # Import UsageData

@pytest.fixture
def mock_anthropic_client():
    """Fixture to mock the Anthropic client."""
    with patch('src.pydantic_llm_tester.llms.anthropic.provider.Anthropic') as MockAnthropic:
        mock_client_instance = MagicMock()
        MockAnthropic.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def anthropic_provider(mock_anthropic_client):
    """Fixture to create an AnthropicProvider instance with a mocked client."""
    # Mock the config object that the provider expects
    mock_config = MagicMock()
    mock_config.name = "anthropic"
    mock_config.provider_type = "anthropic"
    mock_config.env_key = "ANTHROPIC_API_KEY"
    mock_config.system_prompt = "You are a helpful assistant."
    mock_config.llm_models = [ # Provide some mock model configs
        MagicMock(name="claude-3-opus-20240229", cost_input=15.0, cost_output=75.0, max_input_tokens=200000, max_output_tokens=4000, default=True, preferred=False, enabled=True),
        MagicMock(name="claude-3-haiku-20240307", cost_input=0.25, cost_output=1.25, max_input_tokens=200000, max_output_tokens=4000, default=False, preferred=False, enabled=True),
    ]

    # Mock the LLMRegistry to return the mock model configs
    with patch('src.pydantic_llm_tester.llms.anthropic.provider.LLMRegistry') as MockRegistry:
        mock_registry_instance = MockRegistry.get_instance.return_value = MagicMock()
        def get_model_details_side_effect(provider_name, model_name):
            if provider_name == "anthropic":
                for model_config in mock_config.llm_models:
                    if model_config.name == model_name:
                        return model_config
            return None
        mock_registry_instance.get_model_details.side_effect = get_model_details_side_effect

        # Pass the mock config to the provider
        provider = AnthropicProvider(config=mock_config)
        yield provider


def test_anthropic_provider_returns_usage_data(anthropic_provider, mock_anthropic_client):
    """
    Test that AnthropicProvider's get_response method returns UsageData with token counts.
    """
    # Configure the mock Anthropic client to return a mock response with usage data
    mock_message = MagicMock()
    mock_message.content[0].text = "Mock LLM response"
    mock_message.usage.input_tokens = 150
    mock_message.usage.output_tokens = 75
    mock_message.model = "claude-3-haiku-20240307" # Ensure the model name is included

    mock_anthropic_client.messages.create.return_value = mock_message

    # Call the get_response method
    prompt = "Test prompt"
    source = "Test source"
    model_name = "claude-3-haiku-20240307"
    response_text, usage_data = anthropic_provider.get_response(prompt, source, model_name)

    # Verify the response text
    assert response_text == "Mock LLM response"

    # Verify the returned usage_data is a UsageData object
    assert isinstance(usage_data, UsageData)

    # Verify the token counts in the UsageData object
    assert usage_data.provider == "anthropic"
    assert usage_data.model == "claude-3-haiku-20240307"
    assert usage_data.prompt_tokens == 150
    assert usage_data.completion_tokens == 75
    assert usage_data.total_tokens == 150 + 75 # Anthropic usage includes total_tokens

    # Verify that the calculate_cost function within UsageData was implicitly called
    # and calculated costs based on the mocked ModelConfig pricing.
    # We can check the calculated costs in the UsageData object.
    expected_prompt_cost = (150 / 1_000_000) * 0.25
    expected_completion_cost = (75 / 1_000_000) * 1.25
    expected_total_cost = expected_prompt_cost + expected_completion_cost

    assert pytest.approx(usage_data.prompt_cost) == expected_prompt_cost
    assert pytest.approx(usage_data.completion_cost) == expected_completion_cost
    assert pytest.approx(usage_data.total_cost) == expected_total_cost

# Add similar tests for other providers (Mistral, Google, OpenRouter)
