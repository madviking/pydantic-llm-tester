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
                
                for provider in original_results.keys():
                    original_result = original_results.get(provider, {})
                    optimized_result = optimized_results.get(provider, {})
                    
                    original_accuracy = self._get_accuracy(original_result)
                    optimized_accuracy = self._get_accuracy(optimized_result)
                    improvement = optimized_accuracy - original_accuracy
                    
                    # Get model information
                    model = optimized_result.get('model') or original_result.get('model') or "default"
                    
                    report_lines.append(f"| {provider} | {model} | {original_accuracy:.2f}% | {optimized_accuracy:.2f}% | {improvement:+.2f}% |")
                
                report_lines.append("")
                
                # Show original and optimized prompts
                report_lines.append("#### Prompt Optimization")
                report_lines.append("")
                report_lines.append("Original Prompt:")
                report_lines.append("```")
                report_lines.append(test_results.get('original_prompt', 'N/A'))
                report_lines.append("```")
                report_lines.append("")
                report_lines.append("Optimized Prompt:")
                report_lines.append("```")
                report_lines.append(test_results.get('optimized_prompt', 'N/A'))
                report_lines.append("```")
                report_lines.append("")
                
                # Provider-specific details
                report_lines.append("#### Provider Details")
                report_lines.append("")
                
                for provider in optimized_results.keys():
                    report_lines.append(f"##### {provider}")
                    report_lines.append("")
                    
                    provider_result = optimized_results.get(provider, {})
                    validation = provider_result.get('validation', {})
                    
                    if 'error' in provider_result:
                        report_lines.append(f"Error: {provider_result['error']}")
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
                    
                    report_lines.append("")
        else:
            report_lines.append("## Standard Performance Report")
            report_lines.append("")
            
            # Generate report for standard tests
            for test_name, test_results in results.items():
                report_lines.append(f"### Test: {test_name}")
                report_lines.append("")
                
                # Summary table
                report_lines.append("#### Performance Summary")
                report_lines.append("")
                report_lines.append("| Provider | Model | Accuracy |")
                report_lines.append("|----------|-------|----------|")
                
                for provider, provider_result in test_results.items():
                    if provider == 'model_class':
                        continue
                    accuracy = self._get_accuracy(provider_result)
                    model = provider_result.get('model', 'default')
                    report_lines.append(f"| {provider} | {model} | {accuracy:.2f}% |")
                
                report_lines.append("")
                
                # Provider-specific details
                report_lines.append("#### Provider Details")
                report_lines.append("")
                
                for provider, provider_result in test_results.items():
                    if provider == 'model_class':
                        continue
                    report_lines.append(f"##### {provider}")
                    report_lines.append("")
                    
                    # Ensure provider_result is a dict before accessing .get, though _get_accuracy handles it.
                    # The main issue is accessing .get on ModelMetaclass or doing 'in' operator.
                    # The `isinstance` check in `_get_accuracy` handles non-dicts for accuracy calculation.
                    # For other operations, we rely on `provider_result` being a dict due to the filter.
                    validation = provider_result.get('validation', {})
                    
                    if 'error' in provider_result: # This is safe if provider_result is a dict
                        report_lines.append(f"Error: {provider_result['error']}")
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
                    
                    report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _get_accuracy(self, provider_result: Dict[str, Any]) -> float:
        """
        Get accuracy from provider result
        
        Args:
            provider_result: Provider test result
            
        Returns:
            Accuracy percentage
        """
        if not isinstance(provider_result, dict):
            # TODO: Add logging here if a logger becomes available in this class
            # print(f"WARNING: _get_accuracy called with non-dict type: {type(provider_result)}", file=sys.stderr)
            return 0.0 # Return 0.0 for non-dict inputs, as it's an error state for accuracy

        if 'error' in provider_result:
            return 0.0
        
        validation = provider_result.get('validation', {})
        
        if not validation.get('success', False):
            return 0.0
        
        return validation.get('accuracy', 0.0)
