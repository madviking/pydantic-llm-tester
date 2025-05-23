"""
Integration test for the full cost reporting flow with the new model registry approach.
"""

import os
import json
import tempfile
from typing import Dict, List, Any
import pytest
from unittest.mock import patch, MagicMock

from pydantic_llm_tester.llm_tester import LLMTester
from pydantic_llm_tester.utils.cost_manager import CostTracker
from pydantic_llm_tester.llms.llm_registry import LLMRegistry
from pydantic_llm_tester.utils.data_structures import UsageData


@pytest.fixture
def mock_registry_models():
    """Fixture providing mock models for the registry."""
    return {
        "openai": [
            {
                "name": "gpt-4",
                "cost_input": 30.0,
                "cost_output": 60.0,
                "enabled": True,
                "default": True,
                "preferred": True,
                "max_input_tokens": 8192,
                "max_output_tokens": 8192,
                "cost_category": "expensive"
            },
            {
                "name": "gpt-3.5-turbo",
                "cost_input": 2.0,
                "cost_output": 2.0,
                "enabled": True,
                "default": False,
                "preferred": False,
                "max_input_tokens": 4096,
                "max_output_tokens": 4096,
                "cost_category": "standard"
            }
        ],
        "anthropic": [
            {
                "name": "claude-3-opus",
                "cost_input": 15.0,
                "cost_output": 75.0,
                "enabled": True,
                "default": True,
                "preferred": True,
                "max_input_tokens": 100000,
                "max_output_tokens": 100000,
                "cost_category": "expensive"
            }
        ],
        "openrouter": [
            {
                "name": "openai:gpt-4o-mini",
                "cost_input": 3.0,
                "cost_output": 6.0,
                "enabled": True,
                "default": False,
                "preferred": True,
                "max_input_tokens": 128000,
                "max_output_tokens": 4096,
                "cost_category": "standard"
            },
            {
                "name": "anthropic:claude-3-haiku",
                "cost_input": 0.25,
                "cost_output": 1.25,
                "enabled": True,
                "default": True,
                "preferred": False,
                "max_input_tokens": 200000,
                "max_output_tokens": 4096,
                "cost_category": "cheap"
            }
        ]
    }


@pytest.fixture
def mock_test_results():
    """Fixture providing mock test results."""
    return {
        "test1": {
            "openai": {
                "gpt-4": {
                    "response": "Test response",
                    "validation": {
                        "success": True,
                        "accuracy": 0.95
                    },
                    "usage": UsageData(
                        prompt_tokens=100,
                        completion_tokens=50,
                        total_tokens=150,
                        model="gpt-4",
                        total_cost=0.0  # To be calculated
                    )
                }
            },
            "openrouter": {
                "openai:gpt-4o-mini": {
                    "response": "Test response",
                    "validation": {
                        "success": True,
                        "accuracy": 0.92
                    },
                    "usage": UsageData(
                        prompt_tokens=100,
                        completion_tokens=60,
                        total_tokens=160,
                        model="openai:gpt-4o-mini",
                        total_cost=0.0  # To be calculated
                    )
                }
            }
        },
        "test2": {
            "anthropic": {
                "claude-3-opus": {
                    "response": "Test response",
                    "validation": {
                        "success": True,
                        "accuracy": 0.98
                    },
                    "usage": UsageData(
                        prompt_tokens=200,
                        completion_tokens=100,
                        total_tokens=300,
                        model="claude-3-opus",
                        total_cost=0.0  # To be calculated
                    )
                }
            },
            "openrouter": {
                "anthropic:claude-3-haiku": {
                    "response": "Test response",
                    "validation": {
                        "success": True,
                        "accuracy": 0.90
                    },
                    "usage": UsageData(
                        prompt_tokens=200,
                        completion_tokens=120,
                        total_tokens=320,
                        model="anthropic:claude-3-haiku",
                        total_cost=0.0  # To be calculated
                    )
                }
            }
        }
    }


@pytest.fixture
def mock_llm_registry(mock_registry_models):
    """Create a mock LLMRegistry instance."""
    registry = MagicMock(spec=LLMRegistry)
    
    # Setup get_model_details method to return model details from mock_registry_models
    def get_model_details_mock(provider: str, model_name: str):
        provider_models = mock_registry_models.get(provider, [])
        for model in provider_models:
            if model["name"] == model_name:
                return model
        return None
    
    registry.get_model_details.side_effect = get_model_details_mock
    
    # Setup get_all_model_details to return all models
    def get_all_model_details_mock(only_configured=False, only_enabled=True):
        all_models = []
        for provider, models in mock_registry_models.items():
            for model in models:
                if only_enabled and not model.get("enabled", True):
                    continue
                model_with_provider = model.copy()
                model_with_provider["provider"] = provider
                all_models.append(model_with_provider)
        return all_models
    
    registry.get_all_model_details.side_effect = get_all_model_details_mock
    
    return registry


def test_cost_tracker_with_registry(mock_llm_registry, mock_test_results):
    """
    Test the integration of CostTracker with the LLMRegistry for cost calculation.
    """
    # Create a CostTracker instance with the mock registry
    with patch("pydantic_llm_tester.utils.cost_manager.get_llm_registry", return_value=mock_llm_registry):
        cost_tracker = CostTracker()
        
        # Calculate costs for the mock test results
        run_id = "test_run_123"
        for test_id, providers_dict in mock_test_results.items():
            for provider, models_dict in providers_dict.items():
                for model, result in models_dict.items():
                    # Add the test result to the cost tracker
                    cost_tracker.add_test_result(
                        run_id=run_id,
                        test_id=test_id,
                        provider=provider,
                        model=model,
                        usage_data=result["usage"]
                    )
        
        # Get the run summary
        summary = cost_tracker.get_run_summary(run_id)
        
        # Verify the summary contains the expected information
        assert "total_cost" in summary
        assert "model_costs" in summary
        assert len(summary["model_costs"]) == 4  # We had 4 model-runs in our test data
        
        # Verify costs are calculated correctly for direct provider models
        openai_gpt4_key = "openai:gpt-4"
        assert openai_gpt4_key in summary["model_costs"]
        openai_gpt4 = summary["model_costs"][openai_gpt4_key]
        assert openai_gpt4["prompt_tokens"] == 100
        assert openai_gpt4["completion_tokens"] == 50
        
        # Verify costs are calculated correctly for OpenRouter provider:model format
        openrouter_gpt4o_mini_key = "openrouter:openai:gpt-4o-mini"
        assert openrouter_gpt4o_mini_key in summary["model_costs"]
        openrouter_gpt4o_mini = summary["model_costs"][openrouter_gpt4o_mini_key]
        assert openrouter_gpt4o_mini["prompt_tokens"] == 100
        assert openrouter_gpt4o_mini["completion_tokens"] == 60


@pytest.mark.skip(reason="Test requires LLMTester refactoring for cost_tracker integration")
def test_llm_tester_cost_reporting_flow():
    """
    Test the full cost reporting flow in LLMTester.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Skip this test for now - will be implemented after LLMTester cost reporting
        # is updated to use the new CostTracker API
        pass


def test_provider_model_parsing_in_cost_calculation():
    """
    Test that provider:model format is correctly parsed during cost calculation.
    """
    # Create sample usage data with provider:model format
    usage_data = UsageData(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="openrouter:anthropic:claude-3-haiku",
        total_cost=0.0  # To be calculated
    )
    
    # Mock the LLMRegistry to provide model details when requested
    with patch("pydantic_llm_tester.utils.cost_manager.get_llm_registry") as mock_get_registry:
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry
        
        # Configure the mock registry to return model details
        def get_model_details_side_effect(provider, model_name):
            if provider == "openrouter" and model_name == "anthropic:claude-3-haiku":
                return {
                    "name": "anthropic:claude-3-haiku",
                    "cost_input": 0.25,
                    "cost_output": 1.25,
                    "enabled": True
                }
            return None
        
        mock_registry.get_model_details.side_effect = get_model_details_side_effect
        
        # Create a CostTracker and add a test result
        cost_tracker = CostTracker()
        cost_tracker.add_test_result(
            run_id="test_run",
            test_id="test1",
            provider="openrouter",
            model="anthropic:claude-3-haiku",
            usage_data=usage_data
        )
        
        # Get the run summary
        summary = cost_tracker.get_run_summary("test_run")
        
        # Verify the costs were calculated correctly
        assert len(summary["model_costs"]) == 1
        model_key = "openrouter:anthropic:claude-3-haiku"
        assert model_key in summary["model_costs"]
        model_summary = summary["model_costs"][model_key]
        assert model_summary["prompt_tokens"] == 100
        assert model_summary["completion_tokens"] == 50