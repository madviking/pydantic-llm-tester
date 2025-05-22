import pytest
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.llms.google.provider import GoogleProvider
from src.pydantic_llm_tester.utils.cost_manager import UsageData # Import UsageData

@pytest.fixture
def mock_google_client():
    """Fixture to mock the Google client."""
    with patch('src.pydantic_llm_tester.llms.google.provider.GoogleGenerativeAI') as MockGoogleGenerativeAI:
        mock_client_instance = MagicMock()
        MockGoogleGenerativeAI.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def google_provider(mock_google_client):
    """Fixture to create a GoogleProvider instance with a mocked client."""
    # Mock the config object that the provider expects
    mock_config = MagicMock()
    mock_config.name = "google"
    mock_config.provider_type = "google"
    mock_config.env_key = "GOOGLE_API_KEY"
    mock_config.system_prompt = "You are a helpful assistant."
    mock_config.llm_models = [ # Provide some mock model configs
        MagicMock(name="gemini-1.5-pro", cost_input=7.0, cost_output=21.0, max_input_tokens=1000000, max_output_tokens=8000, default=True, preferred=False, enabled=True),
        MagicMock(name="gemini-1.5-flash", cost_input=0.35, cost_output=1.05, max_input_tokens=1000000, max_output_tokens=8000, default=False, preferred=False, enabled=True),
    ]

    # Mock the LLMRegistry to return the mock model configs
    with patch('src.pydantic_llm_tester.llms.google.provider.LLMRegistry') as MockRegistry:
        mock_registry_instance = MockRegistry.get_instance.return_value = MagicMock()
        def get_model_details_side_effect(provider_name, model_name):
            if provider_name == "google":
                for model_config in mock_config.llm_models:
                    if model_config.name == model_name:
                        return model_config
            return None
        mock_registry_instance.get_model_details.side_effect = get_model_details_side_effect

        # Pass the mock config to the provider
        provider = GoogleProvider(config=mock_config)
        yield provider


def test_google_provider_returns_usage_data(google_provider, mock_google_client):
    """
    Test that GoogleProvider's get_response method returns UsageData with token counts.
    """
    # Configure the mock Google client to return a mock response with usage data
    mock_response = MagicMock()
    mock_response.text = "Mock LLM response"
    # Google's client might return usage differently, mock based on expected structure
    mock_response.usage_metadata.prompt_token_count = 250
    mock_response.usage_metadata.candidates_token_count = 120
    mock_response.usage_metadata.total_token_count = 370
    mock_response.model = "gemini-1.5-flash" # Ensure the model name is included

    # Mock the get_generative_model and generate_content calls
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_google_client.get_generative_model.return_value = mock_model


    # Call the get_response method
    prompt = "Test prompt"
    source = "Test source"
    model_name = "gemini-1.5-flash"
    response_text, usage_data = google_provider.get_response(prompt, source, model_name)

    # Verify the response text
    assert response_text == "Mock LLM response"

    # Verify the returned usage_data is a UsageData object
    assert isinstance(usage_data, UsageData)

    # Verify the token counts in the UsageData object
    assert usage_data.provider == "google"
    assert usage_data.model == "gemini-1.5-flash"
    assert usage_data.prompt_tokens == 250
    assert usage_data.completion_tokens == 120
    assert usage_data.total_tokens == 370

    # Verify that the calculate_cost function within UsageData was implicitly called
    # and calculated costs based on the mocked ModelConfig pricing.
    # We can check the calculated costs in the UsageData object.
    expected_prompt_cost = (250 / 1_000_000) * 0.35
    expected_completion_cost = (120 / 1_000_000) * 1.05
    expected_total_cost = expected_prompt_cost + expected_completion_cost

    assert pytest.approx(usage_data.prompt_cost) == expected_prompt_cost
    assert pytest.approx(usage_data.completion_cost) == expected_completion_cost
    assert pytest.approx(usage_data.total_cost) == expected_total_cost

# Add similar tests for OpenRouter provider
