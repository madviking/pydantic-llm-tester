# Plan: Dynamic Loading of OpenRouter Model Information

This document outlines a plan to enhance the `OpenRouterProvider` integration by dynamically fetching model details (pricing, context windows, etc.) directly from the OpenRouter API, reducing reliance on the static `llm_tester/llms/openrouter/config.json` file.

## 1. Goal

Instead of manually maintaining model details like cost and token limits in `config.json`, fetch this information directly from the OpenRouter API (`https://openrouter.ai/api/v1/models`) during application startup or provider loading.

## 2. OpenRouter API Endpoint

*   **URL:** `https://openrouter.ai/api/v1/models`
*   **Method:** `GET`
*   **Authentication:** None required for this endpoint.
*   **Response:** A JSON object containing a `data` array. Each element in the array represents a model and includes fields like:
    *   `id`: The full model identifier (e.g., `google/gemini-flash-1.5`).
    *   `name`: Human-readable name.
    *   `pricing`: Object containing `prompt` (cost per prompt token) and `completion` (cost per completion token) as strings. **Note:** These costs need to be converted to cost per 1 million tokens (multiply by 1,000,000).
    *   `context_length`: Maximum context window size (input + output).
    *   `top_provider`: Information about the underlying provider.
    *   Other potentially useful fields like `architecture`.

## 3. Integration Strategy

Modify the provider loading mechanism, specifically within `llm_tester/llms/provider_factory.py`, to incorporate dynamic fetching for the `openrouter` provider.

*   **Target Function:** Enhance the `load_provider_config` function.
*   **Logic:**
    1.  When `load_provider_config` is called for `provider_name == "openrouter"`, first load the static `config.json` as usual to get base settings (`name`, `provider_type`, `env_key`, `system_prompt`, and potentially a minimal list of models or default flags).
    2.  Make a `GET` request to the OpenRouter `/models` API endpoint.
    3.  Parse the JSON response.
    4.  Iterate through the models returned by the API.
    5.  For each API model, create or update a corresponding `ModelConfig` object:
        *   Use `id` for `ModelConfig.name`.
        *   Convert `pricing.prompt` and `pricing.completion` strings to floats and multiply by 1,000,000 to get `cost_input` and `cost_output`.
        *   Use `context_length` potentially for `max_input_tokens` (needs clarification if this limit applies strictly to input or total context). Assume it's total context for now; `max_output_tokens` might need a default or separate configuration if not provided.
        *   Merge this dynamic data with any corresponding model definitions found in the static `config.json` (e.g., static `default` or `preferred` flags could be preserved). API data should generally override static cost/limit data.
    6.  Replace or update the `models` list in the initially loaded `ProviderConfig` object with the dynamically generated/updated list of `ModelConfig` objects.
    7.  Return the enhanced `ProviderConfig`.

## 4. Implementation Details

*   **HTTP Client:** Use the standard `requests` library (add to `requirements.txt` if not already present) or Python's built-in `urllib.request`. `requests` is generally preferred for simplicity.
*   **Error Handling:** Implement robust error handling for the API call (network errors, timeouts, non-200 status codes, invalid JSON). If the API call fails, log a warning and fall back to using only the data from the static `config.json`.
*   **Data Mapping:** Carefully map the API response fields to `ModelConfig` fields, performing necessary type conversions (string to float for costs) and calculations (cost per token to cost per 1M tokens).
*   **Caching:** Implement simple time-based caching (e.g., using `time.time()` and a global variable or a simple cache class) for the API response within `provider_factory.py` to avoid hitting the API on every provider creation during a single application run. A cache duration of several hours or a day might be appropriate.
*   **Configuration:** Decide if the dynamic loading should be configurable (e.g., an environment variable or a setting in the main `config.json` to enable/disable it). Default to enabled.
*   **Token Limits:** Clarify how OpenRouter's `context_length` maps to `max_input_tokens` and `max_output_tokens`. If `context_length` is the total limit, a sensible default or static configuration might be needed for `max_output_tokens`.

## 5. Testing

*   Add new unit tests in `tests/test_provider_factory.py` (or a dedicated test file).
*   Use `unittest.mock.patch` to mock the `requests.get` call (or equivalent).
*   Test scenarios:
    *   Successful API call and merging with static config.
    *   Correct cost conversion.
    *   API call failure and fallback to static config.
    *   Cache hit and cache miss.
    *   Handling of models present in API but not static config, and vice-versa.

## 6. Documentation

*   Update `docs/future_planning/OPENROUTER_IMPLEMENTATION_PLAN.md` to reflect the dynamic loading capability.
*   Update relevant provider documentation (`docs/guides/providers/ADDING_PROVIDERS.md`) explaining that model details are fetched dynamically for OpenRouter.
*   Document any configuration options related to dynamic loading or caching.

## Benefits

*   Reduces manual maintenance of model details in `config.json`.
*   Ensures cost and limit information is up-to-date.
*   Automatically discovers new models added to OpenRouter.

## Potential Challenges

*   Dependency on the OpenRouter API being available and stable.
*   Mapping API fields precisely to the internal `ModelConfig` structure, especially regarding token limits.
*   Handling potential changes in the OpenRouter API response format over time.
