# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2025-05-07

### Changed
- Changed the structure to confine with Python packaging standards
- Changed the packaging to work purely with pyproject.toml

## 2025-05-06

### Added
- Implemented interactive and non-interactive scaffolding for new LLM providers and extraction models via the `llm-tester scaffold` command.
- Added comprehensive documentation for the `llm-tester scaffold` command in `docs/guides/cli_commands/SCAFFOLDING.md`.
- Added a "Testing" section to `README.md`.
- Added a "bridge to LLM functionalities within your app" use case and a "hello world" example to `README.md`.
- Added PyPI installation instructions to `README.md`.

### Changed
- Updated README and other documentation files (`docs/README.md`, `docs/guides/providers/ADDING_PROVIDERS.md`, `docs/guides/models/ADDING_MODELS.md`, `docs/guides/DEVELOPER_EXPERIENCE_PLAN.md`) for conciseness and clarity, moving detailed information to the `docs/` directory.
- Changed "Supported Models" heading to "Example Models" in `README.md`.
- Prioritized CLI usage within a virtual environment in `README.md`.
- Emphasized starting with scaffolding in `README.md`.

### Removed
- Removed the `docs/future_planning/FUTURE_ENHANCEMENTS.md` file.
- Removed the broken link to the non-existent "Running Tests" guide from `docs/README.md`.

## 2025-03-31

### Added
- Added support for OpenRouter.
- Added integration tests.

### Changed
- Completely refactored the CLI mode and command line mode to make it easier to extend.
- Changed environment loading.

## 2025-03-27

### Changed
- Updated accuracy calculation.
- Improved tests for current accuracy calculation.
- Added tests for upcoming accuracy improvement.

## 2025-03-26

### Changed
- Rearranged documentation structure.
- Finished provider refactoring.

## 2025-03-25

### Added
- Enhanced provider factory with validation and external provider support.
- Added functionality for creating new model scaffolding.
- Added ability to select which modules to test.
- Added option to choose where to output test results.
- Added tests for LLM provider connections.
- Added cost manager and pricing report.

### Changed
- Refactored pluggable system to support both PydanticAI and direct implementation.
- Refactored runner.
- Refactored for better module structure.
- Implemented configuration management, basic test structure improvements, and cleaned up mock response handling.
- Improved handling for missing models.
- Removed model schema from optimized prompts.
- Saved optimized prompts to their own files.
- Moved mock responses out of `runner.py`.
- Setup providers to read from configuration file.
- Cleaned up to move to `runner.py`.
- Fixed environment setup to better detect and report missing API keys.

### Fixed
- Fixed cost manager.
- Fixed various bugs.
