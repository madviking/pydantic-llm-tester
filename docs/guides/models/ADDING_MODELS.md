# Adding New Models to LLM Tester

This guide explains how to add a new extraction model to the LLM Tester framework. Models define the structure of information to extract from text and include test cases for evaluating LLM performance.

## What is a Model in LLM Tester?

In LLM Tester, a "model" refers to a Pydantic schema that defines structured data to be extracted from unstructured text, along with test cases and utilities for testing extraction accuracy. Each model represents a different type of information extraction task.

Examples of existing models:
- `job_ads`: Extracts structured information from job advertisements
- `product_descriptions`: Extracts product details from descriptions

## Steps to Add a New Model

You can manually create the necessary files and directories, or use the `llm-tester scaffold model` command to generate the basic structure and template files automatically.

**Using the `llm-tester scaffold model` command:**

```bash
# Scaffold a new model interactively
llm-tester scaffold model --interactive

# Scaffold a new model non-interactively
llm-tester scaffold model <model_name>
```

This will create the directory structure and template files described in step 1 and partially complete steps 2 and 3.

**Manual Steps:**

### 1. Create Model Directory Structure

Create a new directory for your model in the `llm_tester/models/` directory:

```bash
mkdir -p src/py_models/your_model_name/tests/{sources,prompts,expected,prompts/optimized}
mkdir -p src/py_models/your_model_name/reports
touch src/py_models/your_model_name/__init__.py
touch src/py_models/your_model_name/model.py
touch src/py_models/your_model_name/tests/__init__.py
```

### 2. Implement the Model Class

Create a Pydantic model in `model.py` that defines the structure of the data to extract:

```python
"""
Your model type definition
"""

import os
import json
from typing import List, Optional, Dict, Any, ClassVar
from pydantic import BaseModel, Field
from datetime import date


class YourModelName(BaseModel):
    """
    Model for extracting structured information from your_model_type
    """
    
    # Class variables for module configuration
    MODULE_NAME: ClassVar[str] = "your_model_name"
    TEST_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "tests")
    REPORT_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "reports")
    
    # Define model fields
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name or title")
    description: str = Field(..., description="Detailed description")
    # Add more fields as needed for your model
    
    @classmethod
    def get_test_cases(cls) -> List[Dict[str, Any]]:
        """Discover test cases for this module"""
        test_cases = []
        
        # Check required directories
        sources_dir = os.path.join(cls.TEST_DIR, "sources")
        prompts_dir = os.path.join(cls.TEST_DIR, "prompts")
        expected_dir = os.path.join(cls.TEST_DIR, "expected")
        
        if not all(os.path.exists(d) for d in [sources_dir, prompts_dir, expected_dir]):
            return []
        
        # Get test case base names (from source files without extension)
        for source_file in os.listdir(sources_dir):
            if not source_file.endswith(".txt"):
                continue
                
            base_name = os.path.splitext(source_file)[0]
            prompt_file = f"{base_name}.txt"
            expected_file = f"{base_name}.json"
            
            if not os.path.exists(os.path.join(prompts_dir, prompt_file)):
                continue
                
            if not os.path.exists(os.path.join(expected_dir, expected_file)):
                continue
            
            test_case = {
                "module": cls.MODULE_NAME,
                "name": base_name,
                "model_class": cls,
                "source_path": os.path.join(sources_dir, source_file),
                "prompt_path": os.path.join(prompts_dir, prompt_file),
                "expected_path": os.path.join(expected_dir, expected_file)
            }
            
            test_cases.append(test_case)
        
        return test_cases
    
    @classmethod
    def save_module_report(cls, results: Dict[str, Any], run_id: str) -> str:
        """Save a report specifically for this module"""
        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        
        # Create module-specific report
        report_path = os.path.join(cls.REPORT_DIR, f"report_{cls.MODULE_NAME}_{run_id}.md")
        
        with open(report_path, "w") as f:
            f.write(f"# {cls.MODULE_NAME.replace('_', ' ').title()} Module Report\n\n")
            f.write(f"Run ID: {run_id}\n\n")
            
            # Add test results
            f.write("## Test Results\n\n")
            for test_id, test_results in results.items():
                if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                    continue
                    
                test_name = test_id.split("/")[1]
                f.write(f"### Test: {test_name}\n\n")
                
                for provider, provider_results in test_results.items():
                    f.write(f"#### Provider: {provider}\n\n")
                    
                    if "error" in provider_results:
                        f.write(f"Error: {provider_results['error']}\n\n")
                        continue
                    
                    validation = provider_results.get("validation", {})
                    accuracy = validation.get("accuracy", 0.0) if validation.get("success", False) else 0.0
                    f.write(f"Accuracy: {accuracy:.2f}%\n\n")
                    
                    usage = provider_results.get("usage", {})
                    if usage:
                        f.write("Usage:\n")
                        f.write(f"- Prompt tokens: {usage.get('prompt_tokens', 0)}\n")
                        f.write(f"- Completion tokens: {usage.get('completion_tokens', 0)}\n")
                        f.write(f"- Total tokens: {usage.get('total_tokens', 0)}\n")
                        f.write(f"- Cost: ${usage.get('total_cost', 0):.6f}\n\n")
        
        return report_path
    
    @classmethod
    def save_module_cost_report(cls, cost_data: Dict[str, Any], run_id: str) -> str:
        """Save a cost report specifically for this module"""
        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        
        # Create module-specific cost report
        report_path = os.path.join(cls.REPORT_DIR, f"cost_report_{cls.MODULE_NAME}_{run_id}.json")
        
        # Filter cost data for this module only
        module_cost_data = {
            "run_id": run_id,
            "module": cls.MODULE_NAME,
            "tests": {},
            "summary": {
                "total_cost": 0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "py_models": {}
            }
        }
        
        # Collect tests that belong to this module
        for test_id, test_data in cost_data.get("tests", {}).items():
            if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                continue
                
            module_cost_data["tests"][test_id] = test_data
            
            # Add to summary
            for provider, provider_data in test_data.items():
                module_cost_data["summary"]["total_cost"] += provider_data.get("total_cost", 0)
                module_cost_data["summary"]["total_tokens"] += provider_data.get("total_tokens", 0)
                module_cost_data["summary"]["prompt_tokens"] += provider_data.get("prompt_tokens", 0)
                module_cost_data["summary"]["completion_tokens"] += provider_data.get("completion_tokens", 0)
                
                # Add to model-specific summary
                model_name = provider_data.get("model", "unknown")
                if model_name not in module_cost_data["summary"]["py_models"]:
                    module_cost_data["summary"]["py_models"][model_name] = {
                        "total_cost": 0,
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "test_count": 0
                    }
                
                model_summary = module_cost_data["summary"]["py_models"][model_name]
                model_summary["total_cost"] += provider_data.get("total_cost", 0)
                model_summary["total_tokens"] += provider_data.get("total_tokens", 0)
                model_summary["prompt_tokens"] += provider_data.get("prompt_tokens", 0)
                model_summary["completion_tokens"] += provider_data.get("completion_tokens", 0)
                model_summary["test_count"] += 1
        
        # Write to file
        with open(report_path, "w") as f:
            json.dump(module_cost_data, f, indent=2)
        
        return report_path
```

### 3. Update Model Package Initialization

Create an `__init__.py` file that exports your model:

```python
"""Your model type module"""

from .model import YourModelName

__all__ = ["YourModelName"]
```

### 4. Create Test Cases

Test cases consist of three components:

1. **Source Text**: The text to extract information from
2. **Prompt**: Instructions for the LLM on what to extract
3. **Expected Output**: The correct JSON structure that should be extracted

#### Source Text Example (tests/sources/example.txt):

```
EXAMPLE YOUR_MODEL_TYPE

ID: example-123

NAME: Example Your Model Name

DESCRIPTION:
This is an example description for testing the your_model_name model.
You can replace this with actual content to extract information from.
```

#### Prompt Example (tests/prompts/example.txt):

```
Extract and structure the following information as a JSON object with this schema:

{
  "id": "Unique identifier",
  "name": "Name or title",
  "description": "Detailed description"
}

Respond only with the JSON object, no additional text.
```

#### Expected Output Example (tests/expected/example.json):

```json
{
  "id": "example-123",
  "name": "Example Your Model Name",
  "description": "This is an example description for testing the your_model_name model. You can replace this with actual content to extract information from."
}
```

## Testing Your Model

### 1. Verify Model Discovery

Run the testing tool to check if your model is discovered:

```bash
./runner.py test -m your_model_name
```

### 2. Test with Different Providers

Test your model with different providers:

```bash
./runner.py test -m your_model_name -p openai -p anthropic
```

## Best Practices

1. **Field Definitions**: Use descriptive field names and add clear descriptions
2. **Validation Rules**: Add validation rules to fields where appropriate
3. **Test Cases**: Create diverse test cases of varying complexity
4. **Documentation**: Document your model's purpose and usage

## Model Requirements

Your model implementation must:

1. Inherit from `pydantic.BaseModel`
2. Define class variables for module configuration (MODULE_NAME, TEST_DIR, REPORT_DIR)
3. Implement the `get_test_cases()` class method
4. Implement the reporting methods (`save_module_report()` and `save_module_cost_report()`)

## Adding External Models

Developers using the installed `llm_tester` package will typically define their custom LLM tasks as "models" outside of the installed package directory. This allows you to manage your task definitions and test data separately from the library code.

`llm_tester` can discover and run tests for models located in a directory you specify.

**Recommended Directory Structure for External Models:**

Organize your custom models in a dedicated directory. Each model should reside in its own subdirectory, containing the `model.py` file and a `tests/` subdirectory with your test cases.

```
/path/to/your/custom/models/
└── your_model_name/
    ├── __init__.py
    ├── model.py          # Defines Pydantic model and get_test_cases()
    └── tests/
        ├── __init__.py
        ├── prompts/
        │   └── test1.txt
        ├── sources/
        │   └── test1.txt
        └── expected/
            └── test1.json
```

**Implementing Your External Model:**

The `model.py` file for an external model follows the same structure and requirements as described in step 2 of the "Steps to Add a New Model" section above, including inheriting from `BaseModel` and implementing the `get_test_cases()` class method.

**Using External Models with LLM Tester:**

When using the `LLMTester` class programmatically or the `llm-tester` CLI, you specify the path to the directory containing your custom models using the `test_dir` parameter (for the API) or the `--test-dir` option (for the CLI).

**API Example:**

```python
from src import LLMTester

# Initialize the tester with the path to your custom py_models directory
tester = LLMTester(providers=["openai"], test_dir="/path/to/your/custom/py_models")

# Discover and run tests from your external py_models
test_cases = tester.discover_test_cases()
results = tester.run_tests()
# ... generate reports
```

**CLI Example:**

```bash
# Run tests using py_models from your custom directory
llm-tester run --test-dir /path/to/your/custom/py_models --providers openai
```

`llm_tester` will scan the specified `test_dir` for subdirectories containing `model.py` files with the `get_test_cases()` method to discover your test cases.

## Testing Your Model

### 1. Verify Model Discovery

Run the CLI with your custom test directory to check if your model is discovered:

```bash
llm-tester py_models list --test-dir /path/to/your/custom/py_models
```

### 2. Test with Different Providers

Test your model with different providers using the CLI:

```bash
llm-tester run --test-dir /path/to/your/custom/py_models --providers openai anthropic
```

## Best Practices

1. **Field Definitions**: Use descriptive field names and add clear descriptions
2. **Validation Rules**: Add validation rules to fields where appropriate
3. **Test Cases**: Create diverse test cases of varying complexity
4. **Documentation**: Document your model's purpose and usage

## Example Models

Refer to existing model implementations as examples:

- `llm_tester/models/job_ads/model.py`
- `llm_tester/models/product_descriptions/model.py`

These implementations show how to structure your model and test cases.
