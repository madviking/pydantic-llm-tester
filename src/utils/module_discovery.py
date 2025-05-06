"""
Module discovery utilities for finding and loading test modules
"""

import os
import importlib
import inspect
import logging
from typing import List, Dict, Any, Optional, Type

from pydantic import BaseModel


class ModuleDiscovery:
    """
    Helper class for discovering and loading test modules
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the module discovery helper
        
        Args:
            base_dir: Base directory for the src package
        """
        self.logger = logging.getLogger(__name__)
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(__file__))
        self.models_dir = os.path.join(self.base_dir, "py_models")
        
        # Verify py_models directory exists
        if not os.path.exists(self.models_dir):
            self.logger.warning(f"Models directory not found: {self.models_dir}")
    
    def get_available_modules(self) -> List[str]:
        """
        Get list of available modules
        
        Returns:
            List of module names
        """
        if not os.path.exists(self.models_dir):
            return []
            
        # List all potential module directories
        modules = []
        for item in os.listdir(self.models_dir):
            item_path = os.path.join(self.models_dir, item)
            # Skip non-directories, hidden directories, and special files
            if not os.path.isdir(item_path) or item.startswith('__') or item.startswith('.'):
                continue
            
            # Check for model.py file
            model_file = os.path.join(item_path, "model.py")
            if not os.path.exists(model_file):
                self.logger.debug(f"Skipping directory {item} - no model.py file")
                continue
                
            modules.append(item)
            
        return modules
    
    def load_module_class(self, module_name: str) -> Optional[Type[BaseModel]]:
        """
        Load the model class for a module
        
        Args:
            module_name: Name of the module to load
            
        Returns:
            Model class or None if not found
        """
        try:
            # Try to import the module
            module_path = f"src.py_models.{module_name}"
            self.logger.debug(f"Importing module: {module_path}")
            module = importlib.import_module(module_path)
            
            # First try to find specific model classes by name
            # Standard naming patterns
            class_patterns = [
                # Direct naming matches
                module_name.replace('_', '').capitalize(),  # jobads
                ''.join(word.capitalize() for word in module_name.split('_')),  # JobAds
                # Common naming patterns
                f"{''.join(word.capitalize() for word in module_name.split('_'))}Model",  # JobAdsModel
                module_name.capitalize(),  # Jobads
                # Individual word patterns
                ''.join(word.capitalize() for word in module_name.split('_')) + 's',  # JobAds (if module is job_ad)
                module_name.split('_')[0].capitalize(),  # Job (if module is job_ad or job_ads)
                # Known specific names
                'JobAd' if module_name == 'job_ads' else None,
                'ProductDescription' if module_name == 'product_descriptions' else None
            ]
            
            # Try each pattern
            for pattern in class_patterns:
                if pattern and hasattr(module, pattern):
                    cls = getattr(module, pattern)
                    if inspect.isclass(cls) and issubclass(cls, BaseModel):
                        self.logger.debug(f"Found model class for {module_name}: {pattern}")
                        return cls
            
            # If no matching class found by name, find any BaseModel subclass
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                    self.logger.debug(f"Found BaseModel subclass for {module_name}: {name}")
                    return obj
            
            self.logger.warning(f"No model class found for module {module_name}")
            return None
            
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Error loading model for {module_name}: {str(e)}")
            return None
    
    def discover_modules_and_tests(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover all modules and their test cases
        
        Returns:
            Dictionary mapping module names to module information
        """
        modules_info = {}
        
        # Get available modules
        module_names = self.get_available_modules()
        
        # Load each module and get test cases
        for module_name in module_names:
            # Load the model class
            model_class = self.load_module_class(module_name)
            if not model_class:
                continue
                
            # Get module info
            module_info = {
                'name': module_name,
                'model_class': model_class,
                'test_cases': []
            }
            
            # Get test cases if the model class has the method
            if hasattr(model_class, 'get_test_cases'):
                try:
                    module_info['test_cases'] = model_class.get_test_cases()
                except Exception as e:
                    self.logger.error(f"Error getting test cases for module {module_name}: {str(e)}")
            
            modules_info[module_name] = module_info
            
        return modules_info
