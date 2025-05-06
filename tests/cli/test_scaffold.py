import pytest
import os
import tempfile
import shutil
from typer.testing import CliRunner

from llm_tester.cli.main import app # Import the main Typer app

runner = CliRunner()

# Determine the directory containing the templates relative to the test file
# Determine the directory containing the templates relative to the project root
_project_root = os.getcwd() # Get the current working directory (project root)
_templates_dir = os.path.join(_project_root, "llm_tester", "cli", "templates") # Path is llm_tester/cli/templates relative to root

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
    """Tests the 'scaffold model' command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_name = "test_model"
        result = runner.invoke(app, ["scaffold", "model", model_name, "--models-dir", tmpdir])

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

        # Check content (basic check for placeholders)
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

def test_scaffold_provider_interactive():
    """Tests the 'scaffold provider' command in interactive mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider_name = "interactive_provider"
        result = runner.invoke(app, ["scaffold", "provider", "--interactive", "--providers-dir", tmpdir], input=f"{provider_name}\n")

        assert result.exit_code == 0
        assert f"Interactive Provider Scaffolding" in result.stdout
        assert f"Enter the name of the new provider" in result.stdout
        assert f"Successfully scaffolded provider '{provider_name}' at" in result.stdout

        # Verify directory structure and files (same checks as non-interactive)
        provider_path = os.path.join(tmpdir, provider_name)
        assert os.path.exists(provider_path)
        assert os.path.isdir(provider_path)
        assert os.path.exists(os.path.join(provider_path, "tests"))
        assert os.path.isdir(os.path.join(provider_path, "tests"))

        init_file = os.path.join(provider_path, "__init__.py")
        config_file = os.path.join(provider_path, "config.json")
        provider_file = os.path.join(provider_path, "provider.py")

        assert os.path.exists(init_file)
        assert os.path.exists(config_file)
        assert os.path.exists(provider_file)

        init_content = _read_template("provider_init.py.tmpl").replace("{{provider_name}}", provider_name).replace("{{provider_name_capitalized}}", provider_name.capitalize())
        with open(init_file, "r") as f:
            assert f.read() == init_content

        config_content = _read_template("provider_config.json.tmpl").replace("{{provider_name}}", provider_name).replace("{{provider_name_upper}}", provider_name.upper())
        with open(config_file, "r") as f:
            assert f.read() == config_content

        provider_content = _read_template("provider_provider.py.tmpl").replace("{{provider_name}}", provider_name).replace("{{provider_name_capitalized}}", provider_name.capitalize()).replace("{{provider_name_upper}}", provider_name.upper())
        with open(provider_file, "r") as f:
            assert f.read() == provider_content

def test_scaffold_model_interactive():
    """Tests the 'scaffold model' command in interactive mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_name = "interactive_model"
        result = runner.invoke(app, ["scaffold", "model", "--interactive", "--models-dir", tmpdir], input=f"{model_name}\n")

        assert result.exit_code == 0
        assert f"Interactive Model Scaffolding" in result.stdout
        assert f"Enter the name of the new model" in result.stdout
        assert f"Successfully scaffolded model '{model_name}' at" in result.stdout

        # Verify directory structure and files (same checks as non-interactive)
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

        result = runner.invoke(app, ["scaffold", "model", model_name, "--models-dir", tmpdir])

        assert result.exit_code != 0 # Should fail
        assert "Error: Model directory already exists at" in result.stdout
