"""
File-based Prompt Provider implementation.
"""

import json
import logging
import os
import re
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..base import BasePromptProvider


class FilePromptProvider(BasePromptProvider):
    """
    Provides prompts from the file system with versioning and performance tracking.
    
    This provider stores prompts in a directory structure:
    - Each prompt has its own directory named after the prompt_id
    - Versions are stored in a 'versions' subdirectory
    - Performance data is stored in a 'performance.json' file
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the file-based prompt provider.
        
        Args:
            config: Optional configuration dictionary with keys:
                - storage_path: Base path for prompt storage
                - version_retention: Maximum number of versions to keep
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Set up default config values
        self.storage_path = self.config.get('storage_path', self._get_default_storage_path())
        self.version_retention = self.config.get('version_retention', 10)
        
        # Set up path structure
        self.versions_dir = self.config.get('versions_dir', 'versions')
        self.metadata_suffix = self.config.get('metadata_suffix', '.meta.json')
        self.performance_file = self.config.get('performance_file', 'performance.json')
        self.index_file = self.config.get('index_file', 'index.json')
        self.system_prompts_dir = self.config.get('system_prompts_dir', 'system_prompts')
        
        # Ensure the storage path exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Ensure the system prompts directory exists
        os.makedirs(os.path.join(self.storage_path, self.system_prompts_dir), exist_ok=True)
        
        # Initialize the index if it doesn't exist
        index_path = os.path.join(self.storage_path, self.index_file)
        if not os.path.exists(index_path):
            with open(index_path, 'w') as f:
                json.dump({"prompts": {}, "system_prompts": {}}, f)
    
    def get_prompt(self, prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get a prompt by ID and optional version.
        
        Args:
            prompt_id: Identifier for the prompt
            version: Optional version string (if None, gets the latest version)
            
        Returns:
            Tuple of (prompt_text, metadata)
        """
        # Check if this is a path-based prompt ID (backward compatibility)
        if self._is_file_path(prompt_id):
            return self._get_prompt_from_path(prompt_id)
        
        # Get the prompt directory
        prompt_dir = self._get_prompt_dir(prompt_id)
        if not os.path.exists(prompt_dir):
            self.logger.warning(f"Prompt directory not found for '{prompt_id}': {prompt_dir}")
            return "", {}
        
        # Get the versions directory
        versions_dir = os.path.join(prompt_dir, self.versions_dir)
        if not os.path.exists(versions_dir):
            self.logger.warning(f"Versions directory not found for '{prompt_id}': {versions_dir}")
            return "", {}
        
        # Determine the target version
        target_version = version
        if target_version is None:
            # Get the latest version
            versions = self._get_versions(prompt_id)
            if not versions:
                self.logger.warning(f"No versions found for prompt '{prompt_id}'")
                return "", {}
            target_version = versions[-1]
        
        # Get the prompt file path
        prompt_path = os.path.join(versions_dir, f"{target_version}.txt")
        if not os.path.exists(prompt_path):
            self.logger.warning(f"Prompt file not found: {prompt_path}")
            return "", {}
        
        # Get the metadata file path
        metadata_path = os.path.join(versions_dir, f"{target_version}{self.metadata_suffix}")
        
        # Read the prompt text
        with open(prompt_path, 'r') as f:
            prompt_text = f.read()
        
        # Read the metadata if available
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Add version info to metadata if not present
        if 'version' not in metadata:
            metadata['version'] = target_version
        
        return prompt_text, metadata
    
    def get_system_prompt(self, system_prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get a system prompt by ID and optional version.
        
        Args:
            system_prompt_id: Identifier for the system prompt
            version: Optional version string (if None, gets the latest version)
            
        Returns:
            Tuple of (system_prompt_text, metadata)
        """
        # Check if this is a path-based system prompt ID (backward compatibility)
        if self._is_file_path(system_prompt_id):
            return self._get_prompt_from_path(system_prompt_id)
        
        # Get the system prompts directory
        system_dir = os.path.join(self.storage_path, self.system_prompts_dir)
        
        # Check for a direct file match
        direct_path = os.path.join(system_dir, f"{system_prompt_id}.txt")
        if os.path.exists(direct_path):
            with open(direct_path, 'r') as f:
                system_prompt = f.read()
                
            # Look for metadata
            metadata_path = os.path.join(system_dir, f"{system_prompt_id}{self.metadata_suffix}")
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            return system_prompt, metadata
        
        # Check if there's a versioned system prompt structure
        prompt_dir = os.path.join(system_dir, system_prompt_id)
        if os.path.exists(prompt_dir):
            versions_dir = os.path.join(prompt_dir, self.versions_dir)
            if os.path.exists(versions_dir):
                # Handle it like a regular versioned prompt
                target_version = version
                if target_version is None:
                    # Get the latest version
                    versions = self._get_versions_in_dir(versions_dir)
                    if not versions:
                        self.logger.warning(f"No versions found for system prompt '{system_prompt_id}'")
                        return "", {}
                    target_version = versions[-1]
                
                # Get the paths
                prompt_path = os.path.join(versions_dir, f"{target_version}.txt")
                metadata_path = os.path.join(versions_dir, f"{target_version}{self.metadata_suffix}")
                
                # Read the prompt
                if os.path.exists(prompt_path):
                    with open(prompt_path, 'r') as f:
                        system_prompt = f.read()
                    
                    # Read metadata if available
                    metadata = {}
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    
                    return system_prompt, metadata
        
        self.logger.warning(f"System prompt not found for ID: {system_prompt_id}")
        return "", {}
    
    def list_prompts(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List available prompts with metadata.
        
        Args:
            filter_params: Optional parameters to filter the returned prompts
                - type: 'regular' or 'system'
                - pattern: Regex pattern to match prompt IDs
            
        Returns:
            List of prompt metadata dictionaries
        """
        filter_params = filter_params or {}
        prompt_type = filter_params.get('type', 'regular')
        pattern = filter_params.get('pattern')
        
        # Compile the pattern if provided
        compiled_pattern = None
        if pattern:
            try:
                compiled_pattern = re.compile(pattern)
            except re.error:
                self.logger.warning(f"Invalid regex pattern: {pattern}")
        
        # Load the index file for more efficient listing
        index_path = os.path.join(self.storage_path, self.index_file)
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    index = json.load(f)
                
                if prompt_type == 'system':
                    prompts_dict = index.get('system_prompts', {})
                else:
                    prompts_dict = index.get('prompts', {})
                
                # Convert to list and filter by pattern if needed
                prompt_list = []
                for prompt_id, metadata in prompts_dict.items():
                    if compiled_pattern and not compiled_pattern.search(prompt_id):
                        continue
                    
                    prompt_list.append({
                        'id': prompt_id,
                        **metadata
                    })
                
                return prompt_list
            
            except Exception as e:
                self.logger.error(f"Error reading index file: {e}")
        
        # Fallback to directory scanning if index is unavailable
        prompt_list = []
        
        if prompt_type == 'system':
            # List system prompts
            system_dir = os.path.join(self.storage_path, self.system_prompts_dir)
            if os.path.exists(system_dir):
                # List direct files first
                for filename in os.listdir(system_dir):
                    if filename.endswith('.txt') and not filename.startswith('.'):
                        prompt_id = filename[:-4]  # Remove .txt
                        
                        if compiled_pattern and not compiled_pattern.search(prompt_id):
                            continue
                        
                        metadata_path = os.path.join(system_dir, f"{prompt_id}{self.metadata_suffix}")
                        metadata = {}
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                        
                        prompt_list.append({
                            'id': prompt_id,
                            'type': 'system',
                            **metadata
                        })
                
                # List directories for versioned system prompts
                for dirname in os.listdir(system_dir):
                    dir_path = os.path.join(system_dir, dirname)
                    if os.path.isdir(dir_path) and not dirname.startswith('.'):
                        if compiled_pattern and not compiled_pattern.search(dirname):
                            continue
                        
                        prompt_list.append({
                            'id': dirname,
                            'type': 'system',
                            'versioned': True
                        })
        
        else:
            # List regular prompts
            for prompt_id in os.listdir(self.storage_path):
                dir_path = os.path.join(self.storage_path, prompt_id)
                
                # Skip non-directories, system prompts dir, and hidden files
                if not os.path.isdir(dir_path) or prompt_id == self.system_prompts_dir or prompt_id.startswith('.'):
                    continue
                
                if compiled_pattern and not compiled_pattern.search(prompt_id):
                    continue
                
                # Check if it has a versions directory
                versions_dir = os.path.join(dir_path, self.versions_dir)
                if os.path.exists(versions_dir):
                    # Get the latest version
                    versions = self._get_versions_in_dir(versions_dir)
                    
                    if versions:
                        latest_version = versions[-1]
                        metadata_path = os.path.join(versions_dir, f"{latest_version}{self.metadata_suffix}")
                        
                        metadata = {
                            'latest_version': latest_version,
                            'versions_count': len(versions)
                        }
                        
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata.update(json.load(f))
                        
                        prompt_list.append({
                            'id': prompt_id,
                            'type': 'regular',
                            **metadata
                        })
        
        return prompt_list
    
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
        # Ensure prompt directory exists
        prompt_dir = self._get_prompt_dir(prompt_id)
        os.makedirs(prompt_dir, exist_ok=True)
        
        # Ensure versions directory exists
        versions_dir = os.path.join(prompt_dir, self.versions_dir)
        os.makedirs(versions_dir, exist_ok=True)
        
        # Generate a new version identifier
        version = self._generate_version()
        
        # Save the prompt text
        prompt_path = os.path.join(versions_dir, f"{version}.txt")
        with open(prompt_path, 'w') as f:
            f.write(prompt_text)
        
        # Update metadata with version info and timestamp
        updated_metadata = {
            **metadata,
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'size': len(prompt_text)
        }
        
        # Save the metadata
        metadata_path = os.path.join(versions_dir, f"{version}{self.metadata_suffix}")
        with open(metadata_path, 'w') as f:
            json.dump(updated_metadata, f, indent=2)
        
        # Update the index
        self._update_index(prompt_id, updated_metadata)
        
        # Prune old versions if needed
        self._prune_versions(prompt_id)
        
        return version
    
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
        # Ensure prompt directory exists
        prompt_dir = self._get_prompt_dir(prompt_id)
        if not os.path.exists(prompt_dir):
            self.logger.warning(f"Prompt directory not found: {prompt_dir}")
            return False
        
        # Get the performance file path
        performance_path = os.path.join(prompt_dir, self.performance_file)
        
        # Load existing performance data
        performance_history = []
        if os.path.exists(performance_path):
            with open(performance_path, 'r') as f:
                try:
                    performance_history = json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in performance file: {performance_path}")
                    performance_history = []
        
        # Update performance data with version and timestamp
        updated_performance = {
            **performance_data,
            'version': version,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if we already have data for this version
        for i, entry in enumerate(performance_history):
            if entry.get('version') == version:
                # Update existing entry
                performance_history[i] = updated_performance
                break
        else:
            # Add new entry
            performance_history.append(updated_performance)
        
        # Save the updated performance history
        with open(performance_path, 'w') as f:
            json.dump(performance_history, f, indent=2)
        
        return True
    
    def get_performance_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        Get performance history for a prompt across versions.
        
        Args:
            prompt_id: Identifier for the prompt
            
        Returns:
            List of performance records with version info
        """
        # Get the performance file path
        prompt_dir = self._get_prompt_dir(prompt_id)
        performance_path = os.path.join(prompt_dir, self.performance_file)
        
        # Check if the file exists
        if not os.path.exists(performance_path):
            return []
        
        # Load the performance data
        try:
            with open(performance_path, 'r') as f:
                performance_history = json.load(f)
            
            # Sort by timestamp
            performance_history.sort(key=lambda x: x.get('timestamp', ''))
            
            return performance_history
        
        except Exception as e:
            self.logger.error(f"Error loading performance data for '{prompt_id}': {e}")
            return []
    
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
        # Get performance history
        performance_history = self.get_performance_history(prompt_id)
        
        if not performance_history:
            return None
        
        # Find the entry with the highest metric value
        best_entry = None
        best_value = -float('inf')
        
        for entry in performance_history:
            if metric in entry:
                value = entry[metric]
                if value > best_value:
                    best_value = value
                    best_entry = entry
        
        # Return the version if found
        if best_entry:
            return best_entry.get('version')
        
        return None
    
    # Helper methods
    
    def _get_default_storage_path(self) -> str:
        """Get the default storage path for prompts."""
        # Default is in the same directory as this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, 'prompt_storage')
    
    def _get_prompt_dir(self, prompt_id: str) -> str:
        """Get the directory path for a prompt."""
        return os.path.join(self.storage_path, prompt_id)
    
    def _generate_version(self) -> str:
        """Generate a new version identifier."""
        # Use a timestamp-based version
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"v{timestamp}"
    
    def _get_versions(self, prompt_id: str) -> List[str]:
        """Get all versions for a prompt, sorted by version string."""
        versions_dir = os.path.join(self._get_prompt_dir(prompt_id), self.versions_dir)
        return self._get_versions_in_dir(versions_dir)
    
    def _get_versions_in_dir(self, versions_dir: str) -> List[str]:
        """Get all versions in a directory, sorted by version string."""
        if not os.path.exists(versions_dir):
            return []
        
        # Get all version files
        versions = []
        for filename in os.listdir(versions_dir):
            if filename.endswith('.txt') and not filename.startswith('.'):
                # Remove .txt extension
                version = filename[:-4]
                versions.append(version)
        
        # Sort versions (assuming v{timestamp} format)
        versions.sort()
        
        return versions
    
    def _prune_versions(self, prompt_id: str) -> None:
        """
        Prune old versions to stay within the version retention limit.
        
        Args:
            prompt_id: Identifier for the prompt
        """
        if self.version_retention <= 0:
            return  # No limit
        
        # Get all versions
        versions = self._get_versions(prompt_id)
        
        # If we have more versions than the limit, delete the oldest ones
        if len(versions) > self.version_retention:
            versions_dir = os.path.join(self._get_prompt_dir(prompt_id), self.versions_dir)
            versions_to_delete = versions[:-self.version_retention]
            
            for version in versions_to_delete:
                prompt_path = os.path.join(versions_dir, f"{version}.txt")
                metadata_path = os.path.join(versions_dir, f"{version}{self.metadata_suffix}")
                
                # Delete the files
                if os.path.exists(prompt_path):
                    os.remove(prompt_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
    
    def _update_index(self, prompt_id: str, metadata: Dict[str, Any], 
                     prompt_type: str = 'regular') -> None:
        """
        Update the index file with prompt metadata.
        
        Args:
            prompt_id: Identifier for the prompt
            metadata: Metadata to add to the index
            prompt_type: Type of prompt ('regular' or 'system')
        """
        index_path = os.path.join(self.storage_path, self.index_file)
        
        # Load existing index
        index = {"prompts": {}, "system_prompts": {}}
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    index = json.load(f)
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON in index file: {index_path}")
        
        # Update the index
        if prompt_type == 'system':
            target_dict = index.setdefault('system_prompts', {})
        else:
            target_dict = index.setdefault('prompts', {})
        
        # Extract a subset of metadata for the index
        index_metadata = {
            'version': metadata.get('version', 'unknown'),
            'timestamp': metadata.get('timestamp', datetime.now().isoformat()),
            'description': metadata.get('description', '')
        }
        
        target_dict[prompt_id] = index_metadata
        
        # Save the updated index
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
    
    def _is_file_path(self, path: str) -> bool:
        """Check if a string looks like a file path."""
        return '/' in path or '\\' in path
    
    def _get_prompt_from_path(self, path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get a prompt from a file path (backward compatibility).
        
        Args:
            path: File path to the prompt
            
        Returns:
            Tuple of (prompt_text, metadata)
        """
        # Check if the file exists
        if not os.path.exists(path):
            self.logger.warning(f"Prompt file not found: {path}")
            return "", {}
        
        # Read the prompt text
        with open(path, 'r') as f:
            prompt_text = f.read()
        
        # Create basic metadata
        metadata = {
            'path': path,
            'filename': os.path.basename(path),
            'legacy': True,
            'timestamp': datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        }
        
        return prompt_text, metadata