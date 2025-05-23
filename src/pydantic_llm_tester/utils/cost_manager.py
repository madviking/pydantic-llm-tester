"""
Cost tracking and analysis utilities for LLM Tester
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Use absolute imports
from .common import get_project_root, get_package_dir
from ..llms.base import ModelConfig # Import ModelConfig
from .data_structures import UsageData # Import UsageData from the new file

# Set up logging
logger = logging.getLogger(__name__)

# Default model pricing ($ per 1M tokens) - Keep as fallback
DEFAULT_MODEL_PRICING = {
    "openai": {
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
    },
    "anthropic": {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25}
    },
    "mistral": {
        "mistral-large-latest": {"input": 8.0, "output": 24.0},
        "mistral-medium": {"input": 2.7, "output": 8.1},
        "mistral-small": {"input": 2.0, "output": 6.0}
    },
    "google": {
        "gemini-1.5-pro": {"input": 7.0, "output": 21.0},
        "gemini-1.5-flash": {"input": 0.35, "output": 1.05},
        "text-bison": {"input": 0.5, "output": 1.5}
    }
}

# Removed get_pricing_config_path, load_model_pricing, save_model_pricing
# as pricing is now sourced from LLMRegistry

# Helper function to avoid circular imports
def get_llm_registry():
    """
    Get the LLMRegistry instance.
    
    This function is used to avoid circular imports.
    
    Returns:
        LLMRegistry instance
    """
    from ..llms.llm_registry import LLMRegistry
    return LLMRegistry.get_instance()

def calculate_cost(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> Tuple[float, float, float]:
    """
    Calculate the cost for a specific model and token usage using pricing from LLMRegistry.

    Args:
        provider: Provider name (e.g., "openai", "openrouter")
        model: Model name (e.g., "gpt-4o", "openrouter/google/gemini-pro")
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens

    Returns:
        Tuple containing (prompt_cost, completion_cost, total_cost)
    """
    # Handle provider:model format if model contains provider prefix
    if ":" in model:
        # The model string contains a provider prefix (e.g. "openai:gpt-4")
        # Use the provider from the model string and the part after the colon as the model
        model_parts = model.split(":", 1)
        if len(model_parts) == 2:
            # Use the provider from the model string if it differs from the provided provider
            # This handles cases where the model string includes the provider
            # but the provider parameter is different
            if model_parts[0] != provider:
                logger.debug(f"Model string '{model}' contains different provider than parameter '{provider}'. " +
                            f"Using provider from model string: '{model_parts[0]}'")
            provider = model_parts[0]
            model = model_parts[1]
    
    # Get model details from the central registry using the helper function
    registry = get_llm_registry()
    try:
        model_config = registry.get_model_details(provider, model)

        # Use pricing from the registry
        input_cost_per_token = model_config.cost_input / 1_000_000
        output_cost_per_token = model_config.cost_output / 1_000_000
        logger.debug(f"Using registry pricing for {provider}/{model}: " +
                   f"input={model_config.cost_input}, output={model_config.cost_output}")
    except (ValueError, AttributeError) as e:
        # Model not found in registry or has missing cost attributes
        logger.warning(f"Error getting model details from registry: {str(e)}")
        
        # Fallback to default pricing
        provider_pricing = DEFAULT_MODEL_PRICING.get(provider, {})
        model_pricing = provider_pricing.get(model, {})

        if model_pricing:
            input_cost_per_token = model_pricing.get("input", 0.0) / 1_000_000
            output_cost_per_token = model_pricing.get("output", 0.0) / 1_000_000
            logger.warning(f"Registry pricing not found for {provider}/{model}. Using default pricing.")
        else:
            # Last resort: generic pricing
            input_cost_per_token = 0.5 / 1_000_000
            output_cost_per_token = 1.5 / 1_000_000
            logger.warning(f"No pricing found in registry or defaults for {provider}/{model}. Using generic pricing.")

    prompt_cost = prompt_tokens * input_cost_per_token
    completion_cost = completion_tokens * output_cost_per_token
    total_cost = prompt_cost + completion_cost

    return (prompt_cost, completion_cost, total_cost)


# Removed UsageData class definition as it's moved to data_structures.py


class CostTracker:
    """Tracks and analyzes costs across test runs"""

    def __init__(self):
        self.test_runs = {}
        self.current_run_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.logger = logging.getLogger(__name__)

    def start_new_run(self) -> str:
        """
        Start a new test run

        Returns:
            run_id: Identifier for the new run
        """
        self.current_run_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.test_runs[self.current_run_id] = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total_cost": 0.0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "model_costs": {} # Changed from py_models to model_costs for clarity
            }
        }
        return self.current_run_id

    def add_test_result(
        self,
        run_id: str,
        test_id: str,
        provider: str,
        model: str,
        usage_data: UsageData,
    ) -> None:
        """
        Add a test result to the tracker

        Args:
            run_id: Run identifier
            test_id: Identifier for the test
            provider: Provider name
            model: Model name
            usage_data: Token usage data
        """
        if run_id not in self.test_runs:
            self.logger.warning(f"Run ID {run_id} not found. Cannot add test result.")
            return

        run_data = self.test_runs[run_id]

        # Add test result
        if test_id not in run_data["tests"]:
            run_data["tests"][test_id] = {}

        # Use provider:model format for test results and summary keys
        provider_model_key = f"{provider}:{model}"
        run_data["tests"][test_id][provider_model_key] = usage_data.to_dict()

        # Update summary
        summary = run_data["summary"]
        summary["total_cost"] += usage_data.total_cost
        summary["total_tokens"] += usage_data.total_tokens
        summary["prompt_tokens"] += usage_data.prompt_tokens
        summary["completion_tokens"] += usage_data.completion_tokens

        # Update model-specific summary
        if provider_model_key not in summary["model_costs"]:
            summary["model_costs"][provider_model_key] = {
                "total_cost": 0.0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "test_count": 0
            }

        model_summary = summary["model_costs"][provider_model_key]
        model_summary["total_cost"] += usage_data.total_cost
        model_summary["total_tokens"] += usage_data.total_tokens
        model_summary["prompt_tokens"] += usage_data.prompt_tokens
        model_summary["completion_tokens"] += usage_data.completion_tokens
        model_summary["test_count"] += 1

    def get_run_summary(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary for a specific run

        Args:
            run_id: Optional run identifier (defaults to current run)

        Returns:
            Dictionary containing run summary data
        """
        run_id = run_id or self.current_run_id

        if run_id not in self.test_runs:
            self.logger.error(f"Run ID {run_id} not found")
            return {}

        return self.test_runs[run_id]["summary"]

    def get_run_data(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all data for a specific run

        Args:
            run_id: Optional run identifier (defaults to current run)

        Returns:
            Dictionary containing all run data
        """
        run_id = run_id or self.current_run_id

        if run_id not in self.test_runs:
            self.logger.error(f"Run ID {run_id} not found")
            return {}

        return self.test_runs[run_id]

    def get_cost_report(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a detailed cost report for a run

        Args:
            run_id: Optional run identifier (defaults to current run)

        Returns:
            Dictionary containing detailed cost report
        """
        run_id = run_id or self.current_run_id

        if run_id not in self.test_runs:
            self.logger.error(f"Run ID {run_id} not found")
            return {}

        run_data = self.test_runs[run_id]
        summary = run_data["summary"]

        # Calculate average costs
        model_averages = {}
        for model_name, model_data in summary["model_costs"].items(): # Changed from py_models
            test_count = model_data["test_count"]
            if test_count > 0:
                model_averages[model_name] = {
                    "avg_cost_per_test": model_data["total_cost"] / test_count,
                    "avg_tokens_per_test": model_data["total_tokens"] / test_count,
                    "cost_per_token": model_data["total_cost"] / model_data["total_tokens"] if model_data["total_tokens"] > 0 else 0
                }

        # Create cost breakdown
        most_expensive_model = max(
            summary["model_costs"].items(), # Changed from py_models
            key=lambda x: x[1]["total_cost"]
        )[0] if summary["model_costs"] else None # Changed from py_models

        most_expensive_test = None
        highest_cost = 0

        for test_id, test_data in run_data["tests"].items():
            for provider_model, usage in test_data.items():
                if usage["total_cost"] > highest_cost:
                    highest_cost = usage["total_cost"]
                    most_expensive_test = {
                        "test_id": test_id,
                        "provider_model": provider_model,
                        "cost": usage["total_cost"]
                    }

        # Generate report
        report = {
            "run_id": run_id,
            "timestamp": run_data["timestamp"],
            "total_tests": sum(len(test_data) for test_data in run_data["tests"].values()),
            "total_cost": summary["total_cost"],
            "total_tokens": summary["total_tokens"],
            "prompt_tokens": summary["prompt_tokens"],
            "completion_tokens": summary["completion_tokens"],
            "cost_per_token": summary["total_cost"] / summary["total_tokens"] if summary["total_tokens"] > 0 else 0,
            "model_costs": summary["model_costs"], # Changed from py_models
            "model_averages": model_averages,
            "most_expensive_model": most_expensive_model,
            "most_expensive_test": most_expensive_test
        }

        return report

    def save_cost_report(self, output_dir: str, run_id: Optional[str] = None) -> str:
        """
        Save the cost report to a file

        Args:
            output_dir: Directory to save the report
            run_id: Optional run identifier (defaults to current run)

        Returns:
            Path to the saved report file
        """
        run_id = run_id or self.current_run_id
        report = self.get_cost_report(run_id)

        if not report:
            self.logger.error(f"No data available for run {run_id}")
            return ""

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        report_path = os.path.join(output_dir, f"cost_report_{run_id}_{timestamp}.json")

        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Cost report saved to {report_path}")
            return report_path
        except IOError as e:
            self.logger.error(f"Error saving cost report: {e}")
            return ""


# Create a global instance of the cost tracker
cost_tracker = CostTracker()
