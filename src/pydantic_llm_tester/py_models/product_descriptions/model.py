"""
Product description model
"""

import os
import json
from typing import List, Optional, Dict, Any, Union, ClassVar, Type
from pydantic import BaseModel, Field, HttpUrl # Import BaseModel
from datetime import date
from pydantic_llm_tester.py_models.base import BasePyModel


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


class ProductDescription(BasePyModel):
    """
    Product description model
    """

    # Class variable for module name
    MODULE_NAME: ClassVar[str] = "product_descriptions"

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
