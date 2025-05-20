# Project Brief: Pydantic LLM Tester

This is meant to be used as a base prompt whenever asking LLM to do any changes on the code base. This should be the only file needed to read to get the full scope.

## 1. Overview and Purpose

**Pydantic LLM Tester** (package name: `pydantic-llm-tester`, version: `0.1.17`) is a Python framework designed for benchmarking, comparing, and optimizing various Large Language Model (LLM) providers for structured data extraction tasks. It also serves as a bridge to easily integrate LLM functionalities into Python applications using Pydantic models for defining the desired output structure.

**Core Goals:**
- **Evaluate LLMs:** Objectively measure the accuracy of different LLMs in extracting structured data based on Pydantic schemas.
- **Optimize Prompts:** Help refine prompts to improve extraction accuracy.
- **Analyze Costs:** Track token usage and associated costs across different LLM providers and models.
- **Integrate LLMs:** Provide a straightforward way to add structured data extraction capabilities to Python applications.

The framework emphasizes modularity, extensibility, configuration over coding, and robust testing.

## 2. Project Structure

The project follows a standard Python package structure, with the main source code located in the `src/pydantic_llm_tester/` directory.

Key Directories:
- **`src/pydantic_llm_tester/`**: Main package directory.
    - **`cli/`**: Command-Line Interface implementation using Typer.
        - `main.py`: Main CLI application entry point (`llm-tester` script).
        - `commands/`: Subdirectories for different CLI command groups (e.g., `run`, `providers`, `configure`, `scaffold`).
        - `core/`: Core logic for CLI commands.
        - `templates/`: Templates used by the `scaffold` command.
    - **`llms/`**: LLM Provider implementations.
        - `base.py`: Defines the `BaseLLM` abstract base class for all providers.
        - `llm_registry.py`: Manages provider instances.
        - `provider_factory.py`: Factory for creating provider instances.
        - `<provider_name>/`: Individual provider directories (e.g., `openai/`, `anthropic/`, `google/`, `mock/`). Each contains:
            - `provider.py`: The provider-specific implementation inheriting from `BaseLLM`.
            - `config.json`: Configuration for the provider, including its models, API key environment variable, and default system prompt.
            - `__init__.py`: Makes the provider discoverable.
    - **`py_models/`**: (Referred to as "models" in some docs, but `py_models` in `README.md` to distinguish from LLM models). Contains Pydantic models for structured data extraction tasks and their associated test cases.
        - `<model_name>/`: Directory for each extraction task (e.g., `job_ads/`, `product_descriptions/`).
            - `model.py`: Defines the Pydantic `BaseModel` subclass for the extraction schema and includes methods like `get_test_cases()`, `save_module_report()`, and `save_module_cost_report()`.
            - `tests/`: Contains test data for the model.
                - `sources/`: Raw text files for extraction.
                - `prompts/`: Prompt files for the LLM.
                    - `optimized/`: (Optional) Directory for optimized prompts.
                - `expected/`: JSON files with the expected structured output.
            - `reports/`: Directory where module-specific reports are saved.
            - `__init__.py`: Exports the Pydantic model class.
    - **`utils/`**: Utility modules for common functionalities.
        - `config_manager.py`: Manages global and provider configurations.
        - `cost_manager.py`: Tracks token usage and costs.
        - `provider_manager.py`: High-level manager for provider interactions.
        - `report_generator.py`: Generates test reports.
        - `prompt_optimizer.py`: Logic for optimizing prompts.
        - `module_discovery.py`: Handles discovery of `py_models`.
        - `common.py`: Common utility functions, including path management.
    - `llm_tester.py`: Contains the main `LLMTester` class, which orchestrates test discovery, execution, validation, and reporting.
    - `.env.example`: Example environment file for API keys.
- **`docs/`**: Project documentation.
    - `README.md`: Main documentation entry point (table of contents).
    - `PROJECT_STRUCTURE.md`: Details the project layout.
    - `architecture/`: Documents design principles and system architecture (e.g., `DESIGN_PRINCIPLES.md`, `PROVIDER_SYSTEM.md`).
    - `guides/`: User and developer guides (e.g., adding providers/models, CLI usage, API usage, configuration).
- **`tests/`**: Pytest unit and integration tests.
    - `conftest.py`: Pytest fixtures, including a `mock_tester`.
    - `test_*.py`: Individual test files for different modules and functionalities.
    - `cli/`: Tests for the CLI components.
- **Root Directory Files:**
    - `README.md`: Main project README.
    - `pyproject.toml`: Project build system configuration, dependencies, and metadata (PEP 517/518). Defines the `llm-tester` script entry point.
    - `setup.py`: Minimal setup script (defers to `pyproject.toml`).
    - `requirements.txt`: Often lists dependencies (though `pyproject.toml` is the primary source).
    - `LICENSE`: Project license (MIT).
    - `pyllm_config.json`: (Optional) Global configuration for test settings, output directories, default py_models paths, and enabled/disabled provider status.
    - `external_providers.json`: (Optional) Lists paths to external provider directories.
    - `.env`: (Typically in `src/pydantic_llm_tester/` or project root, managed by `llm-tester configure keys`) Stores API keys. Should be in `.gitignore`.

## 3. Architecture and Design Principles

**Key Design Principles:**
- **Modularity and Extensibility:** Easy to add new LLM providers and `py_models`.
- **Clean Separation of Concerns:** Distinct systems for providers, `py_models`, test execution (runner), and utilities.
- **Consistent Interfaces:** Providers implement `BaseLLM`, `py_models` extend Pydantic's `BaseModel`.
- **Configuration Over Coding:** Behavior is primarily driven by JSON configuration files and environment variables, minimizing the need for code changes for common adjustments. This is a core philosophy.
- **Centralized Path Management:** Key project paths (e.g., for `py_models`, `.env` file, output directories) are managed centrally, primarily within `src/pydantic_llm_tester/utils/config_manager.py` and the `src/pydantic_llm_tester/cli/commands/paths.py` module, providing consistent path resolution. (Removed common.py mention as enabled_providers.json path logic was removed)
- **Testing and Validation:** Core focus on validating LLM outputs against Pydantic schemas and calculating accuracy.
- **Cost Awareness:** Tracks token usage and calculates costs.
- **User Experience:** Supports CLI and interactive modes, provides clear feedback and reports.
- **Dual Operation Mode:** The framework is designed to work both as a clonable repository (for development and direct source use) and as an installable Python package (`pip install pydantic-llm-tester`).

**Provider System Architecture:**
- **`BaseLLM` (`src/pydantic_llm_tester/llms/base.py`):** Abstract base class defining the interface for all LLM providers (e.g., `get_response()`, `_call_llm_api()`).
- **Provider Implementations (`src/pydantic_llm_tester/llms/<provider_name>/provider.py`):** Concrete classes inheriting from `BaseLLM`. Each provider has its own `config.json` defining models, API key env var, etc.
- **`ProviderFactory` (`src/pydantic_llm_tester/llms/provider_factory.py`):** Creates provider instances.
- **`LLMRegistry` (`src/pydantic_llm_tester/llms/llm_registry.py`):** Manages and caches provider instances.
- **`ProviderManager` (`src/pydantic_llm_tester/utils/provider_manager.py`):** High-level class for interacting with multiple providers.
- **Discovery:** Providers are discovered from subdirectories in `src/pydantic_llm_tester/llms/` and optionally from paths defined in `external_providers.json`. Enabled status is determined by `pyllm_config.json`.

**Py_Model System (Extraction Schemas):**
- **Pydantic Models (`src/pydantic_llm_tester/py_models/<model_name>/model.py`):** Define the structure of data to be extracted. These classes must:
    - Inherit from `pydantic.BaseModel`.
    - Define class variables: `MODULE_NAME`, `TEST_DIR`, `REPORT_DIR`.
    - Implement `get_test_cases()`: Returns a list of test case dictionaries (source, prompt, expected paths, model class).
    - Implement `save_module_report()` and `save_module_cost_report()`: For generating module-specific reports.
- **Test Cases:** Located in the `tests/` subdirectory of each `py_model` (`sources/`, `prompts/`, `expected/`).
- **Discovery:** `py_models` are discovered from subdirectories in `src/pydantic_llm_tester/py_models/` and from paths configured in `pyllm_config.json` or passed via CLI/API.

**`LLMTester` Class (`src/pydantic_llm_tester/llm_tester.py`):**
- Orchestrates the testing process.
- Initializes `ProviderManager`, `PromptOptimizer`, `ReportGenerator`, `ConfigManager`, and `cost_tracker`.
- `discover_test_cases()`: Finds all `py_models` and their test cases.
- `run_test()`: Executes a single test case against configured providers and their models.
- `run_tests()`: Executes all discovered (or filtered) test cases.
- `_validate_response()`: Parses the LLM response (handles JSON extraction from text) and validates it against the Pydantic `py_model`.
- `_calculate_accuracy()`: Performs a detailed field-by-field comparison between the validated data and expected data. Supports:
    - Field weighting.
    - Numerical tolerance.
    - Different list comparison modes (`ordered_exact`, `ordered_similarity`, `set_similarity`).
    - String similarity using `rapidfuzz` (if available).
- `generate_report()`: Creates human-readable Markdown reports.
- `save_cost_report()`: Saves detailed cost reports in JSON format.

**Inter-Component Communication Flow (Simplified):**
The primary operational flow involves the CLI/API layer instantiating and invoking methods on the `LLMTester` class. `LLMTester` then delegates tasks to specialized managers and utilities:
-   `ConfigManager` for loading all configurations.
-   `ProviderManager` (which uses `ProviderFactory` and `LLMRegistry`) for interacting with LLM APIs.
-   `CostTracker` for financial and token usage accounting.
-   `ReportGenerator` for creating output summaries.
-   Individual `py_model` classes are responsible for defining their schemas and test cases.
This separation allows for focused development and easier maintenance of different aspects of the framework.

## 4. Test Run Lifecycle (CLI Example: `llm-tester run`)

Understanding the sequence of operations when a test run is initiated is crucial for debugging and extension. Here's a typical lifecycle when using the CLI:

1.  **CLI Invocation & Parsing**:
    *   User executes a command like `llm-tester run --providers openai --test-dir ./custom_tests`.
    *   `src/pydantic_llm_tester/cli/main.py` (the Typer application entry point) parses global options (e.g., `--verbose`, `--env`) and the specific command (`run`) with its options.
    *   Logging is configured based on verbosity flags or the `LOG_LEVEL` environment variable (setup early in `cli/main.py`).
    *   The `.env` file is loaded (by `cli/main.py:load_env()`) to make API keys available as environment variables.
    *   Control is passed to the `run_tests` function (or a similar handler) in `src/pydantic_llm_tester/cli/commands/run.py`.

2.  **`LLMTester` Initialization**:
    *   The command handler (e.g., `run_tests` in `cli/commands/run.py`) instantiates the `LLMTester` class from `src/pydantic_llm_tester/llm_tester.py`, passing relevant CLI arguments like selected providers, specific LLM models to target, and the test directory.
    *   During `LLMTester.__init__`:
        *   `ConfigManager` (`src/pydantic_llm_tester/utils/config_manager.py`) is initialized. It loads `pyllm_config.json` (if found at the project root or a standard location) to get global settings like default `py_models_path`, `output_dir`, etc.
        *   `ProviderManager` (`src/pydantic_llm_tester/utils/provider_manager.py`) is initialized with the list of target providers and LLM models.
            *   It discovers all available provider modules within `src/pydantic_llm_tester/llms/` and any paths specified in `external_providers.json`.
            *   For each discovered provider, its `config.json` is loaded to fetch details like the API key's environment variable name, default system prompt, and the list of LLM models it supports.
            *   Provider instances are created using `ProviderFactory` and managed by `LLMRegistry`. These instances are filtered based on the 'enabled' flag in `pyllm_config.json` and the `--providers` / `--llm_models` CLI flags. (Updated description)
        *   `CostTracker` (`src/pydantic_llm_tester/utils/cost_manager.py`) is initialized, and a new unique `run_id` is generated.
        *   Other utilities like `ReportGenerator` and `PromptOptimizer` are instantiated.

3.  **Test Case Discovery**:
    *   `LLMTester.discover_test_cases()` is called.
    *   This method scans specified `py_models` directories. These include:
        *   The built-in `src/pydantic_llm_tester/py_models/` directory.
        *   Custom paths for `py_models` defined in `pyllm_config.json` (under `py_models.<module_name>.path`).
        *   The path provided via the `--test-dir` CLI option (or `test_dir` parameter if using the API).
    *   For each discovered `py_model` module (which is a directory):
        *   `_find_model_class_from_path()` dynamically imports the `model.py` file within that directory.
        *   It inspects the imported module to find the main Pydantic `BaseModel` subclass (e.g., by looking for a class named `Model` or matching a capitalized version of the module name).
        *   The static `get_test_cases()` method of this Pydantic model class is called. This method is responsible for finding corresponding `sources/*.txt`, `prompts/*.txt`, and `expected/*.json` files within its `tests/` subdirectory and constructing a list of `test_case` dictionaries. Each dictionary contains paths to these files, the Pydantic model class itself, and the module/test name.

4.  **Test Execution Loop**:
    *   `LLMTester.run_tests()` iterates through the discovered (and potentially filtered by `--filter`) `test_case` dictionaries. For each `test_case`, it calls `LLMTester.run_test()`.
    *   Inside `LLMTester.run_test()`:
        *   The source text, prompt text, and expected JSON data are loaded from their respective file paths stored in the `test_case` dictionary.
        *   It then iterates through each enabled provider (e.g., "openai") and each of that provider's configured and enabled LLM models (e.g., "gpt-4o").
            *   `ProviderManager.get_response()` is invoked with the provider name, prompt, source, and target LLM model name.
                *   This retrieves the specific provider instance (e.g., `OpenAIProvider`).
                *   The provider instance's `get_response()` method typically prepares the request and calls its internal `_call_llm_api()` method.
                *   `_call_llm_api()` makes the actual network request to the LLM provider's API using the appropriate SDK or HTTP client.
            *   The LLM's raw response text and `UsageData` (containing token counts and model name used) are returned.
            *   `CostTracker.add_test_result()` records the token usage and calculates the cost for this specific API call, associating it with the `run_id`, test ID, provider, and LLM model.
            *   `LLMTester._validate_response()` is called with the raw LLM response, the Pydantic model class for the current `py_model`, and the expected JSON data.
                *   It first attempts to parse the LLM response as JSON. If direct parsing fails, it tries to extract a JSON object from within markdown code blocks (e.g., ```json ... ```).
                *   If JSON is successfully parsed, it's validated against the Pydantic model class (e.g., `JobAd(**parsed_json)`).
                *   If Pydantic validation is successful, `LLMTester._calculate_accuracy()` is called. This method performs a detailed, field-by-field comparison of the validated data against the `expected.json` data, considering field weights, numerical tolerances, list comparison modes, and string similarity (using `rapidfuzz`).
            *   The results (including raw response, validation success/error, accuracy score, and usage data) are collected and stored, typically in a nested dictionary structure keyed by test ID, then provider name, then LLM model name.

5.  **Report Generation and Output**:
    *   After all test cases have been processed, if running via CLI, the `run_tests` command handler in `cli/commands/run.py` (or `LLMTester.generate_report()` if using API directly) uses `ReportGenerator` to format the collected results into a human-readable Markdown report.
    *   `CostTracker.get_run_summary()` is called to get overall and per-model cost/token summaries for the entire run. This is often appended to the main report.
    *   `LLMTester.save_cost_report()` (or `cost_tracker.save_cost_report()`) saves the detailed cost breakdown to a JSON file (e.g., in `test_results/`).
    *   Individual `py_model` classes might also have their `save_module_report()` and `save_module_cost_report()` methods invoked to generate module-specific views of the results.
    *   Finally, reports are either printed to the standard output or saved to files, as specified by CLI options (e.g., `--output`, `--json`).

This lifecycle provides a detailed flow from command execution to result presentation, highlighting key classes and methods involved at each stage.

### Key Data Structures during a Test Run

-   **`test_case` (Dictionary)**: Created by `py_model.get_test_cases()`. Contains:
    *   `module` (str): Name of the `py_model` module (e.g., "job_ads").
    *   `name` (str): Name of the specific test case (e.g., "simple_test").
    *   `model_class` (Type[BaseModel]): The Pydantic model class for validation.
    *   `source_path` (str): Path to the input text file.
    *   `prompt_path` (str): Path to the prompt file.
    *   `expected_path` (str): Path to the expected JSON output file.
    *   `model_path` (str): Path to the `model.py` file of the `py_model`.
-   **`UsageData` (Dataclass/NamedTuple in `cost_manager.py`)**: Returned by provider's `_call_llm_api` method. Contains:
    *   `prompt_tokens` (int)
    *   `completion_tokens` (int)
    *   `total_tokens` (int)
    *   `model` (str): Name of the LLM model actually used.
    *   `total_cost` (float)
-   **Test Results (Nested Dictionary)**: The final output of `LLMTester.run_tests()` is structured like:
    `{test_id: {provider_name: {llm_model_name: {result_details}}}}`
    where `result_details` includes `response`, `validation` (success, error, accuracy, validated_data), `usage` (from `UsageData`), and `model_class`.

## 5. Configuration

Configuration is managed through several files and environment variables:
- **`pyllm_config.json` (Project Root or User-defined):**
    - `test_settings`: Controls test runner behavior (e.g., `output_dir`, `save_optimized_prompts`, `default_modules`, `py_models_path`).
    - `py_models`: Can define paths to custom `py_model` directories.
    - `providers`: Defines provider-specific settings, including the `enabled` flag for each provider. (Updated description)
- **`external_providers.json` (Project Root):** Optional. Lists paths to directories containing external provider implementations.
- **Provider Configs (`src/pydantic_llm_tester/llms/<provider_name>/config.json`):**
    - `name`: Provider identifier.
    - `provider_type`: Type identifier.
    - `env_key`: Environment variable name for the API key.
    - `system_prompt`: Default system prompt for the provider.
    - `llm_models`: Array of LLM models offered by the provider, including:
        - `name`: Model identifier.
        - `default`, `preferred`, `enabled`: Boolean flags.
        - `cost_input`, `cost_output`: Cost per 1M tokens.
        - `max_input_tokens`, `max_output_tokens`: Token limits.
        (For OpenRouter, cost/token limits are dynamically updated).
- **`.env` file (Typically `src/pydantic_llm_tester/.env` or project root):** Stores API keys. Managed by `llm-tester configure keys`. Precedence: explicit CLI path > default path > system environment variables.

## 6. Command-Line Interface (CLI)

The CLI is accessed via the `llm-tester` command (entry point: `src/pydantic_llm_tester/cli/main.py:app`). It uses Typer.

**Global Options:**
- `-v, --verbose`: Increase verbosity (INFO, DEBUG).
- `--env <path>`: Specify a custom `.env` file path.

**Key Commands:**
- **`run`**: Runs the test suite.
    - Options: `--providers` (`-p`), `--py_models` (`-m` for specific provider:model), `--llm_models` (`-l` for specific LLM model names), `--test-dir`, `--output` (`-o`), `--json`, `--optimize`, `--filter` (`-f`).
- **`list`**: Lists discovered test cases, providers, and models without running tests.
    - Options: `--providers`, `--py_models`, `--llm_models`, `--test-dir`.
- **`providers`**: Manage LLM providers.
    - `list`: Shows discoverable providers and their enabled/disabled status based on `pyllm_config.json`. (Updated description)
    - `enable <name>` / `disable <name>`: Manages the 'enabled' flag for a provider in `pyllm_config.json`. (Updated description)
    - `manage list <provider>`: Lists LLM models within a provider's config.
    - `manage enable/disable <provider> <model_name>`: Toggles `enabled` flag in provider's `config.json`.
    - `manage update <provider>`: Updates model details from API (e.g., OpenRouter costs/limits).
- **`schemas`**: Manage extraction schemas (`py_models`).
    - `list`: Lists discoverable `py_models`.
- **`configure`**: Configure settings.
    - `keys`: Interactively prompts for API keys and saves to `.env`.
- **`scaffold`**: Generate boilerplate for new providers or `py_models`.
    - `provider [name] [--interactive] [--providers-dir]`
    - `model [name] [--interactive] [--path]` (path for `py_models` directory)
- **`recommend-model`**: Interactively recommends LLM models for a task.
- **`interactive`**: Launches a menu-driven interactive session.
- **`paths`**: Display relevant project paths.

## 7. Python API Usage

The primary API entry point is the `LLMTester` class from `src.pydantic_llm_tester.llm_tester`.

**Example Workflow:**
```python
from pydantic_llm_tester import LLMTester # Corrected import based on package structure

# Initialize with providers and path to custom py_models
tester = LLMTester(providers=["openai"], test_dir="/path/to/your/custom/py_models")

# Discover test cases
test_cases = tester.discover_test_cases()
# Filter by specific py_model modules if needed:
# test_cases = tester.discover_test_cases(modules=["my_custom_task"])

# Run tests (can provide model_overrides)
results = tester.run_tests()
# results = tester.run_tests(model_overrides={"openai": "gpt-4o"})

# Generate reports
reports_dict = tester.generate_report(results)
print(reports_dict['main'])

# Save cost report
cost_report_paths = tester.save_cost_report()
print(f"Cost report saved to: {cost_report_paths.get('main')}")
```

- `ProviderFactory` can be used to get individual provider instances.
- Configuration can be accessed via `ConfigManager` utilities.
- Custom `py_models` are defined with a `model.py` (Pydantic schema + `get_test_cases()`) and a `tests/` directory, then used by specifying the `test_dir` to `LLMTester`.

## 8. Testing Strategy (TDD Approach)

The framework is built with testing in mind, facilitating a Test-Driven Development (TDD) approach for data extraction tasks.
- **Define Structure First:** Users define the desired output structure using Pydantic models (`py_models`). This acts as the "contract" or schema.
- **Create Test Cases:** For each `py_model`, users create:
    - `sources/*.txt`: Input texts.
    - `prompts/*.txt`: Instructions for the LLM.
    - `expected/*.json`: The ground truth structured data that the LLM should extract.
- **Iterate and Evaluate:**
    - Run tests using `llm-tester run`.
    - The framework sends the source and prompt to the configured LLMs.
    - LLM responses are validated against the Pydantic `py_model`.
    - **Accuracy Calculation:** A detailed, field-by-field comparison is performed between the LLM's extracted data and the `expected.json` data. This provides quantitative feedback on performance. The `_calculate_accuracy` method in `LLMTester` is central to this, offering fine-grained comparison logic.
    - **Prompt Engineering:** Based on accuracy scores and validation errors, users can iterate on their prompts to improve LLM performance. The `--optimize` flag can assist with this.
- **Mock Providers:** `src/pydantic_llm_tester/llms/mock/` allows testing the framework logic without actual API calls.
- **Unit Tests:** The `tests/` directory contains Pytest unit tests for various components, using fixtures (e.g., `mock_tester` from `conftest.py`) and mocking to isolate units. This ensures the framework's internal logic is correct.

## 9. Code Guidelines and Development

- **Python Version:** Requires Python >= 3.9.
- **Dependencies:** Managed in `pyproject.toml`. Key libraries include Pydantic, Typer, OpenAI/Anthropic/Mistral/Google SDKs, Pydantic-AI, Rapidfuzz.
- **Extensibility:** Designed for adding new providers and `py_models`. The `scaffold` command aids this.
- **Documentation:** A `docs/` directory contains guides and architectural information, which has been reviewed and updated for consistency.
- **Error Handling & Logging:** Emphasis on clear error messages and configurable logging levels. Logging is set up early in `src/pydantic_llm_tester/cli/main.py` and can be controlled via verbosity flags (`-v`, `-vv`) or the `LOG_LEVEL` environment variable.
- **Development Workflow:**
    - **Run Tests Frequently:** After making any code changes, it is crucial to run the test suite using `pytest` from the project root to ensure no regressions are introduced.
    - **Works as Repo and Installed Package:** Development and testing should consider that the tool needs to function correctly both when run from a cloned repository and when installed as a package via pip.
- **CI/CD:** A GitHub Actions workflow (`.github/workflows/python-tests.yml`) is in place for running tests, and likely for publishing as well.

## 10. Extending the Framework & Key Decision Points

This section outlines common scenarios for extending or modifying the framework and points to the primary files and architectural considerations involved.

*   **Adding a New LLM Provider:**
    *   **Goal:** Integrate a new LLM API not currently supported.
    *   **Key Files/Process:**
        *   Use `llm-tester scaffold provider <new_provider_name>` or manually create directory: `src/pydantic_llm_tester/llms/<new_provider_name>/`
        *   Implement `provider.py`: Class inherits from `BaseLLM` (`src/pydantic_llm_tester/llms/base.py`). Key method: `_call_llm_api()`.
        *   Create `config.json`: Define provider name, API key env var, supported `llm_models` with their params (cost, tokens).
        *   Ensure `__init__.py` in the new directory.
    *   **Architectural Considerations:** Adherence to `BaseLLM` interface, API key management, error handling for API calls, `UsageData` reporting.
    *   **Relevant Docs:** `docs/guides/providers/ADDING_PROVIDERS.md`.

*   **Adding a New Extraction Task (`py_model`):**
    *   **Goal:** Define a new Pydantic schema for a new type of data to extract and create test cases.
    *   **Key Files/Process:**
        *   Use `llm-tester scaffold model <new_py_model_name>` or manually create directory: `src/pydantic_llm_tester/py_models/<new_py_model_name>/` (for built-in) or a custom path.
        *   Implement `model.py`: Pydantic `BaseModel` subclass, `MODULE_NAME`, `TEST_DIR`, `REPORT_DIR` class vars, `get_test_cases()`, `save_module_report()`, `save_module_cost_report()` methods.
        *   Create `tests/` subdirectory with `sources/`, `prompts/`, `expected/` files.
    *   **Architectural Considerations:** Schema design, test case diversity, reporting methods.
    *   **Relevant Docs:** `docs/guides/models/ADDING_MODELS.md`.

*   **Modifying Accuracy Calculation:**
    *   **Goal:** Change how similarity or correctness is measured.
    *   **Key File:** `src/pydantic_llm_tester/llm_tester.py`, specifically the `_calculate_accuracy()` method and its helpers (`_compare_values`, `_compare_dicts`, etc.).
    *   **Architectural Considerations:** Impact on existing tests, maintaining clarity of scoring, extensibility for new comparison types.

*   **Adding a New CLI Command or Option:**
    *   **Goal:** Extend the command-line interface.
    *   **Key Files/Process:**
        *   Modify `src/pydantic_llm_tester/cli/main.py` to add new Typer commands or options.
        *   Create new command modules in `src/pydantic_llm_tester/cli/commands/`.
        *   Implement core logic in `src/pydantic_llm_tester/cli/core/`.
    *   **Architectural Considerations:** Typer framework usage, argument parsing, interaction with `LLMTester` or utility classes.

*   **Changing Report Generation:**
    *   **Goal:** Alter the format or content of output reports.
    *   **Key File:** `src/pydantic_llm_tester/utils/report_generator.py` (`ReportGenerator` class).
    *   **Architectural Considerations:** Data structures passed for reporting, template design (if any), output formats (Markdown, JSON).

*   **Adjusting Configuration Loading/Management:**
    *   **Goal:** Change how configuration files or environment variables are handled.
    *   **Key Files:**
        *   `src/pydantic_llm_tester/utils/config_manager.py` (`ConfigManager` class).
        *   `src/pydantic_llm_tester/utils/common.py` (for default paths like `.env`).
        *   Provider-specific `config.json` files in `src/pydantic_llm_tester/llms/<provider_name>/`.
        *   `pyllm_config.json` for global settings.
    *   **Architectural Considerations:** Configuration precedence, discoverability of settings, impact on CLI and API usage.

## 11. Key Files for LLM Interaction

When an LLM needs to work on this project, the following files/concepts are central:

- **This Document (`docs/BRIEF_FOR_LLM.md`)**: Provides the primary overview.
- **`src/pydantic_llm_tester/llm_tester.py`**: The `LLMTester` class is the core orchestrator. Understanding its methods (`discover_test_cases`, `run_test`, `_validate_response`, `_calculate_accuracy`) is key.
- **`src/pydantic_llm_tester/llms/base.py`**: The `BaseLLM` interface for providers.
- **`src/pydantic_llm_tester/llms/<provider_name>/provider.py`**: How individual providers implement `BaseLLM`.
- **`src/pydantic_llm_tester/py_models/<model_name>/model.py`**: How Pydantic schemas and their test cases are defined.
- **`src/pydantic_llm_tester/cli/main.py`**: The CLI structure and command definitions.
- **Configuration Files:** Understanding `pyllm_config.json`, provider `config.json` files, and `.env` for API keys. (Updated description)
- **Documentation in `docs/`**: Especially guides on adding providers/models and the API usage.

By understanding these components, an LLM can effectively analyze, modify, and extend the `pydantic-llm-tester` framework.

## 12. Additional IMPORTANT guidelines for work
- No function should be longer than 200 lines.
- No class should be longer than 700 lines.
- Feel free to create new files to make things more modular.
- Configuration should be kept in pyllm_config.json - extend that when needed. No other config files besides provide config files. 
- ALWAYS write tests before implementing. TDD!
- ALWAYS stop for approval after creating the tests. 
- ALWAYS run tests after making changes.
