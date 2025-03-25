"""
Main LLM Tester class for running tests and generating reports
"""

import os
import importlib
import json
from typing import List, Dict, Any, Optional, Type, Tuple
import logging
import inspect

from pydantic import BaseModel

from .utils.prompt_optimizer import PromptOptimizer
from .utils.report_generator import ReportGenerator, DateEncoder
from .utils.provider_manager import ProviderManager
from .utils.config_manager import load_config, get_test_setting, get_provider_model
from .utils.cost_manager import cost_tracker, UsageData


class LLMTester:
    """
    Main class for testing LLM models against pydantic schemas
    """
    
    def __init__(self, providers: List[str], test_dir: Optional[str] = None):
        """
        Initialize the LLM tester
        
        Args:
            providers: List of LLM provider names to test
            test_dir: Directory containing test files
        """
        self.providers = providers
        self.test_dir = test_dir or os.path.join(os.path.dirname(__file__), "tests")
        self.provider_manager = ProviderManager(providers)
        self.prompt_optimizer = PromptOptimizer()
        self.report_generator = ReportGenerator()
        self.logger = logging.getLogger(__name__)
        
        # Test case directories
        self.cases_dir = os.path.join(self.test_dir, "cases")
        
        # Initialize cost tracking
        self.run_id = cost_tracker.start_new_run()
        self.logger.info(f"Started new test run with ID: {self.run_id}")
        
        self._verify_directories()
    
    def _verify_directories(self) -> None:
        """Verify that required directories exist"""
        if not os.path.exists(self.cases_dir):
            self.logger.warning(f"Cases directory {self.cases_dir} does not exist")
    
    def discover_test_cases(self) -> List[Dict[str, Any]]:
        """
        Discover available test cases by scanning directories
        
        Returns:
            List of test case configurations
        """
        test_cases = []
        
        # Scan for modules under the cases directory
        for module_name in os.listdir(self.cases_dir):
            module_path = os.path.join(self.cases_dir, module_name)
            
            # Skip non-directories and special directories
            if not os.path.isdir(module_path) or module_name.startswith('__'):
                continue
            
            # Check for sources, prompts, and expected subdirectories
            sources_dir = os.path.join(module_path, "sources")
            prompts_dir = os.path.join(module_path, "prompts")
            expected_dir = os.path.join(module_path, "expected")
            
            if not all(os.path.exists(d) for d in [sources_dir, prompts_dir, expected_dir]):
                self.logger.warning(f"Module {module_name} is missing required subdirectories")
                continue
            
            # Get test case base names (from source files without extension)
            for source_file in os.listdir(sources_dir):
                if not source_file.endswith('.txt'):
                    continue
                    
                base_name = os.path.splitext(source_file)[0]
                prompt_file = f"{base_name}.txt"
                expected_file = f"{base_name}.json"
                
                if not os.path.exists(os.path.join(prompts_dir, prompt_file)):
                    self.logger.warning(f"Missing prompt file for {module_name}/{base_name}")
                    continue
                    
                if not os.path.exists(os.path.join(expected_dir, expected_file)):
                    self.logger.warning(f"Missing expected file for {module_name}/{base_name}")
                    continue
                
                # Load associated model
                model_class = self._find_model_class(module_name, base_name)
                if not model_class:
                    self.logger.warning(f"Could not find model for {module_name}/{base_name}")
                    continue
                
                test_case = {
                    'module': module_name,
                    'name': base_name,
                    'model_class': model_class,
                    'source_path': os.path.join(sources_dir, source_file),
                    'prompt_path': os.path.join(prompts_dir, prompt_file),
                    'expected_path': os.path.join(expected_dir, expected_file)
                }
                
                test_cases.append(test_case)
        
        return test_cases
    
    def _find_model_class(self, module_name: str, base_name: str) -> Optional[Type[BaseModel]]:
        """
        Find the pydantic model class for a test case
        
        Args:
            module_name: Name of the module (e.g., 'job_ads')
            base_name: Base name of the test case (doesn't matter, we use the main model)
            
        Returns:
            Pydantic model class or None if not found
        """
        try:
            # Try to import the module
            module_path = f"llm_tester.models.{module_name}"
            module = importlib.import_module(module_path)
            
            # For job_ads, use the single JobAd model
            if module_name == 'job_ads':
                return module.JobAd
                
            # For product_descriptions, use the ProductDescription model
            if module_name == 'product_descriptions':
                return module.ProductDescription
            
            # For other modules, try to find a main model class
            # First try to find a class with the same name as the module
            module_class_name = ''.join(word.capitalize() for word in module_name.split('_'))
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseModel):
                    # Look for the main class in the module
                    if name == module_class_name or name == f"{module_class_name}Model" or name == "Model":
                        return obj
            
            # If no matching class found, return the first BaseModel subclass
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                    return obj
            
            return None
            
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Error loading model: {str(e)}")
            return None
    
    def run_test(self, test_case: Dict[str, Any], model_overrides: Optional[Dict[str, str]] = None, 
                 progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Run a single test for all providers
        
        Args:
            test_case: Test case configuration
            model_overrides: Optional dictionary mapping providers to model names
            progress_callback: Optional callback function for reporting progress
            
        Returns:
            Test results for each provider
        """
        test_id = f"{test_case['module']}/{test_case['name']}"
        
        if progress_callback:
            progress_callback(f"Running test: {test_id}")
        
        # Load source, prompt, and expected data
        with open(test_case['source_path'], 'r') as f:
            source_text = f.read()
        
        with open(test_case['prompt_path'], 'r') as f:
            prompt_text = f.read()
        
        with open(test_case['expected_path'], 'r') as f:
            expected_data = json.load(f)
        
        # Get model class
        model_class = test_case['model_class']
        
        # Run test for each provider
        results = {}
        for provider in self.providers:
            if progress_callback:
                progress_callback(f"  Testing provider: {provider}")
            
            try:
                # Get model name from overrides if available
                model_name = None
                if model_overrides and provider in model_overrides:
                    model_name = model_overrides[provider]
                    
                if progress_callback:
                    model_info = f" with model {model_name}" if model_name else ""
                    progress_callback(f"  Sending request to {provider}{model_info}...")
                
                # Get response from provider
                response, usage_data = self.provider_manager.get_response(
                    provider=provider,
                    prompt=prompt_text,
                    source=source_text,
                    model_name=model_name
                )
                
                if progress_callback:
                    progress_callback(f"  Validating {provider} response...")
                
                # Validate response against model
                validation_result = self._validate_response(response, model_class, expected_data)
                
                # Record cost data
                if usage_data:
                    cost_tracker.add_test_result(
                        test_id=test_id,
                        provider=provider,
                        model=usage_data.model,
                        usage_data=usage_data,
                        run_id=self.run_id
                    )
                    if progress_callback:
                        progress_callback(f"  {provider} tokens: {usage_data.prompt_tokens} prompt, {usage_data.completion_tokens} completion, cost: ${usage_data.total_cost:.6f}")
                
                if progress_callback:
                    accuracy = validation_result.get('accuracy', 0.0) if validation_result.get('success', False) else 0.0
                    progress_callback(f"  {provider} accuracy: {accuracy:.2f}%")
                
                results[provider] = {
                    'response': response,
                    'validation': validation_result,
                    'model': model_name,
                    'usage': usage_data.to_dict() if usage_data else None
                }
            except Exception as e:
                self.logger.error(f"Error testing provider {provider}: {str(e)}")
                if progress_callback:
                    progress_callback(f"  Error with {provider}: {str(e)}")
                    
                results[provider] = {
                    'error': str(e),
                    'model': model_name if 'model_name' in locals() else None
                }
        
        if progress_callback:
            progress_callback(f"Completed test: {test_id}")
            
        return results
    
    def _validate_response(self, response: str, model_class: Type[BaseModel], expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a response against the pydantic model and expected data
        
        Args:
            response: Response text from the LLM
            model_class: Pydantic model class to validate against
            expected_data: Expected data for comparison
            
        Returns:
            Validation results
        """
        self.logger.info(f"Validating response against model {model_class.__name__}")
        self.logger.debug(f"Expected data: {json.dumps(expected_data, indent=2)}")
        self.logger.debug(f"Raw response: {response[:500]}...")
        
        try:
            # Parse the response as JSON
            try:
                response_data = json.loads(response)
                self.logger.info("Successfully parsed response as JSON")
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse response as JSON: {str(e)}")
                # If response is not valid JSON, try to extract JSON from text
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response) or re.search(r'{[\s\S]*}', response)
                if json_match:
                    try:
                        response_data = json.loads(json_match.group(1))
                        self.logger.info("Successfully extracted and parsed JSON from response text")
                    except json.JSONDecodeError as e2:
                        self.logger.error(f"Failed to parse extracted JSON: {str(e2)}")
                        self.logger.debug(f"Extracted text: {json_match.group(1)}")
                        return {
                            'success': False,
                            'error': f'Found JSON-like text but failed to parse: {str(e2)}',
                            'accuracy': 0.0,
                            'response_excerpt': response[:1000]
                        }
                else:
                    self.logger.error("Response is not valid JSON and could not extract JSON from text")
                    return {
                        'success': False,
                        'error': 'Response is not valid JSON and could not extract JSON from text',
                        'accuracy': 0.0,
                        'response_excerpt': response[:1000]
                    }
            
            self.logger.debug(f"Parsed response data: {json.dumps(response_data, indent=2)}")
            
            # Validate against model
            try:
                validated_data = model_class(**response_data)
                self.logger.info(f"Successfully validated response against {model_class.__name__}")
            except Exception as model_error:
                self.logger.error(f"Model validation error: {str(model_error)}")
                return {
                    'success': False,
                    'error': f'Model validation error: {str(model_error)}',
                    'accuracy': 0.0,
                    'response_data': response_data
                }
            
            # Compare with expected data
            # Use model_dump instead of dict for pydantic v2 compatibility
            try:
                # Try model_dump first (pydantic v2)
                validated_data_dict = validated_data.model_dump()
                self.logger.debug("Using model_dump() (Pydantic v2)")
            except AttributeError:
                # Fall back to dict for older pydantic versions
                self.logger.debug("Falling back to dict() (Pydantic v1)")
                validated_data_dict = validated_data.dict()
            
            # Use DateEncoder for consistent date serialization
            try:
                self.logger.debug(f"Validated data: {json.dumps(validated_data_dict, indent=2, cls=DateEncoder)}")
            except TypeError as e:
                self.logger.warning(f"Could not serialize validated data: {str(e)}")
                self.logger.debug("Validated data could not be fully serialized to JSON for logging")
                
            accuracy = self._calculate_accuracy(validated_data_dict, expected_data)
            self.logger.info(f"Calculated accuracy: {accuracy:.2f}%")
            
            return {
                'success': True,
                'validated_data': validated_data_dict,
                'accuracy': accuracy
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'accuracy': 0.0,
                'response_excerpt': response[:1000] if isinstance(response, str) else str(response)[:1000]
            }
    
    def _calculate_accuracy(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """
        Calculate accuracy by comparing actual and expected data
        
        Args:
            actual: Actual data from LLM response
            expected: Expected data
            
        Returns:
            Accuracy as a percentage
        """
        self.logger.info("Calculating accuracy between actual and expected data")
        
        if not expected:
            self.logger.warning("Expected data is empty, returning 100% accuracy")
            return 100.0
            
        # Handle date objects in comparison by normalizing both dictionaries
        def normalize_dates(obj):
            """Normalize dates and date strings for comparison"""
            if isinstance(obj, dict):
                return {k: normalize_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [normalize_dates(i) for i in obj]
            elif hasattr(obj, 'isoformat'):  # This catches date, datetime, etc.
                return obj.isoformat()
            elif isinstance(obj, str):
                # Try to parse as ISO date
                try:
                    from datetime import datetime, date
                    # Try ISO format for date
                    if len(obj) == 10 and obj[4] == '-' and obj[7] == '-':
                        d = date.fromisoformat(obj)
                        return obj  # Return as string for comparison
                    # Try ISO format for datetime
                    if len(obj) >= 19 and obj[4] == '-' and obj[7] == '-' and obj[10] == 'T':
                        dt = datetime.fromisoformat(obj.replace('Z', '+00:00'))
                        return obj  # Return as string for comparison
                except (ValueError, TypeError):
                    pass
            return obj
            
        # Normalize both dictionaries for comparison
        actual_normalized = normalize_dates(actual)
        expected_normalized = normalize_dates(expected)
            
        # Special case for identical dicts
        if actual_normalized == expected_normalized:
            self.logger.info("Actual and expected data are identical, returning 100% accuracy")
            return 100.0
            
        # Initialize points system
        total_points = 0
        earned_points = 0
        field_results = {}
        
        # Go through each expected field
        for key, expected_value in expected_normalized.items():
            field_weight = 1.0  # Each field is worth 1 point by default
            
            # Check if field exists in actual
            if key in actual_normalized:
                actual_value = actual_normalized[key]
                self.logger.debug(f"Comparing field '{key}': expected={expected_value}, actual={actual_value}")
                
                # Compare based on type
                if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                    # Recursively calculate accuracy for nested objects
                    field_accuracy = self._calculate_accuracy(actual[key], expected[key])  # Use original dicts for nested comparison
                    earned_points += field_weight * (field_accuracy / 100.0)
                    field_results[key] = f"{field_accuracy:.1f}% (nested object)"
                    self.logger.debug(f"Field '{key}' (nested object): {field_accuracy:.1f}% accuracy")
                elif isinstance(expected_value, list) and isinstance(actual_value, list):
                    # For lists, compare items
                    if len(expected_value) == 0:
                        # Empty lists match if actual is also empty
                        list_match = len(actual_value) == 0
                        earned_points += field_weight if list_match else 0
                        field_results[key] = f"{100.0 if list_match else 0.0}% (empty list)"
                        self.logger.debug(f"Field '{key}' (empty list): matched={list_match}")
                    else:
                        # For non-empty lists, calculate similarity
                        if len(actual_value) == 0:
                            # No points if actual is empty but expected is not
                            field_results[key] = "0.0% (actual list empty)"
                            self.logger.debug(f"Field '{key}': actual list is empty, expected has {len(expected_value)} items")
                        else:
                            # Calculate similarity based on matching items
                            # This is a simple implementation that could be improved
                            max_matches = min(len(expected_value), len(actual_value))
                            matches = 0
                            
                            # Count exact matches
                            match_details = []
                            for i in range(max_matches):
                                if i < len(expected_value) and i < len(actual_value):
                                    is_match = expected_value[i] == actual_value[i]
                                    if is_match:
                                        matches += 1
                                    match_details.append(f"Item {i}: {'✓' if is_match else '✗'}")
                            
                            list_similarity = matches / len(expected_value)
                            earned_points += field_weight * list_similarity
                            field_results[key] = f"{list_similarity * 100.0:.1f}% ({matches}/{len(expected_value)} items matched)"
                            self.logger.debug(f"Field '{key}' (list): {matches}/{len(expected_value)} items matched ({list_similarity * 100.0:.1f}%)")
                            self.logger.debug(f"List match details: {', '.join(match_details)}")
                else:
                    # Simple field comparison
                    string_match = str(expected_value).lower() == str(actual_value).lower()
                    if string_match:
                        earned_points += field_weight
                        field_results[key] = "100.0% (exact match)"
                        self.logger.debug(f"Field '{key}': exact match")
                    else:
                        # Partial match for strings
                        if isinstance(expected_value, str) and isinstance(actual_value, str):
                            partial_match = expected_value.lower() in actual_value.lower() or actual_value.lower() in expected_value.lower()
                            if partial_match:
                                earned_points += field_weight * 0.5  # Partial credit
                                field_results[key] = "50.0% (partial match)"
                                self.logger.debug(f"Field '{key}': partial match (50%)")
                            else:
                                field_results[key] = "0.0% (no match)"
                                self.logger.debug(f"Field '{key}': no match")
                        else:
                            field_results[key] = "0.0% (no match, different types)"
                            self.logger.debug(f"Field '{key}': no match, different types or values")
            else:
                field_results[key] = "0.0% (missing field)"
                self.logger.debug(f"Field '{key}' is missing in actual data")
            
            total_points += field_weight
        
        # Calculate final percentage
        accuracy = (earned_points / total_points) * 100.0 if total_points > 0 else 0.0
        
        # Log detailed results
        self.logger.info(f"Overall accuracy: {accuracy:.2f}% ({earned_points:.1f}/{total_points} points)")
        self.logger.info("Field-by-field results:")
        for field, result in field_results.items():
            self.logger.info(f"  {field}: {result}")
        
        return accuracy
    
    def run_tests(self, model_overrides: Optional[Dict[str, str]] = None, 
                  modules: Optional[List[str]] = None,
                  progress_callback: Optional[callable] = None) -> Dict[str, Dict[str, Any]]:
        """
        Run all available tests
        
        Args:
            model_overrides: Optional dictionary mapping providers to model names
            modules: Optional list of module names to filter by
            progress_callback: Optional callback function for reporting progress
            
        Returns:
            Test results for each test and provider
        """
        test_cases = self.discover_test_cases()
        results = {}
        
        # Filter test cases by module if specified
        if modules:
            test_cases = [tc for tc in test_cases if tc['module'] in modules]
            if not test_cases:
                self.logger.warning(f"No test cases found for modules: {modules}")
                if progress_callback:
                    progress_callback(f"WARNING: No test cases found for modules: {modules}")
                return {}
        
        if progress_callback:
            progress_callback(f"Running {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases, 1):
            test_id = f"{test_case['module']}/{test_case['name']}"
            
            if progress_callback:
                progress_callback(f"[{i}/{len(test_cases)}] Running test: {test_id}")
                
            results[test_id] = self.run_test(test_case, model_overrides, progress_callback)
            
            if progress_callback:
                progress_callback(f"Completed test: {test_id}")
                progress_callback(f"Progress: {i}/{len(test_cases)} tests completed")
        
        # Generate cost summary after all tests are complete
        cost_summary = cost_tracker.get_run_summary(self.run_id)
        
        if progress_callback and cost_summary:
            progress_callback(f"\nCost Summary:")
            progress_callback(f"Total cost: ${cost_summary.get('total_cost', 0):.6f}")
            progress_callback(f"Total tokens: {cost_summary.get('total_tokens', 0):,}")
            progress_callback(f"Prompt tokens: {cost_summary.get('prompt_tokens', 0):,}")
            progress_callback(f"Completion tokens: {cost_summary.get('completion_tokens', 0):,}")
            
            # Add model-specific costs
            progress_callback(f"\nModel Costs:")
            for model_name, model_data in cost_summary.get('models', {}).items():
                progress_callback(f"- {model_name}: ${model_data.get('total_cost', 0):.6f} "
                               f"({model_data.get('total_tokens', 0):,} tokens, {model_data.get('test_count', 0)} tests)")
        
        if progress_callback:
            progress_callback(f"\nAll {len(test_cases)} tests completed successfully!")
            progress_callback(f"A detailed cost report can be generated with save_cost_report()")
            
        return results
    
    def run_optimized_tests(self, model_overrides: Optional[Dict[str, str]] = None, 
                         save_optimized_prompts: bool = True,
                         modules: Optional[List[str]] = None,
                         progress_callback: Optional[callable] = None) -> Dict[str, Dict[str, Any]]:
        """
        Optimize prompts based on initial results and run tests again
        
        Args:
            model_overrides: Optional dictionary mapping providers to model names
            save_optimized_prompts: Whether to save optimized prompts to files
            modules: Optional list of module names to filter by
            progress_callback: Optional callback function for reporting progress
            
        Returns:
            Test results with optimized prompts
        """
        if progress_callback:
            progress_callback("Phase 1: Running initial tests to establish baseline...")
            
        # First run regular tests
        initial_results = self.run_tests(
            model_overrides=model_overrides, 
            modules=modules,
            progress_callback=progress_callback
        )
        
        if progress_callback:
            progress_callback("\nPhase 2: Optimizing prompts based on initial results...")
            
        # Optimize prompts
        test_cases = self.discover_test_cases()
        
        # Filter test cases by module if specified
        if modules:
            test_cases = [tc for tc in test_cases if tc['module'] in modules]
            if not test_cases:
                self.logger.warning(f"No test cases found for modules: {modules}")
                if progress_callback:
                    progress_callback(f"WARNING: No test cases found for modules: {modules}")
                return {}
                
        optimized_results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            test_id = f"{test_case['module']}/{test_case['name']}"
            
            if progress_callback:
                progress_callback(f"\n[{i}/{len(test_cases)}] Optimizing prompt for: {test_id}")
            
            # Optimize prompt based on initial results
            with open(test_case['prompt_path'], 'r') as f:
                original_prompt = f.read()
            
            with open(test_case['source_path'], 'r') as f:
                source_text = f.read()
                
            with open(test_case['expected_path'], 'r') as f:
                expected_data = json.load(f)
            
            # Get model class
            model_class = test_case['model_class']
            
            if progress_callback:
                progress_callback(f"  Analyzing initial results and optimizing prompt...")
            
            # Optimize prompt
            optimized_prompt = self.prompt_optimizer.optimize_prompt(
                original_prompt=original_prompt,
                source=source_text,
                model_class=model_class,
                expected_data=expected_data,
                initial_results=initial_results.get(test_id, {}),
                save_to_file=save_optimized_prompts,
                original_prompt_path=test_case['prompt_path']
            )
            
            if progress_callback:
                progress_callback(f"  Prompt optimization completed for {test_id}")
            
            # Run test with optimized prompt
            test_case_optimized = test_case.copy()
            
            # Create temporary file for optimized prompt if not saving to permanent files
            optimized_prompt_path = None
            if save_optimized_prompts:
                # Use the saved optimized prompt path
                prompts_dir = os.path.dirname(test_case['prompt_path'])
                optimized_dir = os.path.join(prompts_dir, "optimized")
                
                # Ensure the directory exists
                if not os.path.exists(optimized_dir):
                    try:
                        os.makedirs(optimized_dir, exist_ok=True)
                    except OSError as e:
                        # If there's an error creating the directory, fall back to the parent directory
                        self.logger.warning(f"Could not create optimized directory: {e}")
                        optimized_dir = prompts_dir
                
                filename = os.path.basename(test_case['prompt_path'])
                optimized_prompt_path = os.path.join(optimized_dir, filename)
            else:
                # Create a temporary file
                optimized_prompt_path = os.path.join(
                    os.path.dirname(test_case['prompt_path']), 
                    f"{test_case['name']}_optimized.txt"
                )
            
            # Write the optimized prompt to the file
            with open(optimized_prompt_path, 'w') as f:
                f.write(optimized_prompt)
            
            test_case_optimized['prompt_path'] = optimized_prompt_path
            
            if progress_callback:
                progress_callback(f"  Running tests with optimized prompt...")
                
            # Run test with optimized prompt and pass model_overrides and progress callback
            optimized_test_results = self.run_test(
                test_case_optimized, 
                model_overrides, 
                progress_callback
            )
            
            optimized_results[test_id] = {
                'original_results': initial_results.get(test_id, {}),
                'optimized_results': optimized_test_results,
                'original_prompt': original_prompt,
                'optimized_prompt': optimized_prompt,
                'optimized_prompt_path': optimized_prompt_path
            }
            
            # Clean up temporary file if not saving to permanent files
            if not save_optimized_prompts and optimized_prompt_path:
                os.remove(optimized_prompt_path)
                
            if progress_callback:
                progress_callback(f"  Completed optimization for {test_id}")
                progress_callback(f"  Progress: {i}/{len(test_cases)} completed")
        
        # Generate cost summary after all optimized tests are complete
        cost_summary = cost_tracker.get_run_summary(self.run_id)
        
        if progress_callback and cost_summary:
            progress_callback(f"\nCost Summary:")
            progress_callback(f"Total cost: ${cost_summary.get('total_cost', 0):.6f}")
            progress_callback(f"Total tokens: {cost_summary.get('total_tokens', 0):,}")
            progress_callback(f"Prompt tokens: {cost_summary.get('prompt_tokens', 0):,}")
            progress_callback(f"Completion tokens: {cost_summary.get('completion_tokens', 0):,}")
            
            # Add model-specific costs
            progress_callback(f"\nModel Costs:")
            for model_name, model_data in cost_summary.get('models', {}).items():
                progress_callback(f"- {model_name}: ${model_data.get('total_cost', 0):.6f} "
                               f"({model_data.get('total_tokens', 0):,} tokens, {model_data.get('test_count', 0)} tests)")
        
        if progress_callback:
            progress_callback(f"\nAll optimizations completed successfully!")
            progress_callback(f"A detailed cost report can be generated with save_cost_report()")
            
        return optimized_results
    
    def generate_report(self, results: Dict[str, Any], optimized: bool = False) -> str:
        """
        Generate a report from test results
        
        Args:
            results: Test results
            optimized: Whether results are from optimized tests
            
        Returns:
            Report text
        """
        report_text = self.report_generator.generate_report(results, optimized)
        
        # Add cost summary to the report
        cost_summary = cost_tracker.get_run_summary(self.run_id)
        if cost_summary:
            cost_report_text = "\n\n## Cost Summary\n"
            cost_report_text += f"Total cost: ${cost_summary.get('total_cost', 0):.6f}\n"
            cost_report_text += f"Total tokens: {cost_summary.get('total_tokens', 0):,}\n"
            cost_report_text += f"Prompt tokens: {cost_summary.get('prompt_tokens', 0):,}\n"
            cost_report_text += f"Completion tokens: {cost_summary.get('completion_tokens', 0):,}\n\n"
            
            # Add model-specific costs
            cost_report_text += "### Model Costs\n"
            for model_name, model_data in cost_summary.get('models', {}).items():
                cost_report_text += f"- {model_name}: ${model_data.get('total_cost', 0):.6f} "
                cost_report_text += f"({model_data.get('total_tokens', 0):,} tokens, {model_data.get('test_count', 0)} tests)\n"
            
            report_text += cost_report_text
        
        return report_text
    
    def save_cost_report(self, output_dir: Optional[str] = None) -> str:
        """
        Save the cost report to a file
        
        Args:
            output_dir: Optional directory to save the report (defaults to test_results)
            
        Returns:
            Path to the saved report file
        """
        output_dir = output_dir or get_test_setting("output_dir", "test_results")
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the cost report
        report_path = cost_tracker.save_cost_report(output_dir, self.run_id)
        if report_path:
            self.logger.info(f"Cost report saved to {report_path}")
        else:
            self.logger.warning("Failed to save cost report")
            
        return report_path