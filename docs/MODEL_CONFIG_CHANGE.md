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
    Status: Not started
    Notes for next steps:
    Additional dependencies to check for next step:

    3.1. Create test(s) for identifying when OpenRouter is enabled in `pyllm_config.json`.
    3.2. Implement logic in `ConfigManager` to check OpenRouter's enabled status.
    3.3. Create test(s) for calling the OpenRouter provider method to fetch model data if OpenRouter is enabled during configuration loading.
    3.4. Implement the call to fetch OpenRouter model data in `ConfigManager` during initialization/loading.
    3.5. Create test(s) for storing the fetched OpenRouter model data in the central registry via `ConfigManager`.
    3.6. Implement storing fetched data in the central registry via `ConfigManager`.
    3.7. Create test(s) for parsing the "provider:model-name" format from `pyllm_config.json`.
    3.8. Implement parsing logic for the new format in `ConfigManager`.
    3.9. Create test(s) for looking up model details (pricing, context length) from the central registry when parsing the new format.
    3.10. Implement lookup of model details from the central registry in `ConfigManager`.
    3.11. Create test(s) for raising an exception if a provider specified in "provider:model-name" is not enabled.
    3.12. Implement the check and exception raising for disabled providers in `ConfigManager`.

4.  **Refactor Provider `config.json` Files (`src/pydantic_llm_tester/llms/*/config.json`)**
    Status: Not started
    Notes for next steps: This step primarily involves manual file modification and verification.

    4.1. Create test(s) to verify that provider `config.json` files do NOT contain the `llm_models` array.
    4.2. Manually remove the `llm_models` array from all provider `config.json` files.

5.  **Update `pyllm_config.json` Structure**
    Status: Not started
    Notes for next steps: This step primarily involves defining the new structure and updating documentation/examples.

    5.1. Define the new structure for specifying models using the "provider:model-name" format in `pyllm_config.json`.
    5.2. Update example `pyllm_config.json` files or documentation to show the new format.

6.  **Adjust `LLMRegistry` and `ProviderFactory`**
    Status: Not started
    Notes for next steps:
    Additional dependencies to check for next step:

    6.1. Create test(s) for `LLMRegistry` and `ProviderFactory` to retrieve model details from the central registry instead of provider `config.json`.
    6.2. Modify `LLMRegistry` and `ProviderFactory` to use the central model registry/cache for model details.

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
