"""Base LLM provider class and related utilities"""

from typing import Dict, Any, Tuple, Optional, List, Union, Type # Added Type
from abc import ABC, abstractmethod
import logging
import os
import time

from pydantic import BaseModel, Field

from pydantic_llm_tester.utils.data_structures import UsageData # Import UsageData from the new file

logger = logging.getLogger(__name__)

class ModelConfig(BaseModel):
    """Configuration for an LLM model"""
    name: str = Field(..., description="Full name of the model including provider prefix")
    default: bool = Field(False, description="Whether this is the default model for the provider")
    preferred: bool = Field(False, description="Whether this model is preferred for production use")
    enabled: bool = Field(True, description="Whether this model is enabled for use") # Added
    cost_input: float = Field(..., description="Cost per 1M input tokens in USD")
    cost_output: float = Field(..., description="Cost per 1M output tokens in USD")
    cost_category: str = Field("standard", description="Cost category (cheap, standard, expensive)")
    max_input_tokens: int = Field(4096, description="Maximum input tokens supported")
    max_output_tokens: int = Field(4096, description="Maximum output tokens supported")

class ProviderConfig(BaseModel):
    """Configuration for an LLM provider"""
    name: str = Field(..., description="Provider name (e.g., 'openai', 'anthropic')")
    provider_type: str = Field(..., description="Provider type identifier")
    env_key: str = Field(..., description="Environment variable name for API key")
    env_key_secret: Optional[str] = Field(None, description="Environment variable name for secondary key/secret")
    system_prompt: str = Field("", description="Default system prompt to use")
    default_model: Optional[str] = Field(None, description="Default model name for this provider") # Added default_model
    llm_models: List[ModelConfig] = Field(..., description="Available models for this provider")
    supports_file_upload: bool = Field(False, description="Whether this provider supports file uploads")

class BaseLLM(ABC):
    """Base class for all LLM providers"""
    supports_file_upload: bool = False
    
    def __init__(self, config: Optional[ProviderConfig] = None, llm_models: Optional[List[ModelConfig]] = None):
        """Initialize provider with optional config and model filter"""
        self.config = config
        self._llm_models: Dict[str, ModelConfig] = {model.name: model for model in llm_models} if llm_models else {} # Store ModelConfig objects
        self.name = config.name if config else self.__class__.__name__.lower().replace('provider', '')
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        if config:
            self.supports_file_upload = config.supports_file_upload
    
    def get_response(self, prompt: str, source: str, model_class: Type[BaseModel], model_name: Optional[str] = None, files: Optional[List[str]] = None) -> Tuple[str, UsageData]:
        """Get response from LLM for the given prompt and source
        
        Args:
            prompt: The prompt text to send
            source: The source text to include in the prompt
            model_class: The Pydantic model class for schema guidance.
            model_name: Optional model name to use
            files: Optional list of file paths to upload
            
        Returns:
            Tuple of response text and usage data
        """
        if files and not self.supports_file_upload:
            raise NotImplementedError(f"Provider {self.name} does not support file uploads.")
            
        # Get model config
        model_config = self.get_model_config(model_name)

        if not model_config:
            self.logger.warning(f"Model {model_name} not found, using default")
            model_name = self.get_default_model()
            model_config = self.get_model_config()
            
        if not model_config:
            self.logger.error("No model configuration found")
            raise ValueError("No model configuration found")
            
        # Use the original model name from the config to preserve any provider prefix
        clean_model_name = model_config.name
        
        # Get system prompt from config
        system_prompt = self.config.system_prompt if self.config else ""
        
        # Record start time for elapsed time calculation
        start_time = time.time()
        
        # Call implementation-specific method to get the response
        try:
            response_text, usage = self._call_llm_api(
                prompt=full_prompt,
                system_prompt=system_prompt,
                model_name=clean_model_name,
                model_config=model_config,
                model_class=model_class, # Pass model_class
                files=files
            )
            
            elapsed_time = time.time() - start_time
            
            # Create usage data object if not provided by implementation
            if not isinstance(usage, UsageData):
                usage_data = UsageData(
                    provider=self.name,
                    model=clean_model_name,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    # Removed cost_input_rate and cost_output_rate as they are calculated in UsageData __init__
                )
                
                # Add elapsed time as an attribute
                # This attribute is not part of UsageData constructor, so assign it after.
                # However, it seems UsageData doesn't have an elapsed_time attribute.
                # For now, let's assume it's not strictly needed for cost calculation.
                # If it is, UsageData would need to be modified or this handled differently.
                # setattr(usage_data, 'elapsed_time', elapsed_time) # Example if it were needed

            else: # usage is already a UsageData instance
                usage_data = usage
                # Similarly, if elapsed_time was a standard field:
                # if not hasattr(usage_data, 'elapsed_time') or not usage_data.elapsed_time:
                #     setattr(usage_data, 'elapsed_time', elapsed_time)
            
            # Ensure elapsed_time is set if it's a concept we want to track with UsageData
            # For now, the primary goal is to fix cost calculation.
            # The original code set usage_data.elapsed_time, but UsageData class doesn't define it.
            # This might be an area for future refinement if elapsed time per call is important.

            return response_text, usage_data
            
        except Exception as e:
            self.logger.error(f"Error calling {self.name} API: {str(e)}")
            raise
    
    @abstractmethod
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the LLM
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            model_class: The Pydantic model class for schema guidance.
            files: Optional list of file paths to upload
            
        Returns:
            Tuple of (response_text, usage_data)
            usage_data can be either a UsageData object or a dict with token counts
        """
        pass
        
    def get_default_model(self) -> Optional[str]:
        """Get the default model name for this provider"""
        # Try to get default model from ConfigManager first
        try:
            from pydantic_llm_tester.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            provider_config = config_manager.get_provider_config(self.name)
            if provider_config and "default_model" in provider_config:
                default_model = provider_config["default_model"]
                self.logger.debug(f"Using default model '{default_model}' from ConfigManager for provider {self.name}")
                return default_model
        except Exception as e:
            self.logger.debug(f"Error getting default model from ConfigManager: {e}")
        
        # Try to get default model from registry
        try:
            from pydantic_llm_tester.llms.llm_registry import LLMRegistry
            registry = LLMRegistry()
            registry_models = registry.get_provider_models(self.name)
            if registry_models:
                # Find the *enabled* model marked as default
                enabled_default = next((model.name for model in registry_models.values() 
                                       if hasattr(model, 'default') and model.default 
                                       and (not hasattr(model, 'enabled') or model.enabled)), None)
                if enabled_default:
                    return enabled_default
                
                # If no enabled default, find the first *enabled* model
                first_enabled = next((model.name for model in registry_models.values() 
                                     if not hasattr(model, 'enabled') or model.enabled), None)
                if first_enabled:
                    return first_enabled
        except Exception as e:
            self.logger.debug(f"Error getting default model from registry: {e}")
        
        # Fallback to config.llm_models if necessary
        if self.config and self.config.llm_models:
            # Find the *enabled* model marked as default
            enabled_default = next((model.name for model in self.config.llm_models if model.default and model.enabled), None)
            if enabled_default:
                return enabled_default

            # If no enabled default, find the first *enabled* model
            first_enabled = next((model.name for model in self.config.llm_models if model.enabled), None)
            if first_enabled:
                return first_enabled

        # If no models are enabled at all
        self.logger.warning(f"No enabled models found for provider {self.name}.")
        return None

    # --- Correctly indented methods start here ---
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        if not self.config or not self.config.env_key:
            self.logger.debug("No config or env_key defined for get_api_key.")
            return None

        # Directly get from environment; loading should happen externally (e.g., conftest or cli)
        api_key = os.environ.get(self.config.env_key)
        if api_key is None:
             self.logger.debug(f"API key '{self.config.env_key}' not found in environment.")

        return api_key

    def get_api_secret(self) -> Optional[str]:
        """Get API secret/secondary key from environment variable"""
        if not self.config or not self.config.env_key_secret:
            return None
        return os.environ.get(self.config.env_key_secret)
        
    def get_model_config(self, model_name: Optional[str] = None) -> Optional[ModelConfig]:
        """Get configuration for a specific model
        
        Args:
            model_name: Name of the model to get config for, or None for default
            
        Returns:
            ModelConfig object or None if not found
        """
        # If no model specified, use default
        if not model_name:
            # Try to get default model from config manager first if available
            try:
                from pydantic_llm_tester.utils.config_manager import ConfigManager
                config_manager = ConfigManager()
                provider_config = config_manager.get_provider_config(self.name)
                if provider_config and "default_model" in provider_config:
                    model_name = provider_config["default_model"]
                    self.logger.debug(f"Using default model '{model_name}' from ConfigManager for provider {self.name}")
            except Exception as e:
                self.logger.debug(f"Error getting default model from ConfigManager: {e}")
                
            # Fallback to get_default_model if necessary
            if not model_name:
                model_name = self.get_default_model()
        
        found_model: Optional[ModelConfig] = None
        
        # Try to get model from registry first
        try:
            from pydantic_llm_tester.llms.llm_registry import LLMRegistry
            registry = LLMRegistry()
            
            # Handle provider:model format
            if ":" in model_name:
                model_provider, model_id = model_name.split(":", 1)
                if model_provider != self.name:
                    self.logger.warning(f"Model '{model_name}' is for a different provider ({model_provider}), not {self.name}")
                    return None
                # Look up just the model part in the registry
                model_details = registry.get_model_details(self.name, model_id)
                if model_details:
                    found_model = model_details
            else:
                # Look up model in registry
                model_details = registry.get_model_details(self.name, model_name)
                if model_details:
                    found_model = model_details
                else:
                    # Try with provider prefix
                    prefixed_name = f"{self.name}:{model_name}"
                    model_details = registry.get_model_details(self.name, model_name)
                    if model_details:
                        found_model = model_details
        except Exception as e:
            self.logger.debug(f"Error getting model from registry: {e}")
        
        # Fallback to config.llm_models if necessary
        if not found_model and self.config and self.config.llm_models:
            # Filter models based on self.llm_models_filter if it exists
            available_models = self.config.llm_models
            if self.llm_models_filter is not None:
                # Filter models whose names are in the llm_models_filter list
                available_models = [
                    model for model in self.config.llm_models
                    if model.name in self.llm_models_filter
                ]
                self.logger.debug(f"Filtered models for provider {self.name} based on filter {self.llm_models_filter}: {[m.name for m in available_models]}")
                
                # If the requested model_name is not in the filter, and a specific model was requested,
                # we should not find it. If no specific model was requested (using default),
                # we should only consider models in the filter.
                if model_name and model_name not in self.llm_models_filter:
                    self.logger.warning(f"Requested model '{model_name}' is not in the specified LLM models filter {self.llm_models_filter}.")
                    return None # Requested model is not allowed by the filter

            # Find model by name in the potentially filtered list
            for model in available_models:
                if model.name == model_name:
                    found_model = model
                    break

            # If model name has no provider prefix, try with provider prefix in the filtered list
            if not found_model and model_name and ':' not in model_name:
                prefixed_name = f"{self.name}:{model_name}" # Assuming self.name is the provider name
                # Search the available_models (which are already filtered by the user's list)
                for model in available_models:
                    if model.name == prefixed_name:
                        found_model = model
                        break

        # If still not found, try to create a default model config
        if not found_model and model_name:
            try:
                from pydantic_llm_tester.utils.config_manager import ConfigManager
                config_manager = ConfigManager()
                if ":" in model_name:
                    model_details = config_manager.get_model_details_from_registry(model_name)
                else:
                    model_details = config_manager.get_model_details_from_registry(f"{self.name}:{model_name}")
                
                if model_details:
                    found_model = model_details
            except Exception as e:
                self.logger.debug(f"Error creating default model config: {e}")

        # Return the model only if it's found AND enabled
        if found_model and (not hasattr(found_model, 'enabled') or found_model.enabled):
            return found_model
        elif found_model and hasattr(found_model, 'enabled') and not found_model.enabled:
            self.logger.warning(f"Model '{model_name}' found but is disabled in config.")
            return None
        else:
            # This warning might be redundant if the model was filtered out earlier,
            # but it covers cases where the model isn't in the original config at all.
            if model_name:
                self.logger.warning(f"Model '{model_name}' not found or not enabled for provider {self.name}.")
            return None

    def get_available_models(self) -> List[ModelConfig]:
        """
        Get a list of available ModelConfig objects for this provider,
        respecting the llm_models_filter and enabled flags.

        Returns:
            List of available ModelConfig objects.
        """
        available_models = []
        
        # Try to get models from registry first
        try:
            from pydantic_llm_tester.llms.llm_registry import LLMRegistry
            registry = LLMRegistry()
            registry_models = registry.get_provider_models(self.name)
            if registry_models:
                available_models = list(registry_models.values())
                self.logger.debug(f"Using {len(available_models)} models from central registry for provider {self.name}")
        except Exception as e:
            self.logger.debug(f"Error getting models from registry: {e}")
        
        # Fallback to config.llm_models if registry is empty
        if not available_models and self.config and self.config.llm_models:
            available_models = [model for model in self.config.llm_models if model.enabled]
        
        # Filter based on llm_models_filter if provided
        if self.llm_models_filter is not None:
            # Filter models whose names are in the llm_models_filter list
            available_models = [
                model for model in available_models
                if model.name in self.llm_models_filter
            ]
            self.logger.debug(f"Filtered available models for provider {self.name} based on filter {self.llm_models_filter}: {[m.name for m in available_models]}")

        return available_models
