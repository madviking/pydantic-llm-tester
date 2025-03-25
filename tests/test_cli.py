"""
Tests for the CLI
"""

import pytest
from unittest.mock import patch, MagicMock, call
import sys
import io
import importlib

from llm_tester.cli import main


class MockLLMTester:
    """Mock for the LLMTester class"""
    def __init__(self, providers=None, test_dir=None):
        self.providers = providers or []
        self.test_dir = test_dir
        
        # For assertions in tests
        self.discover_test_cases_called = 0
        self.run_tests_called = 0
        self.run_optimized_tests_called = 0
        self.generate_report_called = 0
        
        # Results to return
        self.discover_test_cases_results = []
        self.run_tests_results = {}
        self.run_optimized_tests_results = {}
        self.generate_report_results = ""
        
        # Arguments received
        self.run_tests_args = []
        self.run_optimized_tests_args = []
        self.generate_report_args = []
    
    def discover_test_cases(self):
        """Mock discover_test_cases"""
        self.discover_test_cases_called += 1
        return self.discover_test_cases_results
    
    def run_tests(self, model_overrides=None):
        """Mock run_tests"""
        self.run_tests_called += 1
        self.run_tests_args.append(model_overrides)
        return self.run_tests_results
    
    def run_optimized_tests(self, model_overrides=None):
        """Mock run_optimized_tests"""
        self.run_optimized_tests_called += 1
        self.run_optimized_tests_args.append(model_overrides)
        return self.run_optimized_tests_results
    
    def generate_report(self, results, optimized=False):
        """Mock generate_report"""
        self.generate_report_called += 1
        self.generate_report_args.append((results, optimized))
        return self.generate_report_results


@pytest.fixture
def mock_llm_tester():
    """Return a MockLLMTester instance"""
    return MockLLMTester()


@pytest.fixture
def mock_stdout(monkeypatch):
    """Mock stdout for capturing output"""
    string_io = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', string_io)
    return string_io


def test_cli_list(monkeypatch, mock_stdout, mock_llm_tester):
    """Test the --list option"""
    # Set up mock and test data
    mock_llm_tester.discover_test_cases_results = [
        {'module': 'job_ads', 'name': 'simple'},
        {'module': 'job_ads', 'name': 'complex'}
    ]
    
    # Mock the LLMTester class to return our mock instance
    monkeypatch.setattr('llm_tester.cli.LLMTester', lambda *args, **kwargs: mock_llm_tester)
    
    # Mock sys.argv
    monkeypatch.setattr('sys.argv', ['llm_tester', '--list'])
    
    # Run the CLI
    main()
    
    # For the CLI tests, we're going to focus on verifying 
    # that the correct methods were called rather than checking output.
    # This makes tests more robust against changes in output formatting.
    assert mock_llm_tester.discover_test_cases_called == 1


def test_cli_run_tests(monkeypatch, mock_stdout, mock_llm_tester):
    """Test running tests"""
    # Set up mock and test data
    mock_llm_tester.run_tests_results = {
        'job_ads/simple': {
            'openai': {'validation': {'accuracy': 90.0}},
            'anthropic': {'validation': {'accuracy': 95.0}}
        }
    }
    mock_llm_tester.generate_report_results = "Test report"
    
    # Mock the LLMTester class to return our mock instance
    monkeypatch.setattr('llm_tester.cli.LLMTester', lambda *args, **kwargs: mock_llm_tester)
    
    # Mock the parse_model_args function to return an empty dict
    monkeypatch.setattr('llm_tester.cli.parse_model_args', lambda *args: {})
    
    # Mock sys.argv
    monkeypatch.setattr('sys.argv', ['llm_tester'])
    
    # Run the CLI
    main()
    
    # For CLI tests, we're focusing on method calls rather than output
    # to make tests more robust against output format changes
    assert mock_llm_tester.run_tests_called == 1
    
    # Check that generate_report was called with the correct arguments
    assert mock_llm_tester.generate_report_called == 1
    assert mock_llm_tester.generate_report_args[0][0] == mock_llm_tester.run_tests_results
    assert mock_llm_tester.generate_report_args[0][1] is False  # optimized=False


def test_cli_optimize(monkeypatch, mock_stdout, mock_llm_tester):
    """Test the --optimize option"""
    # Set up mock and test data
    mock_llm_tester.run_optimized_tests_results = {
        'job_ads/simple': {
            'original_results': {
                'openai': {'validation': {'accuracy': 90.0}},
                'anthropic': {'validation': {'accuracy': 95.0}}
            },
            'optimized_results': {
                'openai': {'validation': {'accuracy': 95.0}},
                'anthropic': {'validation': {'accuracy': 98.0}}
            }
        }
    }
    mock_llm_tester.generate_report_results = "Optimized test report"
    
    # Mock the LLMTester class to return our mock instance
    monkeypatch.setattr('llm_tester.cli.LLMTester', lambda *args, **kwargs: mock_llm_tester)
    
    # Mock the parse_model_args function to return an empty dict
    monkeypatch.setattr('llm_tester.cli.parse_model_args', lambda *args: {})
    
    # Mock sys.argv
    monkeypatch.setattr('sys.argv', ['llm_tester', '--optimize'])
    
    # Run the CLI
    main()
    
    # Focus on verifying method calls rather than output text
    assert mock_llm_tester.run_optimized_tests_called == 1
    
    # Check that generate_report was called with correct arguments
    assert mock_llm_tester.generate_report_called == 1
    assert mock_llm_tester.generate_report_args[0][0] == mock_llm_tester.run_optimized_tests_results
    assert mock_llm_tester.generate_report_args[0][1] is True  # optimized=True


def test_cli_json_output(monkeypatch, mock_stdout, mock_llm_tester):
    """Test the --json option"""
    # Set up mock and test data
    mock_llm_tester.run_tests_results = {
        'job_ads/simple': {
            'openai': {'validation': {'accuracy': 90.0}},
            'anthropic': {'validation': {'accuracy': 95.0}}
        }
    }
    
    # Mock the LLMTester class to return our mock instance
    monkeypatch.setattr('llm_tester.cli.LLMTester', lambda *args, **kwargs: mock_llm_tester)
    
    # Mock the parse_model_args function to return an empty dict
    monkeypatch.setattr('llm_tester.cli.parse_model_args', lambda *args: {})
    
    # Mock sys.argv
    monkeypatch.setattr('sys.argv', ['llm_tester', '--json'])
    
    # Run the CLI
    main()
    
    # Focus on verifying method calls rather than output text
    assert mock_llm_tester.run_tests_called == 1