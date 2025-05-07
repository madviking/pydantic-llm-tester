"""
Cost tracking and analysis utilities for LLM Tester
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Default model pricing ($ per 1M tokens)
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


def get_pricing_config_path() -> str:
    """Get the path to the py_models pricing configuration file"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models_pricing.json')


def load_model_pricing() -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Load model pricing from models_pricing.json or use defaults
    
    Returns:
        Dict containing model pricing information
    """
    pricing_path = get_pricing_config_path()
    
    if os.path.exists(pricing_path):
        try:
            with open(pricing_path, 'r') as f:
                pricing = json.load(f)
            logger.info(f"Loaded model pricing from {pricing_path}")
            return pricing
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading model pricing: {e}")
            return DEFAULT_MODEL_PRICING
    else:
        # Create default pricing file
        save_model_pricing(DEFAULT_MODEL_PRICING)
        return DEFAULT_MODEL_PRICING


def save_model_pricing(pricing: Dict[str, Dict[str, Dict[str, float]]]) -> None:
    """
    Save model pricing configuration to models_pricing.json
    
    Args:
        pricing: Model pricing dictionary to save
    """
    pricing_path = get_pricing_config_path()
    
    try:
        with open(pricing_path, 'w') as f:
            json.dump(pricing, f, indent=2)
        logger.info(f"Saved model pricing to {pricing_path}")
    except IOError as e:
        logger.error(f"Error saving model pricing: {e}")


def calculate_cost(
    provider: str, 
    model: str, 
    prompt_tokens: int, 
    completion_tokens: int
) -> Tuple[float, float, float]:
    """
    Calculate the cost for a specific model and token usage
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic")
        model: Model name (e.g., "gpt-4", "claude-3-opus")
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        
    Returns:
        Tuple containing (prompt_cost, completion_cost, total_cost)
    """
    # Load pricing information
    pricing = load_model_pricing()
    
    # Check if provider and model exist in pricing data
    provider_pricing = pricing.get(provider, {})
    model_pricing = provider_pricing.get(model, {})
    
    if not model_pricing:
        # Try to find a default model or similar model
        for model_name, model_price in provider_pricing.items():
            if model.lower() in model_name.lower() or model_name.lower() in model.lower():
                model_pricing = model_price
                logger.info(f"Using pricing for similar model {model_name} for {model}")
                break
        
        # If still no pricing found, use a default
        if not model_pricing:
            default_models = {
                "openai": "gpt-4", 
                "anthropic": "claude-3-opus-20240229",
                "mistral": "mistral-large-latest",
                "google": "gemini-1.5-pro"
            }
            default_model = default_models.get(provider)
            if default_model and default_model in provider_pricing:
                model_pricing = provider_pricing[default_model]
                logger.info(f"Using default model pricing for {provider}: {default_model}")
            else:
                # Create a generic pricing as last resort
                model_pricing = {"input": 0.5, "output": 1.5}
                logger.warning(f"No pricing found for {provider}/{model}. Using generic pricing.")
    
    # Calculate costs (convert from per 1M tokens to actual tokens)
    input_cost_per_token = model_pricing.get("input", 0.0) / 1_000_000
    output_cost_per_token = model_pricing.get("output", 0.0) / 1_000_000
    
    prompt_cost = prompt_tokens * input_cost_per_token
    completion_cost = completion_tokens * output_cost_per_token
    total_cost = prompt_cost + completion_cost
    
    return (prompt_cost, completion_cost, total_cost)


class UsageData:
    """Class representing token usage data from a model call"""
    
    def __init__(
        self, 
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: Optional[int] = None
    ):
        self.provider = provider
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens or (prompt_tokens + completion_tokens)
        
        # Calculate costs
        self.prompt_cost, self.completion_cost, self.total_cost = calculate_cost(
            provider, model, prompt_tokens, completion_tokens
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert usage data to dictionary"""
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost": self.prompt_cost,
            "completion_cost": self.completion_cost,
            "total_cost": self.total_cost
        }


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
                "py_models": {}
            }
        }
        return self.current_run_id
    
    def add_test_result(
        self, 
        test_id: str, 
        provider: str, 
        model: str, 
        usage_data: UsageData, 
        run_id: Optional[str] = None
    ) -> None:
        """
        Add a test result to the tracker
        
        Args:
            test_id: Identifier for the test
            provider: Provider name
            model: Model name
            usage_data: Token usage data
            run_id: Optional run identifier (defaults to current run)
        """
        run_id = run_id or self.current_run_id
        
        if run_id not in self.test_runs:
            self.logger.warning(f"Run ID {run_id} not found. Creating new run.")
            self.start_new_run()
            run_id = self.current_run_id
        
        run_data = self.test_runs[run_id]
        
        # Add test result
        if test_id not in run_data["tests"]:
            run_data["tests"][test_id] = {}
        
        provider_model = f"{provider}/{model}"
        run_data["tests"][test_id][provider_model] = usage_data.to_dict()
        
        # Update summary
        summary = run_data["summary"]
        summary["total_cost"] += usage_data.total_cost
        summary["total_tokens"] += usage_data.total_tokens
        summary["prompt_tokens"] += usage_data.prompt_tokens
        summary["completion_tokens"] += usage_data.completion_tokens
        
        # Update model-specific summary
        if provider_model not in summary["py_models"]:
            summary["py_models"][provider_model] = {
                "total_cost": 0.0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "test_count": 0
            }
        
        model_summary = summary["py_models"][provider_model]
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
        for model_name, model_data in summary["py_models"].items():
            test_count = model_data["test_count"]
            if test_count > 0:
                model_averages[model_name] = {
                    "avg_cost_per_test": model_data["total_cost"] / test_count,
                    "avg_tokens_per_test": model_data["total_tokens"] / test_count,
                    "cost_per_token": model_data["total_cost"] / model_data["total_tokens"] if model_data["total_tokens"] > 0 else 0
                }
        
        # Create cost breakdown
        most_expensive_model = max(
            summary["py_models"].items(),
            key=lambda x: x[1]["total_cost"]
        )[0] if summary["py_models"] else None
        
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
            "py_models": summary["py_models"],
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
