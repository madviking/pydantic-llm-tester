#!/usr/bin/env python3
"""
Example of running LLM Tester with mock responses (no API keys needed)
Including the new product descriptions model
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the path to import llm_tester
sys.path.append(str(Path(__file__).parent.parent))

from llm_tester import LLMTester

# Sample responses for mocking
JOB_AD_RESPONSE = """
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
    "feature engineering",
    "ML system architecture",
    "ML optimization",
    "statistics",
    "linear algebra"
  ],
  "preferred_skills": [
    "GPT models",
    "fine-tuning",
    "edge deployment",
    "ML infrastructure",
    "MLOps",
    "Cloud platforms (AWS SageMaker, Google AI Platform)",
    "data annotation workflows"
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
    "Mentor junior team members on ML best practices",
    "Collaborate with product teams to translate research into valuable features",
    "Stay current with ML research and evaluate new techniques",
    "Optimize models for performance and deployment constraints",
    "Contribute to research papers and patents"
  ],
  "benefits": [
    {
      "name": "Comprehensive health, dental, and vision insurance",
      "description": "Includes coverage for dependents and domestic partners"
    },
    {
      "name": "401(k) matching program",
      "description": "Up to 5% match with immediate vesting"
    },
    {
      "name": "Flexible work arrangements",
      "description": "Option for 2 days remote work per week"
    },
    {
      "name": "Professional development budget",
      "description": "$5,000 annual stipend for conferences, courses, and certifications"
    },
    {
      "name": "Generous paid time off",
      "description": "4 weeks vacation, plus sick leave and holidays"
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
"""

PRODUCT_RESPONSE = """
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
  "description": "Experience true wireless freedom with our X1 Wireless Earbuds. These compact, lightweight earbuds deliver premium sound quality with deep bass and crystal-clear highs. The ergonomic design ensures a comfortable fit for extended listening sessions.",
  "features": [
    "True wireless design",
    "Bluetooth 5.2 connectivity",
    "8-hour battery life (30 hours with charging case)",
    "Active noise cancellation",
    "Touch controls",
    "IPX7 waterproof rating",
    "Built-in microphones for calls",
    "Voice assistant compatible"
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
    },
    {
      "name": "Battery Capacity",
      "value": "55mAh (earbuds), 500mAh (case)"
    },
    {
      "name": "Charging Time",
      "value": "1.5",
      "unit": "hours"
    },
    {
      "name": "Bluetooth Range",
      "value": "10",
      "unit": "meters"
    },
    {
      "name": "Weight",
      "value": "5.6",
      "unit": "g"
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
    "https://techgear.com/images/wireless-earbuds-x1-case.jpg",
    "https://techgear.com/images/wireless-earbuds-x1-fit.jpg"
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

LAPTOP_RESPONSE = """
{
  "id": "TX15-2025-PRO",
  "name": "UltraBook Pro X15 Laptop (2025 Model)",
  "brand": "TechVantage Electronics",
  "category": "Laptops",
  "subcategory": "Premium Laptops",
  "price": {
    "amount": 1699.99,
    "currency": "USD",
    "discount_percentage": 10.0,
    "original_amount": 1899.99
  },
  "description": "The UltraBook Pro X15 represents the pinnacle of portable computing technology. With its stunning 15.6-inch 4K OLED display, you'll enjoy vibrant colors and perfect blacks for an immersive visual experience.",
  "features": [
    "15.6\\\" 4K OLED Display (3840x2160) with 100% DCI-P3 color gamut",
    "Intel Core i9-13900H processor (14 cores, up to 5.4GHz)",
    "NVIDIA GeForce RTX 4070 with 8GB GDDR6",
    "32GB DDR5-5200MHz RAM",
    "2TB PCIe Gen4 NVMe SSD",
    "Windows 11 Pro pre-installed",
    "Thunderbolt 4, USB-C, HDMI 2.1, and SD card reader",
    "Backlit RGB keyboard with 1.5mm key travel",
    "1080p webcam with IR for Windows Hello",
    "Wi-Fi 6E and Bluetooth 5.3",
    "99.6Whr battery with up to 10 hours of usage"
  ],
  "specifications": [
    {
      "name": "Processor",
      "value": "Intel Core i9-13900H (14 cores: 6 performance + 8 efficiency)"
    },
    {
      "name": "Graphics",
      "value": "NVIDIA GeForce RTX 4070 with 8GB GDDR6"
    },
    {
      "name": "Memory",
      "value": "32GB DDR5-5200MHz (soldered)"
    },
    {
      "name": "Storage",
      "value": "2TB PCIe Gen4 NVMe SSD"
    },
    {
      "name": "Display",
      "value": "15.6\\\" 4K OLED (3840x2160), 400 nits, 100% DCI-P3"
    }
  ],
  "dimensions": {
    "length": 13.6,
    "width": 9.3,
    "height": 0.67,
    "unit": "inches"
  },
  "weight": {
    "value": 3.8,
    "unit": "pounds"
  },
  "colors": [
    "Midnight Black",
    "Platinum Silver",
    "Cobalt Blue"
  ],
  "images": [
    "https://techvantage.com/images/ultrabook-pro-x15-front.jpg",
    "https://techvantage.com/images/ultrabook-pro-x15-angle.jpg"
  ],
  "availability": "In Stock",
  "shipping_info": {
    "ships_within": "1-2 business days",
    "shipping_type": "Free expedited shipping (2-3 days)"
  },
  "warranty": "2-year limited hardware warranty",
  "release_date": "2025-03-15",
  "is_bestseller": true,
  "related_products": [
    "TX15-DOCK",
    "TX-PRO-BAG",
    "TX-SLEEVE-15"
  ]
}
"""

# Mock the get_response method to return a fixed response based on the test case
def mock_get_response(self, provider, prompt, source, model_name=None):
    # For simple job ads
    if "FULL STACK DEVELOPER" in source:
        resp = json.loads(JOB_AD_RESPONSE)
        resp["title"] = "FULL STACK DEVELOPER"
        resp["company"] = "TechInnovate Solutions"
        return json.dumps(resp)
    # For complex job ads
    elif "MACHINE LEARNING ENGINEER" in source:
        return JOB_AD_RESPONSE
    # For simple product
    elif "WIRELESS EARBUDS X1" in source:
        return PRODUCT_RESPONSE
    # For complex product
    elif "ULTRABOOK PRO X15" in source:
        return LAPTOP_RESPONSE
    # Default response
    return JOB_AD_RESPONSE

def main():
    """Main function"""
    # List of providers to test
    providers = ["openai", "anthropic", "google", "mistral"]
    
    # Model overrides (optional)
    model_overrides = {
        "openai": "gpt-4-turbo-mock",
        "google": "gemini-pro-mock",
        "anthropic": "claude-3-haiku-mock",
        "mistral": "mistral-medium-mock"
    }
    
    # Create output directory
    os.makedirs("test_results", exist_ok=True)
    
    # Patch the get_response method
    with patch('llm_tester.utils.provider_manager.ProviderManager.get_response', mock_get_response):
        # Initialize the tester
        tester = LLMTester(providers=providers)
        
        # Discover test cases
        test_cases = tester.discover_test_cases()
        print(f"Found {len(test_cases)} test cases:")
        for test_case in test_cases:
            print(f"  {test_case['module']}/{test_case['name']}")
        
        # Run tests with model overrides
        print("\nRunning tests with mock responses...")
        results = tester.run_tests(model_overrides=model_overrides)
        
        # Generate and save report
        report = tester.generate_report(results)
        report_path = Path("test_results") / "mock_test_report_with_products.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\nReport saved to {report_path}")
        
        # Run optimized tests
        print("\nRunning optimized tests with mock responses...")
        optimized_results = tester.run_optimized_tests(
            model_overrides=model_overrides)
        
        # Generate and save optimized report
        optimized_report = tester.generate_report(optimized_results, optimized=True)
        optimized_report_path = Path("test_results") / "mock_optimized_test_report_with_products.md"
        with open(optimized_report_path, "w") as f:
            f.write(optimized_report)
        print(f"\nOptimized report saved to {optimized_report_path}")
        
        # Print summary
        print("\nTest Summary:")
        for test_name, test_results in results.items():
            print(f"  {test_name}:")
            for provider, provider_result in test_results.items():
                validation = provider_result.get('validation', {})
                accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                model = provider_result.get('model', 'default')
                print(f"    {provider} ({model}): {accuracy:.2f}%")

if __name__ == "__main__":
    main()