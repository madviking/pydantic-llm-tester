# OpenRouter Provider Implementation Plan

This document outlines the steps required to add support for OpenRouter as a dedicated LLM provider within the `llm-tester` project. This approach uses the standard `openai` Python library configured to point to the OpenRouter API endpoint.

## 1. Create Directory Structure

Create the necessary directory and initialization file for the new provider:

```bash
mkdir -p llm_tester/llms/openrouter
touch llm_tester/llms/openrouter/__init__.py
```

## 2. Create Configuration File (`config.json`)

Create `llm_tester/llms/openrouter/config.json`. This file defines the provider settings and the models available through it.

**Structure:**

```json
{
  "name": "openrouter",
  "provider_type": "openrouter",
  "env_key": "OPENROUTER_API_KEY", // Standard environment variable for OpenRouter
  "env_key_secret": null,
  "system_prompt": "Extract the requested information from the provided text as accurate JSON.", // Default system prompt (can be overridden)
  "models": [
    // --- ACTION NEEDED: Populate with specific OpenRouter models ---
    // Example:
    // {
    //   "name": "google/gemini-flash-1.5", // Full OpenRouter model ID (e.g., from https://openrouter.ai/models)
    //   "default": false,                 // Mark one model as default if desired
    //   "preferred": true,                // Mark preferred models
    //   "cost_input": 0.35,               // Cost per 1M input tokens in USD
    //   "cost_output": 0.70,              // Cost per 1M output tokens in USD
    //   "cost_category": "cheap",         // Optional category
    //   "max_input_tokens": 1048576,      // Max input tokens (check model specs)
    //   "max_output_tokens": 8192         // Max output tokens (check model specs)
    // },
    // ... add other desired models here
  ]
}
```

**Note:** The `models` array needs to be populated with the specific models you intend to use via OpenRouter, including their costs and token limits.

## 3. Create Provider Implementation (`provider.py`)

Create `llm_tester/llms/openrouter/provider.py`. This file contains the core logic for interacting with the OpenRouter API.

**Implementation Details:**

*   Define a class `OpenRouterProvider` inheriting from `llm_tester.llms.base.BaseLLM`.
*   Import the `OpenAI` client from the `openai` library.
*   In the `__init__` method:
    *   Call `super().__init__(config)`.
    *   Retrieve the API key using `self.get_api_key()` (which reads the `env_key` specified in `config.json`).
    *   Initialize the `OpenAI` client, setting the `base_url` to OpenRouter's endpoint:
        ```python
        from openai import OpenAI
        # ... other imports

        class OpenRouterProvider(BaseLLM):
            def __init__(self, config=None):
                super().__init__(config)
                api_key = self.get_api_key()
                if not api_key:
                    self.logger.warning(f"No API key found for OpenRouter. Set the {self.config.env_key} environment variable.")
                    self.client = None
                    return

                # --- ACTION NEEDED: Decide on header values ---
                # Replace YOUR_SITE_URL and YOUR_APP_NAME appropriately
                # If not desired, remove default_headers
                headers = {
                    "HTTP-Referer": "https://github.com/madviking/pydantic-llm-tester", # e.g., https://github.com/user/llm-tester
                    "X-Title": "LLM Tester"      # e.g., LLM Tester
                }

                try:
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url="https://openrouter.ai/api/v1",
                        default_headers=headers # Optional, but recommended by OpenRouter
                    )
                    self.logger.info("OpenRouter client initialized")
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenRouter client: {e}")
                    self.client = None
        ```
*   Implement the `_call_llm_api` method:
    *   This method will be very similar to the existing `OpenAIProvider`'s implementation.
    *   Use `self.client.chat.completions.create(...)`.
    *   Pass the `model_name` exactly as defined in `config.json` (e.g., `"google/gemini-flash-1.5"`).
    *   Handle potential API errors.
    *   Extract the response text and usage data (`prompt_tokens`, `completion_tokens`, `total_tokens`) from the API response.
    *   Return `(response_text, usage_data_dict)`.

## 4. Add Unit Tests

Create a new test file `tests/test_openrouter_provider.py`.

*   Use `pytest` and `unittest.mock`.
*   Mock the `openai.OpenAI` client and its `chat.completions.create` method.
*   Test:
    *   Successful initialization.
    *   Initialization failure (missing API key).
    *   Successful API call and response parsing.
    *   Correct handling of usage data.
    *   API error handling.

## 5. Update Documentation

*   Add OpenRouter to the list of supported providers in `README.md` or relevant documentation files (e.g., `docs/guides/providers/ADDING_PROVIDERS.md`).
*   Include instructions on setting the `OPENROUTER_API_KEY` environment variable.

## 6. CLI Enhancements

This section outlines planned enhancements to the `llm-tester` command-line interface (CLI) to improve usability and management.

### 6.1. API Key Management

*   **Goal:** Automatically detect missing API keys required by enabled providers and prompt the user to enter them. Optionally save keys to a `.env` file.
*   **Implementation:**
    *   During startup or via a command (e.g., `llm-tester configure keys`), check environment variables listed in `env_key` for all loaded provider configs.
    *   If a key is missing, securely prompt the user for the value using a library like `getpass`.
    *   Ask the user if they want to save the key to a `.env` file in the project root (this file should be in `.gitignore`). Use a library like `python-dotenv` for reading/writing. Handle file creation and updates carefully.

### 6.2. Update Model Information

*   **Goal:** Provide a command to refresh pricing and token limits in provider `config.json` files using live data from APIs (starting with OpenRouter).
*   **Implementation:**
    *   Create a command like `llm-tester update-models --provider <provider_name>`.
    *   For `openrouter`, trigger the dynamic fetching logic (from the dynamic loading plan: `OPENROUTER_DYNAMIC_MODELS_PLAN.md`).
    *   Read the static `llm_tester/llms/openrouter/config.json`.
    *   For each model returned by the API, find the corresponding entry in the `config.json` object by `name`.
    *   Update *only* the `cost_input`, `cost_output`, `max_input_tokens`, `max_output_tokens` fields in the `config.json` object with the fetched data. Preserve other fields like `default`, `preferred`, `enabled`, etc.
    *   Write the updated `config.json` back to disk, preserving formatting if possible.
    *   Consider how to handle models found in the API but not in the config (e.g., log a message, optionally prompt to add with default settings).

### 6.3. Provider and Model Management

*   **Goal:** Allow users to easily enable/disable providers and select specific models (especially for meta-providers like OpenRouter), potentially with LLM assistance.
*   **Implementation:**
    *   **Provider Enable/Disable:**
        *   Introduce a central configuration (e.g., in the root `config.json` or a new `enabled_providers.json`) listing enabled provider names. This file should store a list of strings.
        *   Modify `provider_factory.py` (`discover_provider_classes` or `get_available_providers`) to filter based on this enabled list.
        *   Add CLI commands: `llm-tester providers list [--all]`, `llm-tester providers enable <name>`, `llm-tester providers disable <name>`. These commands modify the central configuration file.
    *   **OpenRouter Model Selection:**
        *   Extend `llm_tester/llms/openrouter/config.json` models with an `"enabled": true/false` flag (defaulting to `false` or `true` based on preference - perhaps `false` initially).
        *   Modify `OpenRouterProvider`'s `get_model_config` or the logic that uses it to only consider models marked as `"enabled": true` when selecting models for testing.
        *   Add CLI commands: `llm-tester models list --provider openrouter [--all]`, `llm-tester models enable openrouter/<model_id>`, `llm-tester models disable openrouter/<model_id>`. These commands modify the `enabled` flag within `llm_tester/llms/openrouter/config.json`.
    *   **LLM-Assisted Model Recommendation:**
        *   Create an interactive command: `llm-tester recommend-model`.
        *   Prompt user for task description (e.g., "summarize long articles cheaply", "generate creative Python code").
        *   Gather details (name, cost, limits, description if available from API or config) of all *enabled* models from *enabled* providers.
        *   Use an LLM (e.g., a default configured one, maybe via OpenRouter itself, ensuring API key is available) with a carefully crafted prompt including the user's task and formatted model details.
        *   Present the LLM's recommendation/ranking to the user clearly.

## Action Items Summary

1.  **Provide Model Details:** Specify the OpenRouter models to include in `config.json` (name, costs, token limits).
2.  **Provide Header Values:** Specify the values for `HTTP-Referer` and `X-Title` headers in `provider.py`, or decide to omit them.
