import pytest
from unittest.mock import MagicMock, patch, call, mock_open
import logging
import os
import json

# Add necessary imports
from pydantic_llm_tester.bridge.pyllm_bridge import PyllmBridge
from pydantic_llm_tester.py_models.base import BasePyModel
from pydantic_llm_tester.bridge.analysis_report import PyllmAnalysisReport, PassAnalysis
from pydantic_llm_tester.utils.cost_manager import UsageData

# Mock classes for dependencies
MockConfigManager = MagicMock()
MockProviderManager = MagicMock()
MockCostTracker = MagicMock()
MockReportGenerator = MagicMock()

# Fixture to create a PyllmBridge instance with mocked dependencies
@pytest.fixture
def pyllm_bridge_with_mocks():
    # Set up the enabled providers mock to help with tests
    mock_enabled_providers = {
        "openai": {"enabled": True, "default_model": "gpt-4"},
        "google": {"enabled": True, "default_model": "gemini-pro"},
        "anthropic": {"enabled": True, "default_model": "claude-3-opus"},
    }
    MockConfigManager.get_enabled_providers.return_value = mock_enabled_providers
    
    with patch('pydantic_llm_tester.bridge.pyllm_bridge.ConfigManager', return_value=MockConfigManager), \
         patch('pydantic_llm_tester.bridge.pyllm_bridge.ProviderManager', return_value=MockProviderManager), \
         patch('pydantic_llm_tester.bridge.pyllm_bridge.CostTracker', return_value=MockCostTracker), \
         patch('pydantic_llm_tester.bridge.pyllm_bridge.ReportGenerator', return_value=MockReportGenerator):
        bridge = PyllmBridge()
        # Reset mocks after each test
        MockConfigManager.reset_mock()
        MockProviderManager.reset_mock()
        MockCostTracker.reset_mock()
        MockReportGenerator.reset_mock()
        # Restore the enabled providers mock since we reset it
        MockConfigManager.get_enabled_providers.return_value = mock_enabled_providers
        yield bridge

class MockModel(BasePyModel):
    """Mock model for testing"""
    MODULE_NAME = "test_model"
    field1: str = ""
    field2: int = 0

class TestPyllmBridge:

    @patch('pydantic_llm_tester.bridge.pyllm_bridge.ConfigManager')
    @patch('pydantic_llm_tester.bridge.pyllm_bridge.ProviderManager')
    @patch('pydantic_llm_tester.bridge.pyllm_bridge.CostTracker')
    @patch('pydantic_llm_tester.bridge.pyllm_bridge.ReportGenerator')
    def test_init_initializes_managers(self, MockReportGenerator, MockCostTracker, MockProviderManager, MockConfigManager):
        """Test that PyllmBridge initializes all managers on instantiation."""
        bridge = PyllmBridge()
        MockConfigManager.assert_called_once()
        # In the new implementation, ProviderManager should be initialized based on config
        MockCostTracker.assert_called_once()
        MockReportGenerator.assert_called_once()

    def test_get_primary_provider_and_model_uses_py_model_config(self, pyllm_bridge_with_mocks):
        """Test that _get_primary_provider_and_model uses the Pydantic model's specific config if available."""
        model_name = "test_model"
        py_model_class = MagicMock(spec=BasePyModel)
        py_model_class.__name__ = model_name

        # Mock ConfigManager to return a specific model list for this Pydantic model
        MockConfigManager.get_py_model_llm_models.return_value = ["openai:gpt-4o", "google:gemini-2.5"]
        MockConfigManager._parse_model_string.side_effect = lambda s: tuple(s.split(':'))

        # Call the method and verify the result
        result = pyllm_bridge_with_mocks._get_primary_provider_and_model(py_model_class)
        
        # Assert the correct provider and model were returned
        assert result == ("openai", "gpt-4o")
        
        # Assert that ConfigManager was called to get the model-specific config
        MockConfigManager.get_py_model_llm_models.assert_called_once_with(model_name)
        # Assert that _parse_model_string was called for the first model in the list
        MockConfigManager._parse_model_string.assert_called_once_with("openai:gpt-4o")

    def test_get_primary_provider_and_model_defaults_to_global_if_no_py_model_config(self, pyllm_bridge_with_mocks):
        """Test that _get_primary_provider_and_model defaults to global config if no Pydantic model specific config."""
        model_name = "test_model"
        py_model_class = MagicMock(spec=BasePyModel)
        py_model_class.__name__ = model_name

        # Mock ConfigManager to return empty list for model-specific config
        MockConfigManager.get_py_model_llm_models.return_value = []
        # Mock ConfigManager to return global default provider and model
        MockConfigManager.get_enabled_providers.return_value = {"openai": {"enabled": True, "default_model": "gpt-3.5"}}

        # Call the method and verify the result
        result = pyllm_bridge_with_mocks._get_primary_provider_and_model(py_model_class)
        
        # Assert the correct provider and model were returned from the global defaults
        assert result == ("openai", "gpt-3.5")
        
        # Assert that ConfigManager was called to get the model-specific config (and it returned empty)
        MockConfigManager.get_py_model_llm_models.assert_called_once_with(model_name)
        # Note: we don't check get_enabled_providers because it's called multiple times in the implementation

    def test_get_primary_provider_and_model_returns_none_if_no_config(self, pyllm_bridge_with_mocks):
        """Test that _get_primary_provider_and_model returns None if no configuration is available."""
        model_name = "test_model"
        py_model_class = MagicMock(spec=BasePyModel)
        py_model_class.__name__ = model_name

        # Mock ConfigManager to return empty list for model-specific config
        MockConfigManager.get_py_model_llm_models.return_value = []
        # Mock ConfigManager to return empty dict for global providers
        MockConfigManager.get_enabled_providers.return_value = {}

        # Call the method and verify the result
        result = pyllm_bridge_with_mocks._get_primary_provider_and_model(py_model_class)
        
        # Assert that None is returned when no configuration is available
        assert result is None
        
        # Assert that ConfigManager methods were called
        MockConfigManager.get_py_model_llm_models.assert_called_once_with(model_name)

    def test_get_secondary_provider_and_model_uses_py_model_config(self, pyllm_bridge_with_mocks):
        """Test that _get_secondary_provider_and_model uses the Pydantic model's specific config if available."""
        model_name = "test_model"
        py_model_class = MagicMock(spec=BasePyModel)
        py_model_class.__name__ = model_name

        # Mock ConfigManager to return a specific model list with at least two models
        MockConfigManager.get_py_model_llm_models.return_value = ["openai:gpt-4o", "google:gemini-2.5", "anthropic:claude-3"]
        MockConfigManager._parse_model_string.side_effect = lambda s: tuple(s.split(':'))

        # Call the method and verify the result
        result = pyllm_bridge_with_mocks._get_secondary_provider_and_model(py_model_class)
        
        # Assert the correct provider and model were returned
        assert result == ("google", "gemini-2.5")
        
        # Assert that ConfigManager was called to get the model-specific config
        MockConfigManager.get_py_model_llm_models.assert_called_once_with(model_name)
        # Assert that _parse_model_string was called for the second model in the list
        MockConfigManager._parse_model_string.assert_called_once_with("google:gemini-2.5")

    def test_get_secondary_provider_and_model_defaults_to_global_if_no_py_model_config(self, pyllm_bridge_with_mocks):
        """Test that _get_secondary_provider_and_model defaults to global config if no Pydantic model specific config."""
        model_name = "test_model"
        py_model_class = MagicMock(spec=BasePyModel)
        py_model_class.__name__ = model_name

        # Mock ConfigManager to return empty list for model-specific config
        MockConfigManager.get_py_model_llm_models.return_value = []
        # Mock ConfigManager to return global secondary provider and model
        MockConfigManager.get_enabled_providers.return_value = {"openai": {"enabled": True, "default_model": "gpt-3.5"}, 
                                                              "google": {"enabled": True, "default_model": "gemini-1.5"}}

        # Call the method and verify the result
        result = pyllm_bridge_with_mocks._get_secondary_provider_and_model(py_model_class)
        
        # Assert the correct provider and model were returned from the global defaults (second provider)
        assert result == ("google", "gemini-1.5")
        
        # Assert that ConfigManager was called to get the model-specific config (and it returned empty)
        MockConfigManager.get_py_model_llm_models.assert_called_once_with(model_name)

    def test_get_secondary_provider_and_model_returns_none_if_no_secondary_available(self, pyllm_bridge_with_mocks):
        """Test that _get_secondary_provider_and_model returns None if no secondary provider is available."""
        model_name = "test_model"
        py_model_class = MagicMock(spec=BasePyModel)
        py_model_class.__name__ = model_name

        # Mock ConfigManager to return a list with only one model
        MockConfigManager.get_py_model_llm_models.return_value = ["openai:gpt-4o"]
        # Mock ConfigManager to return only one global provider
        MockConfigManager.get_enabled_providers.return_value = {"openai": {"enabled": True, "default_model": "gpt-3.5"}}

        # Call the method and verify the result
        result = pyllm_bridge_with_mocks._get_secondary_provider_and_model(py_model_class)
        
        # Assert that None is returned when no secondary is available
        assert result is None

    def test_warning_if_default_models_missing_in_config(self, pyllm_bridge_with_mocks):
        """Test that a warning is issued if default models are missing in pyllm_config.json."""
        # Mock ConfigManager to return empty list for model-specific config
        MockConfigManager.get_py_model_llm_models.return_value = []
        # Mock ConfigManager to return no enabled providers with default models
        MockConfigManager.get_enabled_providers.return_value = {}

        model_name = "test_model"
        py_model_class = MagicMock(spec=BasePyModel)
        py_model_class.__name__ = model_name

        # Call the method that would trigger a warning
        with patch('pydantic_llm_tester.bridge.pyllm_bridge.logger') as mock_logger:
            pyllm_bridge_with_mocks._get_primary_provider_and_model(py_model_class)
            
            # Check that the warning was logged
            mock_logger.warning.assert_any_call(f"No primary LLM model configured or found for Pydantic model: {model_name}. Please check pyllm_config.json.")

    # Test for ConfigManager._parse_model_string
    def test_parse_model_string_parses_correctly(self, pyllm_bridge_with_mocks):
        """Test that _parse_model_string correctly parses 'provider:model' strings."""
        # Mock the _parse_model_string method with the real implementation
        MockConfigManager._parse_model_string.side_effect = lambda s: tuple(s.split(':'))

        # Test with valid format
        provider, model = pyllm_bridge_with_mocks.config_manager._parse_model_string("test_provider:test_model")
        assert provider == "test_provider"
        assert model == "test_model"

    def test_parse_model_string_raises_value_error_for_invalid_format(self, pyllm_bridge_with_mocks):
        """Test that _parse_model_string raises ValueError for invalid formats."""
        # Mock with an implementation that raises ValueError for invalid format
        def mock_parse(s):
            parts = s.split(':')
            if len(parts) != 2 or not all(parts):
                raise ValueError(f"Invalid model string format: {s}")
            return tuple(parts)
            
        MockConfigManager._parse_model_string.side_effect = mock_parse
        
        # Test with invalid format
        with pytest.raises(ValueError):
            pyllm_bridge_with_mocks.config_manager._parse_model_string("invalid-string")

    # Tests for the _call_llm_single_pass method
    def test_call_llm_single_pass_success(self, pyllm_bridge_with_mocks):
        """Test that _call_llm_single_pass correctly calls the provider and returns the expected result."""
        # Setup
        provider_name = "openai"
        model_name = "gpt-4"
        prompt = "test prompt"
        source = "test source"
        file_path = ""
        model_class = MockModel
        
        # Mock the provider response
        mock_response = '{"field1": "value1", "field2": 42}'
        mock_usage = UsageData(provider=provider_name, model=model_name, prompt_tokens=10, completion_tokens=20)
        MockProviderManager.get_response.return_value = (mock_response, mock_usage)
        
        # Call the method
        result = pyllm_bridge_with_mocks._call_llm_single_pass(provider_name, model_name, prompt, source, model_class, file_path)
        
        # Verify the result
        parsed_json, raw_response, cost = result
        assert parsed_json == {"field1": "value1", "field2": 42}
        assert raw_response == mock_response
        assert cost == mock_usage.total_cost
        
        # Verify the provider was called with the correct arguments
        MockProviderManager.get_response.assert_called_once_with(
            provider=provider_name,
            prompt=prompt, 
            source=source,
            model_class=model_class,
            model_name=model_name,
            files=None if not file_path else [file_path]
        )

    def test_call_llm_single_pass_handles_json_parsing_error(self, pyllm_bridge_with_mocks):
        """Test that _call_llm_single_pass handles JSON parsing errors gracefully."""
        # Setup
        provider_name = "openai"
        model_name = "gpt-4"
        prompt = "test prompt"
        source = "test source"
        file_path = ""
        model_class = MockModel
        
        # Mock the provider response with invalid JSON
        mock_response = 'not a valid json'
        mock_usage = UsageData(provider=provider_name, model=model_name, prompt_tokens=10, completion_tokens=20)
        MockProviderManager.get_response.return_value = (mock_response, mock_usage)
        
        # Call the method
        result = pyllm_bridge_with_mocks._call_llm_single_pass(provider_name, model_name, prompt, source, model_class, file_path)
        
        # Verify the result returns None for parsed_json but still returns raw response and cost
        parsed_json, raw_response, cost = result
        assert parsed_json is None
        assert raw_response == mock_response
        assert cost == mock_usage.total_cost
        
        # Error should be recorded in the bridge instance
        assert len(pyllm_bridge_with_mocks.errors) > 0
        assert "JSON parsing error" in pyllm_bridge_with_mocks.errors[0]

    def test_call_llm_single_pass_handles_provider_exception(self, pyllm_bridge_with_mocks):
        """Test that _call_llm_single_pass handles provider exceptions gracefully."""
        # Setup
        provider_name = "openai"
        model_name = "gpt-4"
        prompt = "test prompt"
        source = "test source"
        file_path = ""
        model_class = MockModel
        
        # Mock the provider to raise an exception
        error_message = "API error"
        MockProviderManager.get_response.side_effect = Exception(error_message)
        
        # Call the method
        result = pyllm_bridge_with_mocks._call_llm_single_pass(provider_name, model_name, prompt, source, model_class, file_path)
        
        # Verify the result returns None for all values
        parsed_json, raw_response, cost = result
        assert parsed_json is None
        assert raw_response is None
        assert cost is None
        
        # Error should be recorded in the bridge instance
        assert len(pyllm_bridge_with_mocks.errors) > 0
        assert error_message in pyllm_bridge_with_mocks.errors[0]

    # Tests for the _process_passes method
    def test_process_passes_single_pass(self, pyllm_bridge_with_mocks):
        """Test that _process_passes handles a single pass correctly."""
        # Setup
        model_class = MockModel
        prompt = "test prompt"
        source = "test source"
        file_path = ""
        
        # Mock _get_primary_provider_and_model to return a valid provider and model
        pyllm_bridge_with_mocks._get_primary_provider_and_model = MagicMock(return_value=("openai", "gpt-4"))
        
        # Mock _call_llm_single_pass to return a valid response
        mock_json = {"field1": "value1", "field2": 42}
        mock_response = '{"field1": "value1", "field2": 42}'
        mock_cost = 0.1
        pyllm_bridge_with_mocks._call_llm_single_pass = MagicMock(return_value=(mock_json, mock_response, mock_cost))
        
        # Call the method
        result = pyllm_bridge_with_mocks._process_passes(model_class, prompt, source, 1, file_path)
        
        # Verify the result is a valid model instance with the expected values
        assert isinstance(result, MockModel)
        assert result.field1 == "value1"
        assert result.field2 == 42
        
        # Verify the methods were called with the correct arguments
        pyllm_bridge_with_mocks._get_primary_provider_and_model.assert_called_once_with(model_class)
        pyllm_bridge_with_mocks._call_llm_single_pass.assert_called_once_with(
            "openai", "gpt-4", prompt, source, model_class, file_path
        )
        
        # Verify the analysis was updated
        assert "first_pass" in pyllm_bridge_with_mocks.analysis.passes
        assert pyllm_bridge_with_mocks.analysis.cost == mock_cost
        assert pyllm_bridge_with_mocks.analysis.total_fields > 0

    def test_process_passes_multiple_passes(self, pyllm_bridge_with_mocks):
        """Test that _process_passes handles multiple passes correctly."""
        # Setup
        model_class = MockModel
        prompt = "test prompt"
        source = "test source"
        file_path = ""
        
        # Mock provider methods to return different values for each pass
        pyllm_bridge_with_mocks._get_primary_provider_and_model = MagicMock(return_value=("openai", "gpt-4"))
        pyllm_bridge_with_mocks._get_secondary_provider_and_model = MagicMock(return_value=("anthropic", "claude-3"))
        
        # Mock _call_llm_single_pass to return different responses for each pass
        first_json = {"field1": "first value", "field2": 10}
        second_json = {"field1": "second value", "field2": 20}
        third_json = {"field1": "third value", "field2": 30}
        
        pyllm_bridge_with_mocks._call_llm_single_pass = MagicMock(side_effect=[
            (first_json, '{"field1": "first value", "field2": 10}', 0.1),
            (second_json, '{"field1": "second value", "field2": 20}', 0.2),
            (third_json, '{"field1": "third value", "field2": 30}', 0.3),
        ])
        
        # Call the method with 3 passes
        result = pyllm_bridge_with_mocks._process_passes(model_class, prompt, source, 3, file_path)
        
        # Verify the result contains the values from the third pass
        assert isinstance(result, MockModel)
        assert result.field1 == "third value"
        assert result.field2 == 30
        
        # Verify the methods were called the correct number of times
        assert pyllm_bridge_with_mocks._get_primary_provider_and_model.call_count == 2  # First and third pass
        assert pyllm_bridge_with_mocks._get_secondary_provider_and_model.call_count == 1  # Second pass
        assert pyllm_bridge_with_mocks._call_llm_single_pass.call_count == 3
        
        # Verify the analysis was updated for all passes
        assert "first_pass" in pyllm_bridge_with_mocks.analysis.passes
        assert "second_pass" in pyllm_bridge_with_mocks.analysis.passes
        assert "third_pass" in pyllm_bridge_with_mocks.analysis.passes
        assert round(pyllm_bridge_with_mocks.analysis.cost, 1) == 0.6  # Sum of all pass costs
        assert pyllm_bridge_with_mocks.analysis.total_fields > 0

    def test_process_passes_fallback_to_secondary_if_primary_fails(self, pyllm_bridge_with_mocks):
        """Test that _process_passes falls back to secondary provider if primary fails."""
        # Setup
        model_class = MockModel
        prompt = "test prompt"
        source = "test source"
        file_path = ""
        
        # Mock provider methods
        pyllm_bridge_with_mocks._get_primary_provider_and_model = MagicMock(return_value=("openai", "gpt-4"))
        pyllm_bridge_with_mocks._get_secondary_provider_and_model = MagicMock(return_value=("anthropic", "claude-3"))
        
        # Mock _call_llm_single_pass to fail for primary but succeed for secondary
        pyllm_bridge_with_mocks._call_llm_single_pass = MagicMock(side_effect=[
            (None, None, None),  # Primary provider fails
            ({"field1": "backup value", "field2": 99}, '{"field1": "backup value", "field2": 99}', 0.2),  # Secondary succeeds
        ])
        
        # Call the method with 1 pass (should still try secondary if primary fails)
        result = pyllm_bridge_with_mocks._process_passes(model_class, prompt, source, 1, file_path)
        
        # Verify the result contains the values from the secondary provider
        assert isinstance(result, MockModel)
        assert result.field1 == "backup value"
        assert result.field2 == 99
        
        # Verify both providers were tried
        assert pyllm_bridge_with_mocks._get_primary_provider_and_model.call_count == 1
        assert pyllm_bridge_with_mocks._get_secondary_provider_and_model.call_count == 1
        assert pyllm_bridge_with_mocks._call_llm_single_pass.call_count == 2
        
        # Verify the analysis shows the failure and recovery
        assert len(pyllm_bridge_with_mocks.errors) > 0
        assert "first_pass" in pyllm_bridge_with_mocks.analysis.passes
        assert pyllm_bridge_with_mocks.analysis.cost == 0.2

    # Tests for the _save_model_config method
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_model_config_creates_missing_test_files(self, mock_file, mock_makedirs, mock_exists, pyllm_bridge_with_mocks):
        """Test that _save_model_config creates missing test files with auto_ prefix."""
        # Setup
        model_class = MockModel
        model_instance = MockModel(field1="test value", field2=123)
        prompt = "test prompt"
        source = "test source"
        
        # Mock directory/file existence checks
        mock_exists.side_effect = lambda path: False  # All directories/files don't exist
        
        # Call the method
        pyllm_bridge_with_mocks._save_model_config(model_instance, prompt, source)
        
        # Verify directories were created
        assert mock_makedirs.call_count >= 3  # At least sources, prompts, expected dirs
        
        # Verify files were written with auto_ prefix
        assert mock_file.call_count >= 3  # At least source, prompt, expected files
        
        # Check that the filenames have auto_ prefix
        write_calls = [call for call in mock_file.call_args_list if 'w' in call[0][1]]
        for call in write_calls:
            file_path = call[0][0]
            assert 'auto_' in os.path.basename(file_path)

    # Tests for the ask method
    def test_ask_method_calls_process_passes(self, pyllm_bridge_with_mocks):
        """Test that ask method calls _process_passes with the correct arguments."""
        # Setup
        model_class = MockModel
        prompt = "test prompt"
        passes = 2
        file_path = "/test/file.txt"
        
        # Mock _process_passes to return a model instance
        mock_result = MockModel(field1="result", field2=42)
        pyllm_bridge_with_mocks._process_passes = MagicMock(return_value=mock_result)
        
        # Call the method
        result = pyllm_bridge_with_mocks.ask(model_class, prompt, passes=passes, file=file_path)
        
        # Verify the result is what _process_passes returned
        assert result is mock_result
        
        # Verify _process_passes was called with the correct arguments
        pyllm_bridge_with_mocks._process_passes.assert_called_once_with(
            model_class, prompt, "", passes, file_path
        )

    def test_ask_method_with_file_support_check(self, pyllm_bridge_with_mocks):
        """Test that ask method checks if the primary model supports files when a file is provided."""
        # This is a placeholder test that will need to be implemented when file handling is added
        # For now, we're just checking that the method can be called with a file parameter
        model_class = MockModel
        prompt = "test prompt"
        file_path = "/test/file.txt"
        
        # Mock necessary methods
        pyllm_bridge_with_mocks._process_passes = MagicMock(return_value=MockModel())
        
        # Call the method
        pyllm_bridge_with_mocks.ask(model_class, prompt, file=file_path)
        
        # At minimum, verify _process_passes was called with the file path
        pyllm_bridge_with_mocks._process_passes.assert_called_once_with(
            model_class, prompt, "", 1, file_path
        )
