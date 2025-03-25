#!/usr/bin/env python3
"""
Example of running LLM Tester with mock responses (no API keys needed)
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the path to import llm_tester
sys.path.append(str(Path(__file__).parent.parent))

from llm_tester import LLMTester

# Sample response for mocking
MOCK_RESPONSE = """
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

# Mock the get_response method to return a fixed response
def mock_get_response(self, provider, prompt, source, model_name=None):
    # For simple jobs, use a simplified version of the response
    if "FULL STACK DEVELOPER" in source:
        resp = json.loads(MOCK_RESPONSE)
        resp["title"] = "FULL STACK DEVELOPER"
        resp["company"] = "TechInnovate Solutions"
        return json.dumps(resp)
    # Otherwise return the full mock response
    return MOCK_RESPONSE

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
        report_path = Path("test_results") / "mock_test_report.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\nReport saved to {report_path}")
        
        # Run optimized tests
        print("\nRunning optimized tests with mock responses...")
        optimized_results = tester.run_optimized_tests(
            model_overrides=model_overrides)
        
        # Generate and save optimized report
        optimized_report = tester.generate_report(optimized_results, optimized=True)
        optimized_report_path = Path("test_results") / "mock_optimized_test_report.md"
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