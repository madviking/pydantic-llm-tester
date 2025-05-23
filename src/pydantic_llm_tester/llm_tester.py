"""
Main LLM Tester class for running tests and generating reports
"""

import os
import importlib
import json
import sys
from typing import List, Dict, Any, Optional, Type, Tuple, Set
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

from pydantic import BaseModel, ValidationError

from .utils.prompt_optimizer import PromptOptimizer
from .utils.report_generator import ReportGenerator, DateEncoder
from .utils.provider_manager import ProviderManager
from .utils.config_manager import ConfigManager
from .utils.data_structures import UsageData


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
        from .utils.common import get_package_dir
        
        self.providers = providers
        self.llm_models = llm_models
        
        # Use the provided test_dir or default to the package's tests directory
        self.test_dir = test_dir or os.path.join(get_package_dir(), "tests")
        
        # Pass the llm_models list to ProviderManager so it can filter loaded models
        self.provider_manager = ProviderManager(providers, llm_models=llm_models)
        self.prompt_optimizer = PromptOptimizer()
        self.report_generator = ReportGenerator()
        self.logger = logging.getLogger(__name__)

        # Test case directories
        self.cases_dir = os.path.join(self.test_dir, "cases")

        self.logger.info("LLMTester.__init__: Initializing ConfigManager.")
        self.config_manager = ConfigManager() # Initialize ConfigManager
        self.logger.info("LLMTester.__init__: ConfigManager initialized.")

        self.logger.debug("LLMTester.__init__: Calling _verify_directories.")
        self._verify_directories()
        self.logger.debug("LLMTester.__init__: _verify_directories finished.")
        self.logger.debug("LLMTester.__init__: Initialization complete.")
        self.all_test_results: Dict[str, Dict[str, Any]] = {} # Initialize attribute to store results

    def _verify_directories(self) -> None:
        """Verify that required directories exist"""
        from .utils.common import get_py_models_dir, get_external_py_models_dir
        
        # Check the default test_dir (e.g., src/tests)
        if not os.path.exists(self.test_dir):
            self.logger.warning(f"Default test directory {self.test_dir} does not exist")

        # Check the configured py_models_path if it's different from the default built-in
        configured_py_models_path = self.config_manager.get_py_models_path()
        builtin_py_models_dir = get_py_models_dir()

        # Check if the configured path exists and is different from the built-in path
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
        from .utils.common import get_py_models_dir, get_external_py_models_dir
        
        test_cases = []
        processed_modules = set() # To avoid processing the same module from different paths

        # Get configured py_models and their paths
        configured_py_models = self.config_manager.get_py_models()
        configured_py_models_path = self.config_manager.get_py_models_path()
        builtin_py_models_dir = get_py_models_dir()

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

        # Get the module directory from the model_path
        module_dir = os.path.dirname(model_path)

        try:
            module_test_cases = model_class.get_test_cases(module_dir) # Pass module_dir
            if module_test_cases:
                self.logger.info(f"Found {len(module_test_cases)} test cases for module {module_name}")
                # Add module_name, model_path, and module_dir to each test case
                for tc in module_test_cases:
                    tc['module'] = module_name # Ensure module name is set
                    tc['model_path'] = model_path
                    tc['module_dir'] = module_dir # Add module_dir to test case
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
        Uses importlib.util to avoid manipulating sys.path.

        Args:
            module_dir: The directory path of the module.
            module_name: The name of the module (e.g., 'job_ads').

        Returns:
            Tuple of (Pydantic model class or None, file path of the model module or None)
        """
        self.logger.debug(f"Attempting to find model class for module '{module_name}' in directory '{module_dir}'")

        model_file_path = os.path.join(module_dir, 'model.py')
        model_class = None

        # First check if the model.py file exists
        if not os.path.exists(model_file_path):
            self.logger.warning(f"Model file not found at: {model_file_path}")
            return None, None

        # Use importlib.util to load the module without modifying sys.path
        try:
            # Create a unique module name to avoid conflicts with existing modules
            unique_module_name = f"_dynamic_import_{module_name}_{id(module_dir)}"
            
            # Create the spec
            spec = importlib.util.spec_from_file_location(unique_module_name, model_file_path)
            if spec is None:
                self.logger.error(f"Failed to create spec from file: {model_file_path}")
                return None, model_file_path
                
            # Create the module
            module = importlib.util.module_from_spec(spec)
            
            # Execute the module
            spec.loader.exec_module(module)
            
            self.logger.debug(f"Successfully imported module from: {model_file_path}")

            # Find all BaseModel subclasses within the imported module
            all_base_model_subclasses = []
            self.logger.debug(f"Inspecting module: {module.__name__} ({module.__file__}) for BaseModel subclasses.")
            for name, obj in inspect.getmembers(module):
                if not inspect.isclass(obj):
                    # self.logger.debug(f"  '{name}' is not a class. Skipping.")
                    continue

                # Perform checks step-by-step for clarity
                is_pydantic_model = False
                try:
                    # Check if obj is a class and a subclass of BaseModel
                    if inspect.isclass(obj) and issubclass(obj, BaseModel):
                        is_pydantic_model = True
                except TypeError:
                    # issubclass can raise TypeError if obj is not a class,
                    # though inspect.isclass should prevent this.
                    self.logger.debug(f"  TypeError during issubclass check for '{name}'.")
                    continue # Skip if not a class or related error

                is_not_base_model_itself = obj != BaseModel
                
                obj_module_name = getattr(obj, '__module__', 'N/A')
                current_module_name = module.__name__
                
                # Check if the class is defined in the current dynamically loaded module
                # This helps exclude imported BaseModel subclasses.
                # We compare the class's __module__ attribute (a string) with the dynamically loaded module's __name__ (a string).
                is_defined_in_current_module = (getattr(obj, '__module__', None) == module.__name__)
                
                # For enhanced debugging, also log what inspect.getmodule finds, as it was the source of the previous issue.
                obj_actual_module_by_inspect = None
                try:
                    obj_actual_module_by_inspect = inspect.getmodule(obj)
                except Exception: # pragma: no cover
                    pass # Ignore errors from inspect.getmodule if it fails, primary check is above.

                #self.logger.debug(f"  Checking class '{name}':")
                #self.logger.debug(f"    - Is Pydantic model (class & subclass of BaseModel)? {is_pydantic_model}")
                #self.logger.debug(f"    - Is not BaseModel itself? {is_not_base_model_itself}")
                #self.logger.debug(f"    - obj.__module__ (class's perspective): {obj_module_name}")
                #self.logger.debug(f"    - current module.__name__ (dynamically loaded module's name): {current_module_name}")
                #self.logger.debug(f"    - inspect.getmodule(obj) name (inspector's perspective): {getattr(obj_actual_module_by_inspect, '__name__', 'N/A')}")
                #self.logger.debug(f"    - Is defined in current module (obj.__module__ == module.__name__)? {is_defined_in_current_module}")
                
                if is_pydantic_model and is_not_base_model_itself and is_defined_in_current_module:
                    self.logger.debug(f"    >>>> Adding '{name}' to all_base_model_subclasses.")
                    all_base_model_subclasses.append((name, obj))
                else:
                    self.logger.debug(f"    >>>> Not adding '{name}'. Reasons: pydantic_model={is_pydantic_model}, not_base_model={is_not_base_model_itself}, defined_here={is_defined_in_current_module}")

            if not all_base_model_subclasses:
                self.logger.warning(f"No BaseModel subclass found in '{model_file_path}' (all_base_model_subclasses list is empty).")
                return None, model_file_path  # Return path even if no class found

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
                    break  # Found the exact match, stop searching

            # 2. If not found, look for a class named "Model".
            if model_class is None:
                for name, obj in all_base_model_subclasses:
                    if name == "Model":
                        model_class = obj
                        self.logger.debug(f"Found main model class by name 'Model': {name}")
                        break  # Found "Model", stop searching

            # 3. If still not found and there's only one BaseModel subclass, use that one.
            if model_class is None and len(all_base_model_subclasses) == 1:
                model_class = all_base_model_subclasses[0][1]
                self.logger.debug(f"Using the single BaseModel subclass found as the main model: {all_base_model_subclasses[0][0]}")

            # 4. If multiple BaseModel subclasses are found and none match the above criteria,
            #    log a warning and indicate that the main model could not be determined automatically.
            if model_class is None:
                class_names = [name for name, _ in all_base_model_subclasses]
                self.logger.warning(f"Could not automatically determine the main BaseModel subclass for module '{module_name}'. Found multiple candidates: {', '.join(class_names)}. Please ensure the main model is named '{capitalized_module_name_singular}' or 'Model', or configure it explicitly.")
                return None, model_file_path  # Indicate failure to find main class

        except (ImportError, AttributeError) as e:
            self.logger.error(f"Error loading or inspecting '{model_file_path}' for module name {module_name}: {str(e)}")
            model_class = None
            model_file_path = None  # Ensure path is None if import fails
        except Exception as e:
            self.logger.error(f"Unexpected error finding model class for module {module_name} at {model_file_path}: {str(e)}", exc_info=True)
            model_class = None
            model_file_path = None

        self.logger.debug(f"Found model_class for module {module_name}: {model_class} (Type: {type(model_class) if model_class else None}) from path {model_file_path})")
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
        self.logger.info(f"Starting run_test for test_id: {test_id}")

        for provider_name in self.providers:
            self.logger.info(f"run_test: Processing provider: {provider_name} for test_id: {test_id}")
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
                self.logger.info(f"run_test: Processing model: {model_name} for provider: {provider_name}, test_id: {test_id}")
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
                    file_paths = test_case.get('file_paths') # Get optional file_paths

                    self.logger.info(f"run_test: Calling provider_manager.get_response for model: {model_to_use}, provider: {provider_name}, test_id: {test_id}")
                    response, usage_data = self.provider_manager.get_response(
                        provider=provider_name,
                        prompt=prompt_text,
                        source=source_text,
                        model_class=model_class, # Pass model_class
                        model_name=model_to_use,
                        files=file_paths
                    )
                    self.logger.info(f"run_test: Received response from provider_manager for model: {model_to_use}, provider: {provider_name}, test_id: {test_id}")

                    if progress_callback:
                        progress_callback(f"    Validating {model_to_use} response...")

                    # Validate response against model
                    validation_result = self._validate_response(response, model_class, expected_data)

                    if progress_callback:
                        progress_callback(f"    {model_to_use} tokens: {usage_data.prompt_tokens} prompt, {usage_data.completion_tokens} completion")

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
                    self.logger.info(f"run_test: Stored result for model: {model_name}, provider: {provider_name}, test_id: {test_id}")

                except Exception as e:
                    self.logger.error(f"Error testing model {model_name} for provider {provider_name}, test_id: {test_id}: {str(e)}", exc_info=True)
                    if progress_callback:
                        progress_callback(f"    Error with {model_name}: {str(e)}")

                    # Store error result under provider and model name
                    test_results_for_case[provider_name][model_name] = {
                        'error': str(e),
                        'model': model_name
                    }

        if progress_callback:
            progress_callback(f"Completed test: {test_id}")

        self.logger.info(f"Finished run_test for test_id: {test_id}")
        # Return the structured results for this test case
        return test_results_for_case

    def _validate_response(self, response: str, model_class: Type[BaseModel], expected_data: Dict[str, Any]) -> Dict[
        str, Any]:
        """
        Validate a response against the pydantic model and expected data

        Args:
            response: Response text from the LLM
            model_class: Pydantic model class to validate against
            expected_data: Expected data for comparison

        Returns:
            Validation results dictionary
        """
        self.logger.info(f"Validating response against model {model_class.__name__}")
        self.logger.debug(f"Expected data: {json.dumps(expected_data, indent=2)}")
        self.logger.debug(f"Raw response: {response[:500]}...")

        # Get skip fields configuration from model class
        skip_fields = set()
        if hasattr(model_class, "SKIP_FIELDS"):
            skip_fields = set(getattr(model_class, "SKIP_FIELDS") or [])
        elif hasattr(model_class, "get_skip_fields") and callable(getattr(model_class, "get_skip_fields")):
            skip_fields = set(model_class.get_skip_fields() or [])

        try:
            # Parse the response JSON
            response_data = self._parse_json_response(response)
            if isinstance(response_data, dict) and "success" in response_data and response_data["success"] is False:
                # This is an error result from _parse_json_response
                return response_data

            # Validate the data against the model
            validation_result = self._validate_against_model(response_data, model_class, skip_fields)
            
            # Calculate accuracy against expected data
            # Even if validation fails, we still want to calculate accuracy on the raw response data
            # because we can still compute partial matching between the response and expected data
            data_to_compare = validation_result.get("validated_data") if validation_result.get("success", False) else response_data
            accuracy = self._calculate_accuracy(data_to_compare, expected_data)
            self.logger.info(f"Calculated accuracy: {accuracy:.2f}%")

            # If validation succeeded, return the success case
            if validation_result.get("success", False):
                return {
                    'success': True,
                    'validated_data': validation_result["validated_data"],
                    'accuracy': accuracy
                }
            else:
                # If validation failed, include the accuracy calculation anyway
                # but mark it as a validation failure
                return {
                    'success': False,
                    'error': validation_result.get("error", "Validation failed"),
                    'response_data': response_data, 
                    'accuracy': accuracy
                }

        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            # Even in case of exception, try to calculate some accuracy if we have the response data
            accuracy = 0.0
            response_data = None
            
            # Try to extract JSON if we haven't already
            if isinstance(response, str):
                try:
                    response_data = json.loads(response)
                    # If we can extract JSON, calculate accuracy even with the exception
                    accuracy = self._calculate_accuracy(response_data, expected_data)
                    self.logger.info(f"Calculated fallback accuracy: {accuracy:.2f}%")
                except:
                    pass
            
            return {
                'success': False,
                'error': str(e),
                'accuracy': accuracy,
                'response_data': response_data,
                'response_excerpt': response[:1000] if isinstance(response, str) else str(response)[:1000]
            }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from response text, attempting to extract JSON from markup if needed

        Args:
            response: Response text that should contain JSON

        Returns:
            Parsed JSON data or error dict
        """
        try:
            response_data = json.loads(response)
            self.logger.info("Successfully parsed response as JSON")
            return response_data
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse response as JSON: {str(e)}")

            # Try to extract JSON from markdown code blocks or raw JSON
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response) or re.search(r'{[\s\S]*}', response)

            if not json_match:
                self.logger.error("Response is not valid JSON and could not extract JSON from text")
                return {
                    'success': False,
                    'error': 'Response is not valid JSON and could not extract JSON from text',
                    'accuracy': 0.0,
                    'response_excerpt': response[:1000]
                }

            try:
                # For the raw JSON pattern, we need the matched text itself
                json_text = json_match.group(1) if '```json' in json_match.group(0) else json_match.group(0)
                response_data = json.loads(json_text)
                self.logger.info("Successfully extracted and parsed JSON from response text")
                return response_data
            except json.JSONDecodeError as e2:
                self.logger.error(f"Failed to parse extracted JSON: {str(e2)}")
                self.logger.debug(f"Extracted text: {json_match.group(0)[:500]}")
                return {
                    'success': False,
                    'error': f'Found JSON-like text but failed to parse: {str(e2)}',
                    'accuracy': 0.0,
                    'response_excerpt': response[:1000]
                }

    def _validate_against_model(self, data: Dict[str, Any], model_class: Type[BaseModel],
                                skip_fields: Set[str]) -> Dict[str, Any]:
        """
        Validate data against a Pydantic model

        Args:
            data: Data to validate
            model_class: Pydantic model class to validate against
            skip_fields: Fields to exclude from validation

        Returns:
            Validation result with validated data or error
        """
        # Try direct validation first
        try:
            validated_data = model_class(**data)
            self.logger.info(f"Successfully validated data against {model_class.__name__}")

            # Convert model to dict using Pydantic v2 method
            validated_data_dict = validated_data.model_dump(exclude=skip_fields)

            # Log the validated data
            try:
                self.logger.debug(f"Validated data: {json.dumps(validated_data_dict, indent=2, cls=DateEncoder)}")
            except TypeError as e:
                self.logger.warning(f"Could not serialize validated data: {str(e)}")

            return {
                'success': True,
                'validated_data': validated_data_dict
            }
        except ValidationError as validation_error:
            # For validation errors, extract what we can
            self.logger.warning(f"Validation error: {validation_error}")

            # Try to create a partial model by removing problematic fields
            from pydantic import create_model

            # Extract all model fields
            model_fields = {}
            for field_name, field_info in model_class.model_fields.items():
                if field_name not in skip_fields:
                    model_fields[field_name] = (field_info.annotation, ... if field_info.is_required() else None)

            # Create a new model with all fields optional
            optional_model = create_model(
                f"Optional{model_class.__name__}",
                **{name: (anno, None) for name, (anno, _) in model_fields.items()}
            )

            try:
                # Validate with the relaxed model
                partial_validated = optional_model(**data)
                partial_dict = partial_validated.model_dump(exclude=skip_fields)

                # Log validation issues
                error_fields = []
                for error in validation_error.errors():
                    if error.get("loc") and error["loc"][0] not in skip_fields:
                        error_fields.append(str(error["loc"][0]))

                if error_fields:
                    self.logger.warning(f"Fields with validation errors: {', '.join(error_fields)}")

                self.logger.info("Created partial validated model with some invalid fields removed")

                return {
                    'success': True,
                    'validated_data': partial_dict,
                    'partial_validation': True,
                    'invalid_fields': error_fields
                }
            except Exception as e:
                self.logger.error(f"Failed to create partial model: {str(e)}")
                return {
                    'success': False,
                    'error': f'Model validation failed: {str(validation_error)}',
                    'accuracy': 0.0,
                    'response_data': data
                }
        except Exception as e:
            # Handle other general exceptions
            self.logger.error(f"Model validation error: {str(e)}")
            return {
                'success': False,
                'error': f'Model validation error: {str(e)}',
                'accuracy': 0.0,
                'response_data': data
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
                  test_name_filter: Optional[str] = None, # New parameter for test name filtering
                  progress_callback: Optional[callable] = None) -> Dict[str, Dict[str, Any]]:
        """
        Run all available tests

        Args:
            model_overrides: Optional dictionary mapping providers to model names
            modules: Optional list of module names to filter by
            test_name_filter: Optional string to filter test cases by name (case-insensitive substring match)
            progress_callback: Optional callback function for reporting progress

        Returns:
            Test results for each test and provider
        """
        self.logger.info("LLMTester.run_tests: Entered method.")
        test_cases = self.discover_test_cases()
        self.logger.info(f"LLMTester.run_tests: Discovered {len(test_cases)} test cases.")
        results = {}
        main_report = ""
        reports = {}
        # self.logger.info("Starting run_tests method.") # Redundant with the one above

        # Filter test cases by module if specified
        if modules:
            original_count = len(test_cases)
            test_cases = [tc for tc in test_cases if tc['module'] in modules]
            self.logger.info(f"Applied module filter '{modules}'. Filtered from {original_count} to {len(test_cases)} test cases.")

        # Filter test cases by name if specified
        if test_name_filter:
            self.logger.info(f"Attempting to apply test name filter: '{test_name_filter}'")
            self.logger.debug(f"Test cases before name filtering ({len(test_cases)}):")
            for tc_debug in test_cases:
                self.logger.debug(f"  - Pre-filter: module='{tc_debug.get('module')}', name='{tc_debug.get('name')}'")
            
            original_count = len(test_cases)
            test_cases = [
                tc for tc in test_cases
                if test_name_filter.lower() in tc['name'].lower() # Case-insensitive substring match on name
            ]
            self.logger.info(f"Applied test name filter '{test_name_filter}'. Filtered from {original_count} to {len(test_cases)} test cases.")
            self.logger.debug(f"Test cases after name filtering ({len(test_cases)}):")
            for tc_debug in test_cases:
                self.logger.debug(f"  - Post-filter: module='{tc_debug.get('module')}', name='{tc_debug.get('name')}'")

        if not test_cases:
            self.logger.warning(f"No test cases found after filtering (modules: {modules}, name_filter: {test_name_filter})")
            if progress_callback:
                progress_callback(f"WARNING: No test cases found after filtering (modules: {modules}, name_filter: {test_name_filter})")
            return {}

        if progress_callback:
            progress_callback(f"Running {len(test_cases)} test cases...")

        for i, test_case in enumerate(test_cases, 1):
            test_id = f"{test_case['module']}/{test_case['name']}"
            self.logger.info(f"run_tests: Processing test case {i}/{len(test_cases)}: {test_id}")

            if progress_callback:
                progress_callback(f"[{i}/{len(test_cases)}] Running test: {test_id}")

            # run_test now returns {provider_name: {model_name: result_data}}
            test_case_results = self.run_test(test_case, model_overrides, progress_callback)
            self.logger.info(f"run_tests: Completed run_test for {test_id}")

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


        reports['main'] = main_report

        # Generate module-specific reports
        self.logger.info("run_tests: Generating module-specific reports.")
        modules_processed = set()
        for test_id in results:
            module_name = test_id.split('/')[0]
            self.logger.debug(f"run_tests: Checking module report for {module_name} from test_id {test_id}")

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
                    # Find a test case for this module to get the module_dir
                    module_dir = None
                    for test_id_iter, test_result_iter in results.items():
                        if test_id_iter.startswith(module_name + "/"):
                            module_dir = test_case.get('module_dir') # Get module_dir from the current test_case
                            if module_dir:
                                break # Found module_dir from the current test_case

                    if not module_dir:
                         self.logger.warning(f"Could not find module_dir for module {module_name} during report saving.")
                         continue


                    self.logger.info(f"run_tests: Attempting to save module report for {module_name} using model_class {model_class} and module_dir {module_dir}")
                    module_report_path = model_class.save_module_report(results, self.run_id, module_dir) # Pass module_dir
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

        self.all_test_results = results # Store the results in an instance attribute
        return results
