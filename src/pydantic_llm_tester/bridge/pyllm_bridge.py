from typing import TypeVar, Type

from pydantic_llm_tester.py_models.base import BasePyModel
from pydantic_llm_tester.py_models.job_ads import JobAd

T = TypeVar('T', bound=BasePyModel)


class PyllmBridge:

    def __init__(self):
        self.errors = []
        self.notices = []
        self.cost = 0
        self.analysis = {}

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
        return model

    """
    We should see what are the configured llm models for this pydantic model. In addition:
    If we don't have anything in "expected", "prompts" or "sources" directories, we should add them based on this run.
    We add auto_ in front of the file name, so we can distinguish between the auto-generated and the manually created ones.
    """
    def _load_model_config(self, model_name: str) -> BasePyModel:
        raise NotImplementedError("Subclasses must implement this method.")

    def _save_model_config(self, model: BasePyModel) -> None:
        raise NotImplementedError("Subclasses must implement this method.")



if __name__ == "__main__":
    obj = PyllmBridge()
    example = obj.ask(JobAd, "What is the job title?")
    print(obj)
