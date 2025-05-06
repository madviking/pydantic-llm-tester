"""
Report generator for creating test reports
"""

from typing import Dict, Any, List
import json
from datetime import datetime, date


# Custom JSON encoder that can handle date objects and other Pydantic types
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        # Handle URL objects from pydantic
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'HttpUrl':
            return str(obj)
        # Handle other pydantic objects with __str__ method
        if hasattr(obj, '__str__'):
            try:
                json.dumps(str(obj))  # Test if the string is JSON serializable
                return str(obj)
            except:
                pass
        return super().default(obj)


class ReportGenerator:
    """
    Generates reports from test results
    """
    
    def generate_report(self, results: Dict[str, Any], optimized: bool = False) -> str:
        """
        Generate a report from test results
        
        Args:
            results: Test results
            optimized: Whether results are from optimized tests
            
        Returns:
            Report text
        """
        report_lines = []
        
        # Add report header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_lines.append(f"# LLM Tester Report - {timestamp}")
        report_lines.append("")
        
        if optimized:
            report_lines.append("## Optimized Prompts Performance Report")
            report_lines.append("")
            
            # Generate report for optimized tests
            for test_name, test_results in results.items():
                report_lines.append(f"### Test: {test_name}")
                report_lines.append("")
                
                # Compare original and optimized results
                original_results = test_results.get('original_results', {})
                optimized_results = test_results.get('optimized_results', {})
                
                # Summary table
                report_lines.append("#### Performance Comparison")
                report_lines.append("")
                report_lines.append("| Provider | Model | Original Accuracy | Optimized Accuracy | Improvement |")
                report_lines.append("|----------|-------|------------------|-------------------|------------|")

                # Iterate through providers and then models for optimized results
                for provider_name, model_results in optimized_results.items():
                    # Ensure model_results is a dictionary before iterating
                    if not isinstance(model_results, dict):
                         continue # Skip if not the expected format

                    for model_name, result_data in model_results.items():
                        original_result = original_results.get(provider_name, {}).get(model_name, {}) # Get corresponding original result
                        optimized_result = result_data # This is the optimized result

                        original_accuracy = self._get_accuracy(original_result)
                        optimized_accuracy = self._get_accuracy(optimized_result)
                        improvement = optimized_accuracy - original_accuracy

                        report_lines.append(f"| {provider_name} | {model_name} | {original_accuracy:.2f}% | {optimized_accuracy:.2f}% | {improvement:+.2f}% |")

                report_lines.append("")

                # Show original and optimized prompts (assuming one prompt per test case)
                report_lines.append("#### Prompt Optimization")
                report_lines.append("")
                report_lines.append("Original Prompt:")
                report_lines.append("```")
                # Assuming original_prompt is stored at the test_name level in optimized results
                report_lines.append(test_results.get('original_prompt', 'N/A'))
                report_lines.append("```")
                report_lines.append("")
                report_lines.append("Optimized Prompt:")
                report_lines.append("```")
                # Assuming optimized_prompt is stored at the test_name level in optimized results
                report_lines.append(test_results.get('optimized_prompt', 'N/A'))
                report_lines.append("```")
                report_lines.append("")

                # Provider-specific details
                report_lines.append("#### Provider Details")
                report_lines.append("")

                # Iterate through providers and then models for optimized results details
                for provider_name, model_results in optimized_results.items():
                    # Ensure model_results is a dictionary before iterating
                    if not isinstance(model_results, dict):
                         continue # Skip if not the expected format

                    report_lines.append(f"##### {provider_name}")
                    report_lines.append("")

                    for model_name, result_data in model_results.items():
                        report_lines.append(f"###### Model: {model_name}")
                        report_lines.append("")

                        validation = result_data.get('validation', {})

                        if 'error' in result_data:
                            report_lines.append(f"Error: {result_data['error']}")
                        elif not validation.get('success', False):
                            report_lines.append(f"Validation failed: {validation.get('error', 'Unknown error')}")
                        else:
                            report_lines.append(f"Accuracy: {validation.get('accuracy', 0.0):.2f}%")

                            # Show validated data
                            validated_data = validation.get('validated_data', {})
                            if validated_data:
                                report_lines.append("")
                                report_lines.append("Extracted Data:")
                                report_lines.append("```json")
                                report_lines.append(json.dumps(validated_data, indent=2, cls=DateEncoder))
                                report_lines.append("```")

                        report_lines.append("") # Add a blank line after each model's details

        else:
            report_lines.append("## Standard Performance Report")
            report_lines.append("")

            # Generate report for standard tests
            for test_name, test_results in results.items():
                # Skip 'model_class' entry if it exists at the test_name level (shouldn't after refactor)
                if test_name == 'model_class':
                    continue

                report_lines.append(f"### Test: {test_name}")
                report_lines.append("")

                # Summary table
                report_lines.append("#### Performance Summary")
                report_lines.append("")
                report_lines.append("| Provider | Model | Accuracy |")
                report_lines.append("|----------|-------|----------|")

                # Iterate through providers and then models for standard results
                for provider_name, model_results in test_results.items():
                    # Ensure model_results is a dictionary before iterating
                    if not isinstance(model_results, dict):
                         continue # Skip if not the expected format

                    for model_name, result_data in model_results.items():
                        accuracy = self._get_accuracy(result_data)
                        report_lines.append(f"| {provider_name} | {model_name} | {accuracy:.2f}% |")

                report_lines.append("")

                # Provider-specific details
                report_lines.append("#### Provider Details")
                report_lines.append("")

                # Iterate through providers and then models for standard results details
                for provider_name, model_results in test_results.items():
                    # Ensure model_results is a dictionary before iterating
                    if not isinstance(model_results, dict):
                         continue # Skip if not the expected format

                    report_lines.append(f"##### {provider_name}")
                    report_lines.append("")

                    for model_name, result_data in model_results.items():
                        report_lines.append(f"###### Model: {model_name}")
                        report_lines.append("")

                        validation = result_data.get('validation', {})

                        if 'error' in result_data:
                            report_lines.append(f"Error: {result_data['error']}")
                        elif not validation.get('success', False):
                            report_lines.append(f"Validation failed: {validation.get('error', 'Unknown error')}")
                        else:
                            report_lines.append(f"Accuracy: {validation.get('accuracy', 0.0):.2f}%")

                            # Show validated data
                            validated_data = validation.get('validated_data', {})
                            if validated_data:
                                report_lines.append("")
                                report_lines.append("Extracted Data:")
                                report_lines.append("```json")
                                report_lines.append(json.dumps(validated_data, indent=2, cls=DateEncoder))
                                report_lines.append("```")

                        report_lines.append("") # Add a blank line after each model's details


        return "\n".join(report_lines)

    def _get_accuracy(self, result_data: Dict[str, Any]) -> float:
        """
        Get accuracy from result data (for a specific model run).

        Args:
            result_data: Dictionary containing the result for a single model run.

        Returns:
            Accuracy percentage.
        """
        if not isinstance(result_data, dict):
            # This should ideally not happen with the new structure, but keep for safety.
            return 0.0

        if 'error' in result_data:
            return 0.0

        validation = result_data.get('validation', {})

        if not validation.get('success', False):
            return 0.0

        return validation.get('accuracy', 0.0)
