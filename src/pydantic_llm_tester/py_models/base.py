import os
import json
from typing import List, Dict, Any, ClassVar, Type, Set, Tuple, Optional, TypeVar
from pydantic import BaseModel, validator, ValidationError

T = TypeVar('T', bound='BasePyModel')

class BasePyModel(BaseModel):
    """
    Base class for all Pydantic LLM Tester py_models.
    Provides common functionality for test case discovery and report saving.
    """

    # Class variable for module name - must be defined by subclasses
    MODULE_NAME: ClassVar[str]

    # Pydantic v1 Config class
    class Config:
        extra = "ignore"
        validate_assignment = True

    @classmethod
    def get_skip_fields(cls) -> Set[str]:
        """
        Get a set of field names that should be skipped during validation.
        Can be overridden by subclasses.
        """
        return set()

    # Root validator for pre-processing incoming data (Pydantic v1 compatible)
    @validator('*', pre=True)
    @classmethod
    def exclude_invalid_fields(cls, value, **kwargs):
        """
        For Pydantic v1 compatibility, we keep this validator but don't use it for field filtering
        """
        return value
        
    # Custom classmethod to create model with field filtering
    @classmethod
    def create_filtered(cls, data: Dict[str, Any]):
        """
        Pre-process the data before validation to exclude fields with type errors
        or fields that are explicitly marked to be skipped.
        """
        if not isinstance(data, dict):
            return data

        # Create a clean copy with only valid fields
        clean_data = {}

        # Get fields to skip
        skip_fields = cls.get_skip_fields()

        for field_name, field_value in data.items():
            # Skip fields that are explicitly defined to be skipped
            if field_name in skip_fields:
                continue

            # Skip fields that don't exist in the model
            if field_name not in cls.__fields__:  # Use __fields__ for Pydantic v1
                continue

            # Add the field to clean data
            clean_data[field_name] = field_value

        # Return a model instance
        return cls(**clean_data)

    @classmethod
    def model_validate_safe(cls: Type[T], obj: Any) -> Tuple[Optional[T], List[str]]:
        """
        Validates the data and creates a model instance, excluding invalid fields.
        Returns a tuple of (model_instance, validation_errors).

        Args:
            obj: The data to validate

        Returns:
            Tuple of (model_instance, list_of_errors)
        """
        errors = []
        result = None

        # First attempt normal validation to get standard errors
        try:
            # Use Pydantic v1 parse_obj instead of model_validate
            result = cls.parse_obj(obj)
            return result, errors
        except ValidationError as e:
            # Extract error messages
            for error in e.errors():
                errors.append(f"{'.'.join(str(loc) for loc in error['loc'])}: {error['msg']}")

            # Try again with more lenient validation by processing fields one by one
            try:
                valid_data = {}

                # Process each field individually
                for field_name, field_info in cls.__fields__.items():  # Use __fields__ for v1
                    if field_name in obj:
                        try:
                            # Try to validate just this field
                            field_value = obj[field_name]
                            # Create a temp model with just this field to validate it
                            temp_data = {field_name: field_value}
                            # Use Pydantic v1 parse_obj instead of model_validate
                            temp = cls.parse_obj(temp_data)
                            # If successful, add to valid_data
                            valid_data[field_name] = getattr(temp, field_name)
                        except Exception:
                            # Skip this field on any error
                            pass

                # Create the final model with only valid fields
                if valid_data:
                    try:
                        result = cls.parse_obj(valid_data)
                    except Exception as final_e:
                        errors.append(f"Final validation failed: {str(final_e)}")
            except Exception as e2:
                errors.append(f"Field-by-field validation failed: {str(e2)}")

        return result, errors

    @classmethod
    def get_test_cases(cls, module_dir: str) -> List[Dict[str, Any]]:
        """
        Discover standard test cases for this module by scanning test directories.
        Subclasses can extend this method to add custom test case discovery logic.

        Args:
            module_dir: The absolute path to the directory of the py_model module.

        Returns:
            List of test case configurations with paths to source, prompt, and expected files
        """
        test_cases = []

        test_dir = os.path.join(module_dir, "tests")
        report_dir = os.path.join(module_dir, "reports") # Although not used for discovery, define here for consistency

        # Check required directories
        sources_dir = os.path.join(test_dir, "sources")
        prompts_dir = os.path.join(test_dir, "prompts")
        expected_dir = os.path.join(test_dir, "expected")

        if not all(os.path.exists(d) for d in [sources_dir, prompts_dir, expected_dir]):
            # print(f"Warning: Missing test directories for module {cls.MODULE_NAME} at {test_dir}") # Optional: add logging
            return []

        # Get test case base names (from source files without extension)
        for source_file in os.listdir(sources_dir):
            if not source_file.endswith('.txt'):
                continue

            base_name = os.path.splitext(source_file)[0]
            prompt_file = f"{base_name}.txt"
            expected_file = f"{base_name}.json"

            prompt_path = os.path.join(prompts_dir, prompt_file)
            expected_path = os.path.join(expected_dir, expected_file)

            if not os.path.exists(prompt_path):
                # print(f"Warning: Missing prompt file {prompt_file} for test case {base_name} in module {cls.MODULE_NAME}") # Optional: add logging
                continue

            if not os.path.exists(expected_path):
                # print(f"Warning: Missing expected file {expected_file} for test case {base_name} in module {cls.MODULE_NAME}") # Optional: add logging
                continue

            test_case = {
                'module': cls.MODULE_NAME,
                'name': base_name,
                'model_class': cls,
                'source_path': os.path.join(sources_dir, source_file),
                'prompt_path': prompt_path,
                'expected_path': expected_path
            }

            test_cases.append(test_case)

        return test_cases

    @classmethod
    def save_module_report(cls, results: Dict[str, Any], run_id: str, module_dir: str) -> str:
        """
        Save a report specifically for this module.

        Args:
            results: Test results for this module.
            run_id: Run identifier.
            module_dir: The absolute path to the directory of the py_model module.

        Returns:
            Path to the saved report file.
        """
        report_dir = os.path.join(module_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)

        # Create module-specific report
        report_path = os.path.join(report_dir, f"report_{cls.MODULE_NAME}_{run_id}.md")

        with open(report_path, 'w') as f:
            f.write(f"# {cls.MODULE_NAME.replace('_', ' ').title()} Module Report\n\n")
            f.write(f"Run ID: {run_id}\n\n")

            # Add test results
            f.write("## Test Results\n\n")
            for test_id, test_results in results.items():
                # Filter results to only include tests for this module
                if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                    continue

                test_name = test_id.split('/', 1)[1] # Use split with maxsplit=1
                f.write(f"### Test: {test_name}\n\n")

                for provider, provider_results in test_results.items():
                    f.write(f"#### Provider: {provider}\n\n")

                    if 'error' in provider_results:
                        f.write(f"Error: {provider_results['error']}\n\n")
                        continue

                    validation = provider_results.get('validation', {})
                    # Ensure accuracy is calculated only if validation was successful
                    accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                    f.write(f"Accuracy: {accuracy:.2f}%\n\n")

                    usage = provider_results.get('usage', {})
                    if usage:
                        f.write("Usage:\n")
                        f.write(f"- Prompt tokens: {usage.get('prompt_tokens', 0)}\n")
                        f.write(f"- Completion tokens: {usage.get('completion_tokens', 0)}\n")
                        f.write(f"- Total tokens: {usage.get('total_tokens', 0)}\n")
                        f.write(f"- Cost: ${usage.get('total_cost', 0):.6f}\n\n")

        return report_path

    @classmethod
    def save_module_cost_report(cls, cost_data: Dict[str, Any], run_id: str, module_dir: str) -> str:
        """
        Save a cost report specifically for this module.

        Args:
            cost_data: Cost data for the entire run.
            run_id: Run identifier.
            module_dir: The absolute path to the directory of the py_model module.

        Returns:
            Path to the saved report file.
        """
        report_dir = os.path.join(module_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)

        # Create module-specific cost report
        report_path = os.path.join(report_dir, f"cost_report_{cls.MODULE_NAME}_{run_id}.json")

        # Filter cost data for this module only
        module_cost_data: Dict[str, Any] = {
            'run_id': run_id,
            'module': cls.MODULE_NAME,
            'tests': {},
            'summary': {
                'total_cost': 0.0,
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'models': {} # Changed 'py_models' to 'models' for clarity in cost report
            }
        }

        # Collect tests that belong to this module and calculate summary
        for test_id, test_data in cost_data.get('tests', {}).items():
            if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                continue

            # Store the test data for this module
            module_cost_data['tests'][test_id] = test_data

            # Add to summary
            for provider, provider_data in test_data.items():
                module_cost_data['summary']['total_cost'] += provider_data.get('total_cost', 0.0)
                module_cost_data['summary']['total_tokens'] += provider_data.get('total_tokens', 0)
                module_cost_data['summary']['prompt_tokens'] += provider_data.get('prompt_tokens', 0)
                module_cost_data['summary']['completion_tokens'] += provider_data.get('completion_tokens', 0)

                # Add to model-specific summary
                model_name = provider_data.get('model', 'unknown')
                if model_name not in module_cost_data['summary']['models']:
                    module_cost_data['summary']['models'][model_name] = {
                        'total_cost': 0.0,
                        'total_tokens': 0,
                        'prompt_tokens': 0,
                        'completion_tokens': 0,
                        'test_count': 0
                    }

                model_summary = module_cost_data['summary']['models'][model_name]
                model_summary['total_cost'] += provider_data.get('total_cost', 0.0)
                model_summary['total_tokens'] += provider_data.get('total_tokens', 0)
                model_summary['prompt_tokens'] += provider_data.get('prompt_tokens', 0)
                model_summary['completion_tokens'] += provider_data.get('completion_tokens', 0)
                model_summary['test_count'] += 1

        # Write to file
        with open(report_path, 'w') as f:
            json.dump(module_cost_data, f, indent=2)

        return report_path

