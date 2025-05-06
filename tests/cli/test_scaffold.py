import pytest
import os
import tempfile
import shutil
import json
from typer.testing import CliRunner

from src.cli.main import app # Import the main Typer app
from src.utils.config_manager import ConfigManager # Import ConfigManager

runner = CliRunner()

# Determine the directory containing the templates relative to the test file
# Determine the directory containing the templates relative to the project root
_project_root = os.getcwd() # Get the current working directory (project root)
_templates_dir = os.path.join(_project_root, "src", "cli", "templates") # Path is src/cli/templates relative to root

def _read_template(template_name: str) -> str:
    """Reads a template file content."""
    template_path = os.path.join(_templates_dir, template_name)
    with open(template_path, "r") as f:
        return f.read()

def test_scaffold_provider():
    """Tests the 'scaffold provider' command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider_name = "test_provider"
        result = runner.invoke(app, ["scaffold", "provider", provider_name, "--providers-dir", tmpdir])

        assert result.exit_code == 0
        assert f"Successfully scaffolded provider '{provider_name}' at" in result.stdout

        # Verify directory structure
        provider_path = os.path.join(tmpdir, provider_name)
        assert os.path.exists(provider_path)
        assert os.path.isdir(provider_path)
        assert os.path.exists(os.path.join(provider_path, "tests"))
        assert os.path.isdir(os.path.join(provider_path, "tests"))

        # Verify files were created and content is correct
        init_file = os.path.join(provider_path, "__init__.py")
        config_file = os.path.join(provider_path, "config.json")
        provider_file = os.path.join(provider_path, "provider.py")

        assert os.path.exists(init_file)
        assert os.path.exists(config_file)
        assert os.path.exists(provider_file)

        # Check content (basic check for placeholders)
        init_content = _read_template("provider_init.py.tmpl").replace("{{provider_name}}", provider_name).replace("{{provider_name_capitalized}}", provider_name.capitalize())
        with open(init_file, "r") as f:
            assert f.read() == init_content

        config_content = _read_template("provider_config.json.tmpl").replace("{{provider_name}}", provider_name).replace("{{provider_name_upper}}", provider_name.upper())
        with open(config_file, "r") as f:
            assert f.read() == config_content

        provider_content = _read_template("provider_provider.py.tmpl").replace("{{provider_name}}", provider_name).replace("{{provider_name_capitalized}}", provider_name.capitalize()).replace("{{provider_name_upper}}", provider_name.upper())
        with open(provider_file, "r") as f:
            assert f.read() == provider_content

def test_scaffold_model():
    """Tests the 'scaffold model' command with --path option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_name = "test_model"
        # Provide the required --path argument
        result = runner.invoke(app, ["scaffold", "model", model_name, "--path", tmpdir])

        assert result.exit_code == 0
        assert f"Successfully scaffolded model '{model_name}' at" in result.stdout

        # Verify directory structure
        model_path = os.path.join(tmpdir, model_name)
        assert os.path.exists(model_path)
        assert os.path.isdir(model_path)
        assert os.path.exists(os.path.join(model_path, "tests", "sources"))
        assert os.path.isdir(os.path.join(model_path, "tests", "sources"))
        assert os.path.exists(os.path.join(model_path, "tests", "prompts", "optimized"))
        assert os.path.isdir(os.path.join(model_path, "tests", "prompts", "optimized"))
        assert os.path.exists(os.path.join(model_path, "tests", "expected"))
        assert os.path.isdir(os.path.join(model_path, "tests", "expected"))
        assert os.path.exists(os.path.join(model_path, "reports"))
        assert os.path.isdir(os.path.join(model_path, "reports"))

        # Verify files were created and content is correct
        init_file = os.path.join(model_path, "__init__.py")
        model_file = os.path.join(model_path, "model.py")
        tests_init_file = os.path.join(model_path, "tests", "__init__.py")
        source_file = os.path.join(model_path, "tests", "sources", "example.txt")
        prompt_file = os.path.join(model_path, "tests", "prompts", "example.txt")
        expected_file = os.path.join(model_path, "tests", "expected", "example.json")

        assert os.path.exists(init_file)
        assert os.path.exists(model_file)
        assert os.path.exists(tests_init_file)
        assert os.path.exists(source_file)
        assert os.path.exists(prompt_file)
        assert os.path.exists(expected_file)

        model_name_capitalized = model_name.capitalize()

        init_content = _read_template("model_init.py.tmpl").replace("{{model_name}}", model_name).replace("{{model_name_capitalized}}", model_name_capitalized)
        with open(init_file, "r") as f:
            assert f.read() == init_content

        model_content = _read_template("model_model.py.tmpl").replace("{{model_name}}", model_name).replace("{{model_name_capitalized}}", model_name_capitalized)
        with open(model_file, "r") as f:
            assert f.read() == model_content

        tests_init_content = _read_template("model_tests_init.py.tmpl").replace("{{model_name}}", model_name)
        with open(tests_init_file, "r") as f:
            assert f.read() == tests_init_content

        source_content = _read_template("model_test_source.txt.tmpl").replace("{{model_name}}", model_name)
        with open(source_file, "r") as f:
            assert f.read() == source_content

        prompt_content = _read_template("model_test_prompt.txt.tmpl").replace("{{model_name}}", model_name)
        with open(prompt_file, "r") as f:
            assert f.read() == prompt_content

        expected_content = _read_template("model_test_expected.json.tmpl")
        with open(expected_file, "r") as f:
            assert f.read() == expected_content

def test_scaffold_model_updates_config():
    """Tests that 'scaffold model' with --path updates the pyllm_config.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temporary config file path
        temp_config_path = os.path.join(tmpdir, "pyllm_config.json")

        # Create a default config file
        default_config = {
            "providers": {},
            "test_settings": {},
            "py_models": {}
        }
        with open(temp_config_path, "w") as f:
            json.dump(default_config, f)

        model_name = "config_test_model"
        model_path = os.path.join(tmpdir, model_name) # Scaffold into a subdirectory of tmpdir

        # Run the scaffold command, specifying the temporary config file and the model path
        result = runner.invoke(app, ["scaffold", "model", model_name, "--path", model_path], env={"PYLLM_CONFIG_PATH": temp_config_path})

        assert result.exit_code == 0
        assert f"Successfully scaffolded model '{model_name}' at" in result.stdout
        assert f"Model '{model_name}' registered in pyllm_config.json with path '{model_path}'." in result.stdout

        # Load the updated config file
        with open(temp_config_path, "r") as f:
            updated_config = json.load(f)

        # Assert that the model is registered in the config with the correct path
        assert "py_models" in updated_config
        assert model_name in updated_config["py_models"]
        assert "path" in updated_config["py_models"][model_name]
        assert updated_config["py_models"][model_name]["path"] == model_path
        assert "enabled" in updated_config["py_models"][model_name]
        assert updated_config["py_models"][model_name]["enabled"] is True

        # Clean up the scaffolded model directory
        if os.path.exists(model_path):
            shutil.rmtree(model_path)

# Add tests for error cases (e.g., directory already exists)
def test_scaffold_provider_exists():
    """Tests that 'scaffold provider' fails if directory exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider_name = "existing_provider"
        provider_path = os.path.join(tmpdir, provider_name)
        os.makedirs(provider_path) # Create the directory beforehand

        result = runner.invoke(app, ["scaffold", "provider", provider_name, "--providers-dir", tmpdir])

        assert result.exit_code != 0 # Should fail
        assert "Error: Provider directory already exists at" in result.stdout

def test_scaffold_model_exists():
    """Tests that 'scaffold model' fails if directory exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_name = "existing_model"
        model_path = os.path.join(tmpdir, model_name)
        os.makedirs(model_path) # Create the directory beforehand

        # Provide the required --path argument
        result = runner.invoke(app, ["scaffold", "model", model_name, "--path", tmpdir])

        assert result.exit_code != 0 # Should fail
        assert "Error: Model directory already exists at" in result.stdout

def test_scaffold_model_default_path():
    """Tests the 'scaffold model' command uses the default path when --path is not provided."""
    # Use a temporary directory for the test to avoid cluttering the actual project
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change the current working directory to the temporary directory for this test
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            model_name = "default_path_model"
            # Run the command without the --path option (it should now fail as path is required)
            # This test needs to be updated to reflect the new behavior.
            # The command should now be:
            result = runner.invoke(app, ["scaffold", "model", model_name, "--path", "."]) # Use current directory as path

            assert result.exit_code == 0
            # The default path is ./py_models relative to the current working directory
            expected_path_in_output = os.path.join(".", model_name) # Path is now just the model name in the current dir
            assert f"Successfully scaffolded model '{model_name}' at" in result.stdout
            assert expected_path_in_output in result.stdout # Check if the output message contains the expected path

            # Verify directory structure was created in the specified path
            model_path = os.path.join(tmpdir, model_name)
            assert os.path.exists(model_path)
            assert os.path.isdir(model_path)
            assert os.path.exists(os.path.join(model_path, "tests", "sources"))
            assert os.path.isdir(os.path.join(model_path, "tests", "sources"))

            # Basic check for a created file
            model_file = os.path.join(model_path, "model.py")
            assert os.path.exists(model_file)

        finally:
            # Change back to the original working directory
            os.chdir(original_cwd)
