"""
Job advertisement model
"""

import os
import json
from typing import List, Optional, Dict, Any, ClassVar, Type
from pydantic import BaseModel, Field, HttpUrl
from datetime import date


class Benefit(BaseModel):
    """Benefits offered by the company"""
    
    name: str = Field(..., description="Name of the benefit")
    description: Optional[str] = Field(None, description="Description of the benefit")


class ContactInfo(BaseModel):
    """Contact information for the job"""
    
    name: Optional[str] = Field(None, description="Name of the contact person")
    email: Optional[str] = Field(None, description="Email address for applications")
    phone: Optional[str] = Field(None, description="Phone number for inquiries")
    website: Optional[HttpUrl] = Field(None, description="Company or application website")


class EducationRequirement(BaseModel):
    """Education requirements for the job"""
    
    degree: str = Field(..., description="Required degree")
    field: str = Field(..., description="Field of study")
    required: bool = Field(..., description="Whether this education is required or preferred")


class JobAd(BaseModel):
    """
    Job advertisement model
    """
    
    # Class variables for module configuration
    MODULE_NAME: ClassVar[str] = "job_ads"
    TEST_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "tests")
    REPORT_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "reports")
    
    # Model fields
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    department: Optional[str] = Field(None, description="Department within the company")
    location: Dict[str, str] = Field(..., description="Job location with city, state, country")
    salary: Dict[str, Any] = Field(..., description="Salary information including range, currency, and period")
    employment_type: str = Field(..., description="Type of employment (full-time, part-time, contract, etc.)")
    experience: Dict[str, Any] = Field(..., description="Experience requirements including years and level")
    required_skills: List[str] = Field(..., description="List of required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="List of preferred skills")
    education: List[EducationRequirement] = Field(default_factory=list, description="List of education requirements")
    responsibilities: List[str] = Field(..., description="List of job responsibilities")
    benefits: List[Benefit] = Field(default_factory=list, description="List of benefits offered")
    description: str = Field(..., description="Detailed job description")
    application_deadline: Optional[date] = Field(None, description="Application deadline date")
    contact_info: ContactInfo = Field(..., description="Contact information for applications")
    remote: bool = Field(..., description="Whether the job is remote or not")
    travel_required: Optional[str] = Field(None, description="Travel requirements if any")
    posting_date: date = Field(..., description="Date when the job was posted")
    
    @classmethod
    def get_test_cases(cls) -> List[Dict[str, str]]:
        """
        Discover test cases for this module
        
        Returns:
            List of test case configurations with paths to source, prompt, and expected files
        """
        test_cases = []
        
        # Check required directories
        sources_dir = os.path.join(cls.TEST_DIR, "sources")
        prompts_dir = os.path.join(cls.TEST_DIR, "prompts")
        expected_dir = os.path.join(cls.TEST_DIR, "expected")
        
        if not all(os.path.exists(d) for d in [sources_dir, prompts_dir, expected_dir]):
            return []
        
        # Get test case base names (from source files without extension)
        for source_file in os.listdir(sources_dir):
            if not source_file.endswith('.txt'):
                continue
                
            base_name = os.path.splitext(source_file)[0]
            prompt_file = f"{base_name}.txt"
            expected_file = f"{base_name}.json"
            
            if not os.path.exists(os.path.join(prompts_dir, prompt_file)):
                continue
                
            if not os.path.exists(os.path.join(expected_dir, expected_file)):
                continue
            
            test_case = {
                'module': cls.MODULE_NAME,
                'name': base_name,
                'model_class': cls,
                'source_path': os.path.join(sources_dir, source_file),
                'prompt_path': os.path.join(prompts_dir, prompt_file),
                'expected_path': os.path.join(expected_dir, expected_file)
            }
            
            test_cases.append(test_case)
        
        return test_cases
    
    @classmethod
    def save_module_report(cls, results: Dict[str, Any], run_id: str) -> str:
        """
        Save a report specifically for this module
        
        Args:
            results: Test results for this module
            run_id: Run identifier
            
        Returns:
            Path to the saved report file
        """
        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        
        # Create module-specific report
        report_path = os.path.join(cls.REPORT_DIR, f"report_{cls.MODULE_NAME}_{run_id}.md")
        
        with open(report_path, 'w') as f:
            f.write(f"# {cls.MODULE_NAME.replace('_', ' ').title()} Module Report\n\n")
            f.write(f"Run ID: {run_id}\n\n")
            
            # Add test results
            f.write("## Test Results\n\n")
            for test_id, test_results in results.items():
                if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                    continue
                    
                test_name = test_id.split('/')[1]
                f.write(f"### Test: {test_name}\n\n")
                
                for provider, provider_results in test_results.items():
                    f.write(f"#### Provider: {provider}\n\n")
                    
                    if 'error' in provider_results:
                        f.write(f"Error: {provider_results['error']}\n\n")
                        continue
                    
                    validation = provider_results.get('validation', {})
                    accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                    f.write(f"Accuracy: {accuracy:.2f}%\n\n")
                    
                    usage = provider_results.get('usage', {})
                    if usage:
                        f.write("Usage:\n")
                        f.write(f"- Prompt tokens: {usage.get('prompt_tokens', 0)}\n")
                        f.write(f"- Completion tokens: {usage.get('completion_tokens', 0)}\n")
                        f.write(f"- Total tokens: {usage.get('total_tokens', 0)}\n")
                        f.write(f"- Cost: ${usage.get('total_cost', 0):.6f}\n\n")
        
        return report_path
    
    @classmethod
    def save_module_cost_report(cls, cost_data: Dict[str, Any], run_id: str) -> str:
        """
        Save a cost report specifically for this module
        
        Args:
            cost_data: Cost data for this module
            run_id: Run identifier
            
        Returns:
            Path to the saved report file
        """
        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        
        # Create module-specific cost report
        report_path = os.path.join(cls.REPORT_DIR, f"cost_report_{cls.MODULE_NAME}_{run_id}.json")
        
        # Filter cost data for this module only
        module_cost_data = {
            'run_id': run_id,
            'module': cls.MODULE_NAME,
            'tests': {},
            'summary': {
                'total_cost': 0,
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'py_models': {}
            }
        }
        
        # Collect tests that belong to this module
        for test_id, test_data in cost_data.get('tests', {}).items():
            if not test_id.startswith(f"{cls.MODULE_NAME}/"):
                continue
                
            module_cost_data['tests'][test_id] = test_data
            
            # Add to summary
            for provider, provider_data in test_data.items():
                module_cost_data['summary']['total_cost'] += provider_data.get('total_cost', 0)
                module_cost_data['summary']['total_tokens'] += provider_data.get('total_tokens', 0)
                module_cost_data['summary']['prompt_tokens'] += provider_data.get('prompt_tokens', 0)
                module_cost_data['summary']['completion_tokens'] += provider_data.get('completion_tokens', 0)
                
                # Add to model-specific summary
                model_name = provider_data.get('model', 'unknown')
                if model_name not in module_cost_data['summary']['py_models']:
                    module_cost_data['summary']['py_models'][model_name] = {
                        'total_cost': 0,
                        'total_tokens': 0,
                        'prompt_tokens': 0,
                        'completion_tokens': 0,
                        'test_count': 0
                    }
                
                model_summary = module_cost_data['summary']['py_models'][model_name]
                model_summary['total_cost'] += provider_data.get('total_cost', 0)
                model_summary['total_tokens'] += provider_data.get('total_tokens', 0)
                model_summary['prompt_tokens'] += provider_data.get('prompt_tokens', 0)
                model_summary['completion_tokens'] += provider_data.get('completion_tokens', 0)
                model_summary['test_count'] += 1
        
        # Write to file
        with open(report_path, 'w') as f:
            json.dump(module_cost_data, f, indent=2)
        
        return report_path
