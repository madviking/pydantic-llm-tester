from typing import TypeVar, Type

from pydantic_llm_tester.py_models.base import BasePyModel
from pydantic_llm_tester.py_models.job_ads import JobAd
# Import managers for initialization
from pydantic_llm_tester.utils.config_manager import ConfigManager
from pydantic_llm_tester.utils.provider_manager import ProviderManager
# TODO: Import other necessary managers (e.g., CostManager, ReportGenerator)

T = TypeVar('T', bound=BasePyModel)


class PyllmBridge:

    def __init__(self):
        self.errors = []
        self.notices = []
        self.cost = 0
        self.analysis = {}

        # Phase 1: Initialize managers
        self.config_manager = ConfigManager() # Scaffolding
        self.provider_manager = ProviderManager(self.config_manager) # Scaffolding
        # TODO: Initialize other managers

    """
    Provide a model and prompt, receive the filled model. Retry with a secondary model if it fails.
    Providing multiple passes will try to refine the model by using additional LLM's:
        - First pass: Use the primary model to fill the prompt.
        - Second pass: Use the secondary model to fill the prompt (fill, but overwrite)
        - Third pass: Use the best model again to fill the prompt (overwrite)
    Analysis:
    {
        "first_pass": {
          "new_fields": 5,
       },
       "second_pass": {
          "new_fields": 2
       },
       "third_pass": {
          "new_fields": 1,
          "overwritten_fields": 1
       },
          "total_fields": 10,
          "cost": 0.5,
    }
    
    If file (path) is provided, make sure we can read the file AND that the LLM model supports file. If 
    not, we should default to LLM model that supports files (primary - this PyModel, secondary - this PyModel, primary - system, secondary - system, best - system).
    """

    def ask(self, model: Type[T], prompt: str, passes=1, file='') -> T:
        # TODO: Implement logic to use managers and helper methods
        # TODO: Handle file input and LLM support
        # TODO: Call _process_passes
        return model # Scaffolding return

    """
    We should see what are the configured llm models for this pydantic model. In addition:
    If we don't have anything in "expected", "prompts" or "sources" directories, we should add them based on this run.
    We add auto_ in front of the file name, so we can distinguish between the auto-generated and the manually created ones.
    """
    def _load_model_config(self, model_name: str) -> BasePyModel:
        raise NotImplementedError("Subclasses must implement this method.")

    def _save_model_config(self, model: BasePyModel) -> None:
        # Phase 1: Scaffolding for saving missing test files
        """
        Saves expected, prompts, and sources files for a model if they are missing.
        Adds 'auto_' prefix to generated files.
        """
        pass # Scaffolding

    # Phase 1 Implementation Scaffolding (Empty Functions)
    def _get_primary_provider_and_model(self, model_class: Type[T]):
        """Determine the primary provider and model based on config and model overrides."""
        # TODO: Use self.config_manager to get preferred/default provider/model
        pass # Scaffolding

    def _get_secondary_provider_and_model(self, model_class: Type[T]):
        """Determine the secondary provider and model based on config and model overrides."""
        # TODO: Use self.config_manager to get secondary provider/model
        pass # Scaffolding

    def _call_llm_single_pass(self, provider_name: str, model_name: str, prompt: str, file: str):
        """Handle a single call to an LLM provider."""
        # TODO: Use self.provider_manager to get provider instance and call LLM
        # TODO: Use self.cost_manager to track cost
        pass # Scaffolding

    def _process_passes(self, model: Type[T], prompt: str, passes: int, file: str):
        """Handle multiple passes of calling LLMs and refining the result."""
        # TODO: Implement logic for multiple passes, calling _call_llm_single_pass
        # TODO: Update self.analysis
        pass # Scaffolding


if __name__ == "__main__":
    obj = PyllmBridge()
    example = obj.ask(JobAd, "What is the job title?")
    print(obj)
