"""
Enhanced prompt optimizer for improving LLM prompts.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel

from .base import BasePromptProvider


class PromptOptimizer:
    """
    Optimizes prompts based on test results and manages improvement cycles.
    
    This is an enhanced version of the original prompt optimizer with
    integration to the prompt provider system and more advanced optimization
    strategies.
    """
    
    def __init__(self, prompt_provider: Optional[BasePromptProvider] = None):
        """
        Initialize with an optional prompt provider.
        
        Args:
            prompt_provider: The prompt provider to use for storage
        """
        self.logger = logging.getLogger(__name__)
        self.prompt_provider = prompt_provider
    
    def optimize_prompt(
        self, 
        prompt_id: str,
        source: str, 
        model_class: Type[BaseModel], 
        expected_data: Dict[str, Any],
        test_results: Dict[str, Any],
        optimization_strategy: str = "auto"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Optimize a prompt based on test results.
        
        Args:
            prompt_id: Identifier for the prompt
            source: Source text used for extraction
            model_class: Pydantic model class for the extraction
            expected_data: Expected structured data
            test_results: Test results containing validation and performance data
            optimization_strategy: Strategy to use ('auto', 'field_focus', 'format_focus')
            
        Returns:
            Tuple of (optimized_prompt_text, optimization_metadata)
        """
        # Fetch the current prompt
        current_prompt = ""
        metadata = {}
        
        if self.prompt_provider:
            # Get from provider
            current_prompt, metadata = self.prompt_provider.get_prompt(prompt_id)
        
        # If we couldn't get it from the provider, or no provider is set, treat prompt_id as the text
        if not current_prompt:
            current_prompt = prompt_id
            self.logger.debug(f"Using prompt_id as the prompt text")
        
        # Analyze test results
        problems = self._analyze_results(test_results, expected_data)
        
        # Get model schema
        model_schema = model_class.schema()
        
        # Choose optimization strategy if set to auto
        if optimization_strategy == "auto":
            optimization_strategy = self._select_optimization_strategy(problems)
        
        # Create optimized prompt based on the selected strategy
        if optimization_strategy == "field_focus":
            optimized_prompt, opt_metadata = self._field_focus_optimization(
                current_prompt, model_schema, problems, source
            )
        elif optimization_strategy == "format_focus":
            optimized_prompt, opt_metadata = self._format_focus_optimization(
                current_prompt, model_schema, problems
            )
        else:
            # Default strategy
            optimized_prompt, opt_metadata = self._default_optimization(
                current_prompt, model_schema, problems
            )
        
        # Combine metadata
        optimization_metadata = {
            **metadata,
            **opt_metadata,
            "optimization_timestamp": datetime.now().isoformat(),
            "optimization_strategy": optimization_strategy,
            "previous_version": metadata.get("version", "unknown")
        }
        
        return optimized_prompt, optimization_metadata
    
    def save_optimized_prompt(
        self,
        prompt_id: str,
        optimized_text: str,
        optimization_metadata: Dict[str, Any]
    ) -> str:
        """
        Save an optimized prompt through the prompt provider.
        
        Args:
            prompt_id: Identifier for the prompt
            optimized_text: The optimized prompt text
            optimization_metadata: Metadata about the optimization
            
        Returns:
            Version identifier of the saved prompt
        """
        if not self.prompt_provider:
            self.logger.warning("No prompt provider available for saving")
            return ""
        
        try:
            return self.prompt_provider.save_prompt(prompt_id, optimized_text, optimization_metadata)
        except Exception as e:
            self.logger.error(f"Error saving optimized prompt: {e}")
            return ""
    
    def optimize_and_save(
        self,
        prompt_id: str,
        source: str,
        model_class: Type[BaseModel],
        expected_data: Dict[str, Any],
        test_results: Dict[str, Any],
        optimization_strategy: str = "auto"
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Optimize a prompt and save it through the prompt provider.
        
        Args:
            prompt_id: Identifier for the prompt
            source: Source text used for extraction
            model_class: Pydantic model class for the extraction
            expected_data: Expected structured data
            test_results: Test results containing validation and performance data
            optimization_strategy: Strategy to use ('auto', 'field_focus', 'format_focus')
            
        Returns:
            Tuple of (optimized_prompt_text, version, optimization_metadata)
        """
        # Optimize the prompt
        optimized_text, optimization_metadata = self.optimize_prompt(
            prompt_id, source, model_class, expected_data, test_results, optimization_strategy
        )
        
        # Save if we have a provider
        version = ""
        if self.prompt_provider:
            version = self.save_optimized_prompt(prompt_id, optimized_text, optimization_metadata)
        
        return optimized_text, version, optimization_metadata
    
    def compare_prompt_versions(
        self,
        prompt_id: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of a prompt.
        
        Args:
            prompt_id: Identifier for the prompt
            version1: First version string
            version2: Second version string
            
        Returns:
            Comparison data
        """
        if not self.prompt_provider:
            self.logger.warning("No prompt provider available for version comparison")
            return {}
        
        try:
            # Get both prompts
            prompt1, metadata1 = self.prompt_provider.get_prompt(prompt_id, version1)
            prompt2, metadata2 = self.prompt_provider.get_prompt(prompt_id, version2)
            
            if not prompt1 or not prompt2:
                self.logger.error(f"Failed to get one or both versions of prompt '{prompt_id}'")
                return {}
            
            # Compare the prompts
            return {
                "prompt_id": prompt_id,
                "versions": {
                    version1: {
                        "metadata": metadata1,
                        "length": len(prompt1)
                    },
                    version2: {
                        "metadata": metadata2,
                        "length": len(prompt2)
                    }
                },
                "diff": self._compute_diff(prompt1, prompt2)
            }
        
        except Exception as e:
            self.logger.error(f"Error comparing prompt versions: {e}")
            return {}
    
    # Private helper methods
    
    def _analyze_results(
        self, 
        results: Dict[str, Any], 
        expected_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze results to identify problems.
        
        Args:
            results: Test results
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
        Identify specific field problems.
        
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
                        if isinstance(expected_item, dict) and isinstance(actual_item, dict):
                            nested_problems = self._identify_field_problems(actual_item, expected_item)
                            for problem in nested_problems:
                                problem['field'] = f"{key}[{i}].{problem['field']}"
                                field_problems.append(problem)
                        elif expected_item != actual_item:
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
    
    def _select_optimization_strategy(self, problems: List[Dict[str, Any]]) -> str:
        """
        Select the best optimization strategy based on problems.
        
        Args:
            problems: List of identified problems
            
        Returns:
            Strategy name
        """
        validation_errors = any(p['type'] == 'validation_error' for p in problems)
        
        if validation_errors:
            return "format_focus"
        
        # Count field problems
        field_problems = []
        for problem in problems:
            if problem['type'] == 'accuracy_issue':
                field_problems.extend(problem.get('field_problems', []))
        
        if field_problems:
            return "field_focus"
        
        return "default"
    
    def _default_optimization(
        self,
        original_prompt: str,
        model_schema: Dict[str, Any],
        problems: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create an optimized prompt using the default strategy.
        
        Args:
            original_prompt: Original prompt text
            model_schema: Pydantic model schema
            problems: Identified problems
            
        Returns:
            Tuple of (optimized_prompt, optimization_metadata)
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
        
        # Create optimization metadata
        optimization_metadata = {
            'strategy': 'default',
            'problems_found': len(problems),
            'clarifications_added': len(clarifications)
        }
        
        return optimized_prompt, optimization_metadata
    
    def _field_focus_optimization(
        self,
        original_prompt: str,
        model_schema: Dict[str, Any],
        problems: List[Dict[str, Any]],
        source: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create an optimized prompt focusing on field extraction.
        
        Args:
            original_prompt: Original prompt text
            model_schema: Pydantic model schema
            problems: Identified problems
            source: Source text
            
        Returns:
            Tuple of (optimized_prompt, optimization_metadata)
        """
        # Start with the default optimization
        optimized_prompt, optimization_metadata = self._default_optimization(
            original_prompt, model_schema, problems
        )
        
        # Get all field problems
        all_field_problems = []
        for problem in problems:
            if problem['type'] == 'accuracy_issue':
                all_field_problems.extend(problem.get('field_problems', []))
        
        # If there are significant field problems, add more specific guidance
        if all_field_problems:
            # Extract schema information
            schema_info = self._extract_schema_info(model_schema)
            
            # Find problematic fields
            problem_fields = set(p['field'] for p in all_field_problems)
            
            # Create field-specific instructions
            field_instructions = []
            
            for field in problem_fields:
                # Get the field schema
                field_schema = schema_info.get(field, {})
                field_type = field_schema.get('type', 'unknown')
                field_description = field_schema.get('description', '')
                
                instruction = f"For the field '{field}':"
                
                if field_description:
                    instruction += f" {field_description}"
                
                if field_type == 'string':
                    instruction += " Extract the exact text as shown."
                elif field_type == 'number':
                    instruction += " Extract as a numeric value without units."
                elif field_type == 'integer':
                    instruction += " Extract as a whole number."
                elif field_type == 'boolean':
                    instruction += " Use true/false values based on yes/no in the text."
                elif field_type == 'array':
                    instruction += " Include all items in a list."
                
                field_instructions.append(instruction)
            
            # Add the field instructions
            if field_instructions:
                field_section = "\n\nFIELD-SPECIFIC INSTRUCTIONS:\n" + "\n".join(field_instructions)
                optimized_prompt += field_section
        
        # Update metadata
        optimization_metadata.update({
            'strategy': 'field_focus',
            'problematic_fields': len(all_field_problems)
        })
        
        return optimized_prompt, optimization_metadata
    
    def _format_focus_optimization(
        self,
        original_prompt: str,
        model_schema: Dict[str, Any],
        problems: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create an optimized prompt focusing on format/structure.
        
        Args:
            original_prompt: Original prompt text
            model_schema: Pydantic model schema
            problems: Identified problems
            
        Returns:
            Tuple of (optimized_prompt, optimization_metadata)
        """
        # Start with the default optimization
        optimized_prompt, optimization_metadata = self._default_optimization(
            original_prompt, model_schema, problems
        )
        
        # Check if there are validation errors
        validation_errors = [p for p in problems if p['type'] == 'validation_error']
        
        if validation_errors:
            # Add explicit JSON format instructions
            json_section = "\n\nJSON FORMAT INSTRUCTIONS:\n"
            json_section += "- Your response MUST be valid JSON\n"
            json_section += "- Use double quotes for all keys and string values\n"
            json_section += "- Do not include comments in the JSON\n"
            json_section += "- Do not include markdown formatting around the JSON\n"
            json_section += "- Ensure all arrays have matching brackets\n"
            json_section += "- Ensure all objects have matching braces\n"
            
            # Add a simplified schema example
            schema_example = self._generate_schema_example(model_schema)
            if schema_example:
                json_section += "\n\nFollow this JSON structure:\n```json\n"
                json_section += schema_example
                json_section += "\n```"
            
            optimized_prompt += json_section
        
        # Update metadata
        optimization_metadata.update({
            'strategy': 'format_focus',
            'validation_errors': len(validation_errors)
        })
        
        return optimized_prompt, optimization_metadata
    
    def _extract_schema_info(self, schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract field information from a Pydantic schema.
        
        Args:
            schema: Pydantic model schema
            
        Returns:
            Dictionary mapping field paths to their schema info
        """
        result = {}
        
        # Process properties
        properties = schema.get('properties', {})
        for field_name, field_schema in properties.items():
            result[field_name] = {
                'type': field_schema.get('type', 'unknown'),
                'description': field_schema.get('description', '')
            }
            
            # Handle nested objects
            if field_schema.get('type') == 'object' and 'properties' in field_schema:
                nested_schema = self._extract_schema_info(field_schema)
                for nested_field, nested_info in nested_schema.items():
                    result[f"{field_name}.{nested_field}"] = nested_info
            
            # Handle arrays
            if field_schema.get('type') == 'array' and 'items' in field_schema:
                items_schema = field_schema['items']
                result[field_name] = {
                    'type': 'array',
                    'items_type': items_schema.get('type', 'unknown'),
                    'description': field_schema.get('description', '')
                }
                
                # Handle arrays of objects
                if items_schema.get('type') == 'object' and 'properties' in items_schema:
                    nested_schema = self._extract_schema_info(items_schema)
                    for nested_field, nested_info in nested_schema.items():
                        result[f"{field_name}[].{nested_field}"] = nested_info
        
        return result
    
    def _generate_schema_example(self, schema: Dict[str, Any]) -> str:
        """
        Generate a simplified JSON example from a schema.
        
        Args:
            schema: Pydantic model schema
            
        Returns:
            JSON example as a string
        """
        try:
            import json
            
            # Create a simplified example
            example = {}
            
            for field_name, field_schema in schema.get('properties', {}).items():
                field_type = field_schema.get('type', 'string')
                
                if field_type == 'string':
                    example[field_name] = "string value"
                elif field_type == 'number':
                    example[field_name] = 123.45
                elif field_type == 'integer':
                    example[field_name] = 123
                elif field_type == 'boolean':
                    example[field_name] = True
                elif field_type == 'array':
                    items_type = field_schema.get('items', {}).get('type', 'string')
                    if items_type == 'string':
                        example[field_name] = ["item1", "item2"]
                    elif items_type == 'object':
                        example[field_name] = [{"prop": "value"}]
                    else:
                        example[field_name] = [1, 2, 3]
                elif field_type == 'object':
                    example[field_name] = {"property": "value"}
            
            return json.dumps(example, indent=2)
        
        except Exception as e:
            self.logger.error(f"Error generating schema example: {e}")
            return ""
    
    def _compute_diff(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compute a simple diff between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Diff information
        """
        try:
            import difflib
            
            # Split into lines
            lines1 = text1.splitlines()
            lines2 = text2.splitlines()
            
            # Compute diff
            diff = list(difflib.unified_diff(
                lines1, lines2, 
                lineterm='',
                n=3  # Context lines
            ))
            
            # Count additions and deletions
            additions = len([line for line in diff if line.startswith('+')])
            deletions = len([line for line in diff if line.startswith('-')])
            
            return {
                'diff': '\n'.join(diff),
                'additions': additions,
                'deletions': deletions,
                'total_changes': additions + deletions,
                'similarity': self._calculate_similarity(text1, text2)
            }
        
        except Exception as e:
            self.logger.error(f"Error computing diff: {e}")
            return {
                'error': str(e)
            }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        try:
            import difflib
            return difflib.SequenceMatcher(None, text1, text2).ratio()
        except Exception:
            # Fallback to a simpler implementation
            if not text1 or not text2:
                return 0.0
            
            chars1 = set(text1)
            chars2 = set(text2)
            
            intersection = len(chars1.intersection(chars2))
            union = len(chars1.union(chars2))
            
            return intersection / union if union > 0 else 0.0