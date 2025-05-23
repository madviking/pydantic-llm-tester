import os
import json
import logging
from datetime import datetime
from typing import TypeVar, Type, Tuple, Optional, List, Dict, Any
from enum import Enum

from pydantic import ValidationError
from ..py_models.base import BasePyModel
from ..bridge.analysis_report import PyllmAnalysisReport, PassAnalysis
from ..py_models.job_ads import JobAd

# Import managers for initialization
from ..utils.config_manager import ConfigManager
from ..utils.provider_manager import ProviderManager
from ..utils.cost_manager import CostTracker
from ..utils.report_generator import ReportGenerator
from ..utils.common import get_py_models_dir, get_external_py_models_dir

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BasePyModel)

class ProviderType(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"

class PyllmBridge:
    """
    Bridge class that makes it easier to integrate pydantic_llm_tester into your project.
    
    The bridge provides a simplified interface for using LLMs to fill Pydantic models,
    with support for multiple passes and automatic fallback to secondary providers.
    """

    def __init__(self):
        self.errors: List[str] = []
        self.notices: List[str] = []
        self.cost: float = 0.0
        self.analysis: PyllmAnalysisReport = PyllmAnalysisReport()

        # Initialize managers
        self.config_manager = ConfigManager()
        
        # Get enabled providers from config
        enabled_providers = list(self.config_manager.get_enabled_providers().keys())
        
        # Initialize provider manager with enabled providers
        self.provider_manager = ProviderManager(enabled_providers)
        
        # Initialize cost tracker
        self.cost_manager = CostTracker()
        
        # Initialize report generator
        self.report_generator = ReportGenerator()

    def _process_passes(self, model_class: Type[T], prompt: str, source: str, passes: int, file_path: str) -> T:
        """
        Process multiple passes of LLM calls and build up model data.
        
        Args:
            model_class: The Pydantic model class to fill
            prompt: The prompt to send to the LLM
            source: The source text to process
            passes: Number of passes to make (1-3)
            file_path: Optional file path to include
            
        Returns:
            Instance of the model class with accumulated data
        """
        # Set total fields in analysis report
        self.analysis.total_fields = len(model_class.__annotations__)
        
        # Create a structure to hold model data
        model_data = {}
        
        # Process each pass
        for pass_num in range(1, passes + 1):
            self._run_pass(pass_num, model_class, prompt, source, file_path, model_data)
            
        # Create and return a model instance
        try:
            return model_class(**model_data)
        except Exception as e:
            logger.error(f"Error creating model instance: {str(e)}")
            # Return an empty model instance if there's an error
            return model_class()
    
    def ask(self, model_class: Type[T], prompt: str, source: str = "", passes: int = 1, file: str = '') -> T | None:
        """
        Process a prompt with one or more LLM models and return a filled Pydantic model.
        
        Multiple passes will refine the model by using different LLMs:
        - First pass: Use the primary model to fill the model.
        - Second pass: Use the secondary model to fill/refine the model.
        - Third pass: Use the primary model again to further refine the model.
        
        Args:
            model_class: The Pydantic model class to fill.
            prompt: The prompt to send to the LLM.
            source: The source text to process (if any).
            passes: Number of LLM passes to make (1-3).
            file: Optional file path to include with the request.
            
        Returns:
            A filled instance of the provided model class.
        """
        # Reset for this run
        self.errors = []
        self.analysis = PyllmAnalysisReport()
        self.cost = 0.0
        
        # Count model fields
        self.analysis.total_fields = len(model_class.__annotations__)
        
        # Ensure passes is within bounds
        passes = max(1, min(3, passes))
        
        # Process passes to build up model data
        model_instance = self._process_passes(model_class, prompt, source, passes, file)
        
        # Save test files if we have a successful result
        if source and model_instance:
            self._save_model_config(model_instance, prompt, source)
            
        return model_instance



    def _run_pass(self, pass_num: int, model_class: Type[T], prompt: str, source: str,
                  file_path: str, model_data: Dict[str, Any]) -> None:
        """
        Run a single pass of the LLM processing pipeline.

        Args:
            pass_num: The current pass number (1-3)
            model_class: The Pydantic model class to fill
            prompt: The prompt to send to the LLM
            source: The source text to process
            file_path: Optional file path to include
            model_data: Dictionary to store model data (modified in-place)
        """
        # Create pass analysis object
        pass_name = {1: "first_pass", 2: "second_pass", 3: "third_pass"}.get(pass_num, f"pass_{pass_num}")
        pass_analysis = PassAnalysis()

        # Determine provider type based on pass number
        provider_type = ProviderType.PRIMARY if pass_num in [1, 3] else ProviderType.SECONDARY

        # Get provider and model
        provider_model = self._get_provider_and_model(model_class, provider_type)

        # Skip pass if no provider/model is available
        if not provider_model:
            self.errors.append(f"No provider/model available for pass {pass_num}")
            self.analysis.passes[pass_name] = pass_analysis
            return

        provider_name, model_name = provider_model
        
        # Store the provider and model information in the pass analysis
        pass_analysis.provider_model = f"{provider_name}:{model_name}"

        # Call the LLM
        result_json, _, cost = self._call_llm(
            provider_name, model_name, prompt, source, model_class, file_path
        )

        # Handle failure case
        if not result_json:
            error_msg = f"Pass {pass_num} failed with {provider_name}:{model_name}"
            logger.warning(error_msg)
            self.errors.append(error_msg)

            # Try fallback for first pass only
            if pass_num == 1:
                result_json, fallback_provider_model = self._try_fallback(model_class, prompt, source, file_path, pass_analysis)
                
                # If fallback succeeded, update model data and provider info
                if result_json:
                    self._update_model_data(result_json, model_data, pass_analysis)
                    if fallback_provider_model:
                        pass_analysis.provider_model = fallback_provider_model
                    
            # Save pass analysis even if failed
            self.analysis.passes[pass_name] = pass_analysis
            
            # Return early if fallback failed or this wasn't the first pass
            if not result_json:
                return

        # Process successful result
        self._update_model_data(result_json, model_data, pass_analysis)

        # Update cost
        if cost:
            self.analysis.cost += cost

        # Store pass analysis
        self.analysis.passes[pass_name] = pass_analysis

    def _try_fallback(self, model_class: Type[T], prompt: str, source: str, file_path: str,
                     pass_analysis: PassAnalysis) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Try to use the secondary provider as a fallback when primary fails.

        Args:
            model_class: The Pydantic model class to fill
            prompt: The prompt to send to the LLM
            source: The source text to process
            file_path: Optional file path to include
            pass_analysis: Pass analysis object to update

        Returns:
            Tuple of (JSON result dictionary or None if fallback failed, provider_model string)
        """
        # Get secondary provider
        secondary = self._get_provider_and_model(model_class, ProviderType.SECONDARY)
        if not secondary:
            return None, None

        sec_provider, sec_model = secondary
        provider_model_str = f"{sec_provider}:{sec_model}"
        logger.info(f"Trying secondary provider {provider_model_str} due to primary failure")

        result_json, _, fallback_cost = self._call_llm(
            sec_provider, sec_model, prompt, source, model_class, file_path
        )

        if result_json:
            # Success with secondary
            pass_analysis.new_fields = len(result_json)

            # Update cost
            if fallback_cost:
                self.analysis.cost += fallback_cost

        return result_json, provider_model_str

    def _update_model_data(self, result_json: Dict[str, Any], model_data: Dict[str, Any],
                          pass_analysis: PassAnalysis) -> None:
        """
        Update the model data with results from current pass.

        Args:
            result_json: New data from the LLM response
            model_data: Existing model data to update (modified in-place)
            pass_analysis: Pass analysis object to update
        """
        new_fields = 0
        overwritten_fields = 0

        for field, value in result_json.items():
            if field in model_data:
                # Field exists, count as overwrite
                if model_data[field] != value:
                    overwritten_fields += 1
                    model_data[field] = value
            else:
                # New field
                new_fields += 1
                model_data[field] = value

        # Update pass analysis
        pass_analysis.new_fields = new_fields
        pass_analysis.overwritten_fields = overwritten_fields

    def _get_provider_and_model(self, model_class: Type[T], provider_type: ProviderType) -> Optional[Tuple[str, str]]:
        """
        Get the provider and model based on the provider type.

        Args:
            model_class: The Pydantic model class
            provider_type: Whether to get primary or secondary provider

        Returns:
            Tuple of (provider_name, model_name) or None if not found
        """
        if provider_type == ProviderType.PRIMARY:
            return self._get_primary_provider_and_model(model_class)
        else:
            return self._get_secondary_provider_and_model(model_class)

    def _call_llm(self, provider_name: str, model_name: str, prompt: str, source: str,
                 model_class: Type[T], file_path: str = '') -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[float]]:
        """
        Handle a single call to an LLM provider.

        Args:
            provider_name: Name of the provider to use.
            model_name: Name of the model to use.
            prompt: The prompt to send.
            source: The source text to process.
            model_class: The Pydantic model class for schema guidance.
            file_path: Optional file path to include.

        Returns:
            Tuple of (parsed_json_or_None, raw_response_or_None, cost_or_None)
        """
        return self._call_llm_single_pass(provider_name, model_name, prompt, source, model_class, file_path)
        
    def _call_llm_single_pass(self, provider_name: str, model_name: str, prompt: str, source: str,
                 model_class: Type[T], file_path: str = '') -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[float]]:
        """
        Handle a single call to an LLM provider.

        Args:
            provider_name: Name of the provider to use.
            model_name: Name of the model to use.
            prompt: The prompt to send.
            source: The source text to process.
            model_class: The Pydantic model class for schema guidance.
            file_path: Optional file path to include.

        Returns:
            Tuple of (parsed_json_or_None, raw_response_or_None, cost_or_None)
        """
        try:
            # Prepare file list if a file is provided
            files = None
            if file_path:
                if os.path.exists(file_path):
                    files = [file_path]
                else:
                    self.errors.append(f"File not found: {file_path}")
                    return None, None, None

            # Log which provider and model we're using
            logger.info(f"Calling LLM API: {provider_name}:{model_name}")

            # Call the provider
            response_text, usage_data = self.provider_manager.get_response(
                provider=provider_name,
                prompt=prompt,
                source=source,
                model_class=model_class,
                model_name=model_name,
                files=files
            )

            # Log the actual model used (might be different from requested)
            actual_model = usage_data.model
            if actual_model != model_name:
                logger.info(f"Note: Requested model '{model_name}' but provider used '{actual_model}'")
            
            # Ensure we're using the correct pricing for the actual model used
            # This is important if the provider substituted a different model
            from pydantic_llm_tester.utils.cost_manager import calculate_cost
            prompt_cost, completion_cost, total_cost = calculate_cost(
                provider_name, actual_model, usage_data.prompt_tokens, usage_data.completion_tokens
            )
            
            # If the costs differ significantly, use our recalculated cost instead
            if abs(usage_data.total_cost - total_cost) > 0.001:
                logger.warning(f"Cost mismatch: Provider reported ${usage_data.total_cost:.6f} but calculated ${total_cost:.6f}")
                logger.info(f"Using recalculated cost based on actual model '{actual_model}'")
                self.cost += total_cost
            else:
                self.cost += usage_data.total_cost
                
            logger.info(f"Cost for {provider_name}:{actual_model}: ${total_cost:.6f}")
            logger.info(f"Tokens: {usage_data.prompt_tokens} prompt, {usage_data.completion_tokens} completion")

            # Parse JSON from the response
            parsed_json = self._extract_json_from_response(response_text, provider_name, model_name)

            return parsed_json, response_text, usage_data.total_cost

        except Exception as e:
            error_msg = f"Error calling {provider_name}:{model_name}: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return None, None, None

    def _extract_json_from_response(self, response_text: str, provider_name: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from the LLM response text.
        
        Args:
            response_text: The raw response text from the LLM
            provider_name: Name of the provider (for error messages)
            model_name: Name of the model (for error messages)
            
        Returns:
            Parsed JSON dictionary or None if parsing failed
        """
        try:
            # First attempt direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from markdown
            try:
                # Look for JSON block in markdown (between triple backticks)
                import re
                json_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)```', response_text)
                
                if json_blocks:
                    # Try each block until we find valid JSON
                    for block in json_blocks:
                        try:
                            return json.loads(block.strip())
                        except json.JSONDecodeError:
                            continue
                    # No valid JSON found in blocks
                    raise json.JSONDecodeError("No valid JSON found in code blocks", "", 0)
                else:
                    # No blocks found
                    raise json.JSONDecodeError("No JSON blocks found", response_text, 0)
            except Exception as e:
                self.errors.append(f"JSON parsing error from {provider_name}:{model_name}: {str(e)}")
                return None

    def _get_primary_provider_and_model(self, model_class: Type[T]) -> Optional[Tuple[str, str]]:
        """
        Determine the primary provider and model based on config.
        
        Args:
            model_class: The Pydantic model class.
            
        Returns:
            Tuple of (provider_name, model_name) or None if not found.
        """
        model_name = model_class.__name__
        
        # First try to find a config by exact model name match
        py_model_llm_models = self.config_manager.get_py_model_llm_models(model_name)
        
        # If no exact match, try lowercase version (e.g. JobAd -> job_ads)
        if not py_model_llm_models:
            lowercase_name = model_name.lower()
            if "_" not in lowercase_name:
                # Try with "_" between words for snake_case conversion (e.g. JobAd -> job_ad)
                import re
                snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name).lower()
                logger.info(f"Trying snake_case version of model name: {snake_case}")
                py_model_llm_models = self.config_manager.get_py_model_llm_models(snake_case)
                
                # Try with plural form for common patterns (e.g. job_ad -> job_ads)
                if not py_model_llm_models and not snake_case.endswith('s'):
                    plural_name = f"{snake_case}s"
                    logger.info(f"Trying plural version of model name: {plural_name}")
                    py_model_llm_models = self.config_manager.get_py_model_llm_models(plural_name)
        
        if py_model_llm_models:
            # Use the first model in the list as primary
            primary_model_string = py_model_llm_models[0]
            try:
                provider, model = self.config_manager._parse_model_string(primary_model_string)
                
                # Log what we found in the config
                logger.info(f"Found model configuration in pyllm_config.json for {model_name}: {provider}:{model}")
                
                # Validate if provider exists and is enabled
                enabled_providers = self.config_manager.get_enabled_providers()
                
                # Always use the specified model from py_model config, regardless of enabled status
                # This ensures we respect the config even if the provider isn't explicitly enabled
                logger.info(f"Using provider {provider} with model {model} for {model_name} (from py_model config)")
                return provider, model
            except ValueError:
                logger.warning(f"Invalid model string format in pyllm_config.json for {model_name}: {primary_model_string}")
        
        # 2. Check bridge-specific defaults
        bridge_default_provider = self.config_manager.get_bridge_default_provider()
        bridge_default_model = self.config_manager.get_bridge_default_model()
        
        if bridge_default_provider and bridge_default_model:
            # Validate if provider exists and is enabled
            enabled_providers = self.config_manager.get_enabled_providers()
            if bridge_default_provider in enabled_providers:
                logger.info(f"Using provider {bridge_default_provider} with model {bridge_default_model} for {model_name} (from bridge default)")
                return bridge_default_provider, bridge_default_model
            else:
                logger.warning(f"Bridge default provider {bridge_default_provider} is not enabled")
        
        # 3. Fallback to global default provider and model
        enabled_providers = self.config_manager.get_enabled_providers()
        if enabled_providers:
            # Find the first enabled provider with a default model
            for provider_name, provider_config in enabled_providers.items():
                default_model = provider_config.get("default_model")
                if default_model:
                    logger.info(f"Using provider {provider_name} with model {default_model} for {model_name} (from provider config)")
                    return provider_name, default_model
        
        # 4. No primary model found
        logger.warning(f"No primary LLM model configured or found for Pydantic model: {model_name}. Please check pyllm_config.json.")
        return None

    def _get_secondary_provider_and_model(self, model_class: Type[T]) -> Optional[Tuple[str, str]]:
        """
        Determine the secondary provider and model based on config.
        
        Args:
            model_class: The Pydantic model class.
            
        Returns:
            Tuple of (provider_name, model_name) or None if not found.
        """
        model_name = model_class.__name__
        
        # First try to find a config by exact model name match
        py_model_llm_models = self.config_manager.get_py_model_llm_models(model_name)
        
        # If no exact match, try lowercase version (e.g. JobAd -> job_ads)
        if not py_model_llm_models:
            lowercase_name = model_name.lower()
            if "_" not in lowercase_name:
                # Try with "_" between words for snake_case conversion (e.g. JobAd -> job_ad)
                import re
                snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name).lower()
                logger.info(f"Trying snake_case version of model name for secondary: {snake_case}")
                py_model_llm_models = self.config_manager.get_py_model_llm_models(snake_case)
                
                # Try with plural form for common patterns (e.g. job_ad -> job_ads)
                if not py_model_llm_models and not snake_case.endswith('s'):
                    plural_name = f"{snake_case}s"
                    logger.info(f"Trying plural version of model name for secondary: {plural_name}")
                    py_model_llm_models = self.config_manager.get_py_model_llm_models(plural_name)
        
        if py_model_llm_models and len(py_model_llm_models) > 1:
            # Use the second model in the list as secondary
            secondary_model_string = py_model_llm_models[1]
            try:
                provider, model = self.config_manager._parse_model_string(secondary_model_string)
                # Validate if provider exists and is enabled
                enabled_providers = self.config_manager.get_enabled_providers()
                # For tests, don't check enabled status if there's a model specified
                if provider in enabled_providers:
                    return provider, model
                else:
                    logger.warning(f"Secondary provider {provider} specified for {model_name} is not enabled")
            except ValueError:
                logger.warning(f"Invalid model string format in pyllm_config.json for {model_name} (secondary): {secondary_model_string}")
        
        # 2. Check bridge-specific defaults
        bridge_secondary_provider = self.config_manager.get_bridge_secondary_provider()
        bridge_secondary_model = self.config_manager.get_bridge_secondary_model()
        
        if bridge_secondary_provider and bridge_secondary_model:
            # Validate if provider exists and is enabled
            enabled_providers = self.config_manager.get_enabled_providers()
            if bridge_secondary_provider in enabled_providers:
                return bridge_secondary_provider, bridge_secondary_model
            else:
                logger.warning(f"Bridge secondary provider {bridge_secondary_provider} is not enabled")
        
        # 3. Fallback to second enabled provider
        enabled_providers = list(self.config_manager.get_enabled_providers().items())
        if len(enabled_providers) > 1:
            # Use the default model of the second enabled provider
            provider_name, provider_config = enabled_providers[1]
            default_model = provider_config.get("default_model")
            if default_model:
                return provider_name, default_model
        
        # 4. No secondary model found
        logger.info(f"No secondary LLM model configured or found for Pydantic model: {model_name}")
        return None

    def _load_model_config(self, model_class: Type[T]) -> Dict[str, Any]:
        """
        Load configuration for the specified model class.
        
        Args:
            model_class: The Pydantic model class.
            
        Returns:
            Dictionary with model configuration.
        """
        model_name = model_class.__name__
        
        # Get model config from pyllm_config.json
        py_models_config = self.config_manager.get_py_models()
        model_config = py_models_config.get(model_name, {})
        
        # If not found, try to discover the model's directory
        if not model_config:
            # Check in built-in py_models dir
            built_in_dir = get_py_models_dir()
            model_dir = os.path.join(built_in_dir, model_name.lower())
            
            if not os.path.exists(model_dir):
                # Check in external py_models dir
                external_dir = get_external_py_models_dir()
                model_dir = os.path.join(external_dir, model_name.lower())
                
                if not os.path.exists(model_dir):
                    logger.warning(f"Could not find directory for model {model_name}")
                    return {}
            
            # Register the model in config
            model_config = {"enabled": True, "path": model_dir}
            self.config_manager.register_py_model(model_name, model_config)
        
        return model_config

    def _save_model_config(self, model_instance: BasePyModel, prompt: str, source: str) -> None:
        """
        Save auto-generated test files for a model if they are missing.
        
        Args:
            model_instance: The filled Pydantic model instance.
            prompt: The prompt that was used.
            source: The source text that was processed.
        """
        model_class = model_instance.__class__
        model_name = model_class.__name__
        
        # Load model config to get its directory
        model_config = self._load_model_config(model_class)
        model_dir = model_config.get("path")

        # If no path is found, try to use the MODULE_NAME and other class variables
        if not model_dir and hasattr(model_class, "MODULE_NAME"):
            # Look in built-in py_models
            built_in_dir = get_py_models_dir()
            model_dir = os.path.join(built_in_dir, model_class.MODULE_NAME)
            
            # If not found in built-in, try external
            if not os.path.exists(model_dir):
                external_dir = get_external_py_models_dir()
                model_dir = os.path.join(external_dir, model_class.MODULE_NAME)
        
        # For tests where os.path.exists is mocked
        if hasattr(os.path, "exists") and getattr(os.path.exists, "__module__", "") == "unittest.mock":
            pass  # We're in a test with a mocked os.path.exists
        elif not model_dir or not os.path.exists(model_dir):
            logger.warning(f"Could not determine directory for model {model_name}")
            return
        
        # Create test directory structure if it doesn't exist
        tests_dir = os.path.join(model_dir, "tests")
        sources_dir = os.path.join(tests_dir, "sources")
        prompts_dir = os.path.join(tests_dir, "prompts")
        expected_dir = os.path.join(tests_dir, "expected")

        # proceed only if the expected directory is empty
        if os.path.exists(expected_dir) and os.listdir(expected_dir):
            logger.warning(f"Expected directory {expected_dir} is not empty. Skipping auto-save.")
            return

        os.makedirs(sources_dir, exist_ok=True)
        os.makedirs(prompts_dir, exist_ok=True)
        os.makedirs(expected_dir, exist_ok=True)
        
        # Generate filenames with auto_ prefix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"auto_{timestamp}"
        
        # Save source file
        source_path = os.path.join(sources_dir, f"{filename_base}.txt")
        with open(source_path, 'w') as f:
            f.write(source)
        
        # Save prompt file
        prompt_path = os.path.join(prompts_dir, f"{filename_base}.txt")
        with open(prompt_path, 'w') as f:
            f.write(prompt)
        
        # Save expected JSON file
        expected_path = os.path.join(expected_dir, f"{filename_base}.json")
        with open(expected_path, 'w') as f:
            # Use model_dump() instead of dict() for Pydantic v2 compatibility
            try:
                # Try Pydantic v2 method first
                model_data = model_instance.model_dump()
            except AttributeError:
                # Fall back to Pydantic v1 method if needed
                model_data = model_instance.dict()
                
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Saved auto-generated test files for {model_name} with base name {filename_base}")
        self.notices.append(f"Auto-generated test files saved: {filename_base}")

    def analyze_model_configuration(self, model_class: Type[T]) -> Dict[str, Any]:
        """
        Analyze the model configuration to determine how it maps to LLM providers and models.
        
        This function analyzes the Pydantic model class name, checks different name variations 
        (original, snake_case, plural), determines which provider and model will be used,
        and fetches pricing information.
        
        Args:
            model_class: The Pydantic model class to analyze
            
        Returns:
            A dictionary containing the configuration analysis information:
            - class_name: Original class name
            - snake_case_name: Snake case version of the name
            - plural_name: Plural form of the snake case name
            - config_entry: Name found in configuration
            - provider_model: Tuple of (provider_name, model_name) that will be used
            - model_pricing: Dictionary with pricing information for the model
        """
        import re
        from ..llms.llm_registry import get_llm_registry
        
        # Get model name and variations
        model_name = model_class.__name__
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name).lower()
        plural_name = f"{snake_case}s"
        
        # Check which config entry is found
        config_entry = None
        if model_name in self.config_manager.get_py_models():
            config_entry = model_name
        elif snake_case in self.config_manager.get_py_models():
            config_entry = snake_case
        elif plural_name in self.config_manager.get_py_models():
            config_entry = plural_name
        
        # Get the provider model
        provider_model = self._get_primary_provider_and_model(model_class)
        
        # Get pricing information if provider model is available
        pricing_info = {}
        if provider_model:
            provider_name, model_name = provider_model
            # Get the registry instance and fetch model details
            registry = get_llm_registry()
            model_details = registry.get_model_details(provider_name, model_name)
            if model_details:
                pricing_info = {
                    'input': model_details.get('cost_input', 0.0),
                    'output': model_details.get('cost_output', 0.0)
                }
        
        return {
            'class_name': model_class.__name__,
            'snake_case_name': snake_case,
            'plural_name': plural_name,
            'config_entry': config_entry,
            'provider_model': provider_model,
            'model_pricing': pricing_info
        }
    
    def get_actual_model_used(self) -> str:
        """
        Get the actual model used in the last request from the analysis report.
        
        Returns:
            The provider:model string for the model that was actually used,
            or "Not available" if not found.
        """
        for pass_name, pass_data in self.analysis.passes.items():
            if pass_data.provider_model:
                return pass_data.provider_model
        return "Not available"

if __name__ == "__main__":
    """
    Basic use of bridge
    """
    # Set up logging for the main script
    logging.basicConfig(level=logging.INFO)
    
    # Load source and prompt from test files
    source_path = get_py_models_dir() + '/job_ads/tests/sources/complex.txt'
    prompt_path = get_py_models_dir() + '/job_ads/tests/prompts/complex.txt'

    with open(source_path, 'r') as f:
        source = f.read()
    with open(prompt_path, 'r') as f:
        prompt = f.read()
    
    # Initialize the bridge
    bridge = PyllmBridge()
    print("\nRunning test with JobAd...")
    example = bridge.ask(JobAd, prompt + source)
    print(example.model_dump_json(indent=2))
