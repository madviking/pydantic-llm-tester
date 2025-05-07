# CLI Refactoring Plan

## Overview
This document outlines the plan to refactor the Command Line Interface (CLI) of the `pydantic-llm-tester` project. The current CLI logic is primarily in `src/cli/main.py` (using Typer) and `src/cli/interactive_ui.py` for the interactive mode. The goal is to improve the structure, maintainability, and testability of the CLI components, ensuring a consistent user experience.

## Principles
-   **Clear Separation of Concerns:** Command logic, UI presentation, and core application interactions should be distinct.
-   **Modularity:** Break down large CLI files into smaller, manageable modules.
-   **Testability:** CLI commands and their underlying logic should be easily testable.
-   **Consistency:** Uniform command structure, argument parsing, and output formatting.
-   **User Experience:** Intuitive commands and helpful feedback.
-   **Alignment with `src/llm_tester/` package structure.**

## Current CLI Structure
-   **`src/cli/main.py`:** Main entry point using Typer, defines top-level commands and subcommands.
-   **`src/cli/commands/`:** Directory for individual command modules (e.g., `run.py`, `scaffold.py`).
-   **`src/cli/core/`:** Contains core logic supporting CLI operations (e.g., `test_runner_logic.py`, `config_logic.py`).
-   **`src/cli/interactive_ui.py`:** Contains the logic for the `llm-tester interactive` mode. This file is quite large.

## Proposed Refinements

---

### Round 1: Refactor `interactive_ui.py`

#### Problem we are solving
`src/cli/interactive_ui.py` is a large file containing numerous functions for different menu sections and interactions. This makes it hard to navigate, maintain, and test.

#### What needs to be done
1.  **Decompose by Menu/Functionality:** Break down `interactive_ui.py` into smaller modules based on the main menu options or distinct functionalities.
    *   Example:
        *   `src/llm_tester/cli/interactive/provider_menu.py` (for `_manage_providers_menu`, `_display_provider_status`, etc.)
        *   `src/llm_tester/cli/interactive/model_menu.py` (for `_manage_llm_models_menu`, `_display_model_status`, etc.)
        *   `src/llm_tester/cli/interactive/config_menu.py` (for `_configure_keys_interactive`)
        *   `src/llm_tester/cli/interactive/execution_menu.py` (for `_run_tests_interactive`)
        *   `src/llm_tester/cli/interactive/scaffold_menu.py` (for `_scaffold_provider_interactive`, `_scaffold_model_interactive`)
        *   `src/llm_tester/cli/interactive/main_menu.py` (for `start_interactive_session` and the main loop, importing functions from other menu modules).
2.  **Use Classes for Menus (Optional but Recommended):** Consider using classes to represent different menu sections. Each class could encapsulate its state and actions.
    ```python
    # Example: src/llm_tester/cli/interactive/provider_menu.py
    class ProviderMenu:
        def __init__(self, app_facade): # Pass a facade for core app logic
            self.app_facade = app_facade

        def display_status(self): ...
        def manage_providers(self): ...
        # etc.
    ```
3.  **Centralize UI Elements:** If common UI patterns emerge (e.g., specific ways of prompting, displaying tables with `rich`), consider creating utility functions or classes in `src/llm_tester/cli/ui_utils.py`.
4.  **Isolate Core Logic:** Ensure that functions in these interactive modules primarily handle UI presentation and user input. They should call functions/methods from `src/llm_tester/cli/core/` or a new application facade/service layer for the actual business logic.

#### Test high level plan
-   Test each interactive menu module/class in isolation by mocking user input and verifying calls to core logic functions.
-   Test navigation between different menus.
-   Verify that the overall interactive session behaves as before the refactoring.

#### Success criteria
-   `src/cli/interactive_ui.py` is significantly smaller or replaced by a main menu orchestrator.
-   New modules/classes for different interactive sections are created under `src/llm_tester/cli/interactive/`.
-   Code is more organized and easier to understand.
-   Individual interactive components are more testable.

#### What are the developer benefits?
-   **Improved Maintainability:** Smaller, focused modules are easier to manage.
-   **Enhanced Readability:** Easier to find and understand specific parts of the interactive UI logic.
-   **Better Testability:** UI components can be tested more effectively in isolation.

#### List the involved files
-   `src/cli/interactive_ui.py` (to be refactored/removed)
-   New files under `src/llm_tester/cli/interactive/` (e.g., `main_menu.py`, `provider_menu.py`, etc.)
-   Potentially a new `src/llm_tester/cli/ui_utils.py`
-   Test files for the new interactive modules.

---

### Round 2: Standardize CLI Command Structure and Core Logic Interaction

#### Problem we are solving
Ensure consistency in how CLI commands in `src/cli/commands/` are structured and how they interact with the core application logic (currently in `src/cli/core/` and the main `LLMTester` class, but planned to be refactored into services/facades).

#### What needs to be done
1.  **Application Facade/Service Layer:**
    *   As part of the broader architectural improvements (e.g., `LLMTester` decomposition, `CostAPI`), a clear service layer or application facade should emerge.
    *   CLI command handlers in `src/cli/commands/` should primarily interact with this facade/service layer, not directly with low-level components or by re-implementing logic.
2.  **Refactor `src/cli/core/`:**
    *   Review the modules in `src/cli/core/` (e.g., `test_runner_logic.py`, `config_logic.py`, `provider_logic.py`, `scaffold_logic.py`).
    *   Much of this logic might move into the new service layer/application facade or be refactored to use it.
    *   The remaining parts of `src/cli/core/` should be utilities specifically for CLI argument parsing, validation, or complex CLI-specific orchestration that doesn't fit into the general application facade.
3.  **Consistent Command Implementation:**
    *   Each command module in `src/cli/commands/` should:
        *   Define its Typer command(s).
        *   Parse and validate arguments.
        *   Call the appropriate methods on the application facade/service layer.
        *   Format and present results to the user (e.g., using `rich` for tables, consistent status messages).
4.  **Error Handling:**
    *   Implement consistent error handling. CLI commands should catch exceptions from the service layer and present user-friendly error messages.
    *   Define custom CLI-specific exceptions if needed (e.g., `CLIArgumentError`).
5.  **Output Formatting:**
    *   Standardize output formatting. Use `rich` library for tables, styled text, progress bars, etc., to provide a polished user experience. Centralize common output formatting utilities if possible.

#### Test high level plan
-   Test individual CLI commands by mocking the application facade/service layer to verify correct argument parsing and calls to the facade.
-   Test CLI command output formatting for various scenarios (success, errors, empty results).
-   End-to-end tests for key CLI workflows.

#### Success criteria
-   CLI command handlers are lean and delegate most work to a well-defined service layer.
-   Logic in `src/cli/core/` is streamlined and focused on CLI-specific tasks.
-   Consistent error handling and output formatting across all commands.
-   CLI commands are easily testable.

#### What are the developer benefits?
-   **Clear Separation:** Decouples CLI presentation from core application logic.
-   **Maintainability:** Easier to modify CLI commands or core logic independently.
-   **Testability:** Both CLI and core logic can be tested more effectively.
-   **Consistency:** Improves user experience and makes the CLI easier to learn.

#### List the involved files
-   All files in `src/cli/commands/`.
-   All files in `src/cli/core/`.
-   `src/cli/main.py`.
-   The new application facade/service layer modules.
-   Test files for CLI commands and core CLI logic.

---

### Round 3: Enhance Configuration-Related CLI Commands

#### Problem we are solving
CLI commands for managing configuration (`llm-tester configure keys`, `llm-tester providers ...`) need to be adapted to the new Unified Configuration System (`3_configuration_unification.md`). The current approach of directly modifying JSON files might not be ideal with the new system based on `pydantic-settings` (which prioritizes env vars and `.env` files).

#### What needs to be done
1.  **Re-evaluate `llm-tester configure keys`:**
    *   **Current:** Prompts for keys and saves to `src/.env`.
    *   **Proposal:**
        *   This command can still be useful. It should guide the user to set environment variables or update their project's `.env` file (or a global user-level `.env` if supported).
        *   It should read the `AppSettings` model to understand which keys are expected (e.g., `cost.openrouter_api_key`, `providers.<name>.api_key`).
        *   Avoid directly writing to `src/.env` if the package is installed globally; focus on project-local `.env` or guiding environment variable setup.
2.  **Re-evaluate `llm-tester providers list/enable/disable/manage`:**
    *   **Current:** Modifies `enabled_providers.json` or provider-specific config files.
    *   **Proposal:**
        *   These commands would now interact with settings defined in `AppSettings` (e.g., `providers.<name>.enabled`, `providers.<name>.llm_models.<model_id>.enabled`).
        *   **Challenge:** `pydantic-settings` primarily loads from env vars/.env files, which are not easily modified programmatically in a way that persists across sessions for all shells.
        *   **Option 1 (Simpler):** These commands could display current effective settings (loaded by `AppSettings`) and guide the user on which environment variables or `.env` entries to set/modify.
        *   **Option 2 (More Complex):** Introduce a user-level configuration file (e.g., `~/.config/llm_tester/user_config.yaml`) that `AppSettings` loads as an override layer. These CLI commands could then programmatically modify this user-level file. This adds complexity to the config loading but provides a better UX for these commands.
        *   **Option 3 (Hybrid):** For simple enable/disable, guide `.env`/env var changes. For more complex management (like adding a new model to a provider's list in the config), it might require manual config file editing, and the CLI could validate the config.
        *   The `providers manage update openrouter` command (to fetch model info) should trigger the `CostInformationService.refresh_models(force=True)`.
3.  **New Command: `llm-tester config show`:**
    *   A new command to display the current effective configuration (potentially redacting sensitive values like API keys). This helps users understand what settings are active.

#### Test high level plan
-   Test `configure keys` correctly identifies missing keys (based on `AppSettings`) and provides correct guidance for setting them.
-   Test `providers list` accurately reflects provider status from `AppSettings`.
-   Test `providers enable/disable/manage` (depending on chosen implementation option):
    *   If guiding: Verify correct instructions are shown.
    *   If modifying user-config: Verify file is updated and `AppSettings` reflects changes on next load.
-   Test `config show` displays the configuration correctly.

#### Success criteria
-   Configuration-related CLI commands are aligned with the `pydantic-settings` based configuration system.
-   Users have a clear way to view and understand how to modify their configuration.
-   Commands are robust and provide helpful feedback.

#### What are the developer benefits?
-   **Consistency:** CLI configuration management aligns with the new config system.
-   **Clarity for Users:** Makes it easier for users to manage their settings.

#### List the involved files
-   `src/cli/commands/configure.py` (or equivalent)
-   `src/cli/commands/providers.py` (or equivalent)
-   `src/llm_tester/config/settings_models.py` (as the source of truth for what to configure)
-   Potentially a new module for managing user-level configuration files if that option is chosen.
-   Test files for these CLI commands.

This refactoring will lead to a more organized, maintainable, and user-friendly CLI.
