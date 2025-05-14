"""
High-level manager for prompt provider operations.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel

from .base import BasePromptProvider
from .prompt_factory import create_prompt_provider, load_provider_config


class PromptManager:
    """
    Manages prompt providers, optimization, and performance tracking.
    
    This class provides a high-level interface for working with prompts,
    regardless of the underlying storage provider.
    """
    
    def __init__(self, provider_type: str = "file", config: Optional[Dict[str, Any]] = None):
        """
        Initialize with provider type and config.
        
        Args:
            provider_type: Type of provider (e.g. "file", "database", "api")
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.provider_type = provider_type
        
        # Load provider configuration
        provider_config = load_provider_config(provider_type)
        
        # Merge with provided config (provided config takes precedence)
        if provider_config and config:
            merged_config = {**provider_config, **config}
        else:
            merged_config = config or provider_config or {}
        
        # Create the provider instance
        self.provider = create_prompt_provider(provider_type, merged_config)
        if not self.provider:
            self.logger.error(f"Failed to create prompt provider of type '{provider_type}'")
    
    def get_prompt(self, prompt_id: str, version: Optional[str] = None, 
                  use_best_performing: bool = False) -> Tuple[str, Dict[str, Any]]:
        """
        Get a prompt by ID, version, or best performing.
        
        Args:
            prompt_id: Identifier for the prompt
            version: Optional version string
            use_best_performing: Whether to get the best performing version
            
        Returns:
            Tuple of (prompt_text, metadata)
        """
        if not self.provider:
            self.logger.error("No prompt provider available")
            return "", {}
        
        try:
            # Determine which version to get
            target_version = version
            if use_best_performing:
                best_version = self.provider.get_best_performing_version(prompt_id)
                if best_version:
                    target_version = best_version
                    self.logger.debug(f"Using best performing version '{best_version}' for prompt '{prompt_id}'")
            
            # Get the prompt
            return self.provider.get_prompt(prompt_id, target_version)
        
        except Exception as e:
            self.logger.error(f"Error getting prompt '{prompt_id}': {e}")
            return "", {}
    
    def get_system_prompt(self, system_prompt_id: str, 
                         version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get a system prompt by ID.
        
        Args:
            system_prompt_id: Identifier for the system prompt
            version: Optional version string
            
        Returns:
            Tuple of (system_prompt_text, metadata)
        """
        if not self.provider:
            self.logger.error("No prompt provider available")
            return "", {}
        
        try:
            return self.provider.get_system_prompt(system_prompt_id, version)
        
        except Exception as e:
            self.logger.error(f"Error getting system prompt '{system_prompt_id}': {e}")
            return "", {}
    
    def save_prompt(self, prompt_id: str, prompt_text: str, 
                   metadata: Dict[str, Any]) -> str:
        """
        Save a prompt.
        
        Args:
            prompt_id: Identifier for the prompt
            prompt_text: The prompt content
            metadata: Additional metadata for the prompt
            
        Returns:
            Version identifier or empty string on failure
        """
        if not self.provider:
            self.logger.error("No prompt provider available")
            return ""
        
        try:
            return self.provider.save_prompt(prompt_id, prompt_text, metadata)
        
        except Exception as e:
            self.logger.error(f"Error saving prompt '{prompt_id}': {e}")
            return ""
    
    def optimize_and_save(self, prompt_id: str, source: str, model_class: Type[BaseModel],
                         expected_data: Dict[str, Any], test_results: Dict[str, Any]) -> str:
        """
        Optimize a prompt based on test results and save it.
        
        Args:
            prompt_id: Identifier for the prompt
            source: Source text used for extraction
            model_class: Pydantic model class
            expected_data: Expected data structure
            test_results: Test results containing performance data
            
        Returns:
            Version identifier of the optimized prompt or empty string on failure
        """
        if not self.provider:
            self.logger.error("No prompt provider available")
            return ""
        
        try:
            from ..utils.prompt_optimizer import PromptOptimizer
            
            # Get the current prompt
            current_prompt, metadata = self.get_prompt(prompt_id)
            if not current_prompt:
                self.logger.error(f"Failed to get prompt '{prompt_id}' for optimization")
                return ""
            
            # Create optimizer and optimize the prompt
            optimizer = PromptOptimizer()
            optimized_prompt = optimizer.optimize_prompt(
                original_prompt=current_prompt,
                source=source,
                model_class=model_class,
                expected_data=expected_data,
                initial_results=test_results,
                save_to_file=False  # We'll save it using the provider instead
            )
            
            # Update metadata with optimization info
            optimization_metadata = {
                "optimized": True,
                "optimization_timestamp": import_datetime_iso(),
                "optimization_source": "PromptOptimizer",
                "previous_version": metadata.get("version", "unknown")
            }
            
            # Merge with existing metadata
            updated_metadata = {**metadata, **optimization_metadata}
            
            # Save the optimized prompt
            return self.provider.save_prompt(prompt_id, optimized_prompt, updated_metadata)
        
        except Exception as e:
            self.logger.error(f"Error optimizing prompt '{prompt_id}': {e}")
            return ""
    
    def record_test_results(self, prompt_id: str, version: str, 
                           test_results: Dict[str, Any]) -> bool:
        """
        Record test results for a prompt version.
        
        Args:
            prompt_id: Identifier for the prompt
            version: Version string
            test_results: Test results data
            
        Returns:
            Success status
        """
        if not self.provider:
            self.logger.error("No prompt provider available")
            return False
        
        try:
            # Extract performance data from test results
            performance_data = extract_performance_data(test_results)
            
            # Record the performance data
            return self.provider.record_performance(prompt_id, version, performance_data)
        
        except Exception as e:
            self.logger.error(f"Error recording performance for prompt '{prompt_id}': {e}")
            return False
    
    def compare_versions(self, prompt_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two versions of a prompt.
        
        Args:
            prompt_id: Identifier for the prompt
            version1: First version string
            version2: Second version string
            
        Returns:
            Comparison data dictionary
        """
        if not self.provider:
            self.logger.error("No prompt provider available")
            return {}
        
        try:
            # Get both prompts
            prompt1, metadata1 = self.get_prompt(prompt_id, version1)
            prompt2, metadata2 = self.get_prompt(prompt_id, version2)
            
            if not prompt1 or not prompt2:
                self.logger.error(f"Failed to get one or both versions of prompt '{prompt_id}'")
                return {}
            
            # Get performance data for both versions
            performance_history = self.provider.get_performance_history(prompt_id)
            perf1 = next((p for p in performance_history if p.get("version") == version1), {})
            perf2 = next((p for p in performance_history if p.get("version") == version2), {})
            
            # Compare the prompts
            return {
                "prompt_id": prompt_id,
                "versions": {
                    version1: {
                        "metadata": metadata1,
                        "performance": perf1,
                        "length": len(prompt1)
                    },
                    version2: {
                        "metadata": metadata2,
                        "performance": perf2,
                        "length": len(prompt2)
                    }
                },
                "diff_summary": simple_diff_summary(prompt1, prompt2)
            }
        
        except Exception as e:
            self.logger.error(f"Error comparing prompt versions for '{prompt_id}': {e}")
            return {}
    
    def get_performance_report(self, prompt_id: str) -> str:
        """
        Generate a performance report.
        
        Args:
            prompt_id: Identifier for the prompt
            
        Returns:
            Markdown formatted report
        """
        if not self.provider:
            self.logger.error("No prompt provider available")
            return ""
        
        try:
            # Get performance history
            performance_history = self.provider.get_performance_history(prompt_id)
            
            if not performance_history:
                return f"No performance data available for prompt '{prompt_id}'"
            
            # Generate markdown report
            report = f"# Performance Report for Prompt '{prompt_id}'\n\n"
            
            # Summary of versions
            report += "## Version Summary\n\n"
            report += "| Version | Date | Accuracy | Tokens |\n"
            report += "|---------|------|----------|--------|\n"
            
            for entry in sorted(performance_history, key=lambda x: x.get("timestamp", "")):
                version = entry.get("version", "unknown")
                timestamp = entry.get("timestamp", "unknown")
                accuracy = entry.get("accuracy", 0)
                tokens = entry.get("tokens", {}).get("total", 0)
                
                report += f"| {version} | {timestamp} | {accuracy:.2f}% | {tokens} |\n"
            
            # Best performing version
            best_version = self.provider.get_best_performing_version(prompt_id)
            if best_version:
                report += f"\n## Best Performing Version\n\n"
                report += f"Version: **{best_version}**\n"
            
            return report
        
        except Exception as e:
            self.logger.error(f"Error generating performance report for '{prompt_id}': {e}")
            return f"Error generating report: {str(e)}"


# Helper functions

def extract_performance_data(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract performance data from test results.
    
    Args:
        test_results: Test results dictionary
        
    Returns:
        Performance data dictionary
    """
    performance_data = {
        "timestamp": import_datetime_iso(),
        "accuracy": 0,
        "tokens": {
            "prompt": 0,
            "completion": 0,
            "total": 0
        },
        "cost": 0.0,
        "validation_success": False
    }
    
    # Extract data from each provider's results
    provider_accuracies = []
    provider_tokens = []
    provider_costs = []
    
    for provider, provider_results in test_results.items():
        if 'validation' in provider_results:
            validation = provider_results['validation']
            
            # Record accuracy
            if 'accuracy' in validation:
                provider_accuracies.append(validation['accuracy'])
            
            # Record validation success
            if validation.get('success', False):
                performance_data['validation_success'] = True
        
        # Record tokens and cost
        if 'usage' in provider_results:
            usage = provider_results['usage']
            tokens = {
                "prompt": usage.get('prompt_tokens', 0),
                "completion": usage.get('completion_tokens', 0),
                "total": usage.get('total_tokens', 0)
            }
            provider_tokens.append(tokens)
            provider_costs.append(usage.get('total_cost', 0.0))
    
    # Calculate averages
    if provider_accuracies:
        performance_data['accuracy'] = sum(provider_accuracies) / len(provider_accuracies)
    
    if provider_tokens:
        avg_tokens = {
            "prompt": sum(t['prompt'] for t in provider_tokens) / len(provider_tokens),
            "completion": sum(t['completion'] for t in provider_tokens) / len(provider_tokens),
            "total": sum(t['total'] for t in provider_tokens) / len(provider_tokens)
        }
        performance_data['tokens'] = avg_tokens
    
    if provider_costs:
        performance_data['cost'] = sum(provider_costs) / len(provider_costs)
    
    return performance_data


def import_datetime_iso() -> str:
    """Get current datetime in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()


def simple_diff_summary(text1: str, text2: str) -> Dict[str, Any]:
    """
    Generate a simple diff summary between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Summary dictionary
    """
    # Split into lines for comparison
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    
    # Basic stats
    return {
        "lines_changed": abs(len(lines2) - len(lines1)),
        "char_diff": abs(len(text2) - len(text1)),
        "similarity": calculate_similarity(text1, text2)
    }


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate a simple similarity score between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    # Simple implementation based on character overlap
    if not text1 or not text2:
        return 0.0
    
    # Set of characters in each text
    chars1 = set(text1)
    chars2 = set(text2)
    
    # Jaccard similarity: intersection / union
    intersection = len(chars1.intersection(chars2))
    union = len(chars1.union(chars2))
    
    return intersection / union if union > 0 else 0.0