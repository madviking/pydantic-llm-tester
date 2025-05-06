import typer
import logging
from typing import Optional, List

# Use absolute imports
from src.cli.core import test_runner_logic

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
ModelsOptionPy = typer.Option(None, "--py_models", "-m", help="Specify Pydantic models to test (e.g., 'job_ads'). Can be used multiple times.")
ModelsOptionLLM = typer.Option(None, "--llm_models", help="Specify LLM models to test (e.g., 'gpt-4o'). Can be used multiple times.")
TestDirOption = typer.Option(None, "--test-dir", help="Directory containing test files (default: uses LLMTester default).")

@app.command("tests") # Explicit command name 'tests' under 'run' group, or maybe just 'run' on main app? Let's use 'tests' for now.
def run_tests(
    providers: Optional[List[str]] = ProvidersOption,
    py_models: Optional[List[str]] = ModelsOptionPy,
    llm_models: Optional[List[str]] = ModelsOptionLLM,
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
    model_overrides = test_runner_logic.parse_model_overrides(llm_models)

    # Extract the list of specified model names from the overrides for filtering
    specified_llm_models_list = list(model_overrides.values()) if model_overrides else None

    success = test_runner_logic.run_test_suite(
        providers=providers,
        model_overrides=model_overrides, # Keep model_overrides for potential override logic within run_test
        llm_models=specified_llm_models_list, # Pass the list of specified models for filtering
        test_dir=test_dir,
        output_file=output_file,
        output_json=json_output, # Corrected parameter name
        optimize=optimize,
        test_filter=filter
    )

    if not success:
        raise typer.Exit(code=1)

@app.command("list")
def list_items(
    providers: Optional[List[str]] = ProvidersOption,
    py_models: Optional[List[str]] = ModelsOptionPy,
    test_dir: Optional[str] = TestDirOption,
):
    """
    List discovered test cases and configured providers/py_models without running tests.
    """
    logger.info("Executing 'run list' command.")
    # The list command doesn't use model overrides in the same way run_tests does,
    # but the list_available_tests_and_providers function expects model_overrides.
    # We should probably pass the py_models list directly or adjust list_available_tests_and_providers.
    # For now, let's pass the py_models list as model_overrides, although it's not a true override dict.
    # A better fix would be to update list_available_tests_and_providers to accept py_models list.
    # Let's create a dummy model_overrides dict for now to avoid breaking the call.
    # This is a temporary fix to address the NameError.
    # TODO: Refactor list_available_tests_and_providers to accept py_models list directly.
    dummy_model_overrides = {f"dummy_provider_{i}": model_name for i, model_name in enumerate(py_models or [])}


    output_string = test_runner_logic.list_available_tests_and_providers(
        providers_list=providers,
        model_overrides=dummy_model_overrides, # Pass the dummy overrides
        test_dir=test_dir
    )
    print(output_string)


if __name__ == "__main__":
    # Allows running the subcommand module directly for testing (optional)
    # e.g., python -m src.cli.commands.run tests --providers mock
    # e.g., python -m src.cli.commands.run list
    app()
