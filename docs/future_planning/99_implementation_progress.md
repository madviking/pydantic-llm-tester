# Implementation Progress Checklist

This document tracks the step-by-step implementation progress for the architectural improvements and new features planned for `pydantic-llm-tester`. Each major section corresponds to a planning document and potentially a feature branch. Each sub-item represents a logical commit or a small group of related commits.

## General Guidelines for Each Step/Commit:
1.  **Branch:** Create a new feature branch for each major plan (e.g., `feature/arch-improvements`, `feature/cost-management`).
2.  **Tests First (TDD approach where applicable):**
    *   Write failing unit tests for the new/changed functionality.
3.  **Implement Changes:** Write or refactor the code to make the tests pass.
4.  **Run All Tests:** Execute the full test suite (`pytest`) to ensure no regressions.
5.  **Manual Verification (Key Milestones):** For significant changes, manually run key CLI commands (e.g., `python -m src.llm_tester.cli.main run --providers mock --py_models job_ads/simple`) to verify behavior.
6.  **Commit:**
    *   Write a clear and concise commit message following conventional commit guidelines (e.g., `feat(module): description`, `fix(module): description`, `refactor(module): description`).
    *   Update `CHANGELOG.md` if the commit introduces user-facing changes, new features, or fixes.
7.  **Push & PR:** Push the changes to the remote branch. Once a logical set of commits for a "Round" or major part of a plan is complete, create a Pull Request.
8.  **Iterate:** Do NOT proceed to the next major "Round" or plan until the current one is reviewed and merged, or explicitly decided otherwise.

## Coding Standards Reminder:
-   No file should ideally exceed 500 lines (guideline).
-   Minimize code duplication (DRY principle).
-   Prefer configuration over hardcoding.
-   Consider using well-tested libraries before implementing custom solutions.
-   Ensure the package works both as a cloned repository and as an installed Python module.
-   All new code should be type-hinted and follow PEP 8.

---

## I. Architectural Improvements (`docs/future_planning/1_architechture_improvement.md`)
**Branch:** `feature/core-architecture-refactor`

### Round 1: Decomposition of `LLMTester` Class
*   [ ] **Define Interfaces:** Sketch out the methods for `TestDiscoverer`, `TestRunner`, `ResponseValidator`, `AccuracyCalculator`.
*   [ ] **Implement `TestDiscoverer`:**
    *   [ ] Create `src/llm_tester/discovery/test_discoverer.py`.
    *   [ ] Write unit tests for `TestDiscoverer`.
    *   [ ] Move discovery logic from `LLMTester` to `TestDiscoverer`.
    *   [ ] Commit: `feat(discovery): Implement TestDiscoverer component`
*   [ ] **Implement `ResponseValidator`:**
    *   [ ] Create `src/llm_tester/validation/response_validator.py`.
    *   [ ] Write unit tests for `ResponseValidator`.
    *   [ ] Move validation logic from `LLMTester` to `ResponseValidator`.
    *   [ ] Commit: `feat(validation): Implement ResponseValidator component`
*   [ ] **Implement `AccuracyCalculator`:**
    *   [ ] Create `src/llm_tester/evaluation/accuracy_calculator.py`.
    *   [ ] Write unit tests for `AccuracyCalculator`.
    *   [ ] Move accuracy calculation logic from `LLMTester` to `AccuracyCalculator`.
    *   [ ] Commit: `feat(evaluation): Implement AccuracyCalculator component`
*   [ ] **Implement `TestRunner`:**
    *   [ ] Create `src/llm_tester/execution/test_runner.py`.
    *   [ ] Write unit tests for `TestRunner` (mocking dependencies).
    *   [ ] Move test execution logic from `LLMTester` to `TestRunner`, integrating `ResponseValidator` and `AccuracyCalculator`.
    *   [ ] Commit: `feat(execution): Implement TestRunner component`
*   [ ] **Refactor `LLMTester` to Facade:**
    *   [ ] Modify `src/llm_tester/llm_tester.py` to use the new components.
    *   [ ] Update unit/integration tests for `LLMTester` facade.
    *   [ ] Commit: `refactor(core): Refactor LLMTester class to a facade using decomposed components`
*   [ ] **Integrate Cost Management:** Ensure `TestRunner` or `LLMTester` facade correctly interacts with the (future) `CostAPI` for usage recording. (This might be done during Cost Management implementation).

### Round 2: Refinement of the Provider System (`src/llms/`)
*   [ ] **Analyze `provider_factory.py` and `llm_registry.py`:** Identify specific responsibilities to move.
*   [ ] **Implement `ExternalProviderLoader` (if deemed necessary):**
    *   [ ] Create `src/llm_tester/llms/external/loader.py`.
    *   [ ] Write unit tests.
    *   [ ] Move external provider loading logic.
    *   [ ] Commit: `feat(llms): Implement ExternalProviderLoader`
*   [ ] **Refactor `provider_factory.py`:**
    *   [ ] Simplify by delegating to `ExternalProviderLoader` and integrating with unified config for provider settings.
    *   [ ] Streamline OpenRouter model data fetching if `CostInformationService` makes parts redundant.
    *   [ ] Update unit tests.
    *   [ ] Commit: `refactor(llms): Streamline ProviderFactory and integrate with new components`
*   [ ] **Review `BaseLLM` and `llm_registry.py`:** Make minor adjustments as needed for consistency.
    *   [ ] Commit: `refactor(llms): Minor adjustments to BaseLLM and LLMRegistry`

---

## II. Unified Configuration System (`docs/future_planning/3_configuration_unification.md`)
**Branch:** `feature/unified-configuration`

### Round 1: Define Core `AppSettings` and Loading Mechanism
*   [ ] **Install `pydantic-settings`**.
    *   [ ] Commit: `build: Add pydantic-settings dependency`
*   [ ] **Create `src/llm_tester/config/settings_models.py`:** Define `AppSettings` and sub-models (`LoggingSettings`, `CacheSettings`, `CostManagementSettings`, `ProviderSettings`, `ProviderModelSettings`).
    *   [ ] Commit: `feat(config): Define core AppSettings Pydantic models`
*   [ ] **Implement `get_app_settings()` loader function.**
    *   [ ] Commit: `feat(config): Implement AppSettings loader with .env and env var support`
*   [ ] **Create `.env.example` and update `.gitignore`.**
    *   [ ] Commit: `docs(config): Add .env.example and update .gitignore`
*   [ ] **Write Unit Tests for `AppSettings` loading and validation.**
    *   [ ] Commit: `test(config): Add unit tests for AppSettings loading`

### Round 2: Migrate Existing Configuration Logic
*   [ ] **Refactor Cost Management components (`OpenRouterClient`, `CostInformationService`) to use `AppSettings`.** (Depends on Cost Management branch or done here if that's later)
    *   [ ] Commit: `refactor(cost): Integrate cost components with AppSettings`
*   [ ] **Refactor Provider Loading (`provider_factory.py`, individual providers) to use `AppSettings`.**
    *   [ ] Deprecate provider-specific `config.json` files.
    *   [ ] Commit: `refactor(llms): Integrate provider loading with AppSettings`
*   [ ] **Phase out `src/utils/config_manager.py` and `pyllm_config.json`.**
    *   [ ] Migrate any essential unique logic.
    *   [ ] Commit: `refactor(config): Deprecate and remove old ConfigManager and pyllm_config.json`
*   [ ] **Migrate `external_providers.json` data/logic to `AppSettings`.**
    *   [ ] Commit: `refactor(config): Migrate external_providers.json to AppSettings`
*   [ ] **Remove usage of `models_pricing.json`.** (Handled by Cost Management)
    *   [ ] Commit: `refactor(config): Remove usage of static models_pricing.json`
*   [ ] **Adapt CLI Configuration Commands (`configure keys`, `providers ...`) to `AppSettings`.** (Details in CLI Refactoring plan)
    *   [ ] Commit: `refactor(cli): Adapt configuration commands to AppSettings` (may be part of CLI branch)
*   [ ] **Implement Logging Setup based on `AppSettings.logging`.**
    *   [ ] Commit: `feat(config): Configure logging based on AppSettings`

### Round 3: Documentation and User Guidance
*   [ ] **Update `README.md` for new configuration.**
*   [ ] **Overhaul `docs/guides/configuration/CONFIG_REFERENCE.md`.**
*   [ ] **Update Provider/Model addition guides.**
*   [ ] **Update CLI documentation for config commands.**
*   [ ] Commit: `docs(config): Update all documentation for unified configuration system`

---

## III. OpenRouter Cost Management (`docs/future_planning/2_cost_management_from_openrouter.md`)
**Branch:** `feature/cost-management` (May depend on/merge with `feature/unified-configuration`)

### Round 1: Core Infrastructure - OpenRouter API Client & Schemas
*   [ ] **Create `src/llm_tester/infrastructure/openrouter/client.py::OpenRouterClient`.**
    *   [ ] Commit: `feat(cost): Implement OpenRouterClient`
*   [ ] **Create `src/llm_tester/infrastructure/openrouter/schemas.py` with Pydantic models.**
    *   [ ] Commit: `feat(cost): Define Pydantic schemas for OpenRouter API responses`
*   [ ] **Write Unit Tests for `OpenRouterClient` and schemas.**
    *   [ ] Commit: `test(cost): Add unit tests for OpenRouterClient and schemas`

### Round 2: (Covered by Unified Configuration) Core Infrastructure - Unified Configuration Settings for Cost
*   Ensure `AppSettings` (from `feature/unified-configuration`) includes `CostManagementSettings` with `openrouter_api_key`, cache settings.

### Round 3: Service Layer - Cost Information Service
*   [ ] **Create `src/llm_tester/services/cost_service.py::CostInformationService`.**
    *   [ ] Implement fetching, caching (file-based), and fallback logic.
    *   [ ] Integrate with `OpenRouterClient` and `AppSettings`.
    *   [ ] Commit: `feat(cost): Implement CostInformationService`
*   [ ] **Prepare fallback data JSON file (e.g., `src/llm_tester/data/openrouter_fallback_models.json`) and ensure packaging.**
    *   [ ] Commit: `feat(cost): Add fallback model data for CostInformationService`
*   [ ] **Write Unit Tests for `CostInformationService`.**
    *   [ ] Commit: `test(cost): Add unit tests for CostInformationService`

### Round 4: Service Layer - Cost Calculator
*   [ ] **Create `src/llm_tester/services/cost_calculator.py::CostCalculator`.**
    *   [ ] Integrate with `CostInformationService`.
    *   [ ] Commit: `feat(cost): Implement CostCalculator service`
*   [ ] **Write Unit Tests for `CostCalculator`.**
    *   [ ] Commit: `test(cost): Add unit tests for CostCalculator`

### Round 5: Service Layer - Token Counter & Usage Tracker
*   [ ] **Create `src/llm_tester/services/token_counter.py::TokenCounter`.**
    *   [ ] Implement default heuristic and `tiktoken` integration.
    *   [ ] Integrate with `CostInformationService` for context length checks.
    *   [ ] Commit: `feat(cost): Implement TokenCounter service`
*   [ ] **Write Unit Tests for `TokenCounter`.**
    *   [ ] Commit: `test(cost): Add unit tests for TokenCounter`
*   [ ] **Create `src/llm_tester/services/usage_tracker.py::UsageTracker` with `UsageEntry` Pydantic model.**
    *   [ ] Implement session-based usage recording and summary.
    *   [ ] Integrate with `CostCalculator`.
    *   [ ] Commit: `feat(cost): Implement UsageTracker service`
*   [ ] **Write Unit Tests for `UsageTracker`.**
    *   [ ] Commit: `test(cost): Add unit tests for UsageTracker`

### Round 6: API Facade - `CostAPI`
*   [ ] **Create `src/llm_tester/cost_api.py::CostAPI`.**
    *   [ ] Implement singleton and facade methods.
    *   [ ] Integrate all underlying cost services.
    *   [ ] Commit: `feat(cost): Implement CostAPI facade`
*   [ ] **Write Unit/Integration Tests for `CostAPI`.**
    *   [ ] Commit: `test(cost): Add tests for CostAPI facade`
*   [ ] **Integrate `CostAPI` into `LLMTester` facade / `TestRunner` for recording usage.**
    *   [ ] Commit: `refactor(core): Integrate CostAPI with LLMTester/TestRunner for usage tracking`

---

## IV. CLI Refactoring (`docs/future_planning/4_cli_refactoring.md`)
**Branch:** `feature/cli-refactor`

### Round 1: Refactor `interactive_ui.py`
*   [ ] **Decompose `interactive_ui.py` into modules/classes under `src/llm_tester/cli/interactive/`.**
    *   [ ] Commit: `refactor(cli): Decompose interactive_ui.py into modular components` (can be multiple commits per menu)
*   [ ] **Create `src/llm_tester/cli/ui_utils.py` for common UI elements (if needed).**
    *   [ ] Commit: `feat(cli): Add ui_utils for common interactive UI elements`
*   [ ] **Write Unit Tests for new interactive menu modules/classes.**
    *   [ ] Commit: `test(cli): Add unit tests for interactive menu components`

### Round 2: Standardize CLI Command Structure and Core Logic Interaction
*   [ ] **Refactor `src/cli/core/` logic into application facade/services or CLI-specific utilities.**
    *   [ ] Commit: `refactor(cli): Streamline cli/core logic and integrate with app facade`
*   [ ] **Ensure CLI commands in `src/cli/commands/` use the application facade/service layer.**
    *   [ ] Commit: `refactor(cli): Update CLI commands to use application facade/services`
*   [ ] **Implement consistent error handling and output formatting in CLI commands.**
    *   [ ] Commit: `style(cli): Standardize error handling and output formatting`

### Round 3: Enhance Configuration-Related CLI Commands
*   [ ] **Adapt `llm-tester configure keys` for `AppSettings`.**
    *   [ ] Commit: `refactor(cli): Update 'configure keys' command for AppSettings`
*   [ ] **Adapt `llm-tester providers ...` commands for `AppSettings`.** (Choose Option 1, 2, or 3 from plan)
    *   [ ] Commit: `refactor(cli): Update 'providers' commands for AppSettings`
*   [ ] **Implement `llm-tester config show` command.**
    *   [ ] Commit: `feat(cli): Add 'config show' command`

---

## V. Testing Strategy Enhancement (`docs/future_planning/5_testing_strategy_enhancement.md`)
**Branch:** `feature/testing-enhancements` (or integrate into other feature branches)

### Round 1: Define Test Structure and Layers
*   [ ] **Restructure `tests/` directory (unit, integration, e2e).**
    *   [ ] Commit: `refactor(tests): Restructure tests directory into unit, integration, e2e layers`
*   [ ] **Migrate existing tests to the new structure.**
    *   [ ] Commit: `refactor(tests): Classify and move existing tests to new structure`

### Round 2: Enhance Unit Test Coverage and Mocking
*   [ ] **Write/improve unit tests for all core components as per the plan.** (This will happen across multiple feature branches)
    *   [ ] Track coverage improvements.

### Round 3: Develop Integration Tests
*   [ ] **Write integration tests for `CostAPI`, Provider Interactions, `LLMTester` Facade.** (Across feature branches)

### Round 4: Enhance End-to-End (E2E) CLI Tests
*   [ ] **Implement/improve E2E tests for key CLI commands using `typer.testing.CliRunner`.**
    *   [ ] Commit: `test(e2e): Add/enhance E2E tests for CLI commands`

### Round 5: CI Integration and Test Reporting
*   [ ] **Configure CI for coverage reporting (e.g., Codecov).**
    *   [ ] Commit: `ci: Add test coverage reporting to CI workflow`
*   [ ] **Add Makefile targets or scripts for easy local test execution.**
    *   [ ] Commit: `build: Add Makefile targets for local test execution`

---
*This checklist will be updated as tasks are completed.*
