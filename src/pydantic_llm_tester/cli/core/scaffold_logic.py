import os

# Import ConfigManager to update the config file
from pydantic_llm_tester.utils.config_manager import ConfigManager

# Determine the directory containing the templates relative to the package root
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_cli_dir = os.path.dirname(_current_file_dir) # Go up one level to src/cli
_llm_tester_dir = os.path.dirname(_cli_dir) # Go up another level to src
_templates_dir = os.path.join(_llm_tester_dir, "cli", "templates") # Path is src/cli/templates

def _read_template(template_name: str, **kwargs) -> str:
    """Reads a template file and replaces placeholders."""
    template_path = os.path.join(_templates_dir, template_name)
    if not os.path.exists(template_path):
        # In core logic, raise an error rather than exiting Typer app
        raise FileNotFoundError(f"Template file not found at {template_path}")

    with open(template_path, "r") as f:
        content = f.read()

    # Replace placeholders
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, str(value))

    return content

def scaffold_provider_files(provider_name: str, base_dir: str):
    """
    Scaffolds the directory structure and template files for a new LLM provider.

    Args:
        provider_name: The name of the new provider.
        base_dir: The base directory to create the provider in.

    Returns:
        True if successful, False otherwise.
    """
    provider_path = os.path.join(base_dir, provider_name)

    if os.path.exists(provider_path):
        # In core logic, return False and let the caller handle the error message
        return False, f"Error: Provider directory already exists at {provider_path}"

    try:
        # Create directory structure
        os.makedirs(provider_path)
        os.makedirs(os.path.join(provider_path, "tests")) # Optional: Add tests directory structure later if needed

        # Read and process templates
        provider_name_capitalized = provider_name.capitalize()
        provider_name_upper = provider_name.upper()

        init_content = _read_template(
            "provider_init.py.tmpl",
            provider_name=provider_name,
            provider_name_capitalized=provider_name_capitalized
        )
        config_content = _read_template(
            "provider_config.json.tmpl",
            provider_name=provider_name,
            provider_name_upper=provider_name_upper
        )
        provider_content = _read_template(
            "provider_provider.py.tmpl",
            provider_name=provider_name,
            provider_name_capitalized=provider_name_capitalized,
            provider_name_upper=provider_name_upper
        )

        # Write files
        with open(os.path.join(provider_path, "__init__.py"), "w") as f:
            f.write(init_content)

        with open(os.path.join(provider_path, "config.json"), "w") as f:
            f.write(config_content)

        with open(os.path.join(provider_path, "provider.py"), "w") as f:
            f.write(provider_content)

        return True, f"Successfully scaffolded provider '{provider_name}' at {provider_path}"

    except OSError as e:
        return False, f"Error creating provider directory or files: {e}"
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"An unexpected error occurred during provider scaffolding: {e}"


def scaffold_model_files(model_name: str, base_dir: str):
    """
    Scaffolds the directory structure and template files for a new LLM tester model.

    Args:
        model_name: The name of the new model.
        base_dir: The base directory to create the model in.

    Returns:
        True if successful, False otherwise.
    """
    model_path = os.path.join(base_dir, model_name)

    if os.path.exists(model_path):
        # In core logic, return False and let the caller handle the error message
        return False, f"Error: Model directory already exists at {model_path}"

    try:
        # Create directory structure
        os.makedirs(os.path.join(model_path, "tests", "sources"))
        os.makedirs(os.path.join(model_path, "tests", "prompts", "optimized"))
        os.makedirs(os.path.join(model_path, "tests", "expected"))
        os.makedirs(os.path.join(model_path, "reports"))

        # Read and process templates
        model_name_capitalized = model_name.capitalize()

        model_init_content = _read_template(
            "model_init.py.tmpl",
            model_name=model_name,
            model_name_capitalized=model_name_capitalized
        )
        model_model_content = _read_template(
            "model_model.py.tmpl",
            model_name=model_name,
            model_name_capitalized=model_name_capitalized
        )
        model_tests_init_content = _read_template(
            "model_tests_init.py.tmpl",
            model_name=model_name
        )
        model_test_source_content = _read_template(
            "model_test_source.txt.tmpl",
            model_name=model_name
        )
        model_test_prompt_content = _read_template(
            "model_test_prompt.txt.tmpl",
            model_name=model_name
        )
        model_test_expected_content = _read_template(
            "model_test_expected.json.tmpl"
            # No model_name placeholder in expected.json template
        )

        # Write files
        with open(os.path.join(model_path, "__init__.py"), "w") as f:
            f.write(model_init_content)

        with open(os.path.join(model_path, "model.py"), "w") as f:
            f.write(model_model_content)

        with open(os.path.join(model_path, "tests", "__init__.py"), "w") as f:
            f.write(model_tests_init_content)

        with open(os.path.join(model_path, "tests", "sources", "example.txt"), "w") as f:
            f.write(model_test_source_content)

        with open(os.path.join(model_path, "tests", "prompts", "example.txt"), "w") as f:
            f.write(model_test_prompt_content)

        with open(os.path.join(model_path, "tests", "expected", "example.json"), "w") as f:
            f.write(model_test_expected_content)

        # Register the new model in the config file
        config_manager = ConfigManager()
        config_manager.register_py_model(model_name, {"enabled": True}) # Register and enable by default

        return True, f"Successfully scaffolded model '{model_name}' at {model_path} and registered in config."

    except OSError as e:
        return False, f"Error creating model directory or files: {e}"
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"An unexpected error occurred during model scaffolding: {e}"

# Determine the directory containing the templates relative to the package root
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_cli_dir = os.path.dirname(_current_file_dir) # Go up one level to src/cli
_llm_tester_dir = os.path.dirname(_cli_dir) # Go up another level to src
_templates_dir = os.path.join(_llm_tester_dir, "cli", "templates") # Path is src/cli/templates

def _read_template(template_name: str, **kwargs) -> str:
    """Reads a template file and replaces placeholders."""
    template_path = os.path.join(_templates_dir, template_name)
    if not os.path.exists(template_path):
        # In core logic, raise an error rather than exiting Typer app
        raise FileNotFoundError(f"Template file not found at {template_path}")

    with open(template_path, "r") as f:
        content = f.read()

    # Replace placeholders
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, str(value))

    return content

def scaffold_provider_files(provider_name: str, base_dir: str):
    """
    Scaffolds the directory structure and template files for a new LLM provider.

    Args:
        provider_name: The name of the new provider.
        base_dir: The base directory to create the provider in.

    Returns:
        True if successful, False otherwise.
    """
    provider_path = os.path.join(base_dir, provider_name)

    if os.path.exists(provider_path):
        # In core logic, return False and let the caller handle the error message
        return False, f"Error: Provider directory already exists at {provider_path}"

    try:
        # Create directory structure
        os.makedirs(provider_path)
        os.makedirs(os.path.join(provider_path, "tests")) # Optional: Add tests directory structure later if needed

        # Read and process templates
        provider_name_capitalized = provider_name.capitalize()
        provider_name_upper = provider_name.upper()

        init_content = _read_template(
            "provider_init.py.tmpl",
            provider_name=provider_name,
            provider_name_capitalized=provider_name_capitalized
        )
        config_content = _read_template(
            "provider_config.json.tmpl",
            provider_name=provider_name,
            provider_name_upper=provider_name_upper
        )
        provider_content = _read_template(
            "provider_provider.py.tmpl",
            provider_name=provider_name,
            provider_name_capitalized=provider_name_capitalized,
            provider_name_upper=provider_name_upper
        )

        # Write files
        with open(os.path.join(provider_path, "__init__.py"), "w") as f:
            f.write(init_content)

        with open(os.path.join(provider_path, "config.json"), "w") as f:
            f.write(config_content)

        with open(os.path.join(provider_path, "provider.py"), "w") as f:
            f.write(provider_content)

        return True, f"Successfully scaffolded provider '{provider_name}' at {provider_path}"

    except OSError as e:
        return False, f"Error creating provider directory or files: {e}"
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"An unexpected error occurred during provider scaffolding: {e}"
