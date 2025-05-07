# OpenRouter Cost Management Implementation Plan

## Overview
This document outlines the implementation plan for migrating cost information management to leverage OpenRouter's API. The goal is to replace static JSON files (like `models_pricing.json`) with dynamic, up-to-date data from OpenRouter, which provides information about model costs, capabilities, and token limits. This will also involve creating a robust system for tracking usage and calculating costs.

## Principles
-   Dynamic cost and model information primarily sourced from OpenRouter API.
-   Effective caching mechanisms for performance and resilience.
-   Fallback mechanisms (e.g., to bundled static data) for offline or API failure scenarios.
-   Clear separation of concerns: client, services, calculator, API facade.
-   Comprehensive testing with mock API responses.
-   Integration with the unified project configuration system.
-   Paths and modules aligned with the `src/llm_tester/` package structure.

## Core Exceptions
Custom exceptions for this system will be defined in `src/llm_tester/core/exceptions.py`:
-   `APIConnectionError(Exception)`: For issues connecting to the OpenRouter API.
-   `CostInfoNotAvailable(Exception)`: When cost or model information cannot be retrieved.
-   `ConfigurationError(Exception)`: For issues related to missing or invalid configuration.

## Implementation Strategy

The implementation will be broken down into logical rounds, each focusing on a specific set of components.

---

### Round 1: Core Infrastructure - OpenRouter API Client & Schemas
**Objective:** Create a dedicated, asynchronous client for interacting with the OpenRouter API and Pydantic schemas for validating API responses.

#### Tasks
1. **Create OpenRouter API Client Class:**
    *   Location: `src/llm_tester/infrastructure/openrouter/client.py`
   ```python
   # src/llm_tester/infrastructure/openrouter/client.py
   import httpx
   from typing import Dict, Any, Optional, List
   import logging
   from pydantic_llm_tester.llm_tester import APIConnectionError # Adjusted import

   class OpenRouterClient:
       BASE_URL = "https://openrouter.ai/api/v1"

       def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
           if not api_key:
               # Integration with unified config system will be handled later
               # For now, this allows instantiation if key is passed directly
               # or raises error if not configured via settings.
               raise ValueError("OpenRouter API key is required.") # Or fetch from settings
           self.api_key = api_key
           self.timeout = timeout
           self._client = httpx.AsyncClient(
               base_url=self.BASE_URL,
               headers={
                   "Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json",
                   "HTTP-Referer": "https://github.com/TimoRailo/pydantic-llm-tester", # Recommended by OpenRouter
                   "X-Title": "Pydantic LLM Tester" # Recommended by OpenRouter
               },
               timeout=timeout
           )
           self.logger = logging.getLogger(__name__)

       async def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
           """Make a request to the OpenRouter API."""
           try:
               response = await self._client.request(
                   method=method,
                   url=endpoint, # Relative to base_url
                   params=params,
                   json=json_data
               )
               response.raise_for_status()
               return response.json()
           except httpx.HTTPStatusError as e:
               self.logger.error(f"HTTP status error {e.response.status_code} when calling OpenRouter API endpoint {endpoint}: {e.response.text}")
               raise APIConnectionError(f"OpenRouter API request failed with status {e.response.status_code}: {e.request.url}") from e
           except httpx.RequestError as e:
               self.logger.error(f"HTTP request error when calling OpenRouter API endpoint {endpoint}: {e}")
               raise APIConnectionError(f"Failed to connect to OpenRouter API: {e.request.url}") from e

       async def get_models(self) -> List[Dict[str, Any]]:
           """Get all available models from OpenRouter."""
           # Corresponds to: https://openrouter.ai/docs#get-models
           result = await self._make_request("models")
           return result.get("data", [])

       # get_model_details is implicitly covered by get_models, as it returns full details.
       # If a specific /models/{model_id} endpoint existed and was needed, it would be added.

       async def close(self):
           """Close the HTTP client session."""
           await self._client.aclose()
   ```

2.  **Create Pydantic Schemas for OpenRouter API Responses:**
    *   Location: `src/llm_tester/infrastructure/openrouter/schemas.py`
    ```python
    # src/llm_tester/infrastructure/openrouter/schemas.py
    from pydantic import BaseModel, Field, HttpUrl
    from typing import Dict, Any, List, Optional, Union

    class OpenRouterModelPricing(BaseModel):
        prompt: Union[str, float] # Price per 1M prompt tokens in USD (can be string like "0.000")
        completion: Union[str, float] # Price per 1M completion tokens in USD
        request: Optional[Union[str, float]] = None # Price per request in USD
        image: Optional[Union[str, float]] = None # Price per image in USD

    class OpenRouterModelLimits(BaseModel):
        max_prompt_tokens: Optional[int] = None
        max_completion_tokens: Optional[int] = None

    class OpenRouterModel(BaseModel):
        id: str = Field(..., description="Model identifier, e.g., 'openai/gpt-3.5-turbo'")
        name: str = Field(..., description="Human-readable model name, e.g., 'GPT-3.5 Turbo'")
        description: Optional[str] = None
        pricing: OpenRouterModelPricing
        context_length: Optional[int] = None # Max context length in tokens
        architecture: Optional[Dict[str, Any]] = None
        top_provider: Optional[Dict[str, Any]] = None
        per_request_limits: Optional[Dict[str, Any]] = None # Deprecated by OpenRouter, but might still appear
        # Add other relevant fields from OpenRouter /models response as needed
        # e.g. "modality", "tokenizer", etc.

    class OpenRouterModelsResponse(BaseModel):
        data: List[OpenRouterModel]
    ```

#### Tests
-   Test `OpenRouterClient._make_request` with mock HTTP responses (success, HTTP errors, network errors).
-   Test `OpenRouterClient.get_models` successfully parses a mock valid response.
-   Test `OpenRouterModel` Pydantic schema correctly parses valid and handles invalid model data.
-   Test client initialization (API key handling).

#### Commit Message
`feat(cost): Implement OpenRouter API client and response schemas`

---

### Round 2: Core Infrastructure - Unified Configuration Settings
**Objective:** Define and integrate settings for the OpenRouter client and cost management system into the project's unified configuration.

#### Tasks
1.  **Extend/Define Unified Configuration Model:**
    *   This will be part of the broader "Unified Configuration System" (see `3_configuration_unification.md`). For this specific feature, ensure the settings model includes:
        *   `openrouter_api_key: Optional[str]`
        *   `cost_cache_dir: Path` (defaulting to a user-local cache like `~/.cache/llm_tester/`)
        *   `cost_cache_ttl_seconds: int` (defaulting to e.g., 3600)
        *   `enable_cost_tracking: bool` (defaulting to True)
    *   Location: e.g., `src/llm_tester/config/settings.py` (or integrated into existing `ConfigManager`'s successor).
    ```python
    # Example snippet for src/llm_tester/config/settings.py (illustrative)
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pathlib import Path
    from typing import Optional

    class CostSettings(BaseSettings):
        openrouter_api_key: Optional[str] = None
        # cache_dir will be determined by a global AppSettings or similar
        # For now, CostInformationService will define its default.
        cache_ttl_seconds: int = 3600  # 1 hour
        enable_tracking: bool = True

        # This would be part of a larger AppSettings class
        # model_config = SettingsConfigDict(env_prefix='LLM_TESTER_COST_', env_file='.env', extra='ignore')

    # def get_cost_settings() -> CostSettings:
    #     return CostSettings()
    ```
    *Note: The final structure will depend on the design of the unified configuration system.*

2.  **Integrate Settings into `OpenRouterClient`:**
    *   Modify `OpenRouterClient.__init__` to fetch `api_key` from the unified settings if not provided directly.

#### Tests
-   Test that `OpenRouterClient` can be initialized using API key from settings.
-   Test that settings provide correct default values for cache TTL and directory.

#### Commit Message
`feat(config): Add OpenRouter and cost management settings to unified configuration`

---

### Round 3: Service Layer - Cost Information Service
**Objective:** Create a service to fetch, cache, and provide model information (costs, context lengths, etc.) from OpenRouter, with a fallback mechanism.

#### Tasks
1. **Create `CostInformationService`:**
    *   Location: `src/llm_tester/services/cost_service.py`
   ```python
   # src/llm_tester/services/cost_service.py
   import json
   import os
   import time
   import logging
   from pathlib import Path
   from typing import Dict, Any, Optional, List, Tuple

   from pydantic_llm_tester.llm_tester import OpenRouterClient
   from pydantic_llm_tester.llm_tester import OpenRouterModel
   # Assuming settings are accessible, e.g., via a global get_settings() or dependency injection
   # from llm_tester.config.settings import get_app_settings (hypothetical)
   from pydantic_llm_tester.llm_tester import CostInfoNotAvailable, ConfigurationError

   class CostInformationService:
       # DEFAULT_CACHE_DIR will be based on app settings
       DEFAULT_CACHE_DIR = Path.home() / ".cache" / "llm_tester" / "model_info"
       DEFAULT_CACHE_TTL_SECONDS = 3600  # 1 hour

       def __init__(
           self,
           openrouter_client: OpenRouterClient,
           cache_dir: Optional[Path] = None,
           cache_ttl_seconds: Optional[int] = None,
           fallback_data_path: Optional[Path] = None
       ):
           self.client = openrouter_client
           # settings = get_app_settings() # hypothetical
           # self.cache_dir = cache_dir or settings.cache_dir / "model_info"
           # self.cache_ttl_seconds = cache_ttl_seconds or settings.cost.cache_ttl_seconds
           self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
           self.cache_ttl_seconds = cache_ttl_seconds or self.DEFAULT_CACHE_TTL_SECONDS
           
           self._ensure_cache_dir()
           self.logger = logging.getLogger(__name__)
           self._models_cache: Dict[str, OpenRouterModel] = {} # Store parsed models
           self._last_refresh_time: float = 0
           
           # Fallback data (e.g., a bundled JSON file with common models)
           self.fallback_data_path = fallback_data_path # e.g., package_data/openrouter_fallback_models.json
           self._fallback_models: Dict[str, OpenRouterModel] = self._load_fallback_data()


       def _ensure_cache_dir(self):
           self.cache_dir.mkdir(parents=True, exist_ok=True)

       def _get_cache_file_path(self) -> Path:
           return self.cache_dir / "openrouter_models_cache.json"

       def _load_models_from_cache(self) -> bool:
           cache_file = self._get_cache_file_path()
           if not cache_file.exists():
               return False
           try:
               with open(cache_file, "r") as f:
                   cached_data = json.load(f)
               timestamp = cached_data.get("timestamp", 0)
               if (time.time() - timestamp) > self.cache_ttl_seconds:
                   self.logger.info("OpenRouter models cache is stale.")
                   return False
               
               self._models_cache = {
                   model_data['id']: OpenRouterModel(**model_data)
                   for model_data in cached_data.get("models", [])
               }
               self._last_refresh_time = timestamp
               self.logger.info(f"Loaded {len(self._models_cache)} models from cache.")
               return True
           except (json.JSONDecodeError, KeyError, Exception) as e:
               self.logger.warning(f"Failed to load valid models from cache file {cache_file}: {e}")
               return False

       def _save_models_to_cache(self):
           cache_file = self._get_cache_file_path()
           try:
               # Serialize Pydantic models to dicts for JSON storage
               models_to_save = [model.model_dump(mode='json') for model in self._models_cache.values()]
               with open(cache_file, "w") as f:
                   json.dump({"timestamp": self._last_refresh_time, "models": models_to_save}, f, indent=2)
               self.logger.info(f"Saved {len(self._models_cache)} models to cache at {cache_file}.")
           except IOError as e:
               self.logger.error(f"Failed to save models to cache file {cache_file}: {e}")
       
       def _load_fallback_data(self) -> Dict[str, OpenRouterModel]:
           if not self.fallback_data_path or not self.fallback_data_path.exists():
               self.logger.warning("No fallback model data path configured or file not found.")
               return {}
           try:
               with open(self.fallback_data_path, "r") as f:
                   data = json.load(f)
               return {model_data['id']: OpenRouterModel(**model_data) for model_data in data.get("data", [])}
           except Exception as e:
               self.logger.error(f"Error loading fallback model data from {self.fallback_data_path}: {e}")
               return {}

       async def refresh_models(self, force: bool = False) -> None:
           """Fetches models from OpenRouter API and updates cache."""
           current_time = time.time()
           if not force and self._models_cache and (current_time - self._last_refresh_time) < self.cache_ttl_seconds:
               self.logger.debug("Model cache is fresh, skipping refresh.")
               return

           if not force and self._load_models_from_cache(): # Try loading from file cache if memory cache is empty/stale
                if (time.time() - self._last_refresh_time) < self.cache_ttl_seconds:
                   self.logger.debug("Model file cache is fresh, skipping refresh.")
                   return

           try:
               self.logger.info("Refreshing models from OpenRouter API...")
               raw_models_data = await self.client.get_models()
               self._models_cache.clear()
               for model_data in raw_models_data:
                   try:
                       model = OpenRouterModel(**model_data)
                       self._models_cache[model.id] = model
                   except Exception as e: # Pydantic ValidationError
                       self.logger.warning(f"Failed to parse model data for ID {model_data.get('id', 'Unknown')}: {e}")
               
               self._last_refresh_time = time.time()
               self._save_models_to_cache()
               self.logger.info(f"Successfully refreshed and cached {len(self._models_cache)} models from OpenRouter.")
           except APIConnectionError as e:
               self.logger.error(f"Failed to refresh models from OpenRouter API: {e}")
               # If API fails, try to load from cache (if not already loaded) or use fallback
               if not self._models_cache and not self._load_models_from_cache():
                   if self._fallback_models:
                       self.logger.warning("Using fallback model data due to API connection error.")
                       self._models_cache = self._fallback_models.copy() # Use a copy
                   else:
                       raise CostInfoNotAvailable("OpenRouter API is unavailable and no cache or fallback data found.") from e
               elif not self._models_cache and self._fallback_models: # API failed, memory cache empty, file cache failed, but fallback exists
                   self.logger.warning("Using fallback model data due to API connection error and failed cache load.")
                   self._models_cache = self._fallback_models.copy()


       async def get_all_models(self) -> List[OpenRouterModel]:
           """Get all available models, ensuring cache is populated."""
           if not self._models_cache or (time.time() - self._last_refresh_time) > self.cache_ttl_seconds:
               await self.refresh_models()
           return list(self._models_cache.values())

       async def get_model_info(self, model_id: str) -> Optional[OpenRouterModel]:
           """Get information for a specific model."""
           if not self._models_cache or (time.time() - self._last_refresh_time) > self.cache_ttl_seconds:
               await self.refresh_models() # Ensure cache is populated
           
           model = self._models_cache.get(model_id)
           if not model and self._fallback_models: # Check fallback if not in primary cache
               model = self._fallback_models.get(model_id)
               if model:
                   self.logger.info(f"Model {model_id} found in fallback data.")
           
           if not model:
                # Attempt one more refresh if model not found, in case it was added recently
               await self.refresh_models(force=True)
               model = self._models_cache.get(model_id)
               if not model:
                   self.logger.warning(f"Model information not available for model ID: {model_id}")
                   return None # Or raise CostInfoNotAvailable
           return model

       async def get_model_cost(self, model_id: str) -> Optional[Dict[str, float]]:
           """Get cost information (prompt, completion, request) for a specific model."""
           model_info = await self.get_model_info(model_id)
           if not model_info:
               return None
           
           # Convert string prices to float, handling potential None for request/image
           pricing = model_info.pricing
           return {
               "prompt": float(pricing.prompt),
               "completion": float(pricing.completion),
               "request": float(pricing.request) if pricing.request is not None else 0.0,
               "image": float(pricing.image) if pricing.image is not None else 0.0,
           }

       async def get_model_context_length(self, model_id: str) -> Optional[int]:
           """Get context length for a specific model."""
           model_info = await self.get_model_info(model_id)
           return model_info.context_length if model_info else None
   ```

2.  **Prepare Fallback Data File (Optional but Recommended):**
    *   Create a JSON file (e.g., `src/llm_tester/data/openrouter_fallback_models.json`) containing data for a few common models in the `OpenRouterModel` schema. This will be used if the API is down and cache is empty.
    *   Ensure this file is included in the package distribution (e.g., via `MANIFEST.in` or `package_data` in `setup.py`).

#### Tests
-   Test service initialization (client, cache path, TTL).
-   Test `refresh_models`:
    *   Successful fetch and cache save.
    *   Cache hit (no API call if cache fresh).
    *   Cache stale (API call made).
    *   API error, fallback to cache.
    *   API error, cache empty, fallback to bundled data.
    *   API error, cache empty, no fallback data (raises `CostInfoNotAvailable`).
-   Test `get_model_info`, `get_model_cost`, `get_model_context_length` for existing and non-existing models.

#### Commit Message
`feat(cost): Implement CostInformationService with OpenRouter integration, caching, and fallback`

---

### Round 4: Service Layer - Cost Calculator
**Objective:** Update or create a cost calculator that uses the `CostInformationService` to determine costs for LLM interactions.

#### Tasks
1. **Create/Update `CostCalculator`:**
    *   Location: `src/llm_tester/services/cost_calculator.py`
    *   This replaces the `CostCalculator` from `src/utils/cost_manager.py`.
   ```python
   # src/llm_tester/services/cost_calculator.py
   import logging
   from typing import Dict, Any, Optional, List
   from pydantic_llm_tester.llm_tester import CostInformationService # Adjusted import
   from pydantic_llm_tester.llm_tester import CostInfoNotAvailable

   class CostCalculator:
       def __init__(self, cost_service: CostInformationService):
           self.cost_service = cost_service
           self.logger = logging.getLogger(__name__)

       async def calculate_cost(
           self,
           model_id: str,
           prompt_tokens: int = 0,
           completion_tokens: int = 0,
           num_requests: int = 1, # For models with per-request pricing
           num_images: int = 0    # For models with per-image pricing
       ) -> Dict[str, Any]:
           """Calculate the cost for a specific usage of a model."""
           try:
               pricing_info = await self.cost_service.get_model_cost(model_id)
               if not pricing_info:
                   raise CostInfoNotAvailable(f"Pricing info not available for model: {model_id}")

               prompt_cost_usd = (pricing_info.get("prompt", 0.0) * prompt_tokens) / 1_000_000
               completion_cost_usd = (pricing_info.get("completion", 0.0) * completion_tokens) / 1_000_000
               request_cost_usd = pricing_info.get("request", 0.0) * num_requests
               image_cost_usd = pricing_info.get("image", 0.0) * num_images
               
               total_cost_usd = prompt_cost_usd + completion_cost_usd + request_cost_usd + image_cost_usd

               return {
                   "model_id": model_id,
                   "prompt_tokens": prompt_tokens,
                   "completion_tokens": completion_tokens,
                   "total_tokens": prompt_tokens + completion_tokens,
                   "num_requests": num_requests,
                   "num_images": num_images,
                   "prompt_cost_usd": prompt_cost_usd,
                   "completion_cost_usd": completion_cost_usd,
                   "request_cost_usd": request_cost_usd,
                   "image_cost_usd": image_cost_usd,
                   "total_cost_usd": total_cost_usd,
                   "currency": "USD",
                   "error": None
               }
           except CostInfoNotAvailable as e:
               self.logger.warning(f"Cost calculation failed for model {model_id}: {e}")
               return {
                   "model_id": model_id,
                   "prompt_tokens": prompt_tokens,
                   "completion_tokens": completion_tokens,
                   "total_tokens": prompt_tokens + completion_tokens,
                   "num_requests": num_requests,
                   "num_images": num_images,
                   "prompt_cost_usd": None,
                   "completion_cost_usd": None,
                   "request_cost_usd": None,
                   "image_cost_usd": None,
                   "total_cost_usd": None,
                   "currency": "USD",
                   "error": str(e)
               }
   ```

#### Tests
-   Test `calculate_cost` with various inputs (prompt tokens, completion tokens, requests, images).
-   Test with models having only token costs, only request costs, or mixed.
-   Test behavior when `CostInformationService` cannot provide pricing (e.g., model not found, returns error).

#### Commit Message
`feat(cost): Implement CostCalculator service using CostInformationService`

---

### Round 5: Service Layer - Token Counter & Usage Tracker
**Objective:** Implement services for counting tokens (potentially model-specific) and tracking LLM usage within a session.

#### Tasks
1.  **Create `TokenCounter` Service:**
    *   Location: `src/llm_tester/services/token_counter.py`
    *   **Challenge:** Accurate token counting is model-specific.
        *   OpenAI models often use `tiktoken`.
        *   Other models might have their own tokenizers or rules (e.g., 1 char = 1 token, or specific libraries).
        *   OpenRouter's `/models` endpoint *may* provide tokenizer info (`architecture.tokenizer`).
    *   **Strategy:**
        *   Default to a simple heuristic (e.g., `len(text) / 4`).
        *   Allow registration of specific tokenizer functions per model ID or provider.
        *   Attempt to use `tiktoken` for known OpenAI models.
        *   The `CostInformationService` could be enhanced to also cache/provide tokenizer information if available from OpenRouter.
    ```python
    # src/llm_tester/services/token_counter.py
    import logging
    from typing import Callable, Dict, Optional
    # import tiktoken # Add as optional dependency

    # from llm_tester.services.cost_service import CostInformationService # For model-specific tokenizer info

    class TokenCounter:
        def __init__(self, cost_service: Optional[CostInformationService] = None):
            self.logger = logging.getLogger(__name__)
            self.cost_service = cost_service # To potentially fetch tokenizer info
            self._tokenizers: Dict[str, Callable[[str], int]] = {}
            self._register_default_tokenizers()

        def _register_default_tokenizers(self):
            # Example: Registering tiktoken for common OpenAI models
            try:
                import tiktoken
                # Common models and their encodings
                # This could be expanded or made configurable
                openai_models = {
                    "gpt-4": "cl100k_base", "gpt-4-turbo": "cl100k_base",
                    "gpt-3.5-turbo": "cl100k_base",
                }
                for model_id_prefix, encoding_name in openai_models.items():
                    try:
                        encoding = tiktoken.get_encoding(encoding_name)
                        self._tokenizers[model_id_prefix] = lambda text, e=encoding: len(e.encode(text))
                        self.logger.info(f"Registered tiktoken '{encoding_name}' for models starting with '{model_id_prefix}'.")
                    except Exception as e:
                        self.logger.warning(f"Could not register tiktoken for {model_id_prefix}: {e}")
            except ImportError:
                self.logger.info("tiktoken library not found. OpenAI token counts will be approximate.")

        def register_tokenizer(self, model_id_prefix: str, tokenizer_func: Callable[[str], int]):
            self._tokenizers[model_id_prefix] = tokenizer_func
            self.logger.info(f"Registered custom tokenizer for models starting with '{model_id_prefix}'.")

        def count_tokens(self, text: str, model_id: str) -> int:
            # Try to find a specific tokenizer by full model_id or prefix
            tokenizer = self._tokenizers.get(model_id)
            if not tokenizer:
                for prefix, func in self._tokenizers.items():
                    if model_id.startswith(prefix):
                        tokenizer = func
                        break
            
            if tokenizer:
                try:
                    return tokenizer(text)
                except Exception as e:
                    self.logger.error(f"Error using registered tokenizer for {model_id}: {e}. Falling back to heuristic.")

            # Default heuristic: average characters per token (very rough)
            # This should be improved, e.g. by using info from OpenRouter if available
            # or allowing users to specify per-model heuristics.
            char_per_token_estimate = 4 
            return (len(text) + char_per_token_estimate -1) // char_per_token_estimate


        async def check_context_length(self, text: str, model_id: str) -> Dict[str, Any]:
            if not self.cost_service:
                return {"fits": None, "message": "CostInformationService not available to check context length."}

            tokens = self.count_tokens(text, model_id)
            max_tokens = await self.cost_service.get_model_context_length(model_id)

            if max_tokens is None:
                return {"fits": None, "tokens": tokens, "max_tokens": None, "message": f"Max context length unknown for {model_id}."}
            
            fits = tokens <= max_tokens
            return {"fits": fits, "tokens": tokens, "max_tokens": max_tokens, "message": "" if fits else "Text exceeds model's context length."}

    ```

2. **Create `UsageTracker` Service:**
    *   Location: `src/llm_tester/services/usage_tracker.py`
    *   This replaces the `CostTracker` from `src/utils/cost_manager.py`.
    *   **Persistence:** For a CLI tool, in-memory tracking per session is primary. Optionally, allow logging usage to a file (e.g., JSONL format) for later analysis.
   ```python
   # src/llm_tester/services/usage_tracker.py
   import logging
   from typing import Dict, Any, Optional, List
   from datetime import datetime
   import uuid

   from pydantic_llm_tester.llm_tester import CostCalculator # Adjusted import

   class UsageEntry(BaseModel): # Requires from pydantic import BaseModel
       entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
       timestamp: datetime = Field(default_factory=datetime.utcnow)
       model_id: str
       prompt_tokens: int
       completion_tokens: int
       num_requests: int
       num_images: int
       cost_details: Dict[str, Any] # Output from CostCalculator
       metadata: Optional[Dict[str, Any]] = None


   class UsageTracker:
       def __init__(self, cost_calculator: CostCalculator):
           self.cost_calculator = cost_calculator
           self.logger = logging.getLogger(__name__)
           self.session_usage: List[UsageEntry] = []
           self.current_run_id: Optional[str] = None # For grouping usage by test runs

       def start_new_run(self, run_id: Optional[str] = None) -> str:
           self.current_run_id = run_id or str(uuid.uuid4())
           self.logger.info(f"Started new usage tracking run: {self.current_run_id}")
           return self.current_run_id

       async def record_usage(
           self,
           model_id: str,
           prompt_tokens: int,
           completion_tokens: int,
           num_requests: int = 1,
           num_images: int = 0,
           metadata: Optional[Dict[str, Any]] = None
       ) -> UsageEntry:
           cost_details = await self.cost_calculator.calculate_cost(
               model_id, prompt_tokens, completion_tokens, num_requests, num_images
           )
           
           # Add run_id to metadata if a run is active
           entry_metadata = metadata.copy() if metadata else {}
           if self.current_run_id:
               entry_metadata["run_id"] = self.current_run_id

           entry = UsageEntry(
               model_id=model_id,
               prompt_tokens=prompt_tokens,
               completion_tokens=completion_tokens,
               num_requests=num_requests,
               num_images=num_images,
               cost_details=cost_details,
               metadata=entry_metadata
           )
           self.session_usage.append(entry)
           self.logger.debug(f"Recorded usage for model {model_id}: {entry.model_dump_json(indent=2)}")
           return entry

       def get_session_summary(self, run_id: Optional[str] = None) -> Dict[str, Any]:
           """Summarizes usage for the current session or a specific run_id."""
           usage_to_summarize = [
               entry for entry in self.session_usage 
               if run_id is None or (entry.metadata and entry.metadata.get("run_id") == run_id)
           ]

           total_prompt_tokens = sum(e.prompt_tokens for e in usage_to_summarize)
           total_completion_tokens = sum(e.completion_tokens for e in usage_to_summarize)
           total_requests = sum(e.num_requests for e in usage_to_summarize)
           total_images = sum(e.num_images for e in usage_to_summarize)
           total_cost_usd = sum(e.cost_details.get("total_cost_usd", 0.0) or 0.0 for e in usage_to_summarize) # Handle None

           model_breakdown: Dict[str, Dict[str, Any]] = {}
           for entry in usage_to_summarize:
               mid = entry.model_id
               if mid not in model_breakdown:
                   model_breakdown[mid] = {
                       "prompt_tokens": 0, "completion_tokens": 0, "requests": 0, 
                       "images": 0, "cost_usd": 0.0, "count": 0
                   }
               model_breakdown[mid]["prompt_tokens"] += entry.prompt_tokens
               model_breakdown[mid]["completion_tokens"] += entry.completion_tokens
               model_breakdown[mid]["requests"] += entry.num_requests
               model_breakdown[mid]["images"] += entry.num_images
               model_breakdown[mid]["cost_usd"] += entry.cost_details.get("total_cost_usd", 0.0) or 0.0
               model_breakdown[mid]["count"] += 1
           
           return {
               "run_id": run_id or "current_session (no specific run)",
               "total_entries": len(usage_to_summarize),
               "total_prompt_tokens": total_prompt_tokens,
               "total_completion_tokens": total_completion_tokens,
               "total_requests": total_requests,
               "total_images": total_images,
               "grand_total_cost_usd": total_cost_usd,
               "model_breakdown": model_breakdown,
               "usage_entries": [e.model_dump(mode='json') for e in usage_to_summarize] # Optional: include all entries
           }
       
       # get_daily_usage might be complex if persistence isn't implemented.
       # For now, focus on session-based tracking.
   ```

#### Tests
-   **TokenCounter:**
    *   Test with default heuristic.
    *   Test with registered `tiktoken` (mocking `tiktoken` library if needed).
    *   Test `check_context_length` with various scenarios (fits, doesn't fit, unknown max length).
-   **UsageTracker:**
    *   Test `record_usage` correctly stores entry and calculates cost.
    *   Test `get_session_summary` provides accurate totals and breakdowns.
    *   Test `start_new_run` and filtering summary by `run_id`.

#### Commit Message
`feat(cost): Implement TokenCounter and UsageTracker services`

---

### Round 6: API Facade - `CostAPI`
**Objective:** Create a clean, high-level API facade for accessing all cost, model info, token counting, and usage tracking functionalities. This makes it easy for other parts of the application (like CLI or `LLMTester` core) to interact with the cost system.

#### Tasks
1. **Create `CostAPI` Facade:**
    *   Location: `src/llm_tester/cost_api.py` (or `src/llm_tester/services/cost_management_api.py`)
   ```python
   # src/llm_tester/cost_api.py
   import logging
   from typing import Dict, Any, Optional, List
   from pathlib import Path

   # Assuming unified settings are available
   # from llm_tester.config.settings import get_app_settings
   from pydantic_llm_tester.llm_tester import OpenRouterClient
   from pydantic_llm_tester.llm_tester import CostInformationService
   from pydantic_llm_tester.llm_tester import CostCalculator
   from pydantic_llm_tester.llm_tester import TokenCounter
   from pydantic_llm_tester.llm_tester import UsageTracker, UsageEntry
   from pydantic_llm_tester.llm_tester import OpenRouterModel
   from pydantic_llm_tester.llm_tester import ConfigurationError


   class CostAPI:
       _instance: Optional["CostAPI"] = None

       @classmethod
       def get_instance(cls) -> "CostAPI":
           if cls._instance is None:
               # settings = get_app_settings() # hypothetical
               # if not settings.cost.openrouter_api_key:
               #     raise ConfigurationError("OpenRouter API key not configured for CostAPI.")
               
               # For now, let OpenRouterClient raise error if key is missing from its direct init or settings
               # This needs to be wired to the unified config system properly.
               # Example: api_key = settings.cost.openrouter_api_key
               
               # Placeholder for API key until full config integration
               # In a real scenario, this would come from settings.
               temp_api_key = os.getenv("OPENROUTER_API_KEY") # Fallback to env var for now
               if not temp_api_key:
                   logging.warning("OPENROUTER_API_KEY not set. CostAPI may not function fully.")
                   # Allow initialization but some features might fail if API key is needed by client.
                   # OpenRouterClient will raise error if key is truly needed and not provided.

               openrouter_client = OpenRouterClient(api_key=temp_api_key) # Pass key from settings
               
               # Determine fallback_data_path (e.g., using importlib.resources)
               # fallback_path = Path(__file__).parent.parent / "data" / "openrouter_fallback_models.json" 
               # This needs a robust way to locate package data.
               
               cost_service = CostInformationService(
                   openrouter_client=openrouter_client
                   # cache_dir=settings.cache_dir / "model_info", # from app settings
                   # cache_ttl_seconds=settings.cost.cache_ttl_seconds, # from cost settings
                   # fallback_data_path=fallback_path
               )
               cost_calculator = CostCalculator(cost_service=cost_service)
               token_counter = TokenCounter(cost_service=cost_service) # Pass cost_service
               usage_tracker = UsageTracker(cost_calculator=cost_calculator)
               
               cls._instance = cls(
                   openrouter_client, cost_service, cost_calculator, token_counter, usage_tracker
               )
           return cls._instance

       def __init__(
           self,
           openrouter_client: OpenRouterClient,
           cost_service: CostInformationService,
           cost_calculator: CostCalculator,
           token_counter: TokenCounter,
           usage_tracker: UsageTracker
       ):
           self.logger = logging.getLogger(__name__)
           self.openrouter_client = openrouter_client # Keep if direct client access is needed
           self.cost_service = cost_service
           self.cost_calculator = cost_calculator
           self.token_counter = token_counter
           self.usage_tracker = usage_tracker
           self.logger.info("CostAPI initialized.")

       async def get_available_openrouter_models(self) -> List[OpenRouterModel]:
           """Get all available models from OpenRouter via the CostInformationService."""
           return await self.cost_service.get_all_models()

       async def get_openrouter_model_info(self, model_id: str) -> Optional[OpenRouterModel]:
           """Get detailed information for a specific OpenRouter model."""
           return await self.cost_service.get_model_info(model_id)

       async def calculate_llm_cost(
           self, model_id: str, prompt_tokens: int, completion_tokens: int,
           num_requests: int = 1, num_images: int = 0
       ) -> Dict[str, Any]:
           """Calculate the cost for a specific LLM usage."""
           return await self.cost_calculator.calculate_cost(
               model_id, prompt_tokens, completion_tokens, num_requests, num_images
           )

       def count_text_tokens(self, text: str, model_id: str) -> int:
           """Count tokens in the given text for a specific model."""
           return self.token_counter.count_tokens(text, model_id)

       async def check_text_context_length(self, text: str, model_id: str) -> Dict[str, Any]:
           """Check if the text fits within the model's context length."""
           return await self.token_counter.check_context_length(text, model_id)

       async def record_llm_usage(
           self, model_id: str, prompt_tokens: int, completion_tokens: int,
           num_requests: int = 1, num_images: int = 0, metadata: Optional[Dict[str, Any]] = None
       ) -> UsageEntry:
           """Record usage of an LLM."""
           return await self.usage_tracker.record_usage(
               model_id, prompt_tokens, completion_tokens, num_requests, num_images, metadata
           )

       def start_usage_run(self, run_id: Optional[str] = None) -> str:
           """Starts a new run context for usage tracking."""
           return self.usage_tracker.start_new_run(run_id)

       def get_usage_summary(self, run_id: Optional[str] = None) -> Dict[str, Any]:
           """Get a summary of LLM usage for the current session or a specific run."""
           return self.usage_tracker.get_session_summary(run_id)
           
       async def close_resources(self):
           """Gracefully close any open resources, like the HTTP client."""
           await self.openrouter_client.close()
           self.logger.info("CostAPI resources closed.")
   ```
    *Note: The `get_instance` method provides a singleton pattern. Dependency injection might be preferred in some parts of the application for better testability of components using `CostAPI`.*
    *Import `os` for `os.getenv` in the `get_instance` placeholder.*
    *Import `BaseModel`, `Field` from `pydantic` for `UsageEntry`.*


#### Tests
-   Test `CostAPI.get_instance()` returns a singleton.
-   Test each public method of `CostAPI` correctly calls the underlying service methods (using mocks for services).
-   Test integration with configuration for API key.
-   Test `close_resources` correctly calls client's close method.

#### Commit Message
`feat(cost): Implement CostAPI facade for integrated cost and usage management`

---

## Overall Success Criteria for OpenRouter Cost Management
-   Dynamic cost and model information is successfully fetched from OpenRouter API.
-   Token counting is reasonably accurate for common models, with a clear mechanism for improvement/extension.
-   LLM usage is tracked correctly, and cost reports can be generated per session/run.
-   Caching works effectively to reduce API calls and improve performance.
-   Fallback mechanisms ensure basic functionality (e.g., using bundled data) if OpenRouter API is unavailable and cache is cold.
-   The new cost system is cleanly integrated into the `llm-tester` CLI and core logic (e.g., `LLMTester` class or its refactored components).
-   The system is well-tested with high coverage for all new components.
-   Configuration is managed through the unified project settings.
