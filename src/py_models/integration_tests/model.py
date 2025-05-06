"""Pydantic model for the simple integration test"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os

class IntegrationTest(BaseModel):
    """Simple model to extract one field."""
    animal: str = Field(..., description="The animal mentioned in the text")

    @classmethod
    def get_test_cases(cls) -> List[Dict[str, Any]]:
        """
        Returns the test case configurations for this model.
        """
        base_dir = os.path.dirname(__file__)
        test_dir = os.path.join(base_dir, "tests")

        # Define the single test case
        test_case_name = "simple"
        test_case = {
            'module': 'integration_tests',
            'name': test_case_name,
            'model_class': cls,
            'source_path': os.path.join(test_dir, "sources", f"{test_case_name}.txt"),
            'prompt_path': os.path.join(test_dir, "prompts", f"{test_case_name}.txt"),
            'expected_path': os.path.join(test_dir, "expected", f"{test_case_name}.json")
        }

        # Check if all files exist
        if all(os.path.exists(test_case[key]) for key in ['source_path', 'prompt_path', 'expected_path']):
            return [test_case]
        else:
            # Log a warning or raise an error if files are missing
            print(f"Warning: Missing files for integration_tests/{test_case_name}")
            return []
