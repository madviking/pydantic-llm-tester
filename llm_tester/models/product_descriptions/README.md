# Product Description Model

This model is designed to extract structured information from product descriptions.

## Structure

The model includes:

- Product ID, name, and brand
- Category and subcategory
- Price information (amount, currency, discount)
- Product features and detailed description
- Technical specifications
- Physical properties (dimensions, weight, materials)
- Available colors
- Product images
- Availability and shipping information
- Warranty and return policy
- Customer review data
- Related products

## Example Usage

```python
from llm_tester.models.product_descriptions import ProductDescription

# Parse product data
product_data = {
    "id": "TX15-PRO",
    "name": "Premium Laptop",
    "brand": "TechBrand",
    "price": {
        "amount": 1499.99,
        "currency": "USD",
        "discount_percentage": 10.0,
        "original_amount": 1699.99
    },
    # ... other fields
}

# Validate with model
product = ProductDescription(**product_data)
```

## Test Cases

Test cases are located in `/llm_tester/tests/cases/product_descriptions/` and include:
- `simple_gadget.txt`: A basic product description
- `tech_gadget.txt`: A detailed product description with extensive specifications