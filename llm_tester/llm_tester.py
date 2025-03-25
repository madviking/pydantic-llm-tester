"""
Main LLM Tester class for running tests and generating reports
"""

import os
import importlib
import json
from typing import List, Dict, Any, Optional, Type
import logging
import inspect

from pydantic import BaseModel

from .utils.prompt_optimizer import PromptOptimizer
from .utils.report_generator import ReportGenerator
from .utils.provider_manager import ProviderManager


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
    
    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test for all providers
        
        Args:
            test_case: Test case configuration
            
        Returns:
            Test results for each provider
        """
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
            try:
                # Get response from provider
                response = self.provider_manager.get_response(
                    provider=provider,
                    prompt=prompt_text,
                    source=source_text
                )
                
                # Validate response against model
                validation_result = self._validate_response(response, model_class, expected_data)
                
                results[provider] = {
                    'response': response,
                    'validation': validation_result
                }
            except Exception as e:
                self.logger.error(f"Error testing provider {provider}: {str(e)}")
                results[provider] = {
                    'error': str(e)
                }
        
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
        try:
            # Parse the response as JSON
            try:
                response_data = json.loads(response)
            except json.JSONDecodeError:
                # If response is not valid JSON, try to extract JSON from text
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response) or re.search(r'{[\s\S]*}', response)
                if json_match:
                    response_data = json.loads(json_match.group(1))
                else:
                    return {
                        'success': False,
                        'error': 'Response is not valid JSON and could not extract JSON from text',
                        'accuracy': 0.0
                    }
            
            # Validate against model
            validated_data = model_class(**response_data)
            
            # Compare with expected data
            # Use model_dump instead of dict for pydantic v2 compatibility
            try:
                # Try model_dump first (pydantic v2)
                validated_data_dict = validated_data.model_dump()
            except AttributeError:
                # Fall back to dict for older pydantic versions
                validated_data_dict = validated_data.dict()
                
            accuracy = self._calculate_accuracy(validated_data_dict, expected_data)
            
            return {
                'success': True,
                'validated_data': validated_data_dict,
                'accuracy': accuracy
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'accuracy': 0.0
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
        if not expected:
            return 100.0
            
        # Special case for identical dicts
        if actual == expected:
            return 100.0
            
        # Initialize points system
        total_points = 0
        earned_points = 0
        
        # Go through each expected field
        for key, expected_value in expected.items():
            field_weight = 1.0  # Each field is worth 1 point by default
            
            # Check if field exists in actual
            if key in actual:
                actual_value = actual[key]
                
                # Compare based on type
                if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                    # Recursively calculate accuracy for nested objects
                    field_accuracy = self._calculate_accuracy(actual_value, expected_value)
                    earned_points += field_weight * (field_accuracy / 100.0)
                elif isinstance(expected_value, list) and isinstance(actual_value, list):
                    # For lists, compare items
                    if len(expected_value) == 0:
                        # Empty lists match if actual is also empty
                        earned_points += field_weight if len(actual_value) == 0 else 0
                    else:
                        # For non-empty lists, calculate similarity
                        if len(actual_value) == 0:
                            # No points if actual is empty but expected is not
                            pass
                        else:
                            # Calculate similarity based on matching items
                            # This is a simple implementation that could be improved
                            max_matches = min(len(expected_value), len(actual_value))
                            matches = 0
                            
                            # Count exact matches
                            for i in range(max_matches):
                                if i < len(expected_value) and i < len(actual_value):
                                    if expected_value[i] == actual_value[i]:
                                        matches += 1
                            
                            list_similarity = matches / len(expected_value)
                            earned_points += field_weight * list_similarity
                else:
                    # Simple field comparison
                    if str(expected_value).lower() == str(actual_value).lower():
                        earned_points += field_weight
                    else:
                        # Partial match for strings
                        if isinstance(expected_value, str) and isinstance(actual_value, str):
                            if expected_value.lower() in actual_value.lower() or actual_value.lower() in expected_value.lower():
                                earned_points += field_weight * 0.5  # Partial credit
            
            total_points += field_weight
        
        # Calculate final percentage
        return (earned_points / total_points) * 100.0 if total_points > 0 else 0.0
    
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
        
        if progress_callback:
            progress_callback(f"All {len(test_cases)} tests completed successfully!")
            
        return results
    
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
                response = self.provider_manager.get_response(
                    provider=provider,
                    prompt=prompt_text,
                    source=source_text,
                    model_name=model_name
                )
                
                if progress_callback:
                    progress_callback(f"  Validating {provider} response...")
                
                # Validate response against model
                validation_result = self._validate_response(response, model_class, expected_data)
                
                if progress_callback:
                    accuracy = validation_result.get('accuracy', 0.0) if validation_result.get('success', False) else 0.0
                    progress_callback(f"  {provider} accuracy: {accuracy:.2f}%")
                
                results[provider] = {
                    'response': response,
                    'validation': validation_result,
                    'model': model_name
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
                filename = os.path.basename(test_case['prompt_path'])
                optimized_prompt_path = os.path.join(optimized_dir, filename)
            else:
                # Create a temporary file
                optimized_prompt_path = os.path.join(
                    os.path.dirname(test_case['prompt_path']), 
                    f"{test_case['name']}_optimized.txt"
                )
                
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
        
        if progress_callback:
            progress_callback(f"\nAll optimizations completed successfully!")
            
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
        return self.report_generator.generate_report(results, optimized)