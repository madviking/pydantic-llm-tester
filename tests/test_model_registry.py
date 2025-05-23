import pytest
from src.pydantic_llm_tester.llms.llm_registry import LLMRegistry
from src.pydantic_llm_tester.llms.base import ModelConfig # Import ModelConfig

# Define some dummy model data for testing
dummy_model_data = {
    "provider1": {
        "model-a": ModelConfig( # Use ModelConfig
            name="model-a",
            provider="provider1",
            cost_input=0.001,
            cost_output=0.002,
            max_input_tokens=1000,
            max_output_tokens=2000,
            preferred=True,
            enabled=True,
            default=False,
            cost_category="standard"
        ),
        "model-b": ModelConfig( # Use ModelConfig
            name="model-b",
            provider="provider1",
            cost_input=0.003,
            cost_output=0.004,
            max_input_tokens=3000,
            max_output_tokens=4000,
            preferred=False,
            enabled=True,
            default=True,
            cost_category="standard"
        ),
    },
    "provider2": {
        "model-c": ModelConfig( # Use ModelConfig
            name="model-c",
            provider="provider2",
            cost_input=0.005,
            cost_output=0.006,
            max_input_tokens=5000,
            max_output_tokens=6000,
            preferred=True,
            enabled=True,
            default=False,
            cost_category="premium"
        ),
        "model-d-disabled": ModelConfig( # A disabled model
            name="model-d-disabled",
            provider="provider2",
            cost_input=0.007,
            cost_output=0.008,
            max_input_tokens=7000,
            max_output_tokens=8000,
            preferred=False,
            enabled=False,
            default=False,
            cost_category="premium"
        ),
    },
}

@pytest.fixture
def model_registry():
    """Fixture to provide a fresh LLMRegistry instance for each test."""
    return LLMRegistry()

def test_store_and_retrieve_model_data(model_registry):
    """Tests storing and retrieving model data for a provider."""
    provider_name = "provider1"
    models = dummy_model_data[provider_name]

    model_registry.store_provider_models(provider_name, models)

    retrieved_models = model_registry.get_provider_models(provider_name)

    assert retrieved_models is not None
    assert len(retrieved_models) == len(models)
    for model_name, model_details in models.items():
        assert model_name in retrieved_models
        assert retrieved_models[model_name] == model_details

def test_retrieve_specific_model(model_registry):
    """Tests retrieving a specific model's details."""
    provider_name = "provider1"
    model_name = "model-a"
    expected_details = dummy_model_data[provider_name][model_name]

    model_registry.store_provider_models(provider_name, dummy_model_data[provider_name])

    retrieved_details = model_registry.get_model_details(provider_name, model_name)

    assert retrieved_details is not None
    assert retrieved_details == expected_details

def test_retrieve_nonexistent_provider(model_registry):
    """Tests retrieving models for a provider that hasn't been stored."""
    provider_name = "nonexistent_provider"
    # According to the new implementation, get_provider_models should return an empty dict
    # rather than raising an exception for nonexistent providers
    result = model_registry.get_provider_models(provider_name)
    assert isinstance(result, dict)
    assert len(result) == 0

def test_retrieve_nonexistent_model(model_registry):
    """Tests retrieving a model that doesn't exist for a stored provider."""
    provider_name = "provider1"
    model_name = "nonexistent-model"

    model_registry.store_provider_models(provider_name, dummy_model_data[provider_name])

    # Expecting a ValueError when trying to get a non-existent model
    with pytest.raises(ValueError, match=f"Model '{model_name}' not found for provider '{provider_name}'."):
        model_registry.get_model_details(provider_name, model_name)

def test_retrieve_model_from_provider_with_no_models(model_registry):
    """Tests retrieving a model from a provider that exists but has no models stored."""
    provider_name = "provider_with_no_models"
    model_name = "some-model"

    # Store the provider with an empty dictionary of models
    model_registry.store_provider_models(provider_name, {})

    # Expecting a ValueError when trying to get a model from this provider
    with pytest.raises(ValueError, match=f"Model '{model_name}' not found for provider '{provider_name}'."):
        model_registry.get_model_details(provider_name, model_name)

import time
from unittest.mock import patch

# Add more tests for edge cases, different data structures, etc. as needed.

def test_cache_stores_timestamp(model_registry):
    """Tests that storing model data includes a timestamp."""
    provider_name = "provider1"
    models = dummy_model_data[provider_name]

    with patch('time.time', return_value=1678886400): # Mock current time
        model_registry.store_provider_models(provider_name, models)

    # Access the internal cache to check for the timestamp
    # This might require making _model_data accessible for testing, or adding a method to LLMRegistry
    # For now, let's assume we can access it for testing purposes.
    # In a real scenario, we might add a method like `_get_cache_entry(provider_name)` for testing.
    # Assuming _model_data is accessible for testing:
    assert provider_name in model_registry._model_data # Check if provider is in the internal data structure
    # The actual timestamp might be stored alongside the model data.
    # Let's refine this test after implementing the caching structure in LLMRegistry.
    # For now, this test serves as a placeholder to remind us to test the timestamp storage.
    pass # Placeholder - will implement properly after LLMRegistry is updated

def test_cache_retrieves_within_expiry(model_registry):
    """Tests retrieving cached data within the expiry period."""
    provider_name = "provider1"
    models = dummy_model_data[provider_name]
    expiry_seconds = 60 # Define a hypothetical expiry time

    with patch('time.time', return_value=1678886400):
        model_registry.store_provider_models(provider_name, models)

    with patch('time.time', return_value=1678886400 + expiry_seconds - 10): # Retrieve before expiry
        # We need a method in LLMRegistry to check if data is fresh/cached
        # Let's assume a method like `is_cache_fresh(provider_name, expiry_seconds)` exists
        # assert model_registry.is_cache_fresh(provider_name, expiry_seconds)
        # And that get_provider_models/get_model_details use the cache if fresh.
        # For now, this is a placeholder.
        pass # Placeholder

def test_cache_expires_after_expiry(model_registry):
    """Tests that cached data is considered expired after the expiry period."""
    provider_name = "provider1"
    models = dummy_model_data[provider_name]
    expiry_seconds = 60

    with patch('time.time', return_value=1678886400):
        model_registry.store_provider_models(provider_name, models)

    with patch('time.time', return_value=1678886400 + expiry_seconds + 1): # Retrieve after expiry
        # We need a method in LLMRegistry to check if data is fresh/cached
        # Let's assume a method like `is_cache_fresh(provider_name, expiry_seconds)` exists
        # assert not model_registry.is_cache_fresh(provider_name, expiry_seconds)
        # And that get_provider_models/get_model_details handle expired cache (e.g., trigger refresh or raise error).
        # For now, this is a placeholder.
        pass # Placeholder

# Note: Proper implementation of these tests requires modifying LLMRegistry
# to include the caching logic and potentially adding methods to check cache status for testing.
# The tests in 2.5 are primarily about defining the *behavior* we expect from the caching mechanism.

def test_get_all_model_details_empty_registry(model_registry):
    """Tests that get_all_model_details returns an empty list when registry is empty."""
    all_models = model_registry.get_all_model_details()
    assert isinstance(all_models, list)
    assert len(all_models) == 0

def test_get_all_model_details(model_registry):
    """Tests retrieving all model details from multiple providers."""
    # Store dummy model data for multiple providers
    for provider, models in dummy_model_data.items():
        model_registry.store_provider_models(provider, models)

    # Get all model details
    all_models = model_registry.get_all_model_details()

    # Verify result structure and content
    assert isinstance(all_models, list)
    
    # Calculate expected number of models (enabled models only)
    expected_model_count = sum(1 for provider in dummy_model_data.values() 
                              for model in provider.values() 
                              if model.enabled)
                              
    assert len(all_models) == expected_model_count
    
    # Verify each model in the result
    for model in all_models:
        # Each item should be a ModelConfig
        assert isinstance(model, ModelConfig)
        assert model.enabled == True  # Only enabled models should be included
        
        # Verify model data matches source
        provider_models = dummy_model_data.get(model.provider, {})
        assert model.name in provider_models, f"Model {model.name} not found in source data for {model.provider}"
        source_model = provider_models.get(model.name)
        
        # Compare key attributes
        assert model.cost_input == source_model.cost_input
        assert model.cost_output == source_model.cost_output
        assert model.max_input_tokens == source_model.max_input_tokens
        assert model.max_output_tokens == source_model.max_output_tokens
