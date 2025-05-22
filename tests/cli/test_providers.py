import pytest
from typer.testing import CliRunner

from src.pydantic_llm_tester.cli.main import app

runner = CliRunner()

def test_providers_manage_command_removed():
    """
    Test that the 'providers manage' command has been removed from the CLI.
    """
    result = runner.invoke(app, ["providers", "manage", "--help"])

    # Expect a non-zero exit code and an error message indicating the command is not found
    assert result.exit_code != 0
    assert "No such command 'manage'." in result.stdout or "Error: No such command 'manage'." in result.stderr

# Add more tests here for other removed model management functionality if necessary
# For example, testing that 'llm-tester providers list' no longer shows model-specific details
# or that direct model flags on 'providers list' are removed.
