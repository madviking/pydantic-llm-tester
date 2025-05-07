# Testing Strategy Enhancement Plan

## Overview
This document outlines the plan to enhance the testing strategy for the `pydantic-llm-tester` project. While tests exist (primarily in the `tests/` directory), a more structured approach with clear distinctions between test types, increased coverage for core components, and robust mocking will improve the project's stability and maintainability. This plan aligns with the architectural improvements proposed in other planning documents.

## Principles
-   **Test Pyramid:** Emphasize a healthy balance of unit, integration, and end-to-end (E2E) tests.
-   **Isolation:** Unit tests should test components in isolation, using mocks for external dependencies.
-   **Realism:** Integration tests should verify interactions between components, using real instances where feasible or high-fidelity mocks.
-   **Coverage:** Aim for high test coverage of critical business logic.
-   **Maintainability:** Tests should be easy to write, understand, and maintain.
-   **Automation:** All tests should be runnable automatically (e.g., via `pytest`) and integrated into CI.

## Current Testing Structure
-   `tests/`: Contains various test files, seemingly a mix of unit and integration tests.
-   `pytest` is used as the test runner.
-   `conftest.py` provides fixtures.
-   Mocking is used, e.g., `src/llms/mock/provider.py` and potentially `unittest.mock`.

## Proposed Enhancements

---

### Round 1: Define Test Structure and Layers

#### Objective
Establish a clear directory structure for tests that reflects the different test layers (unit, integration, E2E) and mirrors the application's structure.

#### What needs to be done
1.  **Restructure `tests/` Directory:**
    *   Create subdirectories within `tests/` for different test types and application modules:
        ```
        tests/
        ├── unit/
        │   ├── config/
        │   │   └── test_settings_models.py
        │   ├── services/
        │   │   ├── test_cost_service.py
        │   │   ├── test_cost_calculator.py
        │   │   └── test_token_counter.py
        │   ├── infrastructure/
        │   │   └── openrouter/
        │   │       └── test_client.py
        │   ├── discovery/
        │   │   └── test_test_discoverer.py  # From LLMTester decomposition
        │   ├── execution/
        │   │   └── test_test_runner.py      # From LLMTester decomposition
        │   ├── validation/
        │   │   └── test_response_validator.py # From LLMTester decomposition
        │   ├── evaluation/
        │   │   └── test_accuracy_calculator.py # From LLMTester decomposition
        │   └── llms/
        │       ├── test_base_llm.py
        │       └── test_provider_factory.py # (Unit aspects)
        ├── integration/
        │   ├── test_cost_api_integration.py
        │   ├── test_provider_integrations.py # (Testing actual provider classes with mocked LLM calls)
        │   ├── test_llm_tester_facade.py    # (Testing the refactored LLMTester facade with integrated components)
        │   └── cli/
        │       └── test_cli_core_logic_integration.py
        ├── e2e/  # End-to-end tests for CLI
        │   ├── test_cli_run_command.py
        │   ├── test_cli_scaffold_command.py
        │   └── test_cli_interactive_mode.py
        ├── conftest.py
        └── fixtures/ # Directory for shared fixture definitions if conftest.py grows too large
            └── ...
        ```
    *   Migrate existing tests to this new structure, classifying them appropriately.
2.  **Clarify Test Types:**
    *   **Unit Tests:** Focus on individual classes or functions. All external dependencies (other classes, network calls, file system) are mocked. Fast execution.
    *   **Integration Tests:** Test the interaction between several components. For example, testing the `CostAPI` with its underlying services, or a provider class with a mocked HTTP client for its LLM API calls. Slower than unit tests but faster than E2E.
    *   **E2E Tests (CLI Tests):** Test the application from the user's perspective by invoking CLI commands and verifying output or side effects (e.g., file creation). These are the slowest and most brittle but crucial for verifying overall functionality.

#### Test high level plan
-   N/A (This round is about structuring tests, not writing new application code).

#### Success criteria
-   The `tests/` directory is reorganized according to the defined structure.
-   Existing tests are moved to appropriate locations.
-   Clear distinction in the codebase where unit, integration, and E2E tests reside.

#### What are the developer benefits?
-   **Clarity:** Easier to find and understand tests for specific components or layers.
-   **Targeted Testing:** Developers can run specific types of tests (e.g., only unit tests) more easily.
-   **Improved Maintainability:** A structured approach makes it easier to add new tests and maintain existing ones.

#### List the involved files
-   All files currently in `tests/`.
-   `conftest.py`.

#### Commit Message
`refactor(tests): Restructure test directory and define test layers`

---

### Round 2: Enhance Unit Test Coverage and Mocking

#### Objective
Increase unit test coverage for all core components, especially those refactored or newly created (e.g., from `LLMTester` decomposition, new services in the cost management system, configuration models). Implement robust mocking strategies.

#### What needs to be done
1.  **Write Unit Tests for New/Refactored Components:**
    *   `AppSettings` and its sub-models.
    *   `OpenRouterClient` (mocking `httpx.AsyncClient`).
    *   `CostInformationService` (mocking `OpenRouterClient`, file system for cache).
    *   `CostCalculator` (mocking `CostInformationService`).
    *   `TokenCounter` (mocking `CostInformationService`, `tiktoken`).
    *   `UsageTracker` (mocking `CostCalculator`).
    *   `CostAPI` (mocking its constituent services).
    *   Refactored components from `LLMTester` (e.g., `TestDiscoverer`, `TestRunner`, `ResponseValidator`, `AccuracyCalculator`), mocking their dependencies.
    *   Refactored components from `provider_factory.py`.
2.  **Improve Mocking Strategy:**
    *   Use `pytest-mock` (provides `mocker` fixture) or `unittest.mock` consistently.
    *   Mock at the correct boundaries (e.g., mock the dependency as it's imported into the module under test).
    *   Ensure mocks are specific and verify call arguments and return values.
3.  **Utilize `src/llms/mock/provider.py`:**
    *   This mock provider is excellent for testing components that interact with `BaseLLM` instances without actual API calls. Ensure it's used effectively in unit and integration tests for `TestRunner`, `LLMTester` facade, etc.
4.  **Fixtures for Common Setup:**
    *   Use `pytest` fixtures (`conftest.py`) extensively for common test setup (e.g., creating instances of Pydantic models, mock objects, temporary directories/files).

#### Test high level plan
-   N/A (This round is about writing tests).

#### Success criteria
-   High unit test coverage for critical components.
-   Effective use of mocking to isolate units under test.
-   Tests are clear, concise, and verify specific behaviors.

#### What are the developer benefits?
-   **Early Bug Detection:** Catch issues in individual components before they integrate.
-   **Confidence in Refactoring:** Good unit tests provide a safety net when changing code.
-   **Documentation:** Tests serve as a form of documentation for how components are intended to be used.

#### List the involved files
-   New test files in `tests/unit/` corresponding to application modules.
-   `conftest.py` for new fixtures.

#### Commit Message
`test(unit): Increase unit test coverage for core components and improve mocking`

---

### Round 3: Develop Integration Tests

#### Objective
Write integration tests to verify the interactions between key components of the application.

#### What needs to be done
1.  **`CostAPI` Integration:**
    *   Test the `CostAPI.get_instance()` and its interaction with `OpenRouterClient`, `CostInformationService`, `CostCalculator`, etc. Mock the `httpx.AsyncClient` within `OpenRouterClient` to simulate API responses, but let the services interact.
2.  **Provider Integration:**
    *   For each actual provider (OpenAI, Anthropic, etc.), write integration tests that:
        *   Instantiate the provider.
        *   Mock its underlying HTTP client (e.g., the `openai` library's client or `httpx` client used by the provider).
        *   Call `get_response` and verify it correctly processes mock API success/error responses and calculates `UsageData`.
3.  **`LLMTester` Facade Integration:**
    *   Test the refactored `LLMTester` facade.
    *   Use mock providers (like `src/llms/mock/provider.py`) and mock versions of `TestDiscoverer`, `ResponseValidator`, `AccuracyCalculator` initially, then gradually replace mocks with real (but internally mocked) components to test their integration.
    *   Example: Test `LLMTester.run_tests()` with a `TestDiscoverer` that returns a mock test case, a `TestRunner` that uses a mock provider, and verify the overall flow and report generation (mocking `ReportGenerator` if needed).
4.  **CLI Core Logic Integration:**
    *   Test integration of core CLI logic modules (formerly in `src/cli/core/`) if they interact with each other or with the application facade in complex ways not covered by E2E tests.

#### Test high level plan
-   N/A (This round is about writing tests).

#### Success criteria
-   Key component interactions are verified.
-   Integration tests catch issues related to incorrect component wiring or interface mismatches.
-   Confidence that major workflows function correctly at an integration level.

#### What are the developer benefits?
-   **Verify Component Collaboration:** Ensures that different parts of the system work together as expected.
-   **Catch Interface Bugs:** Detects issues caused by changes in one component affecting another.

#### List the involved files
-   New test files in `tests/integration/`.
-   `conftest.py` for integration test fixtures.

---

### Round 4: Enhance End-to-End (E2E) CLI Tests

#### Objective
Improve and expand E2E tests for the CLI to cover key user workflows, ensuring the application works correctly from the command line.

#### What needs to be done
1.  **Use a CLI Testing Tool (if not already):**
    *   Consider tools like `pytest-subprocess` or Python's `subprocess` module directly, or specialized CLI testing libraries if more features are needed (e.g., `click.testing.CliRunner` if Typer is based on Click, or Typer's own testing utilities). Typer has `typer.testing.CliRunner`.
2.  **Cover Key CLI Commands:**
    *   `llm-tester run`: Test with various options (providers, models, output files), using mock providers to avoid actual API calls and costs. Verify report generation.
    *   `llm-tester scaffold provider/model`: Test that scaffolding creates the correct directory structure and files.
    *   `llm-tester list`: Verify it lists providers and models correctly.
    *   `llm-tester configure ...` and `llm-tester providers ...`: Test these commands based on their refactored behavior (e.g., verifying guidance for .env, or changes to a mock user config file).
    *   `llm-tester interactive`: This is harder to test E2E. Focus on testing the underlying menu modules/classes with mocked input (unit/integration). Basic E2E could check if interactive mode starts.
3.  **Test Setup and Teardown:**
    *   Use fixtures to set up necessary conditions (e.g., mock configuration files, temporary directories for py_models or output).
    *   Ensure proper cleanup after tests.
4.  **Assert on Output and Side Effects:**
    *   Verify CLI output (stdout, stderr).
    *   Verify file creation/modification where applicable (e.g., reports, scaffolded files).
    *   Verify exit codes.

#### Test high level plan
-   N/A (This round is about writing tests).

#### Success criteria
-   Key CLI workflows are covered by E2E tests.
-   E2E tests catch regressions in CLI behavior.
-   Confidence that the CLI is usable and functions as documented.

#### What are the developer benefits?
-   **Highest Level of Confidence:** Verifies the entire application stack from the user's entry point.
-   **Catch Regressions:** Prevents accidental breaking of CLI functionality.

#### List the involved files
-   New/updated test files in `tests/e2e/`.
-   `conftest.py` for E2E test fixtures.

---

### Round 5: CI Integration and Test Reporting

#### Objective
Ensure all tests are run automatically in CI, and test reports (including coverage) are generated.

#### What needs to be done
1.  **CI Configuration (`.github/workflows/python-tests.yml`):**
    *   Ensure `pytest` is run with options to collect coverage (`pytest --cov=src/llm_tester`).
    *   Configure CI to upload coverage reports (e.g., to Codecov, Coveralls, or as a GitHub artifact).
    *   Consider running different test types in parallel or in stages if execution time becomes an issue.
2.  **Test Coverage Thresholds (Optional):**
    *   Set minimum test coverage thresholds that the CI build must meet.
3.  **Local Test Execution Scripts:**
    *   Provide convenient scripts or Makefile targets for developers to run all tests, or specific types of tests, locally (e.g., `make test-unit`, `make test-integration`, `make test-all`).

#### Test high level plan
-   N/A.

#### Success criteria
-   Tests run automatically on every push/PR.
-   Coverage reports are generated and accessible.
-   Developers can easily run tests locally.

#### What are the developer benefits?
-   **Automated Quality Assurance:** Continuous feedback on code quality.
-   **Visibility:** Easy to track test coverage and identify untested areas.
-   **Collaboration:** Ensures all contributions are tested.

#### List the involved files
-   `.github/workflows/python-tests.yml`
-   `Makefile` or similar for local test scripts.
-   `pyproject.toml` or `setup.cfg` for pytest configuration.

This enhanced testing strategy will significantly contribute to the robustness and quality of the `pydantic-llm-tester` project.
