#!/usr/bin/env python3
"""
Simplified test run that doesn't require actual API calls
Just checks if the structure is working
"""

import os
import sys
from pathlib import Path
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("llm_tester_demo")

# Add the parent directory to the path to import llm_tester
sys.path.append(str(Path(__file__).parent))

# Create a dummy response for testing
DUMMY_RESPONSE = {
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
      "required": True
    },
    {
      "degree": "PhD",
      "field": "Machine Learning or related field",
      "required": False
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
  "description": "As a Senior ML Engineer, you will be at the forefront of our AI research initiatives, working in cross-functional teams to design and implement machine learning solutions that advance our computer vision and NLP capabilities.",
  "application_deadline": "2025-04-30",
  "contact_info": {
    "name": "Dr. Sarah Chen",
    "email": "ml-recruiting@datavisionanalytics.com",
    "phone": "(617) 555-9876",
    "website": "https://careers.datavisionanalytics.com/ml-engineer"
  },
  "remote": True,
  "travel_required": "Occasional travel (10-15%) for conferences, team off-sites, and client meetings",
  "posting_date": "2025-03-15"
}

# Mock the ProviderManager to avoid actual API calls
class MockProviderManager:
    def __init__(self, providers):
        self.providers = providers
        logger.info(f"Initialized mock provider manager with providers: {providers}")
    
    def get_response(self, provider, prompt, source, model_name=None):
        logger.info(f"Mock getting response from {provider} (model: {model_name})")
        return json.dumps(DUMMY_RESPONSE, indent=2)

def check_project_structure():
    """Check if the project structure is valid"""
    # Check for critical files and directories
    structure_items = [
        "llm_tester",
        "llm_tester/__init__.py",
        "llm_tester/llm_tester.py",
        "llm_tester/models",
        "llm_tester/models/job_ads",
        "llm_tester/models/job_ads/model.py",
        "llm_tester/tests/cases/job_ads/sources/complex.txt",
        "llm_tester/tests/cases/job_ads/expected/complex.json",
    ]
    
    for item in structure_items:
        path = Path(item)
        if not path.exists():
            logger.error(f"Missing required item: {item}")
            return False
            
    logger.info("Project structure check: Passed")
    return True

def run_test():
    """Run a simple test of the LLM Tester"""
    try:
        # Import LLMTester class
        from llm_tester.llm_tester import LLMTester
        logger.info("Successfully imported LLMTester")
        
        # Initialize with mock provider manager
        tester = LLMTester(providers=["mock_provider"])
        
        # Replace the provider manager with our mock
        tester.provider_manager = MockProviderManager(["mock_provider"])
        
        # Discover test cases
        test_cases = tester.discover_test_cases()
        if test_cases:
            logger.info(f"Discovered {len(test_cases)} test cases")
            for test_case in test_cases:
                logger.info(f"  Test case: {test_case['module']}/{test_case['name']}")
        else:
            logger.warning("No test cases discovered")
            return
            
        # Run test on first test case
        test_id = f"{test_cases[0]['module']}/{test_cases[0]['name']}"
        logger.info(f"Running test for: {test_id}")
        
        # Check if we can access the model class
        model_class = test_cases[0].get('model_class')
        if model_class:
            logger.info(f"Found model class: {model_class.__name__}")
        else:
            logger.error("Model class not found in test case")
            return
            
        # Attempt to load test files
        try:
            source_path = test_cases[0].get('source_path')
            with open(source_path, 'r') as f:
                source_content = f.read()
            logger.info(f"Successfully read source file ({len(source_content)} chars)")
            
            expected_path = test_cases[0].get('expected_path')
            with open(expected_path, 'r') as f:
                expected_data = json.load(f)
            logger.info(f"Successfully read expected JSON ({len(expected_data)} keys)")
        except Exception as e:
            logger.error(f"Error reading test files: {e}")
            return
            
        # Try instantiating the model
        try:
            model_instance = model_class(**DUMMY_RESPONSE)
            logger.info(f"Successfully created model instance: {model_instance.title}")
        except Exception as e:
            logger.error(f"Error creating model instance: {e}")
            return

        logger.info("All basic functionality tests passed!")
        logger.info("The project structure is working correctly.")
        
    except Exception as e:
        logger.error(f"Error running test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running LLM Tester Validation")
    print("=============================")
    
    if check_project_structure():
        run_test()
    else:
        print("Project structure check failed. Please fix the issues above.")