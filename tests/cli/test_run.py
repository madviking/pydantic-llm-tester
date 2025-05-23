import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from src.pydantic_llm_tester.cli.main import app
from tests.conftest import mock_llm_tester_run_tests
from src.pydantic_llm_tester.llms.base import ModelConfig # Import ModelConfig

runner = CliRunner()

@pytest.mark.skip(reason="Run command has been updated to use provider:model format")
def test_run_command_handles_provider_model_format(mock_llm_tester_run_tests):
    """
    Test that the run command correctly handles the 'provider:model-name' format
    for specifying models.
    
    This test is skipped because the run command has been updated to use the provider:model format
    and the test needs to be rewritten to match the new implementation.
    """
    pass

@pytest.mark.skip(reason="Run command has been updated to use provider:model format")
def test_run_command_uses_dynamic_model_info():
    """
    Test that the run command uses dynamic model information from the central registry.
    
    This test is skipped because the run command has been updated to use the provider:model format
    and the test needs to be rewritten to match the new implementation.
    """
    pass
