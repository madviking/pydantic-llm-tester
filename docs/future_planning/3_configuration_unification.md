# Unified Configuration System Plan

## Overview
This document outlines the plan to establish a unified configuration system for the `pydantic-llm-tester` project. The current configuration is fragmented across `pyllm_config.json` (managed by `src/utils/config_manager.py`, now including provider enabled status which was previously in `enabled_providers.json`), `external_providers.json`, `models_pricing.json`, environment variables, and potentially provider-specific `config.json` files within `src/llms/`. This new system aims to centralize configuration management, making it more robust, easier to understand, and simpler to extend.

## Principles
-   **Single Source of Truth (Logical):** While configuration data might still reside in multiple physical locations (e.g., a primary config file, `.env` file, default values), the application should access it through a single, consistent interface.
-   **Layered Configuration:** Support for default values, values from a configuration file, and overrides from environment variables.
-   **Type Safety:** Utilize Pydantic for defining and validating configuration schemas.
-   **Ease of Use:** Simple for users to understand and modify their settings.
-   **Extensibility:** Easy to add new configuration sections as the application grows.
-   **Alignment with `src/llm_tester/` package structure.**

## Proposed Solution: Pydantic Settings

Leverage `pydantic-settings` (the successor to Pydantic's `BaseSettings`) to manage application configuration.

### Core Configuration Components:

1.  **Main Application Settings (`AppSettings`):**
    *   A Pydantic model that acts as the root for all application settings.
    *   Location: `src/llm_tester/config/settings.py`
    *   It will load settings from:
        *   Default values defined in the model.
        *   A primary YAML or TOML configuration file (e.g., `llm_tester_config.yaml` or `~/.config/llm_tester/config.yaml`).
        *   An `.env` file (for sensitive data like API keys).
        *   Environment variables (prefixed, e.g., `LLM_TESTER_`).

2.  **Modular Setting Sections:**
    *   `AppSettings` will be composed of nested Pydantic models for different configuration areas (e.g., `ProviderSettings`, `CostManagementSettings`, `CLISettings`, `LoggingSettings`).

3.  **Configuration Loading Logic:**
    *   A utility function `get_app_settings()` in `src/llm_tester/config/loader.py` (or directly in `settings.py`) will be responsible for loading and returning a singleton instance of `AppSettings`.

### Detailed Plan:

---

### Round 1: Define Core `AppSettings` and Loading Mechanism

#### Objective
Establish the foundational `AppSettings` model and the logic to load configurations from files and environment variables.

#### Tasks
1.  **Install `pydantic-settings`:** Add `pydantic-settings` to `requirements.txt` and `setup.py`.
2.  **Create `src/llm_tester/config/settings_models.py` (or similar name for Pydantic models):**
    *   Define initial Pydantic models for settings.
    ```python
    # src/llm_tester/config/settings_models.py
    from pydantic import BaseModel, Field, DirectoryPath, FilePath, HttpUrl
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from typing import Dict, List, Optional, Union
    from pathlib import Path

    class LoggingSettings(BaseModel):
        level: str = Field("INFO", description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR)")
        format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log message format")
        # Add other logging settings like file path if needed

    class CacheSettings(BaseModel):
        base_dir: DirectoryPath = Field(Path.home() / ".cache" / "llm_tester", description="Base directory for caching")
        model_info_ttl_seconds: int = Field(3600, description="TTL for cached OpenRouter model info")
        # Add other cache settings as needed

    class CostManagementSettings(BaseModel):
        openrouter_api_key: Optional[str] = Field(None, description="API key for OpenRouter. Can be set via LLM_TESTER_COST_OPENROUTER_API_KEY env var.")
        enable_tracking: bool = Field(True, description="Enable/disable cost tracking features.")
        # Potentially add default currency if more are supported later

    class ProviderModelSettings(BaseModel):
        """Settings for a specific LLM model within a provider."""
        enabled: bool = True
        # Add other model-specific overrides if needed, e.g., custom system prompt template path
        # system_prompt_path: Optional[FilePath] = None 

    class ProviderSettings(BaseModel):
        """Settings for a specific LLM provider."""
        enabled: bool = True
        api_key: Optional[str] = Field(None, description="API key for the provider, if applicable. Can be set via LLM_TESTER_PROVIDERS_{PROVIDER_NAME}_API_KEY.")
        # Example: LLM_TESTER_PROVIDERS_OPENAI_API_KEY
        default_llm_model: Optional[str] = Field(None, description="Default LLM model to use for this provider if not specified.")
        llm_models: Dict[str, ProviderModelSettings] = Field(default_factory=dict, description="Configuration for specific LLM models under this provider.")
        # Add other provider-specific settings, e.g., base_url for self-hosted.
        # base_url: Optional[HttpUrl] = None

    class AppSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_prefix='LLM_TESTER_',
            env_file='.env',
            env_nested_delimiter='__', # For nested models like PROVIDERS__OPENAI__API_KEY
            # Add support for loading from a YAML/TOML file if pydantic-settings supports it directly
            # or implement custom loading logic. For now, focus on .env and env vars.
            extra='ignore' # Ignore extra fields from env/files
        )

        providers: Dict[str, ProviderSettings] = Field(default_factory=dict, description="Configuration for all LLM providers.")
        # Example: LLM_TESTER_PROVIDERS__OPENAI__ENABLED=true
        # LLM_TESTER_PROVIDERS__OPENAI__LLM_MODELS__GPT_4O__ENABLED=true

        py_models_base_dir: DirectoryPath = Field(Path("py_models"), description="Default base directory for custom Pydantic models (py_models).")
        # test_dir in LLMTester class can override this.

        logging: LoggingSettings = Field(default_factory=LoggingSettings)
        cache: CacheSettings = Field(default_factory=CacheSettings)
        cost: CostManagementSettings = Field(default_factory=CostManagementSettings)

        # Default configuration file path (user can override via env var if needed)
        # config_file_path: FilePath = Field(Path.home() / ".config" / "llm_tester" / "config.yaml")
        # For now, we'll rely on .env and direct env vars, simplifying initial setup.
        # A separate config file loader can be added later if complex structures are needed
        # that don't map well to env vars.

    # Singleton instance loader
    _app_settings_instance: Optional[AppSettings] = None

    def get_app_settings() -> AppSettings:
        global _app_settings_instance
        if _app_settings_instance is None:
            _app_settings_instance = AppSettings()
            # Ensure cache directories exist after loading settings
            _app_settings_instance.cache.base_dir.mkdir(parents=True, exist_ok=True)
            (Path(_app_settings_instance.cache.base_dir) / "model_info").mkdir(parents=True, exist_ok=True)
        return _app_settings_instance

    ```
3.  **Create `.env.example`:** Provide an example `.env` file.
    ```dotenv
    # .env.example
    # LLM Tester Configuration - Copy to .env and fill in your values

    # General Settings (Optional - examples)
    # LLM_TESTER_LOGGING__LEVEL=DEBUG

    # Cost Management
    LLM_TESTER_COST__OPENROUTER_API_KEY="your_openrouter_api_key_here"
    # LLM_TESTER_COST__ENABLE_TRACKING=true

    # Provider Specific API Keys (examples)
    LLM_TESTER_PROVIDERS__OPENAI__API_KEY="your_openai_api_key_here"
    # LLM_TESTER_PROVIDERS__ANTHROPIC__API_KEY="your_anthropic_api_key_here"
    # LLM_TESTER_PROVIDERS__GOOGLE__API_KEY="your_google_api_key_here"

    # Example of enabling/disabling a provider and a specific model
    # LLM_TESTER_PROVIDERS__OPENAI__ENABLED=true
    # LLM_TESTER_PROVIDERS__OPENAI__DEFAULT_LLM_MODEL="gpt-4o"
    # LLM_TESTER_PROVIDERS__OPENAI__LLM_MODELS__GPT_4O__ENABLED=true
    # LLM_TESTER_PROVIDERS__MISTRAL__ENABLED=false
    ```
4.  **Update `.gitignore`:** Add `.env` to `.gitignore`.

#### Tests
-   Test `get_app_settings()` loads defaults correctly.
-   Test overrides from environment variables (simple and nested).
-   Test loading from a mock `.env` file.
-   Test type validation (e.g., invalid log level, incorrect path type).

#### Commit Message
`feat(config): Implement core AppSettings with pydantic-settings`

---

### Round 2: Migrate Existing Configuration Logic

#### Objective
Refactor existing configuration consumers (e.g., `ConfigManager`, provider loading, cost management) to use the new `AppSettings`. Phase out old configuration files and mechanisms.

#### Tasks
1.  **Refactor `OpenRouterClient` and `CostInformationService`:**
    *   Update them to fetch `openrouter_api_key`, `cache_dir`, `cache_ttl_seconds` from `get_app_settings().cost` and `get_app_settings().cache`.
2.  **Refactor Provider Loading (`src/llms/provider_factory.py` and individual providers):**
    *   Provider classes (`BaseLLM` subclasses) should receive their specific configuration (API keys, enabled models, default model) from `get_app_settings().providers.get(provider_name)`.
    *   The logic for loading provider-specific `config.json` files (e.g., `src/llms/openai/config.json`) should be replaced. Model lists and their properties (like `input_cost_per_token`) should now come from OpenRouter data (via `CostInformationService`) or be defined within the `ProviderSettings.llm_models` in `AppSettings` if they are not on OpenRouter or need overrides.
    *   The concept of "enabled providers" (previously from `pyllm_config.json`) will now be determined by `ProviderSettings.enabled` in `AppSettings`. (Updated description)
3.  **Refactor `src/utils/config_manager.py::ConfigManager`:**
    *   This class and its associated `pyllm_config.json` are largely superseded.
    *   Identify any unique functionalities of `ConfigManager` not covered by `AppSettings` (e.g., dynamic registration of py_models if that's still needed beyond a simple directory scan).
    *   Plan for its deprecation or refactoring into smaller, focused utilities if parts are still essential. For instance, managing the list of `py_models` and their enabled status might become part of `AppSettings` or a dedicated `PyModelsConfig` section.
4.  **Handle `external_providers.json`:**
    *   The information from `external_providers.json` (module name, class name) should be configurable via `AppSettings`, perhaps under a dedicated `external_providers: Dict[str, ExternalProviderConfig]` section.
5.  **Handle `models_pricing.json`:**
    *   This file is superseded by the `CostInformationService` (which uses OpenRouter API and fallback data). Remove its usage.
6.  **Update CLI Commands:**
    *   Commands related to configuration (`llm-tester configure keys`, `llm-tester providers enable/disable/manage`) need to be re-evaluated.
        *   `configure keys`: Could now guide users to set environment variables or update their `.env` file.
        *   `providers enable/disable/manage`: Would modify environment variables or a user-level configuration file that `AppSettings` can load as an override layer (if direct modification of `.env` is not desired). This is an advanced feature; initially, users might manage this via direct `.env` edits or environment variables.
7.  **Logging Configuration:**
    *   Set up logging based on `get_app_settings().logging` at application startup.

#### Tests
-   Verify providers are loaded and configured correctly using `AppSettings`.
-   Verify API keys are correctly passed to providers.
-   Verify cost management services use settings from `AppSettings`.
-   Test CLI commands that interact with configuration (after their adaptation).

#### Commit Message
`refactor(config): Migrate existing components to use unified AppSettings`

---

### Round 3: Documentation and User Guidance

#### Objective
Update all documentation to reflect the new unified configuration system.

#### Tasks
1.  **Update `README.md`:** Explain the new configuration system, `.env` file usage, and key environment variables.
2.  **Update `docs/guides/configuration/CONFIG_REFERENCE.md`:** This document needs a complete overhaul to detail `AppSettings`, all its sections, how to configure via environment variables, and the `.env` file.
3.  **Update Provider and Model Addition Guides:** Reflect how new providers/models are configured within `AppSettings` if they require specific settings beyond auto-discovery.
4.  **Update CLI Documentation:** Adjust documentation for any changed CLI configuration commands.

#### Tests
-   N/A (Documentation review).

#### Commit Message
`docs(config): Update documentation for unified configuration system`

---

## Future Considerations / Potential Enhancements
-   **User-Specific Configuration File:** Allow `AppSettings` to load from a user-level configuration file (e.g., `~/.config/llm_tester/config.yaml`) that can override defaults but be overridden by environment variables or `.env` in the project directory. This provides more flexibility than just `.env`.
-   **Dynamic Configuration Reloading (if needed):** For long-running applications, though less critical for a CLI tool.
-   **Schema Export:** A CLI command to export the JSON schema of `AppSettings` for documentation or validation purposes.

## Deprecation Plan
-   `src/utils/config_manager.py` and `pyllm_config.json`: To be deprecated and removed once all functionalities are migrated to `AppSettings`.
-   `external_providers.json`: Data to be moved into `AppSettings`.
-   `models_pricing.json`: Superseded by `CostInformationService`.
-   Individual provider `config.json` files: Superseded by `AppSettings` and `CostInformationService`.

This unified system will significantly streamline how `llm-tester` is configured, making it more robust and user-friendly.
