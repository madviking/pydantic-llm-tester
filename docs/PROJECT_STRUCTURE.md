# LLM Tester Project Structure

This document describes the structure of the LLM Tester project, explaining the purpose of each directory and key file.

## Directory Structure

```
pydantic-llm-tester/ (Project Root)
│
├── .github/                  # GitHub Actions workflows
├── docs/                     # Project documentation
├── src/
│   └── pydantic_llm_tester/  # Main package
│       ├── __init__.py       # Package initialization
│       ├── llm_tester.py     # Main LLMTester class
│       │
│       ├── cli/              # Command-Line Interface (Typer)
│       │   ├── __init__.py
│       │   ├── main.py       # CLI entry point (llm-tester script)
│       │   ├── commands/     # CLI command modules (e.g., run, providers, configure)
│       │   │   └── ...
│       │   ├── core/         # Core logic for CLI commands
│       │   │   └── ...
│       │   └── templates/    # Templates for scaffolding
│       │       └── ...
│       │
│       ├── llms/             # LLM Provider implementations
│       │   ├── __init__.py
│       │   ├── base.py       # BaseLLM abstract base class
│       │   ├── llm_registry.py # Registry for LLM providers
│       │   ├── provider_factory.py # Factory for provider instances
│       │   │
│       │   ├── anthropic/    # Anthropic provider
│       │   │   ├── __init__.py
│       │   │   ├── config.json
│       │   │   └── provider.py
│       │   └── ...           # Other providers (google, mistral, mock, openai, openrouter, pydantic_ai)
│       │
│       ├── py_models/        # Pydantic models for extraction tasks & test cases
│       │   ├── __init__.py
│       │   │
│       │   ├── job_ads/      # Example: Job advertisement extraction
│       │   │   ├── __init__.py
│       │   │   ├── model.py  # Pydantic model, get_test_cases(), reporting methods
│       │   │   ├── tests/
│       │   │   │   ├── sources/
│       │   │   │   ├── prompts/
│       │   │   │   │   └── optimized/
│       │   │   │   └── expected/
│       │   │   └── reports/  # Module-specific reports
│       │   └── ...           # Other py_models (e.g., product_descriptions)
│       │
│       ├── utils/            # Utility modules
│       │   ├── __init__.py
│       │   ├── config_manager.py
│       │   ├── cost_manager.py
│       │   ├── provider_manager.py
│       │   ├── report_generator.py
│       │   └── ...           # Other utilities (common, module_discovery, prompt_optimizer)
│       │
│       └── .env.example      # Example environment file for API keys
│
├── tests/                    # Pytest unit and integration tests
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_*.py             # Individual test files
│   └── cli/                  # CLI-specific tests
│       └── ...
│
├── .gitignore
├── LICENSE
├── README.md                 # Main project README
├── pyproject.toml            # Build system, dependencies, project metadata
├── setup.py                  # Minimal setup script (defers to pyproject.toml)
├── requirements.txt          # List of dependencies
├── pyllm_config.json         # Optional: Global test settings, py_models paths
├── enabled_providers.json    # Optional: Explicitly enabled providers
└── external_providers.json   # Optional: Paths to external providers
```

## Root Directory Files (Key Files)

- `README.md`: High-level overview, installation, basic usage.
- `pyproject.toml`: Defines dependencies, build process, and the `llm-tester` script entry point. Core for understanding package structure and build.
- `src/`: Contains the main source code.
    - `src/pydantic_llm_tester/`: The actual Python package.
- `tests/`: Contains all automated tests.
- `docs/`: Contains all project documentation.
- `pyllm_config.json` (optional): Global configuration for test settings, output directories, default `py_models` paths.
- `enabled_providers.json` (optional): If present, lists active providers. Managed by `llm-tester providers enable/disable`.
- `external_providers.json` (optional): If present, lists paths to external provider directories.
- `.env` (typically in `src/pydantic_llm_tester/` or project root, not versioned): Stores API keys.

(Note: Some older files like `runner.py`, `verify_providers.py`, root `config.json`, `models_pricing.json`, `install.sh` mentioned in previous versions of this document might be deprecated or refactored into the current CLI and configuration system.)

## Key Components

### Provider System

Located in `src/pydantic_llm_tester/llms/`, it consists of:
- **Base Provider Class** (`base.py`): `BaseLLM` defines the interface for all providers.
- **Provider Registry** (`llm_registry.py`): Manages provider instances.
- **Provider Factory** (`provider_factory.py`): Creates provider instances.
- **Provider Implementations**: Each subdirectory (e.g., `openai/`, `anthropic/`) contains a specific provider's `provider.py` and `config.json`.

### Py_Model System (Extraction Schemas)

Located in `src/pydantic_llm_tester/py_models/`, it consists of:
- **Pydantic Model Classes** (`<model_name>/model.py`): Define the data structure for extraction, discover test cases (`get_test_cases()`), and handle module-specific reporting.
- **Test Cases**: Each `py_model` includes a `tests/` subdirectory with `sources/`, `prompts/`, and `expected/` data.

### CLI System (Command-Line Interface)

Located in `src/pydantic_llm_tester/cli/`, it provides:
- **Main Entry Point** (`main.py`): Defines the `llm-tester` command using Typer.
- **Command Modules** (`commands/`): Implement various subcommands (e.g., `run`, `providers`, `configure`, `scaffold`).
- **Interactive Mode**: Launched via `llm-tester interactive`.

### Utility Modules

Located in `src/pydantic_llm_tester/utils/`, these provide supporting functionality:

- **Configuration Management** (`config_manager.py`): Handles loading and accessing various configuration files.
- **Cost Management** (`cost_manager.py`): Tracks token usage and costs.
- **Prompt Optimization** (`prompt_optimizer.py`): Logic for optimizing prompts.
- **Report Generation** (`report_generator.py`): Creates test reports.
- **Provider Management** (`provider_manager.py`): High-level interaction with providers.
- **Path Management**: Centralized path resolution is handled within `utils/common.py` and `cli/commands/paths.py`.

## Flow of Execution (CLI Example: `llm-tester run`)

1. User executes `llm-tester run [options]`.
2. `src/pydantic_llm_tester/cli/main.py` processes global options and routes to the `run` command.
3. The `run` command logic (e.g., in `src/pydantic_llm_tester/cli/commands/run.py`) initializes an `LLMTester` instance from `src/pydantic_llm_tester/llm_tester.py`.
4. `LLMTester` loads configurations (API keys from `.env`, provider configs, `pyllm_config.json`).
5. `LLMTester.discover_test_cases()` scans `py_models/` directories (built-in and custom) to find `model.py` files and their associated test cases.
6. For each test case and each enabled provider/model:
    a. The `LLMTester` uses `ProviderManager` to get responses from the LLM.
    b. Responses are validated against the Pydantic schema defined in the `py_model`.
    c. Accuracy is calculated by comparing extracted data with expected data.
    d. Token usage and costs are tracked.
7. Results are collected.
8. Reports (Markdown, JSON) and cost summaries are generated and displayed or saved.

## Adding New Components

- **New Providers**: Use `llm-tester scaffold provider <name>` or manually create a new directory in `src/pydantic_llm_tester/llms/` with `provider.py` (inheriting `BaseLLM`) and `config.json`.
- **New Py_Models**: Use `llm-tester scaffold model <name>` or manually create a new directory in `src/pydantic_llm_tester/py_models/` (or a custom path) with `model.py` (Pydantic schema, `get_test_cases()`) and a `tests/` subdirectory.
- **New Utilities**: Add new modules to `src/pydantic_llm_tester/utils/`.
