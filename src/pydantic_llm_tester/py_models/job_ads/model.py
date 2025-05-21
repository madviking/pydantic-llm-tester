"""
Job advertisement model
"""

import os
import json
from typing import List, Optional, Dict, Any, ClassVar, Type, Set
from pydantic import BaseModel, Field, HttpUrl # Import BaseModel
from datetime import date
from pydantic_llm_tester.py_models.base import BasePyModel


class Benefit(BaseModel):
    """Benefits offered by the company"""
    
    name: str = Field(..., description="Name of the benefit")
    description: Optional[str] = Field(None, description="Description of the benefit")
    model_config = {"extra": "ignore"}



class ContactInfo(BaseModel):
    """Contact information for the job"""
    
    name: Optional[str] = Field(None, description="Name of the contact person")
    email: Optional[str] = Field(None, description="Email address for applications")
    phone: Optional[str] = Field(None, description="Phone number for inquiries")
    website: Optional[HttpUrl] = Field(None, description="Company or application website")
    model_config = {"extra": "ignore"}


class ExperienceRequirement(BaseModel):
    """Experience requirements for the job"""
    
    years: Optional[int] = Field(..., description="Number of years of experience required")
    level: Optional[str] = Field(..., description="Level of experience (e.g., junior, mid, senior)")
    preferred: bool = Field(False, description="Whether this experience is preferred or required")
    model_config = {"extra": "ignore"}


class EducationRequirement(BaseModel):
    """Education requirements for the job"""
    
    degree: Optional[str] = Field(..., description="Required degree")
    field: Optional[str] = Field(..., description="Field of study")
    required: bool = Field(False, description="Whether this education is required or preferred")
    model_config = {"extra": "ignore"}


class Location(BaseModel):
    """Location of the job"""
    
    city: Optional[str] = Field(..., description="City where the job is located")
    state: Optional[str] = Field(None, description="State where the job is located")
    country: Optional[str] = Field(..., description="Country where the job is located")
    remote: bool = Field(False, description="Whether the job is remote or not")
    model_config = {"extra": "ignore"}

class Salary(BaseModel):
    range: Optional[str] = Field(..., description="Salary range")
    currency: Optional[str] = Field(None, description="Currency")
    period: Optional[str] = Field(..., description="Annual or monthly")



class JobAd(BasePyModel):
    """
    Job advertisement model
    """

    # Class variable for module name
    MODULE_NAME: ClassVar[str] = "job_ads"

    # Model fields
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    department: Optional[str] = Field(None, description="Department within the company")
    location: Location = Field(..., description="Job location with city, state, country")
    salary: Optional[Salary] = Field(..., description="Salary information in a string format")
    employment_type: Optional[str] = Field(..., description="Type of employment (full-time, part-time, contract, etc.)")
    experience: Optional[ExperienceRequirement] = Field(..., description="Experience requirements including years and level")
    required_skills: Optional[List[str]] = Field(..., description="List of required skills")
    preferred_skills: Optional[List[str]] = Field(default_factory=list, description="List of preferred skills")
    education: Optional[List[EducationRequirement]] = Field(default_factory=list, description="List of education requirements")
    responsibilities: Optional[List[str]] = Field(..., description="List of job responsibilities")
    benefits: Optional[List[Benefit]] = Field(default_factory=list, description="List of benefits offered")
    description: str = Field(..., description="Detailed job description")
    application_deadline: Optional[date] = Field(None, description="Application deadline date")
    contact_info: Optional[ContactInfo] = Field(..., description="Contact information for applications")
    remote: bool = Field(default=False, description="Whether the job is remote or not")
    travel_required: Optional[str] = Field(None, description="Travel requirements if any")
    posting_date: Optional[date] = Field(..., description="Date when the job was posted")
    image_analysis: Optional[str] = Field(None, description="Analysis of the image content, if applicable")

    @classmethod
    def get_skip_fields(cls) -> Set[str]:
        return {"image_analysis", "some_other_field"}

    @classmethod
    def get_test_cases(cls, module_dir: str) -> List[Dict[str, Any]]:
        """
        Discover test cases for this module.
        Extends the base class method to include image-based test cases.

        Args:
            module_dir: The absolute path to the directory of the py_model module.

        Returns:
            List of test case configurations with paths to source, prompt, and expected files
        """
        # Get standard test cases from the base class
        test_cases = super().get_test_cases(module_dir)

        # Add the new image-based test case
        test_dir = os.path.join(module_dir, "tests")
        sources_dir = os.path.join(test_dir, "sources")
        prompts_dir = os.path.join(test_dir, "prompts")
        expected_dir = os.path.join(test_dir, "expected")

        image_test_case_name = "job_ad_from_image"
        image_source_file = f"{image_test_case_name}_source.txt"
        image_prompt_file = f"{image_test_case_name}_prompt.txt"
        image_expected_file = f"{image_test_case_name}.json"
        image_file_to_upload = "job_ad_pic.png"

        # Construct full paths for this specific test case
        image_source_path = os.path.join(sources_dir, image_source_file)
        image_prompt_path = os.path.join(prompts_dir, image_prompt_file)
        image_expected_path = os.path.join(expected_dir, image_expected_file)
        actual_image_file_path = os.path.join(sources_dir, image_file_to_upload)

        # Check if all files for the image test case exist
        if all(os.path.exists(p) for p in [image_source_path, image_prompt_path, image_expected_path, actual_image_file_path]):
            image_test_case = {
                'module': cls.MODULE_NAME,
                'name': image_test_case_name,
                'model_class': cls,
                'source_path': image_source_path,
                'prompt_path': image_prompt_path,
                'expected_path': image_expected_path,
                'file_paths': [actual_image_file_path] # List of file paths for upload
            }
            test_cases.append(image_test_case)
        else:
            # Log a warning if any of the required files for the image test case are missing
            missing_files = []
            if not os.path.exists(image_source_path): missing_files.append(image_source_path)
            if not os.path.exists(image_prompt_path): missing_files.append(image_prompt_path)
            if not os.path.exists(image_expected_path): missing_files.append(image_expected_path)
            if not os.path.exists(actual_image_file_path): missing_files.append(actual_image_file_path)
            # Consider logging this warning using the class's logger if available, or print
            print(f"Warning: Skipping image test case '{image_test_case_name}' for module '{cls.MODULE_NAME}' due to missing files: {missing_files}")


        return test_cases
