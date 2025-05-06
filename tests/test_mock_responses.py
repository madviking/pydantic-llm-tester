"""
Tests for mock response system
"""

import json
import pytest

from src.utils.mock_responses import (
    get_mock_response, 
    mock_get_response
)


def test_get_mock_response_job_ads():
    """Test getting a mock response for job ads"""
    # Test default job ad
    response = get_mock_response("job_ads", "Some source text")
    
    # Check that the response is valid JSON
    response_data = json.loads(response)
    assert "title" in response_data
    assert "company" in response_data
    assert "location" in response_data
    
    # Check that template selection works correctly
    response = get_mock_response("job_ads", "FULL STACK DEVELOPER position")
    response_data = json.loads(response)
    assert "FULL STACK DEVELOPER" in response_data["title"]
    
    response = get_mock_response("job_ads", "SOFTWARE ENGINEER job")
    response_data = json.loads(response)
    assert "SOFTWARE ENGINEER" in response_data["title"]
    
    # Test customization based on source text
    response = get_mock_response("job_ads", "POSITION: Test Engineer\nCOMPANY: Test Corp")
    response_data = json.loads(response)
    assert response_data["title"] == "TEST ENGINEER"
    assert response_data["company"] == "Test Corp"


def test_get_mock_response_product_descriptions():
    """Test getting a mock response for product descriptions"""
    # Test default product
    response = get_mock_response("product_descriptions", "Some source text")
    
    # Check that the response is valid JSON
    response_data = json.loads(response)
    assert "name" in response_data
    assert "brand" in response_data
    assert "specifications" in response_data
    
    # Check that template selection works correctly
    response = get_mock_response("product_descriptions", "ULTRABOOK laptop details")
    response_data = json.loads(response)
    assert "UltraBook Pro X15 Laptop" == response_data["name"]
    
    response = get_mock_response("product_descriptions", "SMARTPHONE features")
    response_data = json.loads(response)
    assert "SmartPhone X Pro" == response_data["name"]
    
    # Test customization based on source text
    response = get_mock_response("product_descriptions", "PRODUCT: Test Product\nBRAND: Test Brand")
    response_data = json.loads(response)
    assert response_data["name"] == "Test Product"
    assert response_data["brand"] == "Test Brand"


def test_mock_get_response():
    """Test the mock implementation of get_response"""
    # Test job ad detection from prompt
    response = mock_get_response(
        provider="openai", 
        prompt="Extract the job details from the following text", 
        source="Senior Developer position at ABC Corp"
    )
    response_data = json.loads(response)
    assert "title" in response_data
    assert "company" in response_data
    
    # Test product detection from prompt
    response = mock_get_response(
        provider="anthropic", 
        prompt="Extract the product specifications from the following text", 
        source="New gadget from XYZ Inc"
    )
    response_data = json.loads(response)
    assert "name" in response_data
    assert "brand" in response_data
    
    # Test job ad detection from source
    response = mock_get_response(
        provider="mistral", 
        prompt="Extract information", 
        source="SOFTWARE ENGINEER job opening at ABC Corp"
    )
    response_data = json.loads(response)
    assert "SOFTWARE ENGINEER" in response_data["title"]
    
    # Test model name being passed through
    response = mock_get_response(
        provider="google", 
        prompt="Extract information", 
        source="PRODUCT: Test Product\nBRAND: Test Brand",
        model_name="test-model"
    )
    response_data = json.loads(response)
    assert response_data["name"] == "Test Product"
    assert response_data["brand"] == "Test Brand"
