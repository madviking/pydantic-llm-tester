"""
Main LLM Tester class for running tests and generating reports
"""

import os
import importlib
import json
import sys
from typing import List, Dict, Any, Optional, Type, Tuple
import logging
import inspect
import numbers
from datetime import date, datetime

# Import rapidfuzz for string similarity
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

from pydantic import BaseModel

from .utils.prompt_optimizer import PromptOptimizer
from .utils.report_generator import ReportGenerator, DateEncoder
from .utils.provider_manager import ProviderManager
from .utils.config_manager import ConfigManager
from .utils.cost_manager import cost_tracker, UsageData


class LLMTester:
    """
    Main class for testing LLM py_models against pydantic schemas
    """

    def __init__(self, providers: List[str], llm_models: Optional[List[str]] = None, test_dir: Optional[str] = None):
        """
        Initialize the LLM tester

        Args:
            providers: List of LLM provider names to test
            llm_models: Optional list of specific LLM model names to test
            test_dir: Directory containing test files
        """
        self.providers = providers
        self.llm_models = llm_models
        self.test_dir = test_dir or os.path.join(os.path.dirname(__file__), "tests")
        # Pass the llm_models list to ProviderManager so it can filter loaded models
        self.provider_manager = ProviderManager(providers, llm_models=llm_models)
        self.prompt_optimizer = PromptOptimizer()
        self.report_generator = ReportGenerator()
        self.logger = logging.getLogger(__name__)

        # Test case directories
        self.cases_dir = os.path.join(self.test_dir, "cases")

        # Initialize cost tracking
        self.run_id = cost_tracker.start_new_run()
        self.config_manager = ConfigManager() # Initialize ConfigManager
        self.logger.info(f"Started new test run with ID: {self.run_id}")

        self._verify_directories()

    def _verify_directories(self) -> None:
        """Verify that required directories exist"""
        # Check the default test_dir (e.g., src/tests)
        if not os.path.exists(self.test_dir):
            self.logger.warning(f"Default test directory {self.test_dir} does not exist")

        # Check the configured py_models_path if it's different from the default built-in
        configured_py_models_path = self.config_manager.get_py_models_path()
        builtin_py_models_dir = os.path.join(os.path.dirname(__file__), "py_models")

        if configured_py_models_path and os.path.abspath(configured_py_models_path) != os.path.abspath(builtin_py_models_dir):
             if not os.path.exists(configured_py_models_path):
                 self.logger.warning(f"Configured py_models path {configured_py_models_path} does not exist")


    def discover_test_cases(self) -> List[Dict[str, Any]]:
        """
        Discover available test cases by scanning configured py_models directories.
        Supports built-in and custom paths defined in pyllm_config.json.

        Returns:
            List of test case configurations
        """
        test_cases = []
        processed_modules = set() # To avoid processing the same module from different paths

        # Get configured py_models and their paths
        configured_py_models = self.config_manager.get_py_models()
        configured_py_models_path = self.config_manager.get_py_models_path()
        builtin_py_models_dir = os.path.join(os.path.dirname(__file__), "py_models")

        # List of directories to scan for py_models
        py_models_dirs_to_scan = []

        # Add the built-in py_models directory
        if os.path.exists(builtin_py_models_dir):
            py_models_dirs_to_scan.append(builtin_py_models_dir)
            self.logger.info(f"Scanning built-in py_models directory: {builtin_py_models_dir}")

        # Add the configured py_models_path if it's different from the built-in
        if configured_py_models_path and os.path.abspath(configured_py_models_path) != os.path.abspath(builtin_py_models_dir):
            if os.path.exists(configured_py_models_path):
                py_models_dirs_to_scan.append(configured_py_models_path)
                self.logger.info(f"Scanning configured py_models path: {configured_py_models_path}")
            else:
                self.logger.warning(f"Configured py_models path {configured_py_models_path} does not exist. Skipping.")


        # Process modules from scanned directories
        for models_dir in py_models_dirs_to_scan:
            if not os.path.exists(models_dir):
                continue

            for item_name in os.listdir(models_dir):
                item_path = os.path.join(models_dir, item_name)
                # Skip non-directories, hidden directories, and special files
                if not os.path.isdir(item_path) or item_name.startswith('__') or item_name.startswith('.'):
                    continue

                module_name = item_name # Use directory name as module name

                # Check if this module is explicitly configured with a path
                if module_name in configured_py_models and 'path' in configured_py_models[module_name]:
                    # This module will be handled by its explicit path later
                    continue

                # Avoid processing the same module name if found in multiple scanned directories
                if module_name in processed_modules:
                    self.logger.debug(f"Skipping duplicate module name '{module_name}' found in '{models_dir}'")
                    continue

                processed_modules.add(module_name)
                self.logger.info(f"Processing module from directory: {module_name} in {models_dir}")

                # Find model class and get test cases
                model_class, model_path = self._find_model_class_from_path(item_path, module_name)
                if not model_class:
                    self.logger.warning(f"Could not find model class for module {module_name} in {models_dir}")
                    continue

                # Get test cases from model class
                module_test_cases = self._get_test_cases_from_model(model_class, module_name, model_path)
                if module_test_cases:
                    test_cases.extend(module_test_cases)


        # Process modules explicitly defined with a 'path' in the config
        for module_name, config in configured_py_models.items():
            if 'path' in config and module_name not in processed_modules:
                module_path = config['path']
                full_module_path = os.path.abspath(module_path) # Resolve relative paths

                if not os.path.exists(full_module_path):
                    self.logger.warning(f"Configured path for module '{module_name}' does not exist: {full_module_path}. Skipping.")
                    continue

                processed_modules.add(module_name)
                self.logger.info(f"Processing module from configured path: {module_name} at {full_module_path}")

                # Find model class and get test cases
                model_class, model_file_path = self._find_model_class_from_path(full_module_path, module_name)
                if not model_class:
                    self.logger.warning(f"Could not find model class for module {module_name} at {full_module_path}")
                    continue

                # Get test cases from model class
                module_test_cases = self._get_test_cases_from_model(model_class, module_name, model_file_path)
                if module_test_cases:
                    test_cases.extend(module_test_cases)


        # Fallback to legacy test discovery (if cases_dir exists and contains modules not yet processed)
        if os.path.exists(self.cases_dir):
             self.logger.info(f"Checking legacy test cases directory: {self.cases_dir}")
             for item_name in os.listdir(self.cases_dir):
                 item_path = os.path.join(self.cases_dir, item_name)
                 if os.path.isdir(item_path) and not item_name.startswith('__') and item_name not in processed_modules:
                     module_name = item_name
                     processed_modules.add(module_name) # Mark as processed to avoid conflicts

                     self.logger.info(f"Processing legacy module: {module_name} in {self.cases_dir}")

                     # Attempt to find a model class for this legacy module name
                     # We need to find the model class from the built-in src.py_models
                     # or potentially a configured path if a module with the same name exists there.
                     # This part is tricky - how does a legacy test case know which model class to use?
                     # Assuming legacy test cases correspond to built-in models for now.
                     model_class, model_path = self._find_model_class_from_path(os.path.join(builtin_py_models_dir, module_name), module_name)

                     if not model_class:
                         self.logger.warning(f"Could not find corresponding model class for legacy module {module_name}. Skipping legacy tests.")
                         continue

                     self.logger.info(f"Falling back to legacy test discovery for module {module_name}")
                     legacy_test_cases = self._discover_legacy_test_cases(module_name, model_class, model_path)
                     if legacy_test_cases:
                         test_cases.extend(legacy_test_cases)


        self.logger.info(f"Discovered {len(test_cases)} test cases across all modules")
        return test_cases

    def _get_test_cases_from_model(self, model_class: Type[BaseModel], module_name: str, model_path: str) -> List[Dict[str, Any]]:
        """
        Get test cases from a model class that has the get_test_cases method.

        Args:
            model_class: The model class.
            module_name: The name of the module.
            model_path: The file path of the model module.

        Returns:
            List of test case configurations.
        """
        self.logger.debug(f"Checking model_class for module {module_name}: {model_class} (Type: {type(model_class)}) from path {model_path})")
        # Check if the model class has a get_test_cases method
        test_cases = []
        if not hasattr(model_class, 'get_test_cases'):
            self.logger.warning(f"Model class {model_class} (Type: {type(model_class)}) for module {module_name} does not have get_test_cases method. Skipping.")
            return []

        try:
            module_test_cases = model_class.get_test_cases()
            if module_test_cases:
                self.logger.info(f"Found {len(module_test_cases)} test cases for module {module_name}")
                # Add module_name and model_path to each test case
                for tc in module_test_cases:
                    tc['module'] = module_name # Ensure module name is set
                    tc['model_path'] = model_path
                test_cases.extend(module_test_cases)
            else:
                self.logger.warning(f"No test cases found for module {module_name}")
        except Exception as e:
            self.logger.error(f"Error getting test cases for module {module_name}: {str(e)}")

        return test_cases


    def _discover_legacy_test_cases(self, module_name: str, model_class: Type[BaseModel], model_path: str) -> List[Dict[str, Any]]:
        """
        Discover test cases for a module using the legacy directory structure

        Args:
            module_name: Name of the module
            model_class: The model class to use for validation
            model_path: The file path of the model module

        Returns:
            List of test case configurations
        """
        test_cases = []

        # Check if legacy structure exists
        module_path = os.path.join(self.cases_dir, module_name)
        if not os.path.isdir(module_path):
            self.logger.warning(f"Legacy module directory not found: {module_path}")
            return []

        # Check for sources, prompts, and expected subdirectories
        sources_dir = os.path.join(module_path, "sources")
        prompts_dir = os.path.join(module_path, "prompts")
        expected_dir = os.path.join(module_path, "expected")

        if not all(os.path.exists(d) for d in [sources_dir, prompts_dir, expected_dir]):
            self.logger.warning(f"Legacy module {module_name} is missing required subdirectories")
            return []

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

            test_case = {
                'module': module_name,
                'name': base_name,
                'model_class': model_class,
                'source_path': os.path.join(sources_dir, source_file),
                'prompt_path': os.path.join(prompts_dir, prompt_file),
                'expected_path': os.path.join(expected_dir, expected_file),
                'model_path': model_path # Add model_path here
            }

            test_cases.append(test_case)

        self.logger.info(f"Found {len(test_cases)} legacy test cases for module {module_name}")
        return test_cases

    def _find_model_class_from_path(self, module_dir: str, module_name: str) -> Tuple[Optional[Type[BaseModel]], Optional[str]]:
        """
        Find the pydantic model class and its file path for a module given its directory path.

        Args:
            module_dir: The directory path of the module.
            module_name: The name of the module (e.g., 'job_ads').

        Returns:
            Tuple of (Pydantic model class or None, file path of the model module or None)
        """
        # Add the module's directory to sys.path temporarily to allow importing
        original_sys_path = list(sys.path)
        # Add the parent directory of the module_dir to sys.path
        parent_dir = os.path.dirname(module_dir)
        if parent_dir not in sys.path:
             sys.path.insert(0, parent_dir)
             self.logger.debug(f"Added '{parent_dir}' to sys.path")

        self.logger.debug(f"Attempting to find model class for module '{module_name}' in directory '{module_dir}'")

        original_sys_path = list(sys.path)
        # Add the module's directory to sys.path temporarily to allow importing
        if module_dir not in sys.path:
             sys.path.insert(0, module_dir)
             self.logger.debug(f"Added '{module_dir}' to sys.path for module '{module_name}'")

        model_file_path = None
        model_class = None
        module = None # Initialize module to None

        try:
            # Try to import the 'model' file within the module directory
            # This assumes the main model class is defined in a file named 'model.py'
            model_module_name = 'model' # The expected file name without .py
            self.logger.debug(f"Attempting to import '{model_module_name}' from directory: {module_dir}")
            module = importlib.import_module(model_module_name)
            self.logger.debug(f"Successfully imported module: {model_module_name} from {module_dir}")

            # Get the file path of the imported module
            model_file_path = inspect.getfile(module)
            self.logger.debug(f"Model file path: {model_file_path}")

            # Find all BaseModel subclasses within the imported 'model' module
            all_base_model_subclasses = []
            for name, obj in inspect.getmembers(module):
                # Ensure it's a class, a subclass of BaseModel, and not BaseModel itself
                if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                    # Check if the class is defined in the current module file
                    # This helps exclude imported BaseModel subclasses
                    if inspect.getmodule(obj) == module:
                         self.logger.debug(f"Found potential BaseModel subclass in model file: {name}")
                         all_base_model_subclasses.append((name, obj))
                    else:
                         self.logger.debug(f"Skipping imported BaseModel subclass: {name}")


            if not all_base_model_subclasses:
                 self.logger.warning(f"No BaseModel subclass found in '{model_module_name}.py' within directory {module_dir}")
                 return None, model_file_path # Return path even if no class found

            model_class = None
            # Refined capitalization logic to match common Pydantic model naming convention (singular, capitalized words)
            # Example: 'job_ads' -> 'JobAd', 'product_descriptions' -> 'ProductDescription'
            capitalized_module_name_singular = ''.join(word.capitalize() for word in module_name.split('_'))
            # Simple heuristic: if the capitalized name ends with 's' and is longer than 1 character,
            # try the singular form by removing the 's'. This is a heuristic and might not work for all cases.
            if capitalized_module_name_singular.endswith('s') and len(capitalized_module_name_singular) > 1:
                 capitalized_module_name_singular = capitalized_module_name_singular[:-1]


            # Prioritize finding the main model class:
            # 1. Look for a class whose name exactly matches the capitalized, singular module name heuristic.
            for name, obj in all_base_model_subclasses:
                 if name == capitalized_module_name_singular:
                      model_class = obj
                      self.logger.debug(f"Found main model class by capitalized singular module name heuristic: {name}")
                      break # Found the exact match, stop searching

            # 2. If not found, look for a class named "Model".
            if model_class is None:
                 for name, obj in all_base_model_subclasses:
                      if name == "Model":
                           model_class = obj
                           self.logger.debug(f"Found main model class by name 'Model': {name}")
                           break # Found "Model", stop searching

            # 3. If still not found and there's only one BaseModel subclass, use that one.
            if model_class is None and len(all_base_model_subclasses) == 1:
                 model_class = all_base_model_subclasses[0][1]
                 self.logger.debug(f"Using the single BaseModel subclass found as the main model: {all_base_model_subclasses[0][0]}")

            # 4. If multiple BaseModel subclasses are found and none match the above criteria,
            #    log a warning and indicate that the main model could not be determined automatically.
            if model_class is None:
                 class_names = [name for name, _ in all_base_model_subclasses]
                 self.logger.warning(f"Could not automatically determine the main BaseModel subclass for module '{module_name}' in '{model_module_name}.py'. Found multiple candidates: {', '.join(class_names)}. Please ensure the main model is named '{capitalized_module_name_singular}' or 'Model', or configure it explicitly.")
                 return None, model_file_path # Indicate failure to find main class


        except (ImportError, AttributeError) as e:
            self.logger.error(f"Error loading or inspecting 'model.py' from directory {module_dir} for module name {module_name}: {str(e)}")
            model_class = None
            model_file_path = None # Ensure path is None if import fails
        except Exception as e:
             self.logger.error(f"Unexpected error finding model class in 'model.py' for module {module_name} at {module_dir}: {str(e)}", exc_info=True)
             model_class = None
             model_file_path = None
        finally:
            # Restore original sys.path
            # Create a new list to avoid modifying the list while iterating or removing
            current_sys_path = list(sys.path)
            # Remove the parent directory if it was added
            parent_dir = os.path.dirname(module_dir)
            if parent_dir in current_sys_path:
                 try:
                      sys.path.remove(parent_dir)
                      self.logger.debug(f"Removed '{parent_dir}' from sys.path")
                 except ValueError:
                      # Should not happen if we checked 'in current_sys_path', but defensive
                      self.logger.debug(f"'{parent_dir}' not found in sys.path during removal attempt.")

            # Remove the module directory if it was added
            if module_dir in current_sys_path:
                 try:
                      sys.path.remove(module_dir)
                      self.logger.debug(f"Removed '{module_dir}' from sys.path")
                 except ValueError:
                      # Should not happen if we checked 'in current_sys_path', but defensive
                      self.logger.debug(f"'{module_dir}' not found in sys.path during removal attempt.")


            # Ensure original sys.path is fully restored in case of unexpected changes
            # This check might be overly strict if other parts of the application
            # legitimately modify sys.path. A more robust approach might involve
            # a context manager for sys.path modifications. For now, log a warning.
            # if sys.path != original_sys_path:
            #      self.logger.warning("sys.path was unexpectedly modified. Restoring to original state.")
            #      sys.path = original_sys_path


            # Clean up imported module to avoid potential conflicts on subsequent runs
            # We imported 'model', so clean that up
            model_module_name = 'model'
            # Check if the module was actually imported before trying to delete
            if model_module_name in sys.modules:
                 try:
                      # Check if the module object is the one we imported from the target directory
                      # This prevents accidentally deleting a module with the same name imported from elsewhere
                      imported_module = sys.modules[model_module_name]
                      if hasattr(imported_module, '__file__') and imported_module.__file__ and os.path.dirname(imported_module.__file__) == module_dir:
                           del sys.modules[model_module_name]
                           self.logger.debug(f"Cleaned up module from sys.modules: {model_module_name}")
                      else:
                           self.logger.debug(f"Skipping cleanup of module '{model_module_name}' as it was not imported from the target directory.")
                 except KeyError:
                      pass # Module might have been removed already or wasn't fully added
                 except Exception as e:
                      self.logger.warning(f"Error during cleanup of module '{model_module_name}': {str(e)}")


        self.logger.debug(f"Found model_class for module {module_name}: {model_class} (Type: {type(model_class)}) from path {model_file_path})")
        return model_class, model_file_path



    def run_test(self, test_case: Dict[str, Any], model_overrides: Optional[Dict[str, str]] = None,
                 progress_callback: Optional[callable] = None) -> Dict[str, Dict[str, Any]]:
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

        # Get model class and path (now included in test_case)
        model_class = test_case['model_class']
        model_path = test_case.get('model_path') # Get model_path from test_case

        # Run test for each provider and its available models
        test_results_for_case: Dict[str, Dict[str, Any]] = {} # Structure: {provider_name: {model_name: result_data}}

        for provider_name in self.providers:
            if progress_callback:
                progress_callback(f"  Testing provider: {provider_name}")

            provider_instance = self.provider_manager.provider_instances.get(provider_name)

            if not provider_instance:
                self.logger.warning(f"Provider instance not found for {provider_name}. Skipping.")
                if progress_callback:
                    progress_callback(f"  Skipping {provider_name}: Instance not found.")
                continue # Skip if provider instance is not available

            # Get available models for this provider (already filtered by llm_models_filter)
            available_models = provider_instance.get_available_models()

            if not available_models:
                self.logger.warning(f"No enabled or filtered models found for provider {provider_name}. Skipping.")
                if progress_callback:
                    progress_callback(f"  Skipping {provider_name}: No enabled or filtered models.")
                continue # Skip if no models are available for this provider

            test_results_for_case[provider_name] = {} # Initialize nested dict for this provider

            for model_config in available_models:
                model_name = model_config.name
                if progress_callback:
                    progress_callback(f"    Testing model: {model_name}")

                try:
                    # Check for model override for this specific model name
                    # This allows overriding a specific model within the filtered list
                    override_model_name = model_overrides.get(provider_name)
                    if override_model_name and override_model_name != model_name:
                         self.logger.debug(f"Model override '{override_model_name}' specified for provider '{provider_name}', but current model is '{model_name}'. Skipping this model.")
                         if progress_callback:
                              progress_callback(f"    Skipping model {model_name}: Override '{override_model_name}' specified.")
                         continue # Skip this model if a different override is specified for the provider

                    # If an override is specified and matches the current model, use it.
                    # Otherwise, use the current model_name from the loop.
                    model_to_use = override_model_name if override_model_name == model_name else model_name


                    if progress_callback:
                        progress_callback(f"    Sending request to {model_to_use}...")

                    # Get response from provider for the specific model
                    response, usage_data = self.provider_manager.get_response(
                        provider=provider_name,
                        prompt=prompt_text,
                        source=source_text,
                        model_name=model_to_use # Pass the specific model name
                    )

                    if progress_callback:
                        progress_callback(f"    Validating {model_to_use} response...")

                    # Validate response against model
                    validation_result = self._validate_response(response, model_class, expected_data)

                    # Record cost data
                    if usage_data:
                        cost_tracker.add_test_result(
                            test_id=test_id,
                            provider=provider_name,
                            model=usage_data.model, # Use the model name from usage data (actual model used)
                            usage_data=usage_data,
                            run_id=self.run_id
                        )
                        if progress_callback:
                            progress_callback(f"    {model_to_use} tokens: {usage_data.prompt_tokens} prompt, {usage_data.completion_tokens} completion, cost: ${usage_data.total_cost:.6f}")

                    if progress_callback:
                        accuracy = validation_result.get('accuracy', 0.0) if validation_result.get('success', False) else 0.0
                        progress_callback(f"    {model_to_use} accuracy: {accuracy:.2f}%")

                    # Store result under provider and model name
                    test_results_for_case[provider_name][model_name] = {
                        'response': response,
                        'validation': validation_result,
                        'model': model_name, # Store the model name used
                        'usage': usage_data.to_dict() if usage_data else None
                    }

                except Exception as e:
                    self.logger.error(f"Error testing model {model_name} for provider {provider_name}: {str(e)}")
                    if progress_callback:
                        progress_callback(f"    Error with {model_name}: {str(e)}")

                    # Store error result under provider and model name
                    test_results_for_case[provider_name][model_name] = {
                        'error': str(e),
                        'model': model_name
                    }

        if progress_callback:
            progress_callback(f"Completed test: {test_id}")

        # Return the structured results for this test case
        return test_results_for_case

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

    def _calculate_accuracy(
        self,
        actual: Dict[str, Any],
        expected: Dict[str, Any],
        field_weights: Optional[Dict[str, float]] = None,
        numerical_tolerance: float = 0.0, # Default: exact match for numbers
        list_comparison_mode: str = 'ordered_exact', # Options: 'ordered_exact', 'ordered_similarity', 'set_similarity'
        string_similarity_threshold: float = 80.0 # Threshold for rapidfuzz ratio (0-100)
    ) -> float:
        """
        Calculate accuracy by comparing actual and expected data with enhanced options.

        Args:
            actual: Actual data from LLM response.
            expected: Expected data.
            field_weights: Optional dictionary mapping field names to weights (default 1.0).
            numerical_tolerance: Optional relative tolerance for numerical comparisons (e.g., 0.05 for 5%).
            list_comparison_mode: How to compare lists:
                'ordered_exact': Items must match exactly in the same order.
                'ordered_similarity': Compare items in order using recursive similarity logic.
                'set_similarity': Compare lists as sets, using recursive similarity for items.
            string_similarity_threshold: Minimum fuzz.ratio() score (0-100) for a string to be considered a match.

        Returns:
            Accuracy as a percentage (float).
        """
        self.logger.info("Calculating accuracy with enhanced options...")
        if not RAPIDFUZZ_AVAILABLE:
            self.logger.warning("rapidfuzz library not found. String similarity matching will be basic. Install with 'pip install rapidfuzz'")

        # Initialize weights if not provided
        field_weights = field_weights or {}

        # Base case: If expected is empty, accuracy is 100% only if actual is also empty.
        if not expected:
            is_match = not actual
            self.logger.warning(f"Expected data is empty. Actual is {'empty' if is_match else 'not empty'}. Accuracy: {100.0 if is_match else 0.0}%")
            return 100.0 if is_match else 0.0

        # Normalize dates for consistent comparison (handles date objects vs ISO strings)
        def normalize_value(obj):
            if isinstance(obj, dict):
                return {k: normalize_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [normalize_value(i) for i in obj]
            elif isinstance(obj, (date, datetime)):
                return obj.isoformat()
            # Attempt to parse strings that look like dates/datetimes back for comparison consistency if needed,
            # but direct ISO string comparison is usually sufficient if both sides are normalized.
            return obj

        actual_normalized = normalize_value(actual)
        expected_normalized = normalize_value(expected)

        # Special case for identical dicts after normalization
        if actual_normalized == expected_normalized:
            self.logger.info("Actual and expected data are identical after normalization. Accuracy: 100.0%")
            return 100.0

        total_weighted_points = 0
        earned_weighted_points = 0
        field_results_log = {} # For logging details

        # Iterate through expected fields
        for key, exp_val_norm in expected_normalized.items():
            weight = field_weights.get(key, 1.0) # Get weight or default to 1.0
            total_weighted_points += weight

            field_score = 0.0
            field_reason = "Field missing in actual"

            if key in actual_normalized:
                act_val_norm = actual_normalized[key]
                field_score, field_reason = self._compare_values(
                    act_val_norm, exp_val_norm,
                    field_weights=field_weights, # Pass along for deeper levels
                    numerical_tolerance=numerical_tolerance,
                    list_comparison_mode=list_comparison_mode,
                    string_similarity_threshold=string_similarity_threshold
                )

            earned_weighted_points += field_score * weight
            field_results_log[key] = f"Score={field_score:.2f}, Weight={weight}, Reason='{field_reason}'"

        # Calculate final percentage
        accuracy = (earned_weighted_points / total_weighted_points) * 100.0 if total_weighted_points > 0 else 100.0 # Avoid division by zero; 100% if no expected fields

        # Log detailed results
        self.logger.info(f"Overall accuracy: {accuracy:.2f}% ({earned_weighted_points:.2f}/{total_weighted_points:.2f} weighted points)")
        self.logger.info("Field-by-field results (internal scoring):")
        for field, result in field_results_log.items():
            self.logger.info(f"  {field}: {result}")

        return accuracy

    # --- Accuracy Calculation Helpers ---

    def _normalize_value(self, obj: Any) -> Any:
        """Normalize dates/datetimes to ISO strings for comparison."""
        if isinstance(obj, dict):
            return {k: self._normalize_value(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [normalize_value(i) for i in obj]
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        # Attempt to parse strings that look like dates/datetimes back for comparison consistency if needed,
        # but direct ISO string comparison is usually sufficient if both sides are normalized.
        return obj

    def _compare_values(
        self, act_val: Any, exp_val: Any, **kwargs
    ) -> Tuple[float, str]:
        """Dispatch comparison to type-specific helpers."""
        score = 0.0
        reason = "No match"

        # 1. Handle None values
        if exp_val is None:
            return (1.0, "Exact match (None)") if act_val is None else (0.0, "Mismatch (expected None)")
        elif act_val is None:
            return 0.0, "Mismatch (actual is None)"

        # 2. Dictionary comparison
        if isinstance(exp_val, dict) and isinstance(act_val, dict):
            score, reason = self._compare_dicts(act_val, exp_val, **kwargs)
        # 3. List comparison
        elif isinstance(exp_val, list) and isinstance(act_val, list):
            score, reason = self._compare_lists(act_val, exp_val, **kwargs)
        # 4. Numerical comparison
        elif isinstance(exp_val, numbers.Number) and isinstance(act_val, numbers.Number):
            score, reason = self._compare_numbers(act_val, exp_val, **kwargs)
        # 5. String comparison
        elif isinstance(exp_val, str) and isinstance(act_val, str):
            score, reason = self._compare_strings(act_val, exp_val, **kwargs)
        # 6. Other types (exact comparison)
        else:
            score, reason = self._compare_other(act_val, exp_val)

        return score, reason

    def _compare_dicts(
        self, act_val: Dict, exp_val: Dict, **kwargs
    ) -> Tuple[float, str]:
        """Compare dictionaries recursively."""
        # Note: field_weights passed in kwargs are for the parent level,
        # they don't directly apply inside the nested dict comparison here.
        # The nested call to _calculate_accuracy handles weights for its level.
        nested_accuracy_percent = self._calculate_accuracy(
            act_val, exp_val,
            field_weights=kwargs.get('field_weights'), # Pass along for deeper levels
            numerical_tolerance=kwargs.get('numerical_tolerance', 0.0),
            list_comparison_mode=kwargs.get('list_comparison_mode', 'ordered_exact'),
            string_similarity_threshold=kwargs.get('string_similarity_threshold', 80.0)
        )
        score = nested_accuracy_percent / 100.0
        reason = f"Nested object ({nested_accuracy_percent:.1f}%)"
        return score, reason

    def _compare_lists(
        self, act_val: List, exp_val: List, **kwargs
    ) -> Tuple[float, str]:
        """Compare lists based on the specified mode."""
        list_comparison_mode = kwargs.get('list_comparison_mode', 'ordered_exact')
        len_exp = len(exp_val)
        len_act = len(act_val)
        score = 0.0
        reason = "List comparison failed"

        if len_exp == 0:
            return (1.0, "Exact match (empty list)") if len_act == 0 else (0.0, "Mismatch (expected empty list)")
        elif len_act == 0:
            return 0.0, "Mismatch (actual list empty)"

        if list_comparison_mode == 'ordered_exact':
            matches = sum(1 for i in range(len_exp) if i < len_act and act_val[i] == exp_val[i])
            score = matches / len_exp
            reason = f"Ordered exact ({matches}/{len_exp} items matched)"

        elif list_comparison_mode == 'ordered_similarity':
            total_item_score = 0
            for i in range(len_exp):
                item_score = 0.0
                if i < len_act:
                    item_score, _ = self._compare_values(act_val[i], exp_val[i], **kwargs)
                total_item_score += item_score
            score = total_item_score / len_exp
            reason = f"Ordered similarity ({score*100:.1f}%)"

        elif list_comparison_mode == 'set_similarity':
            matched_actual_indices = set()
            total_item_score = 0
            for i in range(len_exp):
                best_item_score = -1.0 # Use -1 to ensure any match is better
                best_j = -1
                for j in range(len_act):
                    if j not in matched_actual_indices:
                        item_score, _ = self._compare_values(act_val[j], exp_val[i], **kwargs)
                        if item_score > best_item_score:
                            best_item_score = item_score
                            best_j = j
                # Ensure we add non-negative scores
                total_item_score += max(0.0, best_item_score)
                if best_j != -1:
                    matched_actual_indices.add(best_j)
            score = total_item_score / len_exp
            reason = f"Set similarity ({score*100:.1f}%)"

        else: # Default to ordered_exact
            matches = sum(1 for i in range(len_exp) if i < len_act and act_val[i] == exp_val[i])
            score = matches / len_exp
            reason = f"Ordered exact (default) ({matches}/{len_exp} items matched)"

        return score, reason

    def _compare_numbers(
        self, act_val: numbers.Number, exp_val: numbers.Number, **kwargs
    ) -> Tuple[float, str]:
        """Compare numbers with optional tolerance."""
        numerical_tolerance = kwargs.get('numerical_tolerance', 0.0)
        score = 0.0
        reason = "Numerical mismatch"

        if numerical_tolerance > 0 and exp_val != 0:
            if abs(act_val - exp_val) / abs(exp_val) <= numerical_tolerance:
                score = 1.0
                reason = f"Numerical match (within {numerical_tolerance*100:.1f}%)"
            else:
                reason = f"Numerical mismatch (outside {numerical_tolerance*100:.1f}%)"
        elif act_val == exp_val:
            score = 1.0
            reason = "Numerical match (exact)"
        else:
             reason = "Numerical mismatch (exact)"

        return score, reason

    def _compare_strings(
        self, act_val: str, exp_val: str, **kwargs
    ) -> Tuple[float, str]:
        """Compare strings with case-insensitivity and optional similarity."""
        string_similarity_threshold = kwargs.get('string_similarity_threshold', 80.0)
        score = 0.0
        reason = "String mismatch"

        if act_val.lower() == exp_val.lower():
            score = 1.0
            reason = "String match (case-insensitive)"
        elif RAPIDFUZZ_AVAILABLE:
            similarity = fuzz.ratio(act_val, exp_val)
            if similarity >= string_similarity_threshold:
                # Scale score between threshold and 100 for partial credit
                score = (similarity - string_similarity_threshold) / (100.0 - string_similarity_threshold)
                # score = 1.0 # Alternative: Full score if above threshold
                reason = f"String similarity ({similarity:.1f}%)"
            else:
                reason = f"String similarity below threshold ({similarity:.1f}%)"
        else: # Fallback if rapidfuzz not available
            if exp_val.lower() in act_val.lower() or act_val.lower() in exp_val.lower():
                 score = 0.5 # Basic partial match
                 reason = "String partial match (basic)"
            else:
                 reason = "String mismatch (basic)"

        return score, reason

    def _compare_other(
        self, act_val: Any, exp_val: Any
    ) -> Tuple[float, str]:
        """Compare other types using exact equality."""
        if act_val == exp_val:
            return 1.0, "Exact match (other type)"
        else:
            return 0.0, f"Mismatch (type {type(exp_val).__name__})"

    # --- End Accuracy Calculation Helpers ---


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
        main_report = ""
        reports = {}

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

            # run_test now returns {provider_name: {model_name: result_data}}
            test_case_results = self.run_test(test_case, model_overrides, progress_callback)

            if progress_callback:
                progress_callback(f"Completed test: {test_id}")
                progress_callback(f"Progress: {i}/{len(test_cases)} tests completed")

            # Store the results for this test case under its test_id
            results[test_id] = test_case_results

            # Add model_class to the results for this test_id (can be stored once per test_id)
            # We can attach it at the test_id level or within each model result.
            # Storing it at the test_id level seems cleaner.
            # However, the report generator expects it within the provider/model structure.
            # Let's add it to each model result for now, although it's redundant.
            # A better approach might be to pass test_cases list to report generator.
            # For now, let's add it to each model result.
            for provider_name, model_results in results[test_id].items():
                 for model_name in model_results:
                      results[test_id][provider_name][model_name]['model_class'] = test_case['model_class']


        # Generate cost summary after all tests are complete
        cost_summary = cost_tracker.get_run_summary(self.run_id)

        if cost_summary:
            cost_report_text = "\n\n## Cost Summary\n"
            cost_report_text += f"Total cost: ${cost_summary.get('total_cost', 0):.6f}\n"
            cost_report_text += f"Total tokens: {cost_summary.get('total_tokens', 0):,}\n"
            cost_report_text += f"Prompt tokens: {cost_summary.get('prompt_tokens', 0):,}\n"
            cost_report_text += f"Completion tokens: {cost_summary.get('completion_tokens', 0):,}\n\n"

            # Add model-specific costs
            cost_report_text += "### Model Costs\n"
            for model_name, model_data in cost_summary.get('py_models', {}).items():
                cost_report_text += f"- {model_name}: ${model_data.get('total_cost', 0):.6f} "
                cost_report_text += f"({model_data.get('total_tokens', 0):,} tokens, {model_data.get('test_count', 0)} tests)\n"

            main_report += cost_report_text
        
        reports['main'] = main_report

        # Generate module-specific reports
        modules_processed = set()
        for test_id in results:
            module_name = test_id.split('/')[0]

            # Skip if already processed
            if module_name in modules_processed:
                continue

            modules_processed.add(module_name)

            # Skip test module as it's used for unit tests
            if module_name == 'test':
                continue

            # Get model class
            # model_class = self._find_model_class(module_name) # Original problematic line
            model_class = None
            # Find the model_class from the results of a test case belonging to this module
            for test_id_iter, test_result_iter in results.items():
                if test_id_iter.startswith(module_name + "/"):
                    model_class = test_result_iter.get('model_class')
                    if model_class:
                        break
            
            if not model_class:
                self.logger.warning(f"Could not retrieve model class for module {module_name} from test results")
                continue

            # Generate module-specific report if the model class has the method
            if hasattr(model_class, 'save_module_report'):
                try:
                    module_report_path = model_class.save_module_report(results, self.run_id)
                    self.logger.info(f"Module report for {module_name} saved to {module_report_path}")

                    # Read the report content
                    try:
                        with open(module_report_path, 'r') as f:
                            module_report = f.read()
                            reports[module_name] = module_report
                    except Exception as e:
                        self.logger.error(f"Error reading module report for {module_name}: {str(e)}")

                except Exception as e:
                    self.logger.error(f"Error generating module report for {module_name}: {str(e)}")

        return results

    def save_cost_report(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Save the cost report to a file

        Args:
            output_dir: Optional directory to save the report (defaults to test_results)
            
        Returns:
            Dictionary of paths to the saved report files
        """
        output_dir = output_dir or get_test_setting("output_dir", "test_results")

        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save the main cost report
        report_paths = {}
        main_report_path = cost_tracker.save_cost_report(output_dir, self.run_id)
        if main_report_path:
            self.logger.info(f"Cost report saved to {main_report_path}")
            report_paths['main'] = main_report_path
        else:
            self.logger.warning("Failed to save main cost report")

        # Get cost data from cost tracker
        cost_data = cost_tracker.get_run_data(self.run_id)
        if not cost_data:
            self.logger.warning("No cost data available to save module-specific reports")
            return report_paths

        # For each model used, save a module-specific report
        modules_processed = set()
        for test_id in cost_data.get('tests', {}):
            module_name = test_id.split('/')[0]

            # Skip if already processed
            if module_name in modules_processed:
                continue

            modules_processed.add(module_name)

            # Skip test module as it's used for unit tests
            if module_name == 'test':
                continue

            # Get model class
            # model_class = self._find_model_class(module_name) # Original problematic line
            model_class = None
            # Find the model_class from the test_case data associated with this module
            # This requires access to the original test_cases list or a mapping.
            # For simplicity, let's assume we can retrieve it if needed, or adjust logic.
            # A more robust way would be to ensure model_class is consistently available.
            # For now, let's try to find it from the test_case data associated with this module.
            # This requires self.discover_test_cases() to have been called or its result stored.
            # For now, let's assume we need to re-discover or have it available.
            # A simpler approach for now, if this method is called after run_tests,
            # is to pass the results from run_tests which now contain model_class.
            # However, save_cost_report is standalone.

            # Let's try to get it from the test_cases discovered at initialization or by re-discovering.
            # This is inefficient if called multiple times.
            # A better long-term solution might be to pass `all_test_results` (which includes model_class)
            # to `save_cost_report` if it's meant to operate on a completed run.

            # For now, let's attempt to find it by re-discovering, acknowledging this isn't optimal.
            # This is a placeholder for a potentially better way to access model_class here.
            discovered_test_cases = self.discover_test_cases() # Inefficient, but for fixing the direct error
            found_tc_for_module = next((tc for tc in discovered_test_cases if tc['module'] == module_name), None)
            if found_tc_for_module:
                model_class = found_tc_for_module.get('model_class')

            if not model_class:
                self.logger.warning(f"Could not find model class for module {module_name} during cost report saving.")
                continue

            # Save module-specific report if the model class has the method
            if hasattr(model_class, 'save_module_cost_report'):
                try:
                    module_report_path = model_class.save_module_cost_report(cost_data, self.run_id)
                    self.logger.info(f"Module cost report for {module_name} saved to {module_report_path}")
                    report_paths[module_name] = module_report_path
                except Exception as e:
                    self.logger.error(f"Error saving module cost report for {module_name}: {str(e)}")

        return report_paths
