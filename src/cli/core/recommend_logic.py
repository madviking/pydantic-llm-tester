import os
import logging
from typing import List, Dict, Optional, Tuple

# Use absolute imports
from src.cli.core.provider_logic import get_available_providers_from_factory
from src.llms.provider_factory import load_provider_config, create_provider, reset_caches
from src.llms.base import BaseLLM, ModelConfig

logger = logging.getLogger(__name__)

def get_recommendation(task_description: str) -> Tuple[bool, str]:
    """
    Gets model recommendations based on a task description using an available LLM.

    Args:
        task_description: The user's description of the task.

    Returns:
        Tuple of (success: bool, message: str). The message contains the recommendation or an error.
    """
    logger.info("Gathering information about enabled py_models for recommendation...")
    reset_caches() # Ensure fresh data
    enabled_providers = get_available_providers_from_factory()
    enabled_models_details = []

    if not enabled_providers:
        return False, "Error: No providers are currently enabled. Use 'llm-tester providers list' and 'llm-tester providers enable <name>'."

    # Collect details of enabled py_models from enabled providers
    for provider_name in enabled_providers:
        config = load_provider_config(provider_name)
        if config and config.llm_models:
            for model_config in config.llm_models:
                # Check the 'enabled' flag from the config (defaults to True if missing)
                if model_config.enabled:
                    # Format details clearly for the LLM
                    details = (
                        f"- Provider: {provider_name}, Model: {model_config.name}\n"
                        f"  Cost (Input/Output per 1M tokens): ${model_config.cost_input:.2f} / ${model_config.cost_output:.2f}\n"
                        f"  Max Tokens (Input/Output): {model_config.max_input_tokens} / {model_config.max_output_tokens}\n"
                        f"  Category: {model_config.cost_category}"
                    )
                    enabled_models_details.append(details)

    if not enabled_models_details:
        return False, "Error: No py_models are enabled across the enabled providers. Use 'llm-tester py_models list --provider <name>' and 'llm-tester py_models enable <provider>/<model_name>'."

    logger.info(f"Found {len(enabled_models_details)} enabled py_models for recommendation context.")

    # --- Select LLM for Recommendation ---
    # Prioritize cheap/fast py_models like OpenRouter Haiku if available and key exists
    recommendation_provider_name: Optional[str] = None
    recommendation_model_name: Optional[str] = None
    llm_provider: Optional[BaseLLM] = None

    # Check OpenRouter first (common choice for cheap py_models)
    if "openrouter" in enabled_providers and os.getenv("OPENROUTER_API_KEY"):
        or_config = load_provider_config("openrouter")
        if or_config:
            # Look for Haiku specifically, check if enabled in its config
            haiku_config = next((m for m in or_config.llm_models if "claude-3-haiku" in m.name and m.enabled), None)
            if haiku_config:
                recommendation_provider_name = "openrouter"
                # Use the exact name from config, might include date suffix etc.
                recommendation_model_name = haiku_config.name
                llm_provider = create_provider(recommendation_provider_name)
                logger.info(f"Selected OpenRouter model '{recommendation_model_name}' for generating recommendation.")

    # Add fallbacks here if needed (e.g., check google gemini-flash, openai gpt-3.5-turbo)
    # Example fallback (needs Google provider enabled and key):
    # if not llm_provider and "google" in enabled_providers and os.getenv("GOOGLE_API_KEY"):
    #     google_config = load_provider_config("google")
    #     if google_config:
    #         # Look for a cheap/fast Gemini model like flash
    #         flash_config = next((m for m in google_config.py_models if "gemini-1.5-flash" in m.name and m.enabled), None)
    #         if flash_config:
    #              recommendation_provider_name = "google"
    #              recommendation_model_name = flash_config.name
    #              llm_provider = create_provider(recommendation_provider_name)
    #              logger.info(f"Selected Google model '{recommendation_model_name}' for generating recommendation.")

    if not llm_provider or not recommendation_model_name:
        return False, ("Error: Could not find a suitable LLM provider/model with an available API key "
                       "to generate recommendations (tried OpenRouter Haiku). "
                       "Ensure at least one provider (like OpenRouter with key OPENROUTER_API_KEY) "
                       "is configured, enabled, and has an enabled model like Haiku.")

    logger.info(f"Using '{recommendation_model_name}' via provider '{recommendation_provider_name}' to generate recommendation...")

    # --- Craft Prompt ---
    available_models_text = "\n\n".join(enabled_models_details)
    system_prompt = "You are an expert assistant helping users choose the best Large Language Model (LLM) for their task based on provided model details."
    prompt = (
        f"The user wants to perform the following task: '{task_description}'\n\n"
        f"Here are the available LLM py_models with their details:\n"
        f"{available_models_text}\n\n"
        f"Based ONLY on the information provided above, please recommend the top 1-3 py_models best suited for the user's task. "
        f"Explain your reasoning for each recommendation briefly, considering factors like cost, token limits, and potential suitability for the task described. "
        f"Format your response clearly."
    )

    # --- Call LLM ---
    try:
        # Use a dummy source for get_response as it's not relevant here
        response_text, usage_data = llm_provider.get_response(
            prompt=prompt,
            source="N/A", # Source text is not needed for this meta-task
            model_name=recommendation_model_name
        )
        if usage_data:
             logger.info(f"Recommendation generated. Usage: {usage_data.total_tokens} tokens, Cost: ${usage_data.total_cost:.6f}")
        else:
             logger.warning("Recommendation generated, but usage data was not returned by the provider.")

        return True, response_text

    except Exception as e:
        logger.error(f"Failed to get recommendation using {recommendation_model_name}: {e}", exc_info=True)
        return False, f"Error getting recommendation from LLM ({recommendation_model_name}): {e}"
