# Job Advertisement Model

This model is designed to extract structured information from job advertisements.

## Structure

The model includes:

- Job title, company, and department
- Location information (city, state, country)
- Salary details (range, currency, period)
- Employment type
- Experience requirements
- Required and preferred skills
- Education requirements
- Responsibilities
- Benefits
- Application details and contact information
- Remote work and travel information

## Example Usage

```python
from llm_tester.models.job_ads import JobAd

# Parse job data
job_data = {
    "title": "Senior Developer",
    "company": "Tech Company",
    "location": {
        "city": "San Francisco",
        "state": "California",
        "country": "USA"
    },
    # ... other fields
}

# Validate with model
job = JobAd(**job_data)
```

## Test Cases

Test cases are located in `/llm_tester/tests/cases/job_ads/` and include:
- `simple.txt`: A basic job posting
- `complex.txt`: A detailed job posting with additional fields