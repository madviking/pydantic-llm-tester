# Developer Experience Improvement Plan

This document outlines the plan to enhance the developer experience for the `llm_tester` Python package, making it easier to install, use, and extend. The goal is to provide clear guidance on using the CLI, integrating custom providers, utilizing the Python API, and managing custom models.

## 1. Launching the CLI

The CLI is already configured to be launched using the command `llm-tester` after the package is installed. This is achieved through a `console_scripts` entry point defined in `setup.py`.

**Action:**
- No action required, this is already implemented.

**Benefit:**
- Users can simply type `llm-tester` in their terminal after installation to launch the CLI.

## 2. Adding Providers

The documentation for adding new LLM providers has been updated in `docs/guides/providers/ADDING_PROVIDERS.md` to include guidance on adding external providers when using the package as an installed library.

**Action:**
- Documentation for adding external providers has been added.
- **Implemented the `llm-tester scaffold provider` command-line utility to help scaffold new provider implementations.**

**Benefit:**
- Simplifies the process for developers to extend the package with support for new LLMs, both internally and externally.

## 3. Using the API

Documentation for using the `llm_tester` Python API programmatically has been created in `docs/guides/USING_THE_API.md`.

**Action:**
- Documentation for the Python API has been created.

**Benefit:**
- Allows developers to integrate `llm_tester`'s capabilities into their existing workflows and applications.

## 4. Model Placement and Management

The documentation for adding new models has been updated in `docs/guides/models/ADDING_MODELS.md` to include guidance on adding external models when using the package as an installed library. This clarifies the recommended directory structure and how to use the `test_dir` parameter/option.

**Action:**
- Documentation for adding external models has been added.
- **Implemented the `llm-tester scaffold model` command-line utility to help initialize a new model directory with the recommended structure.**

**Benefit:**
- Provides a standardized and clear approach for developers to manage their custom LLM tasks and data outside the installed package.

## 5. General Developer Experience Improvements

Beyond the core functionalities, consider other aspects that contribute to a positive developer experience.

**Action:**
- Improve error handling and provide more informative error messages.
- Enhance logging to provide better insights into the package's execution.
- Ensure clear and consistent naming conventions throughout the codebase and documentation.
- Expand unit and integration tests to cover more use cases and ensure stability.
- Set up continuous integration (CI) to automate testing and ensure code quality. (Already have a publish workflow, but need more focus on testing).

**Benefit:**
- Makes the package more robust, easier to debug, and more reliable for developers.

This plan will serve as a roadmap for improving the developer experience of `llm_tester`. Each point will be addressed in subsequent development efforts.
