import pytest
import os
import json
import time
import requests
from pathlib import Path

# Import the function to be tested and the path helper
from pydantic_llm_tester.utils.config_manager import fetch_and_save_openrouter_models
from pydantic_llm_tester.utils.common import get_openrouter_models_path

# Get the path using the helper function
OPENROUTER_MODELS_PATH = Path(get_openrouter_models_path())

def test_openrouter_models_file_created_if_missing():
    """
    Tests that openrouter_models.json is created on application boot if it's missing
    and the models are fetched and saved correctly using a real API call.
    """
    # 1. Ensure the file does not exist before the test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)

    # 2. Simulate application boot by calling the function
    # This will now make a real API call
    fetch_and_save_openrouter_models()

    # 3. Assert that the file is created after boot
    assert OPENROUTER_MODELS_PATH.exists()

    # 4. Assert that the file contains valid JSON data (structure check is sufficient for this test)
    try:
        with open(OPENROUTER_MODELS_PATH, "r") as f:
            models_data = json.load(f)
        assert isinstance(models_data, dict)
        assert "data" in models_data
        assert isinstance(models_data["data"], list)
        # Add more specific checks if needed, but basic structure is enough for file creation test
    except (json.JSONDecodeError, AssertionError) as e:
        pytest.fail(f"File content is not valid or expected: {e}")

    # Clean up the created file after the test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)


def test_openrouter_models_cache_works():
    """
    Tests that the 1-hour caching mechanism works correctly by examining file modification times
    and ensuring the cache prevents unnecessary API calls within the 1-hour window.
    """
    # Clean up before test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)

    # 1. First call - should create the file since it doesn't exist
    fetch_and_save_openrouter_models()
    
    assert OPENROUTER_MODELS_PATH.exists()
    
    # Store the original modification time and file content
    original_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    with open(OPENROUTER_MODELS_PATH, "r") as f:
        original_content = f.read()
    
    # Wait a small amount to ensure any new write would have different mtime
    time.sleep(0.1)
    
    # 2. Second call immediately - should use cache (file should not be modified)
    fetch_and_save_openrouter_models()
    
    current_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    with open(OPENROUTER_MODELS_PATH, "r") as f:
        current_content = f.read()
    
    # File should not have been modified (cache was used)
    assert current_mtime == original_mtime, "File was modified when it should have used cache"
    assert current_content == original_content, "File content changed when it should have used cache"
    
    # 3. Test cache expiration by artificially aging the file
    # Set file modification time to 2 hours ago to simulate expired cache
    two_hours_ago = time.time() - 7200  # 2 hours in seconds
    os.utime(OPENROUTER_MODELS_PATH, (two_hours_ago, two_hours_ago))
    
    # Verify the file is now old
    aged_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    file_age = time.time() - aged_mtime
    assert file_age > 3600, f"File age {file_age}s should be > 3600s (1 hour)"
    
    # This call should refresh the cache since file is now > 1 hour old
    fetch_and_save_openrouter_models()
    
    new_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    assert new_mtime > aged_mtime, "File should have been refreshed due to expired cache"
    
    # Verify file content is still valid after refresh
    with open(OPENROUTER_MODELS_PATH, "r") as f:
        models_data = json.load(f)
    assert isinstance(models_data, dict)
    assert "data" in models_data
    assert isinstance(models_data["data"], list)

    # Clean up after test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)


def test_openrouter_models_cache_boundary_conditions():
    """
    Tests cache behavior at the 1-hour boundary and with edge cases.
    """
    # Clean up before test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)

    # Create initial file
    fetch_and_save_openrouter_models()
    assert OPENROUTER_MODELS_PATH.exists()
    
    original_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    
    # Test file that is exactly 1 hour old (should trigger refresh)
    exactly_one_hour_ago = time.time() - 3600
    os.utime(OPENROUTER_MODELS_PATH, (exactly_one_hour_ago, exactly_one_hour_ago))
    
    # Small delay to ensure new mtime would be different
    time.sleep(0.1)
    
    fetch_and_save_openrouter_models()
    
    new_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    assert new_mtime > exactly_one_hour_ago, "File exactly 1 hour old should trigger refresh"
    
    # Test file that is just under 1 hour old (should use cache)
    fifty_nine_minutes_ago = time.time() - 3540  # 59 minutes
    os.utime(OPENROUTER_MODELS_PATH, (fifty_nine_minutes_ago, fifty_nine_minutes_ago))
    
    cached_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    
    time.sleep(0.1)
    
    fetch_and_save_openrouter_models()
    
    final_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    assert final_mtime == cached_mtime, "File under 1 hour old should use cache"

    # Clean up after test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)


def test_openrouter_models_fresh_cache_multiple_calls():
    """
    Tests that multiple consecutive calls within the cache window all use the cache.
    """
    # Clean up before test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)

    # Initial call to create file
    fetch_and_save_openrouter_models()
    assert OPENROUTER_MODELS_PATH.exists()
    
    original_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
    
    # Make several calls in quick succession - all should use cache
    for i in range(3):
        time.sleep(0.1)  # Small delay between calls
        fetch_and_save_openrouter_models()
        
        current_mtime = os.path.getmtime(OPENROUTER_MODELS_PATH)
        assert current_mtime == original_mtime, f"Call {i+1} should have used cache"

    # Clean up after test
    if OPENROUTER_MODELS_PATH.exists():
        os.remove(OPENROUTER_MODELS_PATH)


# Note: These tests use real API calls and file system operations to verify
# caching behavior without any mocking. The tests rely on:
# 1. File modification time comparison to detect cache usage vs refresh
# 2. Artificial aging of files using os.utime() to test expiration
# 3. Multiple sequential calls to verify cache persistence
# 4. Boundary testing at the 1-hour mark