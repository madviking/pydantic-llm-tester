# LLM Tester Project Structure

This document describes the structure of the LLM Tester project, explaining the purpose of each directory and key file.

## Directory Structure

```
llm_tester/
│
├── __init__.py               # Package initialization
├── cli.py                    # Command-line interface
├── llm_tester.py             # Main LLM Tester class
│
├── llms/                     # LLM Provider implementations
│   ├── __init__.py           # Package initialization
│   ├── base.py               # Base LLM provider class
│   ├── llm_registry.py       # Registry for LLM providers
│   ├── provider_factory.py   # Factory for creating provider instances
│   │
│   ├── anthropic/            # Anthropic provider implementation
│   │   ├── __init__.py
│   │   ├── config.json       # Provider configuration
│   │   └── provider.py       # Provider implementation
│   │
│   ├── google/               # Google provider implementation
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── provider.py
│   │
│   ├── mistral/              # Mistral provider implementation
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── provider.py
│   │
│   ├── mock/                 # Mock provider for testing
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── provider.py
│   │
│   ├── openai/               # OpenAI provider implementation
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── provider.py
│   │
│   └── pydantic_ai/          # PydanticAI provider implementation
│       ├── __init__.py
│       ├── config.json
│       └── provider.py
│
├── models/                   # Data models for extraction tasks
│   ├── __init__.py
│   │
│   ├── job_ads/              # Job advertisement extraction
│   │   ├── __init__.py
│   │   ├── model.py          # Pydantic model
│   │   │
│   │   └── tests/            # Test cases
│   │       ├── __init__.py
│   │       ├── expected/     # Expected JSON outputs
│   │       ├── prompts/      # Prompt templates 
│   │       │   └── optimized/ # Optimized prompts
│   │       └── sources/      # Source text files
│   │
│   └── product_descriptions/ # Product description extraction
│       ├── __init__.py
│       ├── model.py
│       │
│       └── tests/
│           ├── __init__.py
│           ├── expected/
│           ├── prompts/
│           │   └── optimized/
│           └── sources/
│
├── runner/                   # Interactive runner
│   ├── __init__.py
│   ├── config.py             # Configuration utilities
│   ├── main.py               # Main entry point
│   ├── menu_handlers.py      # Menu option handlers
│   ├── non_interactive.py    # Non-interactive mode
│   └── ui.py                 # UI utilities
│
├── tests/                    # Unit and integration tests
│   ├── __init__.py
│   └── cases/                # Test cases
│
└── utils/                    # Utility modules
    ├── __init__.py
    ├── config_manager.py     # Configuration management
    ├── cost_manager.py       # Token usage and cost tracking
    ├── mock_responses.py     # Mock response generation
    ├── module_discovery.py   # Model module discovery
    ├── prompt_optimizer.py   # Prompt optimization
    ├── provider_manager.py   # Provider connection management
    ├── reload_providers.py   # Provider reloading utility
    └── report_generator.py   # Report generation
```

## Root Directory

- `runner.py` - Main entry script for running the tool
- `verify_providers.py` - Script to verify provider setup
- `config.json` - Global configuration file
- `models_pricing.json` - Model pricing information
- `install.sh` - Installation script

## Key Components

### Provider System

The provider system is located in the `llms/` directory and consists of:

- **Base Provider Class** (`base.py`): Defines the interface for all providers
- **Provider Registry** (`llm_registry.py`): Manages provider instances
- **Provider Factory** (`provider_factory.py`): Creates provider instances
- **Provider Implementations**: Each subdirectory contains a provider implementation

### Model System

The model system is located in the `models/` directory and consists of:

- **Model Classes**: Each subdirectory contains a Pydantic model for a specific extraction task
- **Test Cases**: Each model includes test cases with sources, prompts, and expected outputs

### Runner System

The runner system is located in the `runner/` directory and provides:

- **Interactive Mode**: Menu-driven interface for configuring and running tests
- **Non-Interactive Mode**: Command-line interface for automated testing
- **Configuration Management**: Utilities for managing configuration

### Utility Modules

Utility modules in the `utils/` directory provide supporting functionality:

- **Cost Management**: Tracking token usage and costs
- **Prompt Optimization**: Optimizing prompts based on results
- **Report Generation**: Creating test reports
- **Provider Management**: Managing connections to providers

## Flow of Execution

1. User runs `runner.py`
2. Runner loads configuration and initializes the LLM Tester
3. LLM Tester discovers test cases and providers
4. User configures providers and models
5. LLM Tester runs tests using the configured providers
6. Results are collected and analyzed
7. Reports are generated and displayed

## Adding New Components

- **New Providers**: Add a new directory in `llms/` with configuration and implementation
- **New Models**: Add a new directory in `models/` with a Pydantic model and test cases
- **New Utilities**: Add new utility modules in `utils/` as needed