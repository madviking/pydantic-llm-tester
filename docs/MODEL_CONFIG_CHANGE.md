# Planning Document: Refactoring Model Configuration

## Objective

Refactor the Pydantic LLM Tester framework to dynamically fetch the latest model information (including pricing) from OpenRouter on application boot and use a simplified "provider:model-name" format for specifying models in the main configuration file (`pyllm_config.json`). This will remove the need to manually update model details in individual provider `config.json` files.

## Current State

- Model information (names, costs, token limits) is stored in `llms/{provider}/config.json` files.
- `pyllm_config.json` is used for global settings and enabling/disabling providers and models.
- The framework relies on the static information in `config.json` files for model details.
- LLM model management is available via the CLI.
- Cost calculation relies on static pricing information in provider `config.json` files.

## Desired State

- On application boot, if OpenRouter is enabled, the framework fetches the latest model list and pricing from the OpenRouter API. This process does not require an API key and is independent of other provider configurations.
- This dynamic model information (including `pricing` and `context_length`) is used as the primary source of truth for OpenRouter models.
- `pyllm_config.json` allows specifying models using a "provider:model-name" string format (e.g., "openrouter:mistral-large-latest", "openai:chatgpt-4o-latest").
- Provider `config.json` files no longer contain model-specific details.
- An exception is raised if a user attempts to use a provider that is not enabled in `pyllm_config.json`.
- LLM model management functionality is removed from the CLI.
- Cost calculation logic uses the dynamically fetched pricing information for OpenRouter models.

## Refactoring Steps

IMPORTANT: Always stop after each step and before stopping, update this document with status and notes.

### What has been done:

Steps 1 through 6 of the refactoring plan have been completed:
1. Get model info from OpenRouter: Implemented fetching OpenRouter models from the API and saving to `openrouter_models.json`.
2. Create a Central Model Registry/Cache: Established a central registry in `LLMRegistry` for storing and retrieving model data.
3. Modify Configuration Loading (`src/pydantic_llm_tester/utils/config_manager.py`): Enhanced `ConfigManager` to handle OpenRouter data fetching, processing, and parsing the new "provider:model-name" format.
4. Refactor Provider `config.json` Files (`src/pydantic_llm_tester/llms/*/config.json`): Removed `llm_models` array from provider config files and updated `BaseLLM` methods to use the central registry.
5. Update `pyllm_config.json` Structure: Documented the new "provider:model-name" format in `CONFIG_REFERENCE.md`.
6. Adjust `LLMRegistry` and `ProviderFactory`: Ensured `LLMRegistry` and `ProviderFactory` correctly interact with the central registry for model details.

### What still needs to be done:

Based on the plan, the following steps remain:
7. Update CLI Commands and Core Logic (`src/pydantic_llm_tester/cli/`):
    - Handle the new "provider:model-name" input format in relevant CLI commands.
    - Access model information from the central dynamic source in CLI commands.
    - Remove LLM model management commands and associated logic from the CLI.
    - Ensure general run commands require the user to define which models to test with.
8. Update Cost Calculation Logic:
    - Modify `CostManager` to use dynamic pricing from the central registry for OpenRouter models.
    - Update `LLMTester` to work with the updated `CostManager`.
    - Ensure provider implementations return necessary token usage data.
    - Update CLI cost/price commands to display costs based on dynamic pricing.
9. Develop Tests (`tests/`): This is integrated into the sub-steps of each refactoring step.
10. Update Documentation (`docs/`): Manually update documentation to reflect changes, remove references to CLI model management, and explain dynamic cost calculation for OpenRouter.

1.  **Get model info from OpenRouter**
    Status: Completed
    Notes:
    - Implemented logic to fetch OpenRouter models from the API and save to `openrouter_models.json` if the file is missing.
    - Moved fetching logic to `src/pydantic_llm_tester/utils/config_manager.py` for broader accessibility.
    - Added path helpers for `openrouter_models.json` and the OpenRouter API URL to `src/pydantic_llm_tester/utils/common.py`.
    - Updated the test in `tests/test_openrouter_model_fetch.py` to use the path helper and make a real API call to verify file creation and content structure. The test suite for this functionality is passing.

2.  **Create a Central Model Registry/Cache**
    Status: Completed
    Notes:
    - Created a central model registry within the `LLMRegistry` class (`src/pydantic_llm_tester/llms/llm_registry.py`).
    - Added methods to `LLMRegistry` for storing (`store_provider_models`) and retrieving (`get_provider_models`, `get_model_details`) model data.
    - Implemented basic caching logic in `LLMRegistry` using timestamps to check cache freshness.
    - Created a new test file `tests/test_model_registry.py` to specifically test the new model registry functionality, including storing/retrieving data and handling missing providers/models. All tests in this file are passing.
    - Updated existing tests in `tests/test_llm_registry.py` to correctly interact with the refactored `LLMRegistry` and ensured all tests in this file are passing.
    - Ensured that `ModelConfig` from `src.pydantic_llm_tester.llms.base` is used consistently for model details.

3.  **Modify Configuration Loading (`src/pydantic_llm_tester/utils/config_manager.py`)**
    Status: Completed
    Notes:
    Added several new methods and functionality to ConfigManager:
    - Added `is_openrouter_enabled()` method to check if OpenRouter is enabled in the config
    - Added conditional fetch of OpenRouter model data during ConfigManager initialization
    - Implemented `process_openrouter_models()` to convert OpenRouter API data to our ModelConfig format
    - Added `get_model_details_from_registry()` method to look up model details from the central registry
    - Added provider checking methods (`check_provider_enabled()` and `is_provider_enabled()`)
    - Enhanced `_parse_model_string()` method to handle the "provider:model-name" format

    Additional improvements made after review:
    - Added detailed documentation for the OpenRouter model ID parsing logic
    - Enhanced error handling with more robust validation of API responses
    - Added extensive type checking and validation for data structures
    - Implemented defensive parsing for pricing and context length values
    - Improved logging with detailed error messages for troubleshooting

    The following subtasks have been completed:
    3.1. Created tests for identifying when OpenRouter is enabled in `pyllm_config.json`.
    3.2. Implemented logic in `ConfigManager` to check OpenRouter's enabled status.
    3.3. Created tests for calling the OpenRouter provider method to fetch model data if OpenRouter is enabled during configuration loading.
    3.4. Implemented the call to fetch OpenRouter model data in `ConfigManager` during initialization/loading.
    3.5. Created tests for storing the fetched OpenRouter model data in the central registry via `ConfigManager`.
    3.6. Implemented storing fetched data in the central registry via `ConfigManager`.
    3.7. Created tests for parsing the "provider:model-name" format from `pyllm_config.json`.
    3.8. Implemented parsing logic for the new format in `ConfigManager`.
    3.9. Created tests for looking up model details (pricing, context length) from the central registry when parsing the new format.
    3.10. Implemented lookup of model details from the central registry in `ConfigManager`.
    3.11. Created tests for raising an exception if a provider specified in "provider:model-name" is not enabled.
    3.12. Implemented the check and exception raising for disabled providers in `ConfigManager`.

4.  **Refactor Provider `config.json` Files (`src/pydantic_llm_tester/llms/*/config.json`)**
    Status: Completed
    Notes: 
    - Created a test in `tests/test_provider_config_files.py` to verify that provider `config.json` files do not contain the `llm_models` array.
    - Removed the `llm_models` array from all provider `config.json` files.
    - Updated BaseLLM.get_model_config, BaseLLM.get_default_model, and BaseLLM.get_available_models methods to retrieve model details from the central model registry.
    - Modified the provider_factory.load_provider_config to add an empty llm_models list if none exists and fetch models from the registry.

5.  **Update `pyllm_config.json` Structure**
    Status: Completed
    Notes:
    - Updated documentation (`docs/guides/configuration/CONFIG_REFERENCE.md`) to fully document the new "provider:model-name" format for specifying models in `pyllm_config.json`.
    - Confirmed that no additional configuration properties are immediately needed to support the new format based on the current plan.

6.  **Adjust `LLMRegistry` and `ProviderFactory`**
    Status: Completed
    Notes:
    - Added tests to `tests/test_llm_registry.py` to verify storing and retrieving model details from the central registry.
    - Updated the `test_get_provider_info` in `tests/test_llm_registry.py` to rely on the central registry for model details.
    - Removed fallback logic in `src/pydantic_llm_tester/llms/llm_registry.py`'s `get_provider_info` to strictly use data from the central registry.
    - Added tests to `tests/test_provider_factory.py` to verify that `create_provider` retrieves models from the `LLMRegistry` and passes them to the provider's constructor.
    - Confirmed that `src/pydantic_llm_tester/llms/provider_factory.py`'s `create_provider` and `load_provider_config` correctly interact with the `LLMRegistry` to source model details.

7.  **Update CLI Commands and Core Logic (`src/pydantic_llm_tester/cli/`)**
    Status: Not started
    Notes for next steps:
    Additional dependencies to check for next step:

    7.1. Create test(s) to verify that CLI commands handle the new "provider:model-name" input format.
    7.2. Modify relevant CLI commands and core logic to handle the new input format.
    7.3. Create test(s) to verify that CLI commands access model information from the central dynamic source.
    7.4. Modify relevant CLI commands and core logic to access model information from the central dynamic source.
    7.5. Create test(s) to verify that LLM model management commands have been removed from the CLI.
    7.6. Remove LLM model management commands and associated logic from the CLI.
    7.7. For general run commands, user should always define which models to test with.

8.  **Update Cost Calculation Logic**
    Status: Not started
    Notes for next steps:
    Additional dependencies to check for next step:

    8.1. Create test(s) for `CostManager` to accurately calculate costs using dynamic pricing (prompt and completion costs) from the central registry for OpenRouter models.
    8.2. Modify `src/pydantic_llm_tester/utils/cost_manager.py` to use dynamic pricing from the central registry for OpenRouter models.
    8.3. Create test(s) for `LLMTester` to correctly interact with the updated `CostManager`.
    8.4. Update `LLMTester` to work with the updated `CostManager`.
    8.5. Create test(s) for provider implementations to return necessary token usage data for cost calculation.
    8.6. Ensure provider implementations return correct token usage data.
    8.7. Create test(s) for CLI cost/price commands to display costs based on dynamic pricing.
    8.8. Update CLI cost/price commands and core logic to use dynamic pricing for reporting.

9.  **Develop Tests (`tests/`)**
    Status: Not started
    Notes for next steps: This step is integrated into the sub-steps of each refactoring step.

    9.1. (Covered in sub-steps of 1-8)

10. **Update Documentation (`docs/`)**
    Status: Not started
    Notes for next steps: This step primarily involves manual documentation updates.

    10.1. Manually update `docs/guides/configuration/CONFIG_REFERENCE.md` to explain the new model specification format.
    10.2. Manually update other relevant documentation sections, removing references to CLI model management and explaining dynamic cost calculation for OpenRouter.

## Considerations

-   **Error Handling:** Implement robust error handling for fetching model data from OpenRouter (API errors, network issues, invalid data).
-   **Caching:** Consider implementing a caching mechanism for the fetched OpenRouter data to avoid hitting the API on every boot, perhaps with a configurable refresh interval.
-   **Fallback:** Define a fallback mechanism if fetching dynamic data fails (e.g., use a cached version or a static list).
-   **Other Providers:** While the primary goal is OpenRouter, consider how this change might pave the way for dynamically fetching model data from other providers in the future.
-   **Backward Compatibility:** Assess the impact on existing configurations and provide clear migration instructions if necessary.

## Next Steps

1.  Review this updated plan.
2.  Toggle to ACT mode to begin implementation, starting with writing tests for fetching OpenRouter model data (Step 1.1).
