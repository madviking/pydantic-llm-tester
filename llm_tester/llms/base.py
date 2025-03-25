"""Base LLM provider class and related utilities"""

from typing import Dict, Any, Tuple, Optional, List, Union
from abc import ABC, abstractmethod
import json
import logging
import os
import inspect
import time

from pydantic import BaseModel, Field

from ..utils.cost_manager import UsageData

logger = logging.getLogger(__name__)

class ModelConfig(BaseModel):
    """Configuration for an LLM model"""
    name: str = Field(..., description="Full name of the model including provider prefix")
    default: bool = Field(False, description="Whether this is the default model for the provider")
    preferred: bool = Field(False, description="Whether this model is preferred for production use")
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
    models: List[ModelConfig] = Field(..., description="Available models for this provider")

class BaseLLM(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        """Initialize provider with optional config"""
        self.config = config
        self.name = config.name if config else self.__class__.__name__.lower().replace('provider', '')
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    def get_response(self, prompt: str, source: str, model_name: Optional[str] = None) -> Tuple[str, UsageData]:
        """Get response from LLM for the given prompt and source
        
        Args:
            prompt: The prompt text to send
            source: The source text to include in the prompt
            model_name: Optional model name to use
            
        Returns:
            Tuple of response text and usage data
        """
        # Get model config
        model_config = self.get_model_config(model_name)
        if not model_config:
            self.logger.warning(f"Model {model_name} not found, using default")
            model_name = self.get_default_model()
            model_config = self.get_model_config()
            
        if not model_config:
            self.logger.error("No model configuration found")
            raise ValueError("No model configuration found")
            
        # Clean model name to remove provider prefix if present
        clean_model_name = model_config.name
        if ':' in clean_model_name:
            clean_model_name = clean_model_name.split(':')[-1]
        
        # Get system prompt from config
        system_prompt = self.config.system_prompt if self.config else ""
        
        # Prepare full prompt
        full_prompt = f"{prompt}\n\nSource Text:\n{source}"
        
        # Record start time for elapsed time calculation
        start_time = time.time()
        
        # Call implementation-specific method to get the response
        try:
            response_text, usage = self._call_llm_api(
                prompt=full_prompt,
                system_prompt=system_prompt,
                model_name=clean_model_name,
                model_config=model_config
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
                    elapsed_time=elapsed_time
                )
                
                # Calculate costs based on model config
                prompt_cost = (usage_data.prompt_tokens / 1000000) * model_config.cost_input
                completion_cost = (usage_data.completion_tokens / 1000000) * model_config.cost_output
                total_cost = prompt_cost + completion_cost
                
                usage_data.prompt_cost = prompt_cost
                usage_data.completion_cost = completion_cost
                usage_data.total_cost = total_cost
            else:
                usage_data = usage
                
                # Make sure elapsed_time is set
                if not usage_data.elapsed_time:
                    usage_data.elapsed_time = elapsed_time
            
            return response_text, usage_data
            
        except Exception as e:
            self.logger.error(f"Error calling {self.name} API: {str(e)}")
            raise
    
    @abstractmethod
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call to the LLM
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
            usage_data can be either a UsageData object or a dict with token counts
        """
        pass
        
    def get_default_model(self) -> Optional[str]:
        """Get the default model name for this provider"""
        if not self.config or not self.config.models:
            return None
            
        # Find the model marked as default
        for model in self.config.models:
            if model.default:
                return model.name
                
        # If no default marked, use the first one
        return self.config.models[0].name
        
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable"""
        if not self.config or not self.config.env_key:
            return None
            
        return os.environ.get(self.config.env_key)
        
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
        if not self.config or not self.config.models:
            return None
            
        # If no model specified, use default
        if not model_name:
            model_name = self.get_default_model()
            
        # Find model by name
        for model in self.config.models:
            if model.name == model_name:
                return model
                
        # If model name has no provider prefix, try with provider prefix
        if model_name and ':' not in model_name:
            prefixed_name = f"{self.name}:{model_name}"
            for model in self.config.models:
                if model.name == prefixed_name:
                    return model
                    
        return None