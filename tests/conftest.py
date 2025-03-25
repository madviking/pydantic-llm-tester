"""
Pytest configuration
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from llm_tester import LLMTester
from llm_tester.models.job_ads import JobAd


@pytest.fixture
def mock_provider_manager():
    """Mock provider manager"""
    with patch('llm_tester.utils.provider_manager.ProviderManager') as mock:
        manager_instance = MagicMock()
        mock.return_value = manager_instance
        
        # Mock the get_response method
        def mock_get_response(provider, prompt, source, model_name=None):
            # Return a dummy response based on the source content
            if "SENIOR MACHINE LEARNING ENGINEER" in source:
                return """
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
                  "description": "As a Senior ML Engineer, you will be at the forefront of our AI research initiatives, working in cross-functional teams to design and implement machine learning solutions that advance our computer vision and NLP capabilities. You'll collaborate closely with research scientists, software engineers, and product managers to transform cutting-edge research into scalable, production-ready systems. This role requires a blend of theoretical knowledge and practical implementation skills. You'll face complex challenges requiring innovative approaches while maintaining a focus on creating real-world impact through your work.",
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
            elif "FULL STACK DEVELOPER" in source:
                return """
                {
                  "title": "FULL STACK DEVELOPER",
                  "company": "TechInnovate Solutions",
                  "department": "Web Development Team",
                  "location": {
                    "city": "Austin",
                    "state": "Texas",
                    "country": "United States"
                  },
                  "salary": {
                    "range": "$95,000 - $120,000",
                    "currency": "USD",
                    "period": "annually"
                  },
                  "employment_type": "Full-time",
                  "experience": {
                    "years": "3+ years",
                    "level": "Mid-level"
                  },
                  "required_skills": [
                    "JavaScript/TypeScript",
                    "React or Vue.js",
                    "Node.js and Express",
                    "RESTful API design and development",
                    "SQL and NoSQL databases (PostgreSQL, MongoDB)",
                    "Git version control",
                    "HTML/CSS"
                  ],
                  "preferred_skills": [
                    "GraphQL",
                    "AWS or Azure cloud services",
                    "Docker and containerization",
                    "CI/CD pipelines",
                    "Testing frameworks (Jest, Mocha)",
                    "Agile development methodologies"
                  ],
                  "education": [
                    {
                      "degree": "Bachelor's degree",
                      "field": "Computer Science or related field",
                      "required": false
                    }
                  ],
                  "responsibilities": [
                    "Develop and maintain web applications",
                    "Write clean, maintainable, and efficient code",
                    "Collaborate with UX/UI designers",
                    "Implement responsive design",
                    "Optimize applications for performance",
                    "Debug and troubleshoot issues",
                    "Participate in code reviews",
                    "Stay updated with emerging technologies"
                  ],
                  "benefits": [
                    {
                      "name": "Comprehensive health insurance",
                      "description": "Includes medical, dental, and vision coverage"
                    },
                    {
                      "name": "401(k) retirement plan",
                      "description": "With 4% company match"
                    },
                    {
                      "name": "Flexible work schedule",
                      "description": "Core hours with flexibility"
                    },
                    {
                      "name": "Professional development",
                      "description": "Conference attendance and learning stipend"
                    },
                    {
                      "name": "Generous PTO",
                      "description": "3 weeks vacation plus holidays"
                    }
                  ],
                  "description": "As a Full Stack Developer at TechInnovate Solutions, you will work in a collaborative environment to build and maintain web applications for our clients. You will be involved in all stages of the development lifecycle, from planning and design to testing and deployment. We value clean code, innovation, and continuous learning. Our tech stack includes React, Node.js, and PostgreSQL, but we're always open to adopting new technologies that improve our development process.",
                  "application_deadline": "2025-03-15",
                  "contact_info": {
                    "name": "HR Department",
                    "email": "recruiting@techinnovatesolutions.com",
                    "phone": "(512) 555-7890",
                    "website": "https://careers.techinnovatesolutions.com/full-stack"
                  },
                  "remote": true,
                  "travel_required": "Minimal travel required (less than 5%) for occasional team or client meetings",
                  "posting_date": "2025-02-10"
                }
                """
            else:
                return "{}"
        
        manager_instance.get_response.side_effect = mock_get_response
        yield manager_instance


@pytest.fixture
def mock_tester(mock_provider_manager):
    """Mock LLM tester"""
    # Get the path to the llm_tester directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(base_dir, "llm_tester", "tests")
    
    tester = LLMTester(providers=["openai", "anthropic"], test_dir=test_dir)
    
    # Replace provider manager with mock
    tester.provider_manager = mock_provider_manager
    
    return tester


@pytest.fixture
def job_ad_model():
    """Job ad model"""
    return JobAd