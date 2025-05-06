import typer
import logging

# Use absolute imports for clarity
from src.cli.core import config_logic

logger = logging.getLogger(__name__)

# Create a Typer app for this subcommand group
app = typer.Typer(
    name="configure",
    help="Configure llm-tester settings (e.g., API keys)."
)

@app.command("keys")
def configure_keys():
    """
    Check for and interactively configure missing API keys.

    Scans discovered providers for required API key environment variables
    (defined in their config.json). Prompts the user for any missing keys
    and offers to save them to the .env file in the src directory.
    """
    logger.info("Executing 'configure keys' command.")

    # Call the core logic function, always prompting in this command
    success, keys_set = config_logic.check_and_configure_api_keys(prompt_user=True)

    if not success:
        # Error message or cancellation message already printed by core logic
        raise typer.Exit(code=1)
    # If successful, messages are already printed by core logic

# Add other configuration commands here if needed in the future

if __name__ == "__main__":
    # Allows running the subcommand module directly for testing (optional)
    # e.g., python -m src.cli.commands.configure keys
    app()
