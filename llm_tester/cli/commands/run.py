import typer
import logging
from typing import Optional, List

# Use absolute imports
from llm_tester.cli.core import test_runner_logic

logger = logging.getLogger(__name__)

# Create a Typer app for this command group (though it might just be top-level commands)
# For simplicity, we can define these as direct commands on the main app later,
# or keep them grouped if more run-related commands are expected.
# Let's define them here for modularity.
app = typer.Typer(
    name="run", # This name might not be used if added directly to main app
    help="Run tests or list available tests and configurations."
)

# Define common options used by both run and list
ProvidersOption = typer.Option(None, "--providers", "-p", help="LLM providers to test (default: all enabled).")
ModelsOption = typer.Option(None, "--models", "-m", help="Specify models as 'provider:model_name' or 'provider/model_name'. Can be used multiple times.")
TestDirOption = typer.Option(None, "--test-dir", help="Directory containing test files (default: uses LLMTester default).")

@app.command("tests") # Explicit command name 'tests' under 'run' group, or maybe just 'run' on main app? Let's use 'tests' for now.
def run_tests(
    providers: Optional[List[str]] = ProvidersOption,
    models: Optional[List[str]] = ModelsOption,
    test_dir: Optional[str] = TestDirOption,
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for report/JSON (default: stdout)."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON instead of Markdown report."),
    optimize: bool = typer.Option(False, "--optimize", help="Optimize prompts before running final tests."),
    filter: Optional[str] = typer.Option(None, "--filter", "-f", help="Filter test cases by pattern (e.g., 'module/name'). Not fully implemented.") # Added filter option
):
    """
    Run the LLM test suite with the specified configurations.
    """
    logger.info("Executing 'run tests' command.")
    model_overrides = test_runner_logic.parse_model_overrides(models)

    success = test_runner_logic.run_test_suite(
        providers=providers,
        model_overrides=model_overrides,
        test_dir=test_dir,
        output_file=output_file,
        output_json=json_output,
        optimize=optimize,
        test_filter=filter
    )

    if not success:
        raise typer.Exit(code=1)

@app.command("list")
def list_items(
    providers: Optional[List[str]] = ProvidersOption,
    models: Optional[List[str]] = ModelsOption,
    test_dir: Optional[str] = TestDirOption,
):
    """
    List discovered test cases and configured providers/models without running tests.
    """
    logger.info("Executing 'run list' command.")
    model_overrides = test_runner_logic.parse_model_overrides(models)

    output_string = test_runner_logic.list_available_tests_and_providers(
        providers_list=providers,
        model_overrides=model_overrides,
        test_dir=test_dir
    )
    print(output_string)


if __name__ == "__main__":
    # Allows running the subcommand module directly for testing (optional)
    # e.g., python -m llm_tester.cli.commands.run tests --providers mock
    # e.g., python -m llm_tester.cli.commands.run list
    app()
