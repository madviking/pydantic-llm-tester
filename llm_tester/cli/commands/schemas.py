import typer
import logging
from typing import List

# Use absolute imports
from llm_tester.cli.core import schema_logic

logger = logging.getLogger(__name__)

# Create a Typer app for this command group
app = typer.Typer(
    name="schemas",
    help="Manage Extraction Schemas (Pydantic models and test modules)."
)

@app.command("list")
def list_schemas():
    """
    List all discoverable extraction schemas (test modules).

    Looks for directories in 'llm_tester/models/' containing a 'model.py'.
    """
    logger.info("Executing 'schemas list' command.")
    schemas = schema_logic.get_discovered_schemas()

    if not schemas:
        print("No extraction schemas discovered in 'llm_tester/models/'.")
        return

    print("Discovered Extraction Schemas:")
    for schema_name in schemas:
        print(f"  - {schema_name}")

# Add other schema management commands here later (e.g., create, validate)

if __name__ == "__main__":
    # Allows running the subcommand module directly for testing (optional)
    # e.g., python -m llm_tester.cli.commands.schemas list
    app()
