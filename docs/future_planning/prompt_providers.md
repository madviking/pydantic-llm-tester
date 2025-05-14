# Prompt Providers Improvement Proposal

## Overview

This document outlines a proposed enhancement to the Pydantic LLM Tester framework to introduce a standardized "Prompt Providers" system. This system would create an abstraction layer for prompt sources, while also providing comprehensive facilities for prompt improvement, versioning, performance tracking, and optimization.

## Background and Motivation

Currently, the framework handles prompts exclusively through the file system:
- Prompts are stored in the `src/pydantic_llm_tester/py_models/<model_name>/tests/prompts/` directory
- The `prompt_optimizer.py` utility can create optimized versions of these prompts in an `optimized/` subdirectory
- Each provider has a default system prompt in its `config.json`

This approach has several limitations:
- No support for retrieving prompts from databases or APIs
- Limited tracking of prompt performance and improvement history
- No structured way to compare different prompt versions
- Difficult to correlate prompt changes with extraction accuracy improvements
- No centralized management of prompts across different extraction tasks

The proposed Prompt Providers system would address these limitations by creating a comprehensive prompt management solution that supports different storage backends while focusing on prompt improvement and performance tracking.

## Design Principles

The Prompt Providers system should follow the same core design principles as the rest of the framework:

1. **Modularity and Extensibility**: Support for multiple backend types and easy extension
2. **Clean Separation of Concerns**: Clear distinction between storage, optimization, and performance tracking
3. **Consistent Interfaces**: Standardized interfaces regardless of backend
4. **Configuration Over Coding**: Provider behavior driven by configuration files
5. **Performance Tracking**: Built-in support for tracking and comparing prompt performance

## Architecture

### Key Components

#### 1. Base Prompt Provider Class

```python
class BasePromptProvider(ABC):
    """Base class for all prompt providers (sources)"""
    
    def __init__(self, config=None):
        """Initialize prompt provider with optional config"""
        
    @abstractmethod
    def get_prompt(self, prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get a prompt by ID and optional version
        Returns: (prompt_text, metadata)
        """
        
    @abstractmethod
    def get_system_prompt(self, system_prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get a system prompt by ID and optional version
        Returns: (system_prompt_text, metadata)
        """
        
    @abstractmethod
    def list_prompts(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List available prompts with metadata
        Returns: List of prompt metadata dictionaries
        """
        
    @abstractmethod
    def save_prompt(self, prompt_id: str, prompt_text: str, metadata: Dict[str, Any]) -> str:
        """
        Save a prompt with metadata
        Returns: Version identifier of the saved prompt
        """
        
    @abstractmethod
    def record_performance(self, prompt_id: str, version: str, 
                           performance_data: Dict[str, Any]) -> bool:
        """
        Record performance metrics for a prompt version
        Returns: Success status
        """
        
    @abstractmethod
    def get_performance_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        Get performance history for a prompt across versions
        Returns: List of performance records with version info
        """
        
    @abstractmethod
    def get_best_performing_version(self, prompt_id: str, 
                                    metric: str = "accuracy") -> Optional[str]:
        """
        Get the best performing version of a prompt based on a metric
        Returns: Version identifier or None if no data
        """
```

#### 2. File-Based Prompt Provider

```python
class FilePromptProvider(BasePromptProvider):
    """Provides prompts from the file system with versioning and performance tracking"""
    
    def get_prompt(self, prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Get a prompt from a file, with version support"""
        
    def get_system_prompt(self, system_prompt_id: str, version: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Get a system prompt from a file or config"""
        
    def list_prompts(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List prompts from the file system with metadata"""
        
    def save_prompt(self, prompt_id: str, prompt_text: str, metadata: Dict[str, Any]) -> str:
        """Save a prompt to the file system with versioning"""
        
    def record_performance(self, prompt_id: str, version: str, 
                          performance_data: Dict[str, Any]) -> bool:
        """Record performance metrics in a JSON file"""
        
    def get_performance_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get performance history from performance tracking files"""
        
    def get_best_performing_version(self, prompt_id: str, 
                                   metric: str = "accuracy") -> Optional[str]:
        """Determine best version based on tracked performance"""
```

#### 3. Prompt Optimizer

Enhanced version of the existing optimizer with integration to prompt providers:

```python
class PromptOptimizer:
    """Optimizes prompts based on test results and manages improvement cycles"""
    
    def __init__(self, prompt_provider: BasePromptProvider):
        """Initialize with a prompt provider"""
        
    def optimize_prompt(self, prompt_id: str, source: str, model_class: Any, 
                       expected_data: Dict[str, Any], test_results: Dict[str, Any],
                       optimization_strategy: str = "auto") -> Tuple[str, Dict[str, Any]]:
        """
        Optimize a prompt based on test results
        Returns: (optimized_prompt_text, optimization_metadata)
        """
        
    def save_optimized_prompt(self, prompt_id: str, optimized_text: str, 
                             optimization_metadata: Dict[str, Any]) -> str:
        """
        Save an optimized prompt through the prompt provider
        Returns: Version identifier of the saved prompt
        """
        
    def compare_prompt_versions(self, prompt_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two versions of a prompt
        Returns: Comparison data
        """
```

#### 4. Performance Tracker

New component for tracking and analyzing prompt performance:

```python
class PerformanceTracker:
    """Tracks and analyzes prompt performance"""
    
    def __init__(self, prompt_provider: BasePromptProvider):
        """Initialize with a prompt provider"""
        
    def record_test_results(self, prompt_id: str, version: str, 
                           test_results: Dict[str, Any]) -> bool:
        """
        Record test results for a prompt version
        Returns: Success status
        """
        
    def analyze_performance_trends(self, prompt_id: str) -> Dict[str, Any]:
        """
        Analyze performance trends across versions
        Returns: Analysis data
        """
        
    def generate_performance_report(self, prompt_id: str) -> str:
        """
        Generate a detailed performance report
        Returns: Markdown formatted report
        """
```

#### 5. Prompt Manager

High-level manager that ties everything together:

```python
class PromptManager:
    """Manages prompt providers, optimization, and performance tracking"""
    
    def __init__(self, provider_type: str = "file", config: Dict[str, Any] = None):
        """Initialize with provider type and config"""
        
    def get_prompt(self, prompt_id: str, version: Optional[str] = None, 
                  use_best_performing: bool = False) -> Tuple[str, Dict[str, Any]]:
        """
        Get a prompt by ID, version, or best performing
        Returns: (prompt_text, metadata)
        """
        
    def get_system_prompt(self, system_prompt_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get a system prompt by ID
        Returns: (system_prompt_text, metadata)
        """
        
    def save_prompt(self, prompt_id: str, prompt_text: str, 
                   metadata: Dict[str, Any]) -> str:
        """
        Save a prompt
        Returns: Version identifier
        """
        
    def optimize_and_save(self, prompt_id: str, source: str, model_class: Any,
                         expected_data: Dict[str, Any], test_results: Dict[str, Any]) -> str:
        """
        Optimize a prompt based on test results and save it
        Returns: Version identifier of the optimized prompt
        """
        
    def record_test_results(self, prompt_id: str, version: str, 
                           test_results: Dict[str, Any]) -> bool:
        """
        Record test results for a prompt version
        Returns: Success status
        """
        
    def compare_versions(self, prompt_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two versions of a prompt
        Returns: Comparison data
        """
        
    def get_performance_report(self, prompt_id: str) -> str:
        """
        Generate a performance report
        Returns: Markdown formatted report
        """
```

### Directory Structure

```
src/pydantic_llm_tester/
└── prompt_providers/
    ├── __init__.py
    ├── base.py                  # BasePromptProvider
    ├── prompt_factory.py        # Factory for creating providers
    ├── prompt_manager.py        # High-level management
    ├── optimizer.py             # Enhanced prompt optimizer
    ├── performance_tracker.py   # Performance tracking
    │
    ├── file/                    # File-based provider
    │   ├── __init__.py
    │   ├── config.json
    │   └── provider.py
    │
    ├── database/                # Future: Database provider
    │   ├── __init__.py
    │   ├── config.json
    │   └── provider.py
    │
    └── api/                     # Future: API provider
        ├── __init__.py
        ├── config.json
        └── provider.py
```

#### File-Based Provider Directory Structure

For the file-based provider, a structured approach might look like:

```
prompt_storage/
├── <prompt_id>/                 # Directory for each prompt
│   ├── versions/
│   │   ├── v1.txt               # Original prompt
│   │   ├── v1.meta.json         # Metadata for v1
│   │   ├── v2.txt               # Optimized version
│   │   └── v2.meta.json         # Metadata for v2
│   └── performance.json         # Performance tracking
├── system_prompts/
│   ├── default.txt
│   ├── openai_gpt4.txt
│   └── anthropic_claude.txt
└── index.json                   # Prompt index with metadata
```

### Configuration

The system would be configured through:

1. Global configuration in `pyllm_config.json`:
   ```json
   {
     "prompt_providers": {
       "provider_type": "file",
       "storage_path": "custom/path/to/prompts",
       "performance_tracking": true,
       "auto_optimize": true,
       "version_retention": 10
     }
   }
   ```

2. Provider-specific configuration in each provider's `config.json`:
   ```json
   {
     "name": "file",
     "provider_type": "file",
     "version": "1.0.0",
     "description": "File-based prompt provider",
     "storage_structure": {
       "versions_dir": "versions",
       "metadata_suffix": ".meta.json",
       "performance_file": "performance.json",
       "index_file": "index.json"
     },
     "optimization": {
       "save_optimization_steps": true,
       "max_optimization_iterations": 3
     }
   }
   ```

## Integration with Existing System

The Prompt Providers system would be integrated with the existing framework:

1. **LLMTester Integration**:
   - Add a `prompt_manager` property to the `LLMTester` class
   - Extend `run_test()` to use the prompt manager
   - Add automatic performance recording after tests
   - Support for using best-performing prompts automatically

2. **CLI Integration**:
   - Add a comprehensive prompt management command group:
     - `llm-tester prompts list [--filter <params>]`
     - `llm-tester prompts show <id> [--version <v>]`
     - `llm-tester prompts save <id> --text "prompt text" [--metadata <json>]`
     - `llm-tester prompts optimize <id> --results <results_file> [--strategy <strategy>]`
     - `llm-tester prompts performance <id> [--format <json|md>]`
     - `llm-tester prompts compare <id> --v1 <version1> --v2 <version2>`

3. **Reporting Integration**:
   - Include prompt performance data in test reports
   - Add prompt improvement metrics
   - Create dedicated prompt performance reports

## Implementation Plan

### Phase 1: Core Structure and File Provider

1. Design and implement the core interfaces:
   - `BasePromptProvider`
   - `prompt_factory.py`
   - `PromptManager` (basic functionality)

2. Implement the `FilePromptProvider`:
   - Basic prompt storage and retrieval
   - Simple versioning system
   - Performance data storage

3. Integrate with the existing system:
   - Ensure backward compatibility with current file paths
   - Add basic CLI commands
   - Modify `LLMTester` to use the prompt manager

### Phase 2: Optimization and Performance Tracking

1. Enhance the `PromptOptimizer`:
   - Integrate with prompt providers
   - Improve optimization strategies
   - Support for saving optimization history

2. Implement the `PerformanceTracker`:
   - Record test results by prompt version
   - Calculate performance metrics
   - Generate performance reports

3. Extend `PromptManager` with optimization and tracking features:
   - Methods for optimizing and tracking in one step
   - Support for best-performing prompt selection
   - Comparison utilities

### Phase 3: Advanced Features and Additional Providers

1. Add advanced prompt management features:
   - A/B testing of prompt versions
   - Automated improvement cycles
   - Performance visualization

2. Implement additional providers:
   - `DatabasePromptProvider`
   - `APIPromptProvider`

3. Complete CLI integration:
   - Full command set for all features
   - Interactive prompt management

## Benefits

The Prompt Providers system offers several significant benefits:

1. **Structured Prompt Management**: Organized approach to storing and retrieving prompts
2. **Performance Improvement**: Track prompt effectiveness and optimize automatically
3. **Versioning and History**: Keep a history of prompt evolution and improvements
4. **Backend Flexibility**: Store prompts in files, databases, or retrieve from APIs
5. **Integrated Optimization**: Built-in tools for improving prompts based on test results
6. **Data-Driven Decisions**: Make decisions about prompt strategies based on performance data

## Backward Compatibility

The implementation will maintain backward compatibility with the existing approach:
- The `FilePromptProvider` will support existing prompt file paths
- `PromptManager` will provide a compatible interface for existing code
- Performance tracking can be optionally enabled

## Future Possibilities

Once the core system is implemented, several advanced features could be considered:

1. **AI-Driven Prompt Optimization**: Using LLMs to generate and refine prompts automatically
2. **Collaborative Prompt Management**: Multi-user interface for team prompt development
3. **Prompt Templates**: Parameterized templates with variable substitution
4. **Advanced Analytics**: Statistical analysis of prompt performance patterns
5. **Integration with External Tools**: Connecting with specialized prompt engineering tools

## Conclusion

The Prompt Providers system represents a significant enhancement to the Pydantic LLM Tester framework, providing a comprehensive solution for prompt management, optimization, and performance tracking. By implementing this system, we can significantly improve the framework's capabilities for structured data extraction by systematically optimizing prompts based on real performance data while supporting flexible storage options.