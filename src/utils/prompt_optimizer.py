"""
Prompt optimizer for improving LLM prompts
"""

from typing import Dict, Any, List, Optional
import json
import logging


class PromptOptimizer:
    """
    Optimizes prompts based on initial test results
    """
    
    def __init__(self):
        """Initialize the prompt optimizer"""
        self.logger = logging.getLogger(__name__)
    
    def optimize_prompt(
        self, 
        original_prompt: str, 
        source: str, 
        model_class: Any, 
        expected_data: Dict[str, Any],
        initial_results: Dict[str, Any],
        save_to_file: bool = False,
        original_prompt_path: Optional[str] = None
    ) -> str:
        """
        Optimize a prompt based on initial results
        
        Args:
            original_prompt: Original prompt text
            source: Source text
            model_class: Pydantic model class
            expected_data: Expected data
            initial_results: Initial test results
            save_to_file: Whether to save the optimized prompt to a file
            original_prompt_path: Path to the original prompt file, used to determine where to save
            
        Returns:
            Optimized prompt text
        """
        # Analyze initial results to identify problems
        problems = self._analyze_results(initial_results, expected_data)
        
        # Get model schema
        model_schema = model_class.schema()
        
        # Create optimized prompt
        optimized_prompt = self._create_optimized_prompt(
            original_prompt=original_prompt,
            model_schema=model_schema,
            problems=problems
        )
        
        # Save optimized prompt to a file if requested
        if save_to_file and original_prompt_path:
            import os
            
            # Create the optimized prompts directory
            prompts_dir = os.path.dirname(original_prompt_path)
            optimized_dir = os.path.join(prompts_dir, "optimized")
            
            # Ensure the directory exists
            if not os.path.exists(optimized_dir):
                try:
                    os.makedirs(optimized_dir, exist_ok=True)
                except OSError as e:
                    # If there's an error creating the directory, fall back to the parent directory
                    self.logger.warning(f"Could not create optimized directory: {e}")
                    optimized_dir = prompts_dir
            
            # Get the filename from the original path
            filename = os.path.basename(original_prompt_path)
            base_name, ext = os.path.splitext(filename)
            
            # Create the optimized prompt path
            optimized_path = os.path.join(optimized_dir, f"{base_name}{ext}")
            
            # Save the optimized prompt
            with open(optimized_path, 'w') as f:
                f.write(optimized_prompt)
        
        return optimized_prompt
    
    def _analyze_results(
        self, 
        results: Dict[str, Any], 
        expected_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze results to identify problems
        
        Args:
            results: Initial test results
            expected_data: Expected data
            
        Returns:
            List of identified problems
        """
        problems = []
        
        for provider, provider_results in results.items():
            if 'error' in provider_results:
                # Provider had an error
                problems.append({
                    'type': 'provider_error',
                    'provider': provider,
                    'error': provider_results['error']
                })
                continue
            
            validation = provider_results.get('validation', {})
            
            if not validation.get('success', False):
                # Validation failed
                problems.append({
                    'type': 'validation_error',
                    'provider': provider,
                    'error': validation.get('error', 'Unknown validation error')
                })
                continue
            
            # Check accuracy
            accuracy = validation.get('accuracy', 0.0)
            
            if accuracy < 100.0:
                # Not fully accurate
                validated_data = validation.get('validated_data', {})
                
                # Find specific fields with problems
                field_problems = self._identify_field_problems(validated_data, expected_data)
                
                problems.append({
                    'type': 'accuracy_issue',
                    'provider': provider,
                    'accuracy': accuracy,
                    'field_problems': field_problems
                })
        
        return problems
    
    def _identify_field_problems(
        self, 
        actual: Dict[str, Any], 
        expected: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify specific field problems
        
        Args:
            actual: Actual data
            expected: Expected data
            
        Returns:
            List of field problems
        """
        field_problems = []
        
        for key, expected_value in expected.items():
            if key not in actual:
                # Missing field
                field_problems.append({
                    'field': key,
                    'type': 'missing_field',
                    'expected': expected_value
                })
            else:
                actual_value = actual[key]
                
                if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                    # Recursively check nested fields
                    nested_problems = self._identify_field_problems(actual_value, expected_value)
                    
                    for problem in nested_problems:
                        problem['field'] = f"{key}.{problem['field']}"
                        field_problems.append(problem)
                elif isinstance(expected_value, list) and isinstance(actual_value, list):
                    # Check lists
                    if len(expected_value) != len(actual_value):
                        field_problems.append({
                            'field': key,
                            'type': 'list_length_mismatch',
                            'expected_length': len(expected_value),
                            'actual_length': len(actual_value)
                        })
                    
                    for i, (expected_item, actual_item) in enumerate(zip(expected_value, actual_value)):
                        if expected_item != actual_item:
                            field_problems.append({
                                'field': f"{key}[{i}]",
                                'type': 'value_mismatch',
                                'expected': expected_item,
                                'actual': actual_item
                            })
                elif expected_value != actual_value:
                    # Simple value mismatch
                    field_problems.append({
                        'field': key,
                        'type': 'value_mismatch',
                        'expected': expected_value,
                        'actual': actual_value
                    })
        
        # Check for extra fields
        for key in actual:
            if key not in expected:
                field_problems.append({
                    'field': key,
                    'type': 'unexpected_field',
                    'value': actual[key]
                })
        
        return field_problems
    
    def _create_optimized_prompt(
        self, 
        original_prompt: str, 
        model_schema: Dict[str, Any],
        problems: List[Dict[str, Any]]
    ) -> str:
        """
        Create an optimized prompt based on problems
        
        Args:
            original_prompt: Original prompt text
            model_schema: Pydantic model schema (for reference only, not included in prompt)
            problems: Identified problems
            
        Returns:
            Optimized prompt text
        """
        # Start with the original prompt
        optimized_prompt = original_prompt
        
        # Add clarifications based on problems
        clarifications = []
        
        # Check for validation errors
        validation_errors = [p for p in problems if p['type'] == 'validation_error']
        if validation_errors:
            clarifications.append("IMPORTANT: Your response must be valid JSON with the requested fields and formats.")
        
        # Check for accuracy issues
        accuracy_issues = [p for p in problems if p['type'] == 'accuracy_issue']
        
        if accuracy_issues:
            # Collect all field problems
            all_field_problems = []
            for issue in accuracy_issues:
                all_field_problems.extend(issue.get('field_problems', []))
            
            # Group by field
            field_to_problems = {}
            for problem in all_field_problems:
                field = problem['field']
                if field not in field_to_problems:
                    field_to_problems[field] = []
                field_to_problems[field].append(problem)
            
            # Add clarifications for problematic fields
            for field, field_problems in field_to_problems.items():
                problem_types = set(p['type'] for p in field_problems)
                
                if 'missing_field' in problem_types:
                    clarifications.append(f"The field '{field}' must be included in your response.")
                elif 'value_mismatch' in problem_types:
                    clarifications.append(f"Pay special attention to the value of '{field}' to ensure accuracy.")
                elif 'list_length_mismatch' in problem_types:
                    clarifications.append(f"Ensure you extract all items for the list '{field}'.")
                elif 'unexpected_field' in problem_types:
                    clarifications.append(f"Do not include extra field '{field}' in your response.")
        
        # Combine clarifications with the original prompt
        if clarifications:
            clarifications_text = "\n".join(clarifications)
            optimized_prompt = f"{original_prompt}\n\nADDITIONAL INSTRUCTIONS:\n{clarifications_text}"
            
            # Add general tips for better extraction
            optimized_prompt += "\n\nIMPORTANT TIPS FOR ACCURATE EXTRACTION:"
            optimized_prompt += "\n- Extract all required information exactly as presented in the source text"
            optimized_prompt += "\n- Format dates in ISO format (YYYY-MM-DD)"
            optimized_prompt += "\n- Use proper boolean values (true/false) for yes/no fields"
            optimized_prompt += "\n- Keep list items in the order they appear in the text"
            optimized_prompt += "\n- Format your response as valid JSON"
        else:
            # If no specific problems, just add general guidance
            optimized_prompt = original_prompt
        
        return optimized_prompt