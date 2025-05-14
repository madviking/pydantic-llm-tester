"""
Base class for Prompt Providers in the Pydantic LLM Tester.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BasePromptProvider(ABC):
    """
    Base class for all prompt providers (sources).
    
    A Prompt Provider is responsible for retrieving and storing prompts from
    different backends (file system, database, API, etc.).
    
    It also supports versioning, performance tracking, and metadata management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize prompt provider with optional config.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    def get_prompt(self, prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get a prompt by ID and optional version.
        
        Args:
            prompt_id: Identifier for the prompt
            version: Optional version string (if None, gets the latest version)
            
        Returns:
            Tuple of (prompt_text, metadata)
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self, system_prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get a system prompt by ID and optional version.
        
        Args:
            system_prompt_id: Identifier for the system prompt
            version: Optional version string (if None, gets the latest version)
            
        Returns:
            Tuple of (system_prompt_text, metadata)
        """
        pass
    
    @abstractmethod
    def list_prompts(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List available prompts with metadata.
        
        Args:
            filter_params: Optional parameters to filter the returned prompts
            
        Returns:
            List of prompt metadata dictionaries
        """
        pass
    
    @abstractmethod
    def save_prompt(self, prompt_id: str, prompt_text: str, metadata: Dict[str, Any]) -> str:
        """
        Save a prompt with metadata.
        
        Args:
            prompt_id: Identifier for the prompt
            prompt_text: The prompt content
            metadata: Additional metadata for the prompt
            
        Returns:
            Version identifier of the saved prompt
        """
        pass
    
    @abstractmethod
    def record_performance(self, prompt_id: str, version: str, 
                           performance_data: Dict[str, Any]) -> bool:
        """
        Record performance metrics for a prompt version.
        
        Args:
            prompt_id: Identifier for the prompt
            version: Version string
            performance_data: Performance metrics data
            
        Returns:
            Success status (True if successfully recorded)
        """
        pass
    
    @abstractmethod
    def get_performance_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        Get performance history for a prompt across versions.
        
        Args:
            prompt_id: Identifier for the prompt
            
        Returns:
            List of performance records with version info
        """
        pass
    
    @abstractmethod
    def get_best_performing_version(self, prompt_id: str, 
                                   metric: str = "accuracy") -> Optional[str]:
        """
        Get the best performing version of a prompt based on a metric.
        
        Args:
            prompt_id: Identifier for the prompt
            metric: The metric to use for comparison (default: "accuracy")
            
        Returns:
            Version identifier or None if no data
        """
        pass