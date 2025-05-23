"""
Tests for the cost_manager module with the new model registry approach.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.pydantic_llm_tester.llms.base import ModelConfig
from src.pydantic_llm_tester.utils.data_structures import UsageData
from src.pydantic_llm_tester.utils.cost_manager import (
    calculate_cost,
    CostTracker
)


def test_calculate_cost_with_registry():
    """Test that calculate_cost correctly uses the model registry."""
    provider = "openai"
    model = "gpt-4"
    prompt_tokens = 100
    completion_tokens = 50
    
    # Create a mock ModelConfig
    mock_model_config = ModelConfig(
        name=model,
        provider=provider,
        cost_input=10.0,  # $10 per 1M tokens
        cost_output=20.0,  # $20 per 1M tokens
        enabled=True,
        default=False,
        preferred=False,
        cost_category="premium",
        max_input_tokens=8000,
        max_output_tokens=4000
    )
    
    # Mock the LLMRegistry to return our mock ModelConfig
    with patch('src.pydantic_llm_tester.utils.cost_manager.LLMRegistry') as MockRegistry:
        mock_instance = MagicMock()
        MockRegistry.get_instance.return_value = mock_instance
        mock_instance.get_model_details.return_value = mock_model_config
        
        # Call the function under test
        prompt_cost, completion_cost, total_cost = calculate_cost(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Check the results
        expected_prompt_cost = (10.0 / 1_000_000) * prompt_tokens  # $0.001 * 100 = $0.1
        expected_completion_cost = (20.0 / 1_000_000) * completion_tokens  # $0.002 * 50 = $0.1
        expected_total_cost = expected_prompt_cost + expected_completion_cost  # $0.2
        
        assert pytest.approx(prompt_cost) == expected_prompt_cost
        assert pytest.approx(completion_cost) == expected_completion_cost
        assert pytest.approx(total_cost) == expected_total_cost
        
        # Verify the registry was called correctly
        mock_instance.get_model_details.assert_called_once_with(provider, model)


def test_calculate_cost_with_provider_model_format():
    """Test that calculate_cost correctly handles provider:model format."""
    provider = "openai"
    model_with_provider = f"{provider}:gpt-4"
    prompt_tokens = 100
    completion_tokens = 50
    
    # Create a mock ModelConfig
    mock_model_config = ModelConfig(
        name="gpt-4",  # Note: Just the model name part
        provider=provider,
        cost_input=10.0,
        cost_output=20.0,
        enabled=True,
        default=False,
        preferred=False,
        cost_category="premium",
        max_input_tokens=8000,
        max_output_tokens=4000
    )
    
    # Mock the LLMRegistry to return our mock ModelConfig
    with patch('src.pydantic_llm_tester.utils.cost_manager.LLMRegistry') as MockRegistry:
        mock_instance = MagicMock()
        MockRegistry.get_instance.return_value = mock_instance
        mock_instance.get_model_details.return_value = mock_model_config
        
        # Call the function under test with provider:model format
        prompt_cost, completion_cost, total_cost = calculate_cost(
            provider="some_other_provider",  # This should be overridden by the provider in the model string
            model=model_with_provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Check the results
        expected_prompt_cost = (10.0 / 1_000_000) * prompt_tokens  # $0.001 * 100 = $0.1
        expected_completion_cost = (20.0 / 1_000_000) * completion_tokens  # $0.002 * 50 = $0.1
        expected_total_cost = expected_prompt_cost + expected_completion_cost  # $0.2
        
        assert pytest.approx(prompt_cost) == expected_prompt_cost
        assert pytest.approx(completion_cost) == expected_completion_cost
        assert pytest.approx(total_cost) == expected_total_cost
        
        # Verify the registry was called with the correct provider and model (after splitting)
        mock_instance.get_model_details.assert_called_once_with("openai", "gpt-4")


def test_cost_tracker_with_provider_model_format():
    """Test that CostTracker correctly handles provider:model format."""
    # Initialize the cost tracker
    tracker = CostTracker()
    run_id = tracker.start_new_run()
    
    # Create test data
    test_id = "test_module/test_case"
    provider = "openai"
    model = "gpt-4"
    provider_model_key = f"{provider}:{model}"
    
    # Create a UsageData object with token usage
    usage_data = UsageData(
        provider=provider,
        model=model,
        prompt_tokens=100,
        completion_tokens=50
    )
    
    # Add costs manually for testing
    usage_data.prompt_cost = 0.1
    usage_data.completion_cost = 0.1
    usage_data.total_cost = 0.2
    
    # Add the test result
    tracker.add_test_result(
        run_id=run_id,
        test_id=test_id,
        provider=provider,
        model=model,
        usage_data=usage_data
    )
    
    # Get the run summary
    summary = tracker.get_run_summary(run_id)
    
    # Check the summary
    assert summary["total_cost"] == 0.2
    assert summary["total_tokens"] == 150
    assert summary["prompt_tokens"] == 100
    assert summary["completion_tokens"] == 50
    
    # Check that the model-specific summary uses provider:model format
    assert provider_model_key in summary["model_costs"]
    model_summary = summary["model_costs"][provider_model_key]
    assert model_summary["total_cost"] == 0.2
    assert model_summary["total_tokens"] == 150
    assert model_summary["prompt_tokens"] == 100
    assert model_summary["completion_tokens"] == 50
    assert model_summary["test_count"] == 1
    
    # Check the full run data
    run_data = tracker.get_run_data(run_id)
    assert test_id in run_data["tests"]
    assert provider_model_key in run_data["tests"][test_id]
    test_result = run_data["tests"][test_id][provider_model_key]
    assert test_result["total_cost"] == 0.2
    
    # Test cost report generation
    cost_report = tracker.get_cost_report(run_id)
    assert cost_report["total_cost"] == 0.2
    assert provider_model_key in cost_report["model_costs"]
    assert provider_model_key == cost_report["most_expensive_model"]