# LLM Tester Documentation

Welcome to the LLM Tester documentation. This directory contains comprehensive documentation for using and extending the LLM Tester framework.

## Documentation Structure

The documentation is organized into the following sections:

### Project Structure

- [Project Structure](PROJECT_STRUCTURE.md) - Detailed overview of the project structure

### Guides

- **Providers**
  - [Adding Providers](guides/providers/ADDING_PROVIDERS.md) - Guide for adding new LLM providers

- **Models**
  - [Adding Models](guides/models/ADDING_MODELS.md) - Guide for adding new extraction models

- **Configuration**
  - [Configuration Reference](guides/configuration/CONFIG_REFERENCE.md) - Reference for configuration options

- **CLI Commands**
  - [Scaffolding](guides/cli_commands/SCAFFOLDING.md) - Guide for scaffolding new providers and models

### Architecture

- [Design Principles](architecture/DESIGN_PRINCIPLES.md) - Core design principles
- [Provider System](architecture/PROVIDER_SYSTEM.md) - Architecture of the provider system

### Examples

- [Basic Usage](examples/BASIC_USAGE.md) - Basic usage examples
- [Advanced Usage](examples/ADVANCED_USAGE.md) - Advanced usage examples

## Getting Started

If you're new to LLM Tester, we recommend starting with:

1. Read the [Project Structure](PROJECT_STRUCTURE.md) document to understand the framework
2. Follow the [Running Tests](guides/testing/RUNNING_TESTS.md) guide to run your first tests
3. Explore the [Basic Usage](examples/BASIC_USAGE.md) examples

## Contributing

If you'd like to contribute to LLM Tester:

1. Read the [Design Principles](architecture/DESIGN_PRINCIPLES.md) to understand the framework's philosophy
2. Follow the appropriate guide for the component you want to extend:
   - [Adding Providers](guides/providers/ADDING_PROVIDERS.md)
   - [Adding Models](guides/models/ADDING_MODELS.md)

## Troubleshooting

If you encounter issues:

1. Check the [Configuration Reference](guides/configuration/CONFIG_REFERENCE.md) to ensure proper setup
2. Run the verification script: `./verify_providers.py`
3. Look for error messages in the logs (use `--debug` for detailed logging)
