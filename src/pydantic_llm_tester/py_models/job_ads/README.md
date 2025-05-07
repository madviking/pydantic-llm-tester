# Job Ads Module

This module provides functionality for extracting structured information from job advertisements using Large Language Models (LLMs).

## Model Structure

The main model class is `JobAd` which validates job advertisement data with the following fields:

- `title`: Job title
- `company`: Company name
- `department`: Department within the company (optional)
- `location`: Job location with city, state, country
- `salary`: Salary information including range, currency, and period
- `employment_type`: Type of employment (full-time, part-time, contract, etc.)
- `experience`: Experience requirements including years and level
- `required_skills`: List of required skills
- `preferred_skills`: List of preferred skills (optional)
- `education`: List of education requirements (optional)
- `responsibilities`: List of job responsibilities
- `benefits`: List of benefits offered (optional)
- `description`: Detailed job description
- `application_deadline`: Application deadline date (optional)
- `contact_info`: Contact information for applications
- `remote`: Whether the job is remote or not
- `travel_required`: Travel requirements if any (optional)
- `posting_date`: Date when the job was posted

## Directory Structure

- `/model.py` - The Pydantic model definition
- `/tests/` - Test cases for this module
  - `/sources/` - Source text files (job ad content)
  - `/prompts/` - Prompt templates
  - `/expected/` - Expected JSON outputs
  - `/optimized/` - Optimized prompts (generated)
- `/reports/` - Module-specific test and cost reports (generated)

## Usage

This module is used by the LLMTester class to test various LLM providers' ability to extract job information from job postings.

To add new test cases:

1. Add the job posting text to `tests/sources/your_case_name.txt`
2. Create a prompt in `tests/prompts/your_case_name.txt`
3. Add the expected output in `tests/expected/your_case_name.json`

## Module-Specific Reports

This module generates its own reports in the `reports/` directory:

1. Test reports - `report_job_ads_<run_id>.md`
2. Cost reports - `cost_report_job_ads_<run_id>.json`

These reports provide module-specific insights into test performance and costs.