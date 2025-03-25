"""
Job advertisement model
"""

from typing import List, Optional, Dict, Any
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