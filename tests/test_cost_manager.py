import pytest
from unittest.mock import MagicMock, patch

from src.pydantic_llm_tester.utils.cost_manager import CostTracker
from src.pydantic_llm_tester.utils.data_structures import UsageData
from src.pydantic_llm_tester.llms.base import ModelConfig # Import ModelConfig

@pytest.fixture
def mock_llm_registry():
    """Fixture to mock the LLMRegistry."""
    with patch('src.pydantic_llm_tester.utils.cost_manager.get_llm_registry') as mock_get_registry:
        registry_instance = mock_get_registry.return_value = MagicMock()
        # Configure the mock registry to return specific model details
        mock_model_config_openai = ModelConfig(
            name="gpt-4o",
            cost_input=5.0,  # Example static cost
            cost_output=15.0, # Example static cost
            max_input_tokens=128000,
            max_output_tokens=4096,
            default=True,
            preferred=False,
            enabled=True
        )
        mock_model_config_openrouter = ModelConfig(
            name="openrouter/google/gemini-pro",
            cost_input=0.1,  # Example dynamic cost from OpenRouter
            cost_output=0.15, # Example dynamic cost from OpenRouter
            max_input_tokens=32000,
            max_output_tokens=4000,
            default=False,
            preferred=True,
            enabled=True
        )
        mock_model_config_openrouter_other = ModelConfig(
            name="openrouter/mistral/mistral-large-latest",
            cost_input=0.8,  # Another example dynamic cost from OpenRouter
            cost_output=0.24, # Another example dynamic cost from OpenRouter
            max_input_tokens=32000,
            max_output_tokens=4000,
            default=False,
            preferred=False,
            enabled=True
        )

        def get_model_details_side_effect(provider_name, model_name):
            if provider_name == "openai" and model_name == "gpt-4o":
                return mock_model_config_openai
            elif provider_name == "openrouter" and model_name == "openrouter/google/gemini-pro":
                return mock_model_config_openrouter
            elif provider_name == "openrouter" and model_name == "openrouter/mistral/mistral-large-latest":
                return mock_model_config_openrouter_other
            return None # Model not found

        registry_instance.get_model_details.side_effect = get_model_details_side_effect

        yield registry_instance

def test_cost_manager_calculates_cost_with_dynamic_pricing(mock_llm_registry):
    """
    Test that CostTracker uses dynamic pricing from the registry for cost calculation.
    """
    cost_tracker = CostTracker()
    run_id = cost_tracker.current_run_id # Get the generated run_id

    # Simulate adding test results with token usage for different models
    usage_openai = UsageData(prompt_tokens=100, completion_tokens=50, total_tokens=150, model="gpt-4o", total_cost=0.0) # total_cost will be calculated
    cost_tracker.add_test_result(run_id, "test_id_1", "openai", "gpt-4o", usage_openai)

    usage_openrouter_gemini = UsageData(prompt_tokens=200, completion_tokens=100, total_tokens=300, model="openrouter/google/gemini-pro", total_cost=0.0)
    cost_tracker.add_test_result(run_id, "test_id_2", "openrouter", "openrouter/google/gemini-pro", usage_openrouter_gemini)

    usage_openrouter_mistral = UsageData(prompt_tokens=50, completion_tokens=20, total_tokens=70, model="openrouter/mistral/mistral-large-latest", total_cost=0.0)
    cost_tracker.add_test_result(run_id, "test_id_3", "openrouter", "openrouter/mistral/mistral-large-latest", usage_openrouter_mistral)

    # Calculate expected costs based on mocked dynamic pricing (cost per 1M tokens)
    expected_cost_openai = (100 * (5.0 / 1_000_000)) + (50 * (15.0 / 1_000_000))
    expected_cost_openrouter_gemini = (200 * (0.1 / 1_000_000)) + (100 * (0.15 / 1_000_000))
    expected_cost_openrouter_mistral = (50 * (0.8 / 1_000_000)) + (20 * (0.24 / 1_000_000))

    # Get the run summary to check calculated costs
    run_summary = cost_tracker.get_run_summary(run_id)

    # Verify the calculated costs for each model
    assert "openai:gpt-4o" in run_summary["model_costs"]
    assert pytest.approx(run_summary["model_costs"]["openai:gpt-4o"]["total_cost"]) == expected_cost_openai

    assert "openrouter:openrouter/google/gemini-pro" in run_summary["model_costs"]
    assert pytest.approx(run_summary["model_costs"]["openrouter:openrouter/google/gemini-pro"]["total_cost"]) == expected_cost_openrouter_gemini

    assert "openrouter:openrouter/mistral/mistral-large-latest" in run_summary["model_costs"]
    assert pytest.approx(run_summary["model_costs"]["openrouter:openrouter/mistral/mistral-large-latest"]["total_cost"]) == expected_cost_openrouter_mistral

    # Verify the total cost
    expected_total_cost = expected_cost_openai + expected_cost_openrouter_gemini + expected_cost_openrouter_mistral
    assert pytest.approx(run_summary["total_cost"]) == expected_total_cost

# Add more test cases for edge cases, different providers, zero tokens, etc.
