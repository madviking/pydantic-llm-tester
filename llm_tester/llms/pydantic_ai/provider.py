"""PydanticAI provider implementation"""

import logging
import json
import os
from typing import Dict, Any, Tuple, Optional, List, Union, Type, get_type_hints
import inspect

from pydantic import BaseModel, Field

try:
    import pydantic_ai
    from pydantic_ai import LLMRunner
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    
from ..base import BaseLLM, ModelConfig
from ...utils.cost_manager import UsageData


class PydanticAIProvider(BaseLLM):
    """Provider implementation using PydanticAI"""
    
    def __init__(self, config=None):
        """Initialize the PydanticAI provider"""
        super().__init__(config)
        
        # Check if PydanticAI is available
        if not PYDANTIC_AI_AVAILABLE:
            self.logger.warning("PydanticAI not available. Install with 'pip install pydantic-ai'")
            self.runner = None
            return
            
        # We don't initialize a client here because PydanticAI will create one on demand
        self.logger.info("PydanticAI provider initialized")
        
        # We'll initialize runners on demand based on the model requested
        self.runners = {}
        
    def _get_runner(self, provider: str, model: str) -> LLMRunner:
        """Get or create a runner for the specified provider and model
        
        Args:
            provider: The provider to use (openai, anthropic)
            model: The model name
            
        Returns:
            A PydanticAI LLMRunner instance
        """
        runner_key = f"{provider}:{model}"
        
        # Check if runner already exists
        if runner_key in self.runners:
            return self.runners[runner_key]
        
        # Create new runner based on provider
        if provider == "openai":
            # Get API key
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.logger.error("No API key found for OpenAI")
                raise ValueError("No API key found for OpenAI")
                
            # Create OpenAI runner
            runner = LLMRunner(
                provider="openai",
                model=model,
                api_key=api_key
            )
            
        elif provider == "anthropic":
            # Get API key
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                self.logger.error("No API key found for Anthropic")
                raise ValueError("No API key found for Anthropic")
                
            # Create Anthropic runner
            runner = LLMRunner(
                provider="anthropic",
                model=model,
                api_key=api_key
            )
            
        else:
            self.logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
            
        # Cache the runner
        self.runners[runner_key] = runner
        return runner
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call using PydanticAI
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not PYDANTIC_AI_AVAILABLE:
            self.logger.error("PydanticAI not available")
            raise ValueError("PydanticAI not available")
            
        # Parse model name to get provider and model
        # Format is provider:model (already cleaned of pydantic_ai: prefix)
        name_parts = model_name.split(':')
        if len(name_parts) < 2:
            self.logger.error(f"Invalid model name format: {model_name}")
            raise ValueError(f"Invalid model name format: {model_name}")
            
        provider_name = name_parts[0]
        model_name = name_parts[1]
        
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "Extract the requested information from the provided text accurately."
        
        # Extract model class from the caller
        model_class = None
        
        # Try to get it from the calling frames
        frame = inspect.currentframe()
        while frame:
            if frame.f_locals and 'test_case' in frame.f_locals:
                test_case = frame.f_locals['test_case']
                if 'model_class' in test_case:
                    model_class = test_case['model_class']
                    break
            frame = frame.f_back
            
        if not model_class:
            self.logger.error("No model class found for PydanticAI extraction")
            raise ValueError("No model class found for PydanticAI extraction")
        
        # Get or create runner for the specified provider
        runner = self._get_runner(provider_name, model_name)
        
        # Generate response using PydanticAI
        result = runner.generate(
            prompt=prompt,
            system=system_prompt,
            response_model=model_class,
            temperature=0.1,
            max_tokens=model_config.max_output_tokens
        )
        
        # Get usage stats from result
        usage = getattr(result, "_usage", None)
        if not usage:
            self.logger.warning("No usage information available from PydanticAI")
            
            # Create dummy usage data
            usage_data = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        else:
            # Parse usage data from PydanticAI
            usage_data = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        
        # Convert result to JSON string
        try:
            if hasattr(result, "model_dump"):
                # Pydantic v2
                result_dict = result.model_dump()
            else:
                # Pydantic v1
                result_dict = result.dict()
                
            response_text = json.dumps(result_dict, indent=2)
        except Exception as e:
            self.logger.error(f"Error converting result to JSON: {str(e)}")
            # Fall back to string representation
            response_text = str(result)
        
        return response_text, usage_data
        
    def get_response(self, prompt: str, source: str, model_name: Optional[str] = None,
                     model_class: Optional[Type[BaseModel]] = None) -> Tuple[str, UsageData]:
        """Override to handle model_class parameter"""
        # Store model_class in a frame local for _call_llm_api to access
        # This is needed because we can't modify the base class's get_response signature
        frame_locals = inspect.currentframe().f_locals
        
        # Create a test_case-like structure to pass the model_class
        if model_class:
            frame_locals['test_case'] = {'model_class': model_class}
            
        # Call parent implementation
        return super().get_response(prompt, source, model_name)