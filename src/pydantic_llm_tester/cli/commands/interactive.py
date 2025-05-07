import logging

# Use absolute imports
from pydantic_llm_tester.cli import interactive_ui

logger = logging.getLogger(__name__)

# Define the function that will become the command
def start_interactive_command():
    """
    Explicitly launch the interactive session for LLM Tester.
    """
    logger.info("Executing 'interactive' command.")
    interactive_ui.start_interactive_session()

# Example of how to create a standalone app for this command if needed
# app = typer.Typer()
# app.command("interactive")(start_interactive_command)
# if __name__ == "__main__":
#     app()
