# Using the LLM Tester Python API

This guide explains how to use the `llm_tester` package programmatically in your own Python applications and scripts.

## Installation

First, install the package using pip:

```bash
pip install pydantic-llm-tester
```

## Basic Usage

The main entry point for the API is the `LLMTester` class.

```python
from src import LLMTester

# Initialize the tester with a list of providers to use
# You can specify the directory containing your test cases (py_models)
# If test_dir is not provided, it defaults to the 'py_models' directory within the installed package
tester = LLMTester(providers=["openai", "google"], test_dir="/path/to/your/custom/py_models")

# Discover test cases
# This scans the test_dir for your defined py_models and their test cases
test_cases = tester.discover_test_cases()

# You can filter test cases by module if needed
# test_cases = tester.discover_test_cases(modules=["job_ads", "product_descriptions"])

# Run all discovered tests
# You can optionally provide model overrides for specific providers
# results = tester.run_tests(model_overrides={"openai": "gpt-4", "google": "gemini-pro"})
results = tester.run_tests()

# Run tests with optimized prompts (requires initial run data)
# optimized_results = tester.run_optimized_tests()

# Generate reports from the results
reports = tester.generate_report(results)

# The 'reports' dictionary contains different report types (e.g., 'main')
print("Main Report:")
print(reports.get('main'))

# Save the cost report
cost_report_paths = tester.save_cost_report()
print(f"Cost report saved to: {cost_report_paths.get('main')}")

# You can also run a single test case
# if test_cases:
#     single_test_result = tester.run_test(test_cases[0])
#     print("\nSingle Test Result:")
#     print(single_test_result)
```

## Key Components

### `LLMTester` Class

- `__init__(self, providers: List[str], test_dir: Optional[str] = None)`: Initializes the tester.
    - `providers`: A list of provider names (matching the names in their `config.json`) to enable for this tester instance.
    - `test_dir`: The path to the directory containing your test case modules (models). Defaults to the `llm_tester/models` directory within the installed package.
- `discover_test_cases(self, modules: Optional[List[str]] = None) -> List[Dict[str, Any]]`: Discovers test cases.
    - `modules`: Optional list of module names to filter the discovery by.
    - Returns a list of dictionaries, each representing a test case.
- `run_test(self, test_case: Dict[str, Any], model_overrides: Optional[Dict[str, str]] = None, progress_callback: Optional[callable] = None) -> Dict[str, Any]`: Runs a single test case.
    - `test_case`: A test case dictionary obtained from `discover_test_cases`.
    - `model_overrides`: Optional dictionary mapping provider names to specific model names to use for this test.
    - `progress_callback`: Optional function to receive progress updates.
    - Returns a dictionary containing results for each provider for the given test case.
- `run_tests(self, model_overrides: Optional[Dict[str, str]] = None, modules: Optional[List[str]] = None, progress_callback: Optional[callable] = Optional[callable]) -> Dict[str, Dict[str, Any]]`: Runs multiple test cases.
    - `model_overrides`: Optional dictionary mapping provider names to specific model names to use for all tests.
    - `modules`: Optional list of module names to filter the tests by.
    - `progress_callback`: Optional function to receive progress updates.
    - Returns a nested dictionary: `{test_id: {provider_name: result}}`.
- `run_optimized_tests(self, model_overrides: Optional[Dict[str, str]] = None, save_optimized_prompts: bool = True, modules: Optional[List[str]] = None, progress_callback: Optional[callable] = None) -> Dict[str, Dict[str, Any]]`: Runs tests with prompts optimized based on initial results.
    - `model_overrides`, `modules`, `progress_callback`: Same as `run_tests`.
    - `save_optimized_prompts`: If True, saves the optimized prompts to files.
    - Returns a nested dictionary similar to `run_tests`, but with original and optimized results.
- `generate_report(self, results: Dict[str, Any], optimized: bool = False) -> Dict[str, str]`: Generates human-readable reports.
    - `results`: The results dictionary from `run_tests` or `run_optimized_tests`.
    - `optimized`: Set to True if the results are from `run_optimized_tests`.
    - Returns a dictionary of report strings, typically including a 'main' report.
- `save_cost_report(self, output_dir: Optional[str] = None) -> Dict[str, str]`: Saves the cost report to a file.
    - `output_dir`: Optional directory to save the report. Defaults to the configured output directory (usually `test_results`).
    - Returns a dictionary of paths to the saved report files.

### Provider Interaction

While the `LLMTester` class handles running tests through providers, you might want to interact with providers directly.

You can obtain a provider instance using the `ProviderFactory`:

```python
from pydantic_llm_tester.llms import ProviderFactory

# Get an instance of a specific provider
# The factory handles initialization and configuration loading
openai_provider = ProviderFactory.get_provider("openai")

# You can then use the provider's internal methods,
# though direct use of _call_llm_api is generally not recommended
# unless you are building custom logic on top of the provider.
# The primary interaction is via the LLMTester class.
```

### Configuration Management

Configuration is typically loaded automatically by the `LLMTester` and `ProviderFactory`. However, you can access and potentially modify configuration programmatically using the `config_manager` utilities:

```python
from pydantic_llm_tester.utils import load_config, get_test_setting, get_provider_model

# Load the main configuration
config = load_config()
print(f"Loaded config version: {config.get('version')}")

# Get a specific test setting
output_dir = get_test_setting("output_dir")
print(f"Test output directory: {output_dir}")

# Get configuration for a specific provider model
openai_gpt4_config = get_provider_model("openai", "gpt-4")
if openai_gpt4_config:
  print(f"OpenAI GPT-4 config: {openai_gpt4_config}")
```

## Adding Custom Models Programmatically

When using `llm_tester` as an adapter, you define your LLM tasks as "models" with associated test cases (prompts, sources, expected outputs). These are typically organized in a directory structure that `LLMTester.discover_test_cases` can find.

Your custom model directory should contain:
- A Python file defining your Pydantic model and a `get_test_cases()` function.
- A `tests/` subdirectory with `prompts/`, `sources/`, and `expected/` subdirectories containing your test files.

Example structure for a custom model `my_task`:

```
/path/to/your/custom/models/
└── my_task/
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

In `model.py`:

```python
from pydantic import BaseModel
from typing import List, Dict, Any
import os

class MyTaskModel(BaseModel):
    # Define your schema fields here
    field1: str
    field2: int

def get_test_cases() -> List[Dict[str, Any]]:
    """
    Define and return test cases for this model.
    """
    module_dir = os.path.dirname(__file__)
    tests_dir = os.path.join(module_dir, "tests")

    test_cases = []

    # Example of defining a test case
    test_cases.append({
        'module': 'my_task',
        'name': 'test1',
        'model_class': MyTaskModel,
        'source_path': os.path.join(tests_dir, 'sources', 'test1.txt'),
        'prompt_path': os.path.join(tests_dir, 'prompts', 'test1.txt'),
        'expected_path': os.path.join(tests_dir, 'expected', 'test1.json')
    })

    # You can add more test cases here
    # ...

    return test_cases

# You can also use the legacy directory structure if preferred,
# but the get_test_cases() method is the recommended approach.
```

Then, initialize `LLMTester` with the path to the directory containing `my_task/`:

```python
from src import LLMTester

tester = LLMTester(providers=["openai"], test_dir="/path/to/your/custom/py_models")
test_cases = tester.discover_test_cases()
# ... run tests
```

This allows you to manage your LLM tasks and their test data separately from the installed `llm_tester` package.
