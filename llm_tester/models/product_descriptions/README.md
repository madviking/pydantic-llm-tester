# Product Descriptions Module

This module provides functionality for extracting structured information from product descriptions using Large Language Models (LLMs).

## Model Structure

The main model class is `ProductDescription` which validates product data with the following fields:

- `id`: Unique identifier for the product
- `name`: Product name
- `brand`: Brand name
- `category`: Product category
- `subcategory`: Product subcategory (optional)
- `price`: Price information (amount, currency, discount)
- `description`: Detailed product description
- `features`: List of product features
- `specifications`: Technical specifications
- `dimensions`: Product dimensions (optional)
- `weight`: Product weight information (optional)
- `materials`: Materials used in the product (optional)
- `colors`: Available colors (optional)
- `images`: Product image URLs
- `availability`: Product availability status
- `shipping_info`: Shipping information (optional)
- `warranty`: Warranty information (optional)
- `return_policy`: Return policy information (optional)
- `reviews`: Review information (optional)
- `release_date`: Date when the product was released (optional)
- `is_bestseller`: Whether the product is a bestseller
- `related_products`: IDs of related products (optional)

## Directory Structure

- `/model.py` - The Pydantic model definition
- `/tests/` - Test cases for this module
  - `/sources/` - Source text files (product description content)
  - `/prompts/` - Prompt templates
  - `/expected/` - Expected JSON outputs
  - `/optimized/` - Optimized prompts (generated)
- `/reports/` - Module-specific test and cost reports (generated)

## Usage

This module is used by the LLMTester class to test various LLM providers' ability to extract structured information from product descriptions.

To add new test cases:

1. Add the product description text to `tests/sources/your_case_name.txt`
2. Create a prompt in `tests/prompts/your_case_name.txt`
3. Add the expected output in `tests/expected/your_case_name.json`

## Module-Specific Reports

This module generates its own reports in the `reports/` directory:

1. Test reports - `report_product_descriptions_<run_id>.md`
2. Cost reports - `cost_report_product_descriptions_<run_id>.json`

These reports provide module-specific insights into test performance and costs.