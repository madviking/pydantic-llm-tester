"""
Mock responses for LLM Tester

This module provides standardized mock responses for testing without API access.
"""

import json
import re
from typing import Dict, Any, Optional

# Dictionary of mock responses by module type
MOCK_RESPONSES: Dict[str, Dict[str, str]] = {
    "job_ads": {
        "default": """
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
            "GPT py_models",
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
        "full_stack": """
        {
          "title": "FULL STACK DEVELOPER",
          "company": "TechInnovate Solutions",
          "department": "Product Development",
          "location": {
            "city": "Austin",
            "state": "Texas",
            "country": "United States"
          },
          "salary": {
            "range": "$120,000 - $160,000",
            "currency": "USD",
            "period": "annually"
          },
          "employment_type": "Full-time",
          "experience": {
            "years": "3+ years",
            "level": "Mid-level to Senior"
          },
          "required_skills": [
            "JavaScript/TypeScript",
            "React",
            "Node.js",
            "SQL databases",
            "RESTful APIs",
            "Git"
          ],
          "preferred_skills": [
            "GraphQL",
            "Docker",
            "AWS/Azure",
            "Testing frameworks"
          ],
          "education": [
            {
              "degree": "Bachelor's degree",
              "field": "Computer Science or related field",
              "required": true
            }
          ],
          "responsibilities": [
            "Design and implement web applications from front to back end",
            "Collaborate with product and design teams",
            "Optimize applications for performance and scalability"
          ],
          "benefits": [
            {
              "name": "Health and dental insurance",
              "description": "Full coverage for employee and dependents"
            },
            {
              "name": "Unlimited PTO",
              "description": "Flexible vacation policy"
            }
          ],
          "description": "Join our innovative team developing modern web applications with cutting-edge technology.",
          "application_deadline": "2025-05-15",
          "contact_info": {
            "name": "HR Department",
            "email": "careers@techinnovate.com",
            "phone": "(512) 555-7890",
            "website": "https://techinnovate.com/careers"
          },
          "remote": true,
          "travel_required": "Minimal travel (quarterly team meetings)",
          "posting_date": "2025-04-01"
        }
        """,
        "software_engineer": """
        {
          "title": "SOFTWARE ENGINEER",
          "company": "CodeCraft Inc.",
          "department": "Engineering",
          "location": {
            "city": "Seattle",
            "state": "Washington",
            "country": "United States"
          },
          "salary": {
            "range": "$130,000 - $170,000",
            "currency": "USD",
            "period": "annually"
          },
          "employment_type": "Full-time",
          "experience": {
            "years": "2+ years",
            "level": "Mid-level"
          },
          "required_skills": [
            "Java",
            "Spring Boot",
            "Microservices",
            "CI/CD",
            "Unit testing"
          ],
          "preferred_skills": [
            "Kubernetes",
            "Kafka",
            "AWS",
            "Python"
          ],
          "education": [
            {
              "degree": "Bachelor's degree",
              "field": "Computer Science or Engineering",
              "required": true
            }
          ],
          "responsibilities": [
            "Develop and maintain backend services",
            "Collaborate with cross-functional teams",
            "Participate in code reviews and system design"
          ],
          "benefits": [
            {
              "name": "Comprehensive benefits package",
              "description": "Medical, dental, vision, and 401(k)"
            },
            {
              "name": "Professional development",
              "description": "Conference attendance and learning stipend"
            }
          ],
          "description": "Build robust, scalable software systems as part of our talented engineering team.",
          "application_deadline": "2025-06-30",
          "contact_info": {
            "name": "Technical Recruiting",
            "email": "recruiting@codecraft.com",
            "phone": "(206) 555-1234",
            "website": "https://codecraft.com/jobs"
          },
          "remote": true,
          "travel_required": "None",
          "posting_date": "2025-04-15"
        }
        """
    },
    "product_descriptions": {
        "default": """
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
          "availability": "In Stock",
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
        """,
        "laptop": """
        {
          "id": "UB-X15-PRO",
          "name": "UltraBook Pro X15 Laptop",
          "brand": "TechVantage",
          "category": "Laptops",
          "price": {
            "amount": 1299.99,
            "currency": "USD",
            "discount_percentage": 15.0,
            "original_amount": 1499.99
          },
          "description": "The ultimate productivity ultrabook with premium performance and exceptional battery life.",
          "features": [
            "14-inch 4K OLED display",
            "Intel Core i7 processor",
            "16GB DDR5 RAM",
            "1TB NVMe SSD",
            "18-hour battery life"
          ],
          "specifications": [
            {
              "name": "Processor",
              "value": "Intel Core i7-1260P"
            },
            {
              "name": "Graphics",
              "value": "Intel Iris Xe"
            },
            {
              "name": "Memory",
              "value": "16",
              "unit": "GB"
            },
            {
              "name": "Storage",
              "value": "1",
              "unit": "TB"
            }
          ],
          "dimensions": {
            "length": 32.4,
            "width": 22.0,
            "height": 1.5,
            "unit": "cm"
          },
          "weight": {
            "value": 1.2,
            "unit": "kg"
          },
          "colors": [
            "Space Gray",
            "Silver"
          ],
          "images": [
            "https://techvantage.com/images/ultrabook-pro-x15-gray.jpg",
            "https://techvantage.com/images/ultrabook-pro-x15-silver.jpg"
          ],
          "availability": "In Stock",
          "shipping_info": {
            "ships_within": "2 business days",
            "shipping_type": "Free expedited shipping"
          },
          "warranty": "3-year premium warranty",
          "return_policy": "60-day return period",
          "reviews": {
            "rating": 4.8,
            "count": 542
          },
          "release_date": "2025-02-01",
          "is_bestseller": true,
          "related_products": [
            "UB-DOCK-USB",
            "UB-SLEEVE-15",
            "UB-POWER-GAN"
          ]
        }
        """,
        "smartphone": """
        {
          "id": "SP-X-PRO",
          "name": "SmartPhone X Pro",
          "brand": "TechMobile",
          "category": "Smartphones",
          "price": {
            "amount": 899.99,
            "currency": "USD",
            "discount_percentage": 10.0,
            "original_amount": 999.99
          },
          "description": "The cutting-edge smartphone with revolutionary camera system and all-day battery life.",
          "features": [
            "6.5-inch ProMotion XDR display",
            "Triple camera system (48MP main)",
            "5G connectivity",
            "A16 Bionic chip",
            "256GB storage"
          ],
          "specifications": [
            {
              "name": "Processor",
              "value": "A16 Bionic"
            },
            {
              "name": "RAM",
              "value": "8",
              "unit": "GB"
            },
            {
              "name": "Storage",
              "value": "256",
              "unit": "GB"
            },
            {
              "name": "Battery",
              "value": "4500",
              "unit": "mAh"
            }
          ],
          "dimensions": {
            "length": 14.8,
            "width": 7.2,
            "height": 0.8,
            "unit": "cm"
          },
          "weight": {
            "value": 189,
            "unit": "g"
          },
          "colors": [
            "Midnight Black",
            "Stellar Blue",
            "Pure Silver"
          ],
          "images": [
            "https://techmobile.com/images/smartphone-x-pro-black.jpg",
            "https://techmobile.com/images/smartphone-x-pro-blue.jpg"
          ],
          "availability": "In Stock",
          "shipping_info": {
            "ships_within": "1 business day",
            "shipping_type": "Free priority shipping"
          },
          "warranty": "2-year manufacturer warranty",
          "return_policy": "30-day return period",
          "reviews": {
            "rating": 4.7,
            "count": 1235
          },
          "release_date": "2025-03-15",
          "is_bestseller": true,
          "related_products": [
            "SP-CASE-PRO",
            "SP-SCREEN-ARMOR",
            "SP-CHARGER-FAST"
          ]
        }
        """
    },
    "integration_tests": {
        "default": """
        {
          "animal": "mock_dog"
        }
        """
    }
}


def get_mock_response(module: str, source: str, model_name: Optional[str] = None) -> str:
    """
    Get a mock response based on the module type and source content
    
    Args:
        module: The module type (e.g., 'job_ads', 'product_descriptions')
        source: The source text
        model_name: Optional model name (not used, but included for API compatibility)
        
    Returns:
        A mock response as a JSON string
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Generating mock response for module: {module}")
    
    # Default to job_ads if module not found
    if module not in MOCK_RESPONSES:
        logger.warning(f"Module '{module}' not found in MOCK_RESPONSES, defaulting to 'job_ads'")
        module = "job_ads"
    
    # Select the appropriate response template based on source text
    if module == "job_ads":
        if "FULL STACK" in source.upper() or "FRONTEND" in source.upper() or "BACKEND" in source.upper():
            response_key = "full_stack"
            logger.info(f"Selected template: {module}/{response_key} based on keywords")
        elif "SOFTWARE ENGINEER" in source.upper() or "SOFTWARE DEVELOPER" in source.upper():
            response_key = "software_engineer"
            logger.info(f"Selected template: {module}/{response_key} based on keywords")
        else:
            response_key = "default"
            logger.info(f"Selected template: {module}/{response_key} (default)")
    elif module == "product_descriptions":
        if any(keyword in source.upper() for keyword in ["ULTRABOOK", "LAPTOP", "COMPUTER", "NOTEBOOK"]):
            response_key = "laptop"
            logger.info(f"Selected template: {module}/{response_key} based on keywords")
        elif any(keyword in source.upper() for keyword in ["SMARTPHONE", "PHONE", "MOBILE"]):
            response_key = "smartphone"
            logger.info(f"Selected template: {module}/{response_key} based on keywords")
        else:
            response_key = "default"
            logger.info(f"Selected template: {module}/{response_key} (default)")
    else:
        response_key = "default"
        logger.info(f"Selected template: {module}/{response_key} (default)")
    
    # Get the response template
    response_template = MOCK_RESPONSES[module].get(response_key, MOCK_RESPONSES[module]["default"])
    template_preview = response_template.strip()[:100] + "..." if len(response_template) > 100 else response_template
    logger.debug(f"Template preview: {template_preview}")
    
    # Parse the template to create a customizable copy
    try:
        response_data = json.loads(response_template)
        logger.info(f"Successfully parsed template JSON")
        
        # Customize the response based on the source text
        # Extract potential values from source using regex patterns
        
        # For job ads, look for potential job title
        if module == "job_ads":
            title_match = re.search(r'(POSITION|JOB TITLE|ROLE):\s*([^\n]+)', source, re.IGNORECASE)
            if title_match:
                title_value = title_match.group(2).strip().upper()
                logger.info(f"Extracted title from source: '{title_value}'")
                response_data["title"] = title_value
                
            # Look for company name
            company_match = re.search(r'(COMPANY|ORGANIZATION):\s*([^\n]+)', source, re.IGNORECASE)
            if company_match:
                company_value = company_match.group(2).strip()
                logger.info(f"Extracted company from source: '{company_value}'")
                response_data["company"] = company_value
        
        # For product descriptions, look for product name
        elif module == "product_descriptions":
            name_match = re.search(r'(PRODUCT|ITEM|MODEL):\s*([^\n]+)', source, re.IGNORECASE)
            if name_match:
                name_value = name_match.group(2).strip()
                logger.info(f"Extracted product name from source: '{name_value}'")
                response_data["name"] = name_value
                
            # Look for brand
            brand_match = re.search(r'(BRAND|MANUFACTURER):\s*([^\n]+)', source, re.IGNORECASE)
            if brand_match:
                brand_value = brand_match.group(2).strip()
                logger.info(f"Extracted brand from source: '{brand_value}'")
                response_data["brand"] = brand_value
        
        response_json = json.dumps(response_data, indent=2)
        logger.info(f"Generated customized JSON response ({len(response_json)} chars)")
        logger.debug(f"Response preview: {response_json[:100]}...")
        return response_json
    except json.JSONDecodeError as e:
        # If template parsing fails, return the template as is
        logger.error(f"Failed to parse template JSON: {str(e)}")
        logger.debug(f"Template that failed to parse: {response_template}")
        return response_template


def mock_get_response(provider: str, prompt: str, source: str, model_name: Optional[str] = None) -> str:
    """
    Mock implementation for ProviderManager.get_response
    
    Args:
        provider: The provider name (not used in mock implementation)
        prompt: The prompt text (used to determine response type)
        source: The source text
        model_name: Optional model name
        
    Returns:
        A mock response
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Mock response requested for provider: {provider}, model: {model_name}")
    logger.debug(f"Prompt snippet: {prompt[:100]}...")
    logger.debug(f"Source snippet: {source[:100]}...")
    
    # Determine the module type from the prompt or source
    if "job" in prompt.lower() or "position" in prompt.lower() or "company" in prompt.lower():
        module = "job_ads"
        logger.info(f"Detected module from prompt keywords: {module}")
    elif "product" in prompt.lower() or "item" in prompt.lower() or "specifications" in prompt.lower():
        module = "product_descriptions"
        logger.info(f"Detected module from prompt keywords: {module}")
    elif "MACHINE LEARNING ENGINEER" in source or "job" in source.lower() or "software engineer" in source.lower():
        module = "job_ads"
        logger.info(f"Detected module from source keywords: {module}")
    else:
        module = "product_descriptions"
        logger.info(f"Using default module: {module}")
    
    response = get_mock_response(module, source, model_name)
    logger.info(f"Generated mock response for module: {module} ({len(response)} chars)")
    logger.debug(f"Response snippet: {response[:100]}...")
    
    return response
