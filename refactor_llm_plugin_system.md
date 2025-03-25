# LLM Tester Refactoring Plan: Pluggable LLM System

## Overview

This refactoring plan aims to leverage the pluggable LLM system in the `llms` directory to reduce code duplication and centralize provider-specific code that's currently spread across the codebase. The existing infrastructure in `llms/` already provides a solid foundation with:

- A base class (`BaseLLM`) defining the provider interface
- Provider implementations (e.g., `AnthropicProvider`)
- Provider factory and registry (`provider_factory.py`, `llm_registry.py`)

However, the rest of the codebase doesn't fully utilize this system, continuing to handle provider-specific code in multiple places.

## Goals

1. Eliminate provider-specific code from `provider_manager.py` and other parts of the codebase
2. Centralize all provider implementations in the `llms/` directory
3. Ensure all provider interactions go through the pluggable system
4. Reduce code duplication and improve maintainability
5. Make adding new providers easier by requiring only additions to the `llms/` directory

## Changes Required

### 1. Update Provider Registry and Factory

- Enhance `llm_registry.py` to load all available providers
- Update factory with better error handling and logging
- Ensure model configs are properly loaded for all providers

### 2. Provider Manager Refactoring

- Refactor `ProviderManager` to use the LLM registry instead of direct provider implementations
- Replace direct API calls with calls to pluggable LLM providers
- Remove provider-specific code in `_get_openai_response()`, `_get_anthropic_response()`, etc.

### 3. Mock Provider Implementation

- Create a proper `MockProvider` class in `llms/mock/provider.py`
- Move mock response generation from `utils/mock_responses.py` to the provider class
- Register the mock provider in the LLM system

### 4. LLMTester Class Updates

- Update the `LLMTester` class to work fully with the pluggable system
- Route all LLM interactions through the provider registry
- Remove any remaining provider-specific code

### 5. CLI Updates

- Update CLI to use the provider registry for listing available providers
- Ensure model selection works with the provider registry
- Remove hardcoded provider references

### 6. Testing Updates

- Update tests to use the pluggable system
- Create mocks for the BaseLLM interface rather than specific providers
- Ensure all tests pass with the refactored code

## Implementation Steps

### Step 1: Complete Provider Implementations

1. Ensure each provider in `llms/` has a complete implementation
2. Implement any missing provider methods
3. Standardize error handling and logging
4. Add proper configuration loading

### Step 2: Create Mock Provider

1. Create `llms/mock/provider.py` with a `MockProvider` class
2. Implement the BaseLLM interface for the mock provider
3. Move mock response generation logic from utils
4. Register the mock provider in the system

### Step 3: Refactor Provider Manager

1. Update `ProviderManager.__init__` to use the LLM registry
2. Replace direct client creation with provider instances from registry
3. Redirect `get_response()` method to use provider instances
4. Remove provider-specific methods (_get_openai_response, etc.)

### Step 4: Update LLMTester

1. Update LLMTester to use the provider manager's simplified interface
2. Remove any remaining provider-specific code
3. Ensure all test runs use the pluggable system

### Step 5: Update CLI and Runner

1. Use provider registry for listing available providers
2. Update model selection to use provider configurations
3. Remove hardcoded provider references

### Step 6: Testing and Validation

1. Update all tests to work with the refactored code
2. Add tests for the pluggable system
3. Ensure all existing tests pass
4. Manually test key workflows

## Impact Analysis

### Before Refactoring

- Provider-specific code spread across multiple files
- Duplicate API client creation in different parts of the codebase
- Direct dependency on provider SDKs throughout the code
- Hard to add new providers (changes needed in multiple places)

### After Refactoring

- All provider-specific code isolated to `llms/{provider}/provider.py` files
- Single place to update when provider APIs change
- Easily add new providers by adding a new directory under `llms/`
- Cleaner, more maintainable codebase with less duplication

## Identified Files to Modify

1. `llm_tester/utils/provider_manager.py` - Major refactoring
2. `llm_tester/llm_tester.py` - Updates to use the registry
3. `llm_tester/cli.py` - Remove hardcoded provider references
4. `llm_tester/runner/menu_handlers.py` - Update to use registry
5. `llm_tester/utils/mock_responses.py` - Move functionality to mock provider
6. Create `llm_tester/llms/mock/provider.py`
7. Various test files that need updating

## Fallback Plan

If issues arise during refactoring, we can:
1. Roll back to the previous version
2. Implement changes incrementally, testing each step
3. Create a hybrid approach that maintains both systems temporarily

## Timeline Estimate

- Step 1-2: 1-2 days
- Step 3-4: 2-3 days
- Step 5-6: 1-2 days
- Testing and bug fixes: 2-3 days

Total: Approximately 6-10 days for complete refactoring