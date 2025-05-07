"""
Product description model
"""

import os
import json
from typing import List, Optional, Dict, Any, Union, ClassVar, Type
from pydantic import BaseModel, Field, HttpUrl
from datetime import date


class Price(BaseModel):
    """Price information for a product"""
    
    amount: float = Field(..., description="The numerical value of the price")
    currency: str = Field(..., description="The currency code (e.g., USD, EUR)")
    discount_percentage: Optional[float] = Field(None, description="The discount percentage if the product is on sale")
    original_amount: Optional[float] = Field(None, description="The original price before discount")


class Dimension(BaseModel):
    """Physical dimensions of a product"""
    
    length: float = Field(..., description="Length in specified unit")
    width: float = Field(..., description="Width in specified unit")
    height: float = Field(..., description="Height in specified unit")
    unit: str = Field(..., description="Unit of measurement (e.g., cm, inches)")


class Review(BaseModel):
    """Customer review information"""
    
    rating: float = Field(..., ge=0, le=5, description="Rating from 0 to 5")
    count: int = Field(..., description="Number of reviews")


class Specification(BaseModel):
    """Technical specification for a product"""
    
    name: str = Field(..., description="Name of the specification")
    value: Union[str, float, int, bool] = Field(..., description="Value of the specification")
    unit: Optional[str] = Field(None, description="Unit of measurement if applicable")


class ProductDescription(BaseModel):
    """
    Product description model
    """
    
    # Class variables for module configuration
    MODULE_NAME: ClassVar[str] = "product_descriptions"
    TEST_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "tests")
    REPORT_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "reports")
    
    # Model fields
    id: str = Field(..., description="Unique identifier for the product")
    name: str = Field(..., description="Product name")
    brand: str = Field(..., description="Brand name")
    category: str = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    price: Price = Field(..., description="Price information")
    description: str = Field(..., description="Detailed product description")
    features: List[str] = Field(..., description="List of product features")
    specifications: List[Specification] = Field(..., description="Technical specifications")
    dimensions: Optional[Dimension] = Field(None, description="Product dimensions")
    weight: Optional[Dict[str, Any]] = Field(None, description="Product weight information")
    materials: Optional[List[str]] = Field(None, description="Materials used in the product")
    colors: Optional[List[str]] = Field(None, description="Available colors")
    images: List[HttpUrl] = Field(..., description="Product image URLs")
    availability: str = Field(..., description="Product availability status")
    shipping_info: Optional[Dict[str, Any]] = Field(None, description="Shipping information")
    warranty: Optional[str] = Field(None, description="Warranty information")
    return_policy: Optional[str] = Field(None, description="Return policy information")
    reviews: Optional[Review] = Field(None, description="Review information")
    release_date: Optional[date] = Field(None, description="Date when the product was released")
    is_bestseller: bool = Field(..., description="Whether the product is a bestseller")
    related_products: Optional[List[str]] = Field(None, description="IDs of related products")
    
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
