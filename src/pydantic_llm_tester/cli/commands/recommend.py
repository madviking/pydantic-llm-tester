import typer
import logging

# Use absolute imports
from pydantic_llm_tester.cli.core import recommend_logic

logger = logging.getLogger(__name__)

# Create a Typer app for this command (or it could be a direct command on the main app)
# Let's make it a direct command on the main app later.
# For now, define the function that will become the command.

def recommend_model_command():
    """
    Get LLM-assisted model recommendations for a specific task.

    Prompts for a task description, then uses an available LLM (like Haiku via OpenRouter)
    to analyze enabled py_models and suggest the best fit based on cost, limits, etc.
    """
    logger.info("Executing 'recommend-model' command.")

    try:
        # Prompt user for task description
        task_description = typer.prompt(
            "Describe the task you need the model for (e.g., 'summarize long articles cheaply', 'generate creative Python code')",
            type=str
        )
        if not task_description:
            print("Task description cannot be empty. Aborting.")
            raise typer.Exit(code=1)

    except typer.Abort:
        print("\nOperation cancelled by user.")
        raise typer.Exit(code=1) # Ensure exit on abort

    print("\nGenerating recommendation (this may take a moment)...")
    success, message = recommend_logic.get_recommendation(task_description)

    if success:
        print("\n--- LLM Recommendation ---")
        print(message)
        print("--------------------------")
    else:
        print(f"\nError: {message}")
        raise typer.Exit(code=1)

# Example of how to create a standalone app for this command if needed
# app = typer.Typer()
# app.command("recommend-model")(recommend_model_command)
# if __name__ == "__main__":
#     app()
