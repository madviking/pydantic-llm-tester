"""
Mock responses for LLM Tester

This module contains mock responses for different test modules to use
when testing without actual API access.
"""

import json
from typing import Dict, Any

# Mock responses for testing without API keys
MOCK_RESPONSES: Dict[str, str] = {
    "job_ads": """
    {
      "title": "SENIOR MACHINE LEARNING ENGINEER",
      "company": "DataVision Analytics",
      "department": "AI Research Division",
      "location": {
        "city": "Boston",
        "state": "Massachusetts",
        "country": "United States"
      },
      "salary": {
        "range": "$150,000 - $190,000",
        "currency": "USD",
        "period": "annually"
      },
      "employment_type": "Full-time",
      "experience": {
        "years": "5+ years",
        "level": "Senior"
      },
      "required_skills": [
        "Python",
        "TensorFlow/PyTorch",
        "computer vision or NLP algorithms",
        "distributed computing",
        "data preprocessing",
        "feature engineering"
      ],
      "preferred_skills": [
        "GPT models",
        "fine-tuning",
        "edge deployment"
      ],
      "education": [
        {
          "degree": "Master's degree",
          "field": "Computer Science, AI, or related field",
          "required": true
        },
        {
          "degree": "PhD",
          "field": "Machine Learning or related field",
          "required": false
        }
      ],
      "responsibilities": [
        "Design and implement novel ML architectures for complex problems",
        "Lead research projects exploring state-of-the-art approaches",
        "Mentor junior team members on ML best practices"
      ],
      "benefits": [
        {
          "name": "Comprehensive health, dental, and vision insurance",
          "description": "Includes coverage for dependents and domestic partners"
        },
        {
          "name": "401(k) matching program",
          "description": "Up to 5% match with immediate vesting"
        }
      ],
      "description": "As a Senior ML Engineer, you will be at the forefront of our AI research initiatives.",
      "application_deadline": "2025-04-30",
      "contact_info": {
        "name": "Dr. Sarah Chen",
        "email": "ml-recruiting@datavisionanalytics.com",
        "phone": "(617) 555-9876",
        "website": "https://careers.datavisionanalytics.com/ml-engineer"
      },
      "remote": true,
      "travel_required": "Occasional travel (10-15%) for conferences, team off-sites, and client meetings",
      "posting_date": "2025-03-15"
    }
    """,
    "product_descriptions": """
    {
      "id": "WE-X1-BLK",
      "name": "Wireless Earbuds X1",
      "brand": "TechGear",
      "category": "Audio Accessories",
      "price": {
        "amount": 79.99,
        "currency": "USD",
        "discount_percentage": 20.0,
        "original_amount": 99.99
      },
      "description": "Experience true wireless freedom with our X1 Wireless Earbuds.",
      "features": [
        "True wireless design",
        "Bluetooth 5.2 connectivity",
        "8-hour battery life (30 hours with charging case)",
        "Active noise cancellation"
      ],
      "specifications": [
        {
          "name": "Driver Size",
          "value": "10",
          "unit": "mm"
        },
        {
          "name": "Frequency Response",
          "value": "20Hz-20KHz"
        }
      ],
      "dimensions": {
        "length": 2.1,
        "width": 1.8,
        "height": 2.5,
        "unit": "cm"
      },
      "weight": {
        "value": 5.6,
        "unit": "g"
      },
      "colors": [
        "Midnight Black",
        "Arctic White",
        "Navy Blue"
      ],
      "images": [
        "https://techgear.com/images/wireless-earbuds-x1-black.jpg",
        "https://techgear.com/images/wireless-earbuds-x1-case.jpg"
      ],
      "shipping_info": {
        "ships_within": "1 business day",
        "shipping_type": "Free standard shipping"
      },
      "warranty": "1-year limited warranty",
      "return_policy": "30-day money-back guarantee",
      "reviews": {
        "rating": 4.6,
        "count": 352
      },
      "release_date": "2025-01-15",
      "is_bestseller": true,
      "related_products": [
        "WE-X1-TIPS",
        "WE-X1-CASE",
        "BT-SPK-10"
      ]
    }
    """
}

def get_mock_response(module: str, source: str) -> str:
    """
    Get a mock response for a given module and source text
    
    Args:
        module: The module name to get a response for
        source: The source text to use for customizing the response
        
    Returns:
        A mock response as a JSON string
    """
    if module not in MOCK_RESPONSES:
        # Default to job_ads if module not found
        module = "job_ads"
        
    mock_data = json.loads(MOCK_RESPONSES[module])
    
    # Customize the response based on the source
    if module == "job_ads":
        if "FULL STACK" in source:
            mock_data["title"] = "FULL STACK DEVELOPER"
            mock_data["company"] = "TechInnovate Solutions"
        elif "SOFTWARE ENGINEER" in source:
            mock_data["title"] = "SOFTWARE ENGINEER"
            mock_data["company"] = "CodeCraft Inc."
    elif module == "product_descriptions":
        if "ULTRABOOK" in source:
            mock_data["name"] = "UltraBook Pro X15 Laptop"
            mock_data["brand"] = "TechVantage"
            mock_data["category"] = "Laptops"
        elif "SMARTPHONE" in source:
            mock_data["name"] = "SmartPhone X Pro"
            mock_data["brand"] = "TechMobile"
            mock_data["category"] = "Smartphones"
    
    return json.dumps(mock_data, indent=2)

def mock_get_response(*args, **kwargs) -> str:
    """
    Mock implementation of get_response for ProviderManager
    
    Can be used in two ways:
    1. As a method with self: mock_get_response(self, provider, prompt, source, model_name=None)
    2. As a standalone function: mock_get_response(provider, prompt, source, model_name=None)
    
    Args:
        Either (self, provider, prompt, source, model_name=None)
        Or (provider, prompt, source, model_name=None)
        
    Returns:
        A mock response
    """
    # Parse arguments based on whether this is called as a method or function
    if len(args) >= 3 and hasattr(args[0], 'get_response'):
        # Called as method with self
        _, provider, prompt, source = args[:4]
        model_name = kwargs.get('model_name')
    elif len(args) >= 3:
        # Called as standalone function
        provider, prompt, source = args[:3]
        model_name = kwargs.get('model_name')
    else:
        # Not enough arguments
        raise ValueError(f"Not enough arguments for mock_get_response: {args}, {kwargs}")
    
    # Determine which mock response to use based on source content
    if "job" in source.lower() or "software engineer" in source.lower() or "developer" in source.lower():
        return get_mock_response("job_ads", source)
    else:
        return get_mock_response("product_descriptions", source)