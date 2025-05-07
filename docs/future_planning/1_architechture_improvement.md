# Architectural Improvements Plan

## Overview
This document outlines the architectural improvements for the `pydantic-llm-tester` project, focusing on proper separation of concerns and creating a maintainable, testable structure. The project code is located within the `src/` directory.

## Principles
- Each component should have a single responsibility.
- Dependencies should be explicitly defined and injected wherever possible.
- All core components should be testable in isolation.
- Clear boundaries between modules and layers of the application.

## Suggested improvements

### Round 1: Decomposition of `LLMTester` Class

#### Problem we are solving
The `src/llm_tester.py::LLMTester` class currently has a wide range of responsibilities, including:
- Discovering test cases (`discover_test_cases`, `_get_test_cases_from_model`, `_discover_legacy_test_cases`, `_find_model_class_from_path`).
- Running individual tests and suites of tests (`run_test`, `run_tests`).
- Validating LLM responses against Pydantic models (`_validate_response`).
- Calculating accuracy metrics (`_calculate_accuracy` and its helper methods).
- Managing cost reporting (`save_cost_report`).

This violates the Single Responsibility Principle, making the class large, complex, difficult to understand, harder to test in isolation, and more prone to bugs when changes are made.

#### What needs to be done
Decompose the `LLMTester` class into smaller, more focused classes/modules, each with a clear, single responsibility. The `LLMTester` class can then act as an orchestrator or facade, delegating tasks to these specialized components.

1.  **`TestDiscoverer` Component:**
    *   **Responsibility:** Discovering and loading test cases from specified directories and Pydantic models.
    *   **Methods:** Would encapsulate logic from `discover_test_cases`, `_get_test_cases_from_model`, `_discover_legacy_test_cases`, `_find_model_class_from_path`.
    *   **Location:** e.g., `src/llm_tester/discovery/test_discoverer.py`

2.  **`TestRunner` Component:**
    *   **Responsibility:** Managing the execution of individual test cases and suites of tests against different LLM providers. It would interact with the `ProviderManager` (or its successor) and the `ResponseValidator`.
    *   **Methods:** Would encapsulate logic from `run_test` (the execution part) and `run_tests`.
    *   **Location:** e.g., `src/llm_tester/execution/test_runner.py`

3.  **`ResponseValidator` Component:**
    *   **Responsibility:** Validating the raw string response from an LLM against a given Pydantic model and expected data.
    *   **Methods:** Would encapsulate logic from `_validate_response`.
    *   **Location:** e.g., `src/llm_tester/validation/response_validator.py`

4.  **`AccuracyCalculator` Component:**
    *   **Responsibility:** Calculating various accuracy metrics by comparing extracted data with expected data.
    *   **Methods:** Would encapsulate logic from `_calculate_accuracy` and its private helper methods (`_normalize_value`, `_compare_values`, `_compare_dicts`, etc.).
    *   **Location:** e.g., `src/llm_tester/evaluation/accuracy_calculator.py`

5.  **`CostManager` Integration (from `src/utils/cost_manager.py` or future OpenRouter integration):**
    *   The existing `CostTracker` in `src/utils/cost_manager.py` (or its evolution as per `2_cost_management_from_openrouter.md`) should be the primary component for cost tracking and reporting.
    *   The `LLMTester` facade or `TestRunner` would interact with this `CostManager` to record usage and retrieve cost reports. The `save_cost_report` method in `LLMTester` would likely be removed or delegate directly.

6.  **`LLMTester` Facade:**
    *   The `src/llm_tester.py::LLMTester` class would be refactored to become a higher-level facade.
    *   It would initialize and coordinate these new components.
    *   Its public API methods (`run_tests`, `discover_test_cases`, etc.) would delegate to the respective components.

#### Test high level plan
- **TestDiscoverer:** Verify it correctly finds and structures test cases from various valid and invalid directory layouts and model definitions.
- **TestRunner:** Verify it can execute a test case using a mock provider and mock validator, focusing on the orchestration logic.
- **ResponseValidator:** Verify it correctly validates correct and incorrect LLM responses against different Pydantic models and expected outputs.
- **AccuracyCalculator:** Verify it calculates accuracy scores correctly for various scenarios of matching and mismatching data structures.
- **LLMTester Facade:** Verify its public API methods correctly orchestrate the underlying components and produce the expected overall results (e.g., running a full test suite and getting a combined report).
- Ensure that after refactoring, the overall functionality of running tests and generating reports remains the same from an end-user (CLI/API) perspective.

#### Success criteria
- The `LLMTester` class is significantly smaller and its methods primarily delegate to specialized components.
- New classes (`TestDiscoverer`, `TestRunner`, `ResponseValidator`, `AccuracyCalculator`) are created, each with a well-defined single responsibility.
- Each new component has its own set of unit tests.
- The overall application behavior (CLI and API) remains consistent with pre-refactoring functionality.
- Code is more modular, easier to understand, and individual components can be tested in isolation.

#### What are the developer benefits?
- **Improved Maintainability:** Smaller, focused classes are easier to understand, modify, and debug.
- **Enhanced Testability:** Individual components can be unit-tested thoroughly and in isolation, leading to more robust tests.
- **Better Reusability:** Specialized components might be reusable in other contexts or for new features.
- **Reduced Complexity:** Overall cognitive load for understanding the system is reduced.
- **Easier Collaboration:** Developers can work on different components with fewer merge conflicts.

#### List the involved files
- `src/llm_tester.py` (to be refactored into a facade)
- New files for each component:
    - `src/llm_tester/discovery/test_discoverer.py` (and `__init__.py`)
    - `src/llm_tester/execution/test_runner.py` (and `__init__.py`)
    - `src/llm_tester/validation/response_validator.py` (and `__init__.py`)
    - `src/llm_tester/evaluation/accuracy_calculator.py` (and `__init__.py`)
- Test files for each new component (e.g., `tests/discovery/test_test_discoverer.py`, etc.).
- `src/utils/cost_manager.py` (for integration, or its successor).
- Files that currently instantiate or use `LLMTester` (e.g., CLI command handlers in `src/cli/commands/` or `src/cli/core/`) will need to be updated to use the refactored facade or its components if necessary.

---

### Round 3: Refinement of the Provider System (`src/llms/`)

#### Problem we are solving
The provider system, primarily located in `src/llms/`, has several key files (`base.py`, `llm_registry.py`, `provider_factory.py`) that handle provider discovery, instantiation, configuration, and interaction. While functional, there are opportunities to clarify responsibilities and improve the design, especially concerning `provider_factory.py` which seems to handle many diverse tasks (caching, OpenRouter model fetching, static model merging, provider class discovery, external provider registration).

#### What needs to be done
1.  **Clarify Roles of `llm_registry.py` and `provider_factory.py`:**
    *   **`llm_registry.py`:** Should primarily be responsible for *accessing* registered/discovered provider instances. `get_llm_provider` seems appropriate here. `discover_providers` (listing names) and `get_provider_info` also fit.
    *   **`provider_factory.py`:** Should focus on the *creation and registration* of provider instances. This includes loading configurations, discovering provider classes (both built-in and external), and instantiating them.
2.  **Decompose `provider_factory.py`:**
    *   **External Provider Loading:** The logic for `_create_external_provider`, `load_external_providers`, and `register_external_provider` could be moved to a dedicated `ExternalProviderLoader` class or module (e.g., `src/llms/external/loader.py`). This would simplify `provider_factory.py`.
    *   **OpenRouter Model Fetching & Caching:** The logic `_fetch_openrouter_models_with_cache` and `_merge_static_and_api_models` is specific to OpenRouter integration for enriching model data. If the new OpenRouter client (from `2_cost_management_from_openrouter.md`) handles its own comprehensive model data fetching and caching, this logic in `provider_factory.py` might become redundant or significantly simpler. If it's still needed for merging with locally defined provider models, it should be clearly delineated.
    *   **Provider Class Discovery:** `discover_provider_classes` is a core factory responsibility.
3.  **Configuration Loading:** `load_provider_config` in `provider_factory.py` should integrate with the new Unified Configuration System (planned in `3_configuration_unification.md`). It should fetch the specific configuration for a given provider from the central config manager.
4.  **Caching Strategy Review:**
    *   The `_is_cache_stale` and general caching for OpenRouter models in `provider_factory.py` needs to be harmonized with the caching strategy in the `CostInformationService` (from `2_cost_management_from_openrouter.md`). Avoid duplicate caching mechanisms. The `CostInformationService` should be the source of truth for OpenRouter model data, including pricing and context length.
    *   The `reset_caches` function should be clear about which caches it's resetting.
5.  **`BaseLLM` (`src/llms/base.py`):**
    *   Review the `BaseLLM` abstract class. Ensure its contract is clear and sufficient for all provider types.
    *   The `get_model_config` method returning `Optional[ModelConfig]` and `get_available_models` returning `List[ModelConfig]` should source their information consistently, potentially via the `CostInformationService` or the unified configuration for model details not covered by OpenRouter (e.g., custom system prompts per model).

#### Test high level plan
- **ExternalProviderLoader:** Verify it can correctly load and register provider classes from external modules. Test with valid and invalid external provider definitions.
- **ProviderFactory (Refactored):** Verify it can correctly create provider instances for built-in and (mocked) external providers, using the unified configuration system. Test error handling for missing configurations or invalid provider names.
- **LLMRegistry:** Verify it can retrieve already created provider instances.
- **Caching:** Verify that if any caching remains in `provider_factory.py`, it functions correctly (stale checks, cache refresh) and doesn't conflict with other caching layers.
- **BaseLLM Interactions:** Ensure that provider instances created through the factory correctly implement the `BaseLLM` interface and can interact with (mocked) LLM APIs.

#### Success criteria
- `provider_factory.py` is smaller and more focused on provider creation and registration.
- Responsibilities like external provider loading and OpenRouter model data fetching are either delegated to specialized components or streamlined by them.
- Clear distinction between the roles of `llm_registry.py` (accessing providers) and `provider_factory.py` (creating/registering providers).
- Provider configuration loading is integrated with the unified configuration system.
- Caching mechanisms are consolidated and efficient.
- The system can still discover, configure, and instantiate all types of providers (built-in, external, mock).

#### What are the developer benefits?
- **Improved Modularity:** Easier to understand and maintain the provider system.
- **Simplified `provider_factory.py`:** Reduces the complexity of a critical file.
- **Better Extensibility:** Clearer separation makes it easier to add new types of provider discovery or instantiation logic in the future.
- **Consistent Configuration:** Integration with a unified config system simplifies how providers get their settings.

#### List the involved files
- `src/llms/provider_factory.py` (major refactoring)
- `src/llms/llm_registry.py` (minor adjustments)
- `src/llms/base.py` (review and potential minor adjustments)
- New file: `src/llms/external/loader.py` (and `__init__.py`) (tentative)
- `src/utils/config_manager.py` (or its successor, for integration)
- `docs/future_planning/2_cost_management_from_openrouter.md` (for aligning OpenRouter data fetching)
- Individual provider implementations (e.g., `src/llms/openai/provider.py`) to ensure they adapt to any changes in configuration or base class.
- Test files for the provider system (e.g., `tests/test_provider_factory.py`, new tests for `ExternalProviderLoader`).
