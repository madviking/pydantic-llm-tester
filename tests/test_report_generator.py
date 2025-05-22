import pytest
from unittest.mock import MagicMock

from src.pydantic_llm_tester.utils.report_generator import ReportGenerator

@pytest.fixture
def report_generator():
    """Fixture to create a ReportGenerator instance."""
    return ReportGenerator()

def test_report_generator_includes_cost_info(report_generator):
    """
    Test that ReportGenerator includes cost information in the generated report.
    """
    # Create mock test results with usage data including costs
    mock_results = {
        "module1/test1": {
            "openai:gpt-4o": {
                "response": "...",
                "validation": {"success": True, "accuracy": 100.0},
                "usage": {
                    "provider": "openai", "model": "gpt-4o",
                    "prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30,
                    "prompt_cost": 0.00005, "completion_cost": 0.0003, "total_cost": 0.00035
                }
            },
            "openrouter:openrouter/google/gemini-pro": {
                "response": "...",
                "validation": {"success": False, "accuracy": 50.0},
                "usage": {
                    "provider": "openrouter", "model": "openrouter/google/gemini-pro",
                    "prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80,
                    "prompt_cost": 0.000005, "completion_cost": 0.0000045, "total_cost": 0.0000095
                }
            }
        },
        "module1/test2": {
             "openai:gpt-4o": {
                "response": "...",
                "validation": {"success": True, "accuracy": 90.0},
                "usage": {
                    "provider": "openai", "model": "gpt-4o",
                    "prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40,
                    "prompt_cost": 0.000075, "completion_cost": 0.000375, "total_cost": 0.00045
                }
            }
        }
    }

    # Mock the cost_tracker.get_run_summary to provide a summary
    mock_run_summary = {
        "total_cost": 0.00035 + 0.0000095 + 0.00045,
        "total_tokens": 30 + 80 + 40,
        "prompt_tokens": 10 + 50 + 15,
        "completion_tokens": 20 + 30 + 25,
        "model_costs": {
            "openai:gpt-4o": {"total_cost": 0.00035 + 0.00045, "total_tokens": 30 + 40, "test_count": 2},
            "openrouter:openrouter/google/gemini-pro": {"total_cost": 0.0000095, "total_tokens": 80, "test_count": 1}
        }
    }
    with patch('src.pydantic_llm_tester.utils.report_generator.cost_tracker.get_run_summary', return_value=mock_run_summary):
        # Generate the report
        report_content = report_generator.generate_report(mock_results, optimized=False)

        # Verify that cost information is present in the report string
        assert "## Cost Summary" in report_content
        assert f"Total Cost: ${mock_run_summary['total_cost']:.6f}" in report_content
        assert f"Total Tokens: {mock_run_summary['total_tokens']}" in report_content
        assert "### Cost Breakdown by Model" in report_content
        assert "openai:gpt-4o" in report_content
        assert "openrouter:openrouter/google/gemini-pro" in report_content
        # Check for cost per model (approximate matching for floats)
        assert f"${mock_run_summary['model_costs']['openai:gpt-4o']['total_cost']:.6f}" in report_content
        assert f"${mock_run_summary['model_costs']['openrouter:openrouter/google/gemini-pro']['total_cost']:.6f}" in report_content

        # Verify that cost information is included per test case
        assert "Cost:" in report_content # Check for the label
        assert f"Cost: ${mock_results['module1/test1']['openai:gpt-4o']['usage']['total_cost']:.6f}" in report_content
        assert f"Cost: ${mock_results['module1/test1']['openrouter:openrouter/google/gemini-pro']['usage']['total_cost']:.6f}" in report_content
        assert f"Cost: ${mock_results['module1/test2']['openai:gpt-4o']['usage']['total_cost']:.6f}" in report_content

# Add more tests for different scenarios (e.g., optimized runs, no cost data)
