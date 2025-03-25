# LLM Tester Report - 2025-03-25 10:42:44

## Optimized Prompts Performance Report

### Test: job_ads/complex

#### Performance Comparison

| Provider | Model | Original Accuracy | Optimized Accuracy | Improvement |
|----------|-------|------------------|-------------------|------------|
| openai | gpt-4-turbo | 0.00% | 0.00% | +0.00% |
| anthropic | claude-3-haiku-20240307 | 0.00% | 0.00% | +0.00% |
| google | gemini-1.5-pro | 0.00% | 0.00% | +0.00% |
| mistral | mistral-medium | 0.00% | 0.00% | +0.00% |

#### Prompt Optimization

Original Prompt:
```
Extract detailed information from the provided job advertisement and format it as a structured JSON object. Your response should include all of the following information when available:

1. Job title
2. Company name
3. Department within the company
4. Location details (city, state, country)
5. Salary information (range, currency, payment period)
6. Employment type (full-time, part-time, contract, etc.)
7. Experience requirements (years, level)
8. Required skills (as a list)
9. Preferred skills (as a list)
10. Education requirements (degree, field, and whether required or preferred)
11. Job responsibilities (as a list)
12. Benefits offered (name and description)
13. Detailed job description
14. Application deadline
15. Contact information (name, email, phone, website)
16. Remote work options
17. Travel requirements
18. Posting date

Format your response as a valid JSON object with appropriate nesting of objects and arrays. Ensure all dates are in ISO format (YYYY-MM-DD). Respond only with the JSON object, no additional text.
```

Optimized Prompt:
```
Extract detailed information from the provided job advertisement and format it as a structured JSON object. Your response should include all of the following information when available:

1. Job title
2. Company name
3. Department within the company
4. Location details (city, state, country)
5. Salary information (range, currency, payment period)
6. Employment type (full-time, part-time, contract, etc.)
7. Experience requirements (years, level)
8. Required skills (as a list)
9. Preferred skills (as a list)
10. Education requirements (degree, field, and whether required or preferred)
11. Job responsibilities (as a list)
12. Benefits offered (name and description)
13. Detailed job description
14. Application deadline
15. Contact information (name, email, phone, website)
16. Remote work options
17. Travel requirements
18. Posting date

Format your response as a valid JSON object with appropriate nesting of objects and arrays. Ensure all dates are in ISO format (YYYY-MM-DD). Respond only with the JSON object, no additional text.

Your response MUST conform to this JSON schema:
```json
{
  "$defs": {
    "Benefit": {
      "description": "Benefits offered by the company",
      "properties": {
        "name": {
          "description": "Name of the benefit",
          "title": "Name",
          "type": "string"
        },
        "description": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Description of the benefit",
          "title": "Description"
        }
      },
      "required": [
        "name"
      ],
      "title": "Benefit",
      "type": "object"
    },
    "ContactInfo": {
      "description": "Contact information for the job",
      "properties": {
        "name": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Name of the contact person",
          "title": "Name"
        },
        "email": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Email address for applications",
          "title": "Email"
        },
        "phone": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Phone number for inquiries",
          "title": "Phone"
        },
        "website": {
          "anyOf": [
            {
              "format": "uri",
              "maxLength": 2083,
              "minLength": 1,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Company or application website",
          "title": "Website"
        }
      },
      "title": "ContactInfo",
      "type": "object"
    },
    "EducationRequirement": {
      "description": "Education requirements for the job",
      "properties": {
        "degree": {
          "description": "Required degree",
          "title": "Degree",
          "type": "string"
        },
        "field": {
          "description": "Field of study",
          "title": "Field",
          "type": "string"
        },
        "required": {
          "description": "Whether this education is required or preferred",
          "title": "Required",
          "type": "boolean"
        }
      },
      "required": [
        "degree",
        "field",
        "required"
      ],
      "title": "EducationRequirement",
      "type": "object"
    }
  },
  "description": "Job advertisement model",
  "properties": {
    "title": {
      "description": "Job title",
      "title": "Title",
      "type": "string"
    },
    "company": {
      "description": "Company name",
      "title": "Company",
      "type": "string"
    },
    "department": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Department within the company",
      "title": "Department"
    },
    "location": {
      "additionalProperties": {
        "type": "string"
      },
      "description": "Job location with city, state, country",
      "title": "Location",
      "type": "object"
    },
    "salary": {
      "description": "Salary information including range, currency, and period",
      "title": "Salary",
      "type": "object"
    },
    "employment_type": {
      "description": "Type of employment (full-time, part-time, contract, etc.)",
      "title": "Employment Type",
      "type": "string"
    },
    "experience": {
      "description": "Experience requirements including years and level",
      "title": "Experience",
      "type": "object"
    },
    "required_skills": {
      "description": "List of required skills",
      "items": {
        "type": "string"
      },
      "title": "Required Skills",
      "type": "array"
    },
    "preferred_skills": {
      "description": "List of preferred skills",
      "items": {
        "type": "string"
      },
      "title": "Preferred Skills",
      "type": "array"
    },
    "education": {
      "description": "List of education requirements",
      "items": {
        "$ref": "#/$defs/EducationRequirement"
      },
      "title": "Education",
      "type": "array"
    },
    "responsibilities": {
      "description": "List of job responsibilities",
      "items": {
        "type": "string"
      },
      "title": "Responsibilities",
      "type": "array"
    },
    "benefits": {
      "description": "List of benefits offered",
      "items": {
        "$ref": "#/$defs/Benefit"
      },
      "title": "Benefits",
      "type": "array"
    },
    "description": {
      "description": "Detailed job description",
      "title": "Description",
      "type": "string"
    },
    "application_deadline": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Application deadline date",
      "title": "Application Deadline"
    },
    "contact_info": {
      "$ref": "#/$defs/ContactInfo",
      "description": "Contact information for applications"
    },
    "remote": {
      "description": "Whether the job is remote or not",
      "title": "Remote",
      "type": "boolean"
    },
    "travel_required": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Travel requirements if any",
      "title": "Travel Required"
    },
    "posting_date": {
      "description": "Date when the job was posted",
      "format": "date",
      "title": "Posting Date",
      "type": "string"
    }
  },
  "required": [
    "title",
    "company",
    "location",
    "salary",
    "employment_type",
    "experience",
    "required_skills",
    "responsibilities",
    "description",
    "contact_info",
    "remote",
    "posting_date"
  ],
  "title": "JobAd",
  "type": "object"
}
```
```

#### Provider Details

##### openai

Error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: your_ope************here. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}

##### anthropic

Error: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}}

##### google

Error: Failed to get response from Google Vertex AI: File path/to/your/credentials.json was not found.

##### mistral

Error: Provider mistral not initialized

### Test: job_ads/simple

#### Performance Comparison

| Provider | Model | Original Accuracy | Optimized Accuracy | Improvement |
|----------|-------|------------------|-------------------|------------|
| openai | gpt-4-turbo | 0.00% | 0.00% | +0.00% |
| anthropic | claude-3-haiku-20240307 | 0.00% | 0.00% | +0.00% |
| google | gemini-1.5-pro | 0.00% | 0.00% | +0.00% |
| mistral | mistral-medium | 0.00% | 0.00% | +0.00% |

#### Prompt Optimization

Original Prompt:
```
Extract the key information from the provided job advertisement and format it as JSON. Include the job title, company name, location, salary range if provided, experience requirements, a list of required skills, a brief job description, and whether the job is remote or not.

Respond only with the JSON object, no additional text.
```

Optimized Prompt:
```
Extract the key information from the provided job advertisement and format it as JSON. Include the job title, company name, location, salary range if provided, experience requirements, a list of required skills, a brief job description, and whether the job is remote or not.

Respond only with the JSON object, no additional text.

Your response MUST conform to this JSON schema:
```json
{
  "$defs": {
    "Benefit": {
      "description": "Benefits offered by the company",
      "properties": {
        "name": {
          "description": "Name of the benefit",
          "title": "Name",
          "type": "string"
        },
        "description": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Description of the benefit",
          "title": "Description"
        }
      },
      "required": [
        "name"
      ],
      "title": "Benefit",
      "type": "object"
    },
    "ContactInfo": {
      "description": "Contact information for the job",
      "properties": {
        "name": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Name of the contact person",
          "title": "Name"
        },
        "email": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Email address for applications",
          "title": "Email"
        },
        "phone": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Phone number for inquiries",
          "title": "Phone"
        },
        "website": {
          "anyOf": [
            {
              "format": "uri",
              "maxLength": 2083,
              "minLength": 1,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Company or application website",
          "title": "Website"
        }
      },
      "title": "ContactInfo",
      "type": "object"
    },
    "EducationRequirement": {
      "description": "Education requirements for the job",
      "properties": {
        "degree": {
          "description": "Required degree",
          "title": "Degree",
          "type": "string"
        },
        "field": {
          "description": "Field of study",
          "title": "Field",
          "type": "string"
        },
        "required": {
          "description": "Whether this education is required or preferred",
          "title": "Required",
          "type": "boolean"
        }
      },
      "required": [
        "degree",
        "field",
        "required"
      ],
      "title": "EducationRequirement",
      "type": "object"
    }
  },
  "description": "Job advertisement model",
  "properties": {
    "title": {
      "description": "Job title",
      "title": "Title",
      "type": "string"
    },
    "company": {
      "description": "Company name",
      "title": "Company",
      "type": "string"
    },
    "department": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Department within the company",
      "title": "Department"
    },
    "location": {
      "additionalProperties": {
        "type": "string"
      },
      "description": "Job location with city, state, country",
      "title": "Location",
      "type": "object"
    },
    "salary": {
      "description": "Salary information including range, currency, and period",
      "title": "Salary",
      "type": "object"
    },
    "employment_type": {
      "description": "Type of employment (full-time, part-time, contract, etc.)",
      "title": "Employment Type",
      "type": "string"
    },
    "experience": {
      "description": "Experience requirements including years and level",
      "title": "Experience",
      "type": "object"
    },
    "required_skills": {
      "description": "List of required skills",
      "items": {
        "type": "string"
      },
      "title": "Required Skills",
      "type": "array"
    },
    "preferred_skills": {
      "description": "List of preferred skills",
      "items": {
        "type": "string"
      },
      "title": "Preferred Skills",
      "type": "array"
    },
    "education": {
      "description": "List of education requirements",
      "items": {
        "$ref": "#/$defs/EducationRequirement"
      },
      "title": "Education",
      "type": "array"
    },
    "responsibilities": {
      "description": "List of job responsibilities",
      "items": {
        "type": "string"
      },
      "title": "Responsibilities",
      "type": "array"
    },
    "benefits": {
      "description": "List of benefits offered",
      "items": {
        "$ref": "#/$defs/Benefit"
      },
      "title": "Benefits",
      "type": "array"
    },
    "description": {
      "description": "Detailed job description",
      "title": "Description",
      "type": "string"
    },
    "application_deadline": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Application deadline date",
      "title": "Application Deadline"
    },
    "contact_info": {
      "$ref": "#/$defs/ContactInfo",
      "description": "Contact information for applications"
    },
    "remote": {
      "description": "Whether the job is remote or not",
      "title": "Remote",
      "type": "boolean"
    },
    "travel_required": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Travel requirements if any",
      "title": "Travel Required"
    },
    "posting_date": {
      "description": "Date when the job was posted",
      "format": "date",
      "title": "Posting Date",
      "type": "string"
    }
  },
  "required": [
    "title",
    "company",
    "location",
    "salary",
    "employment_type",
    "experience",
    "required_skills",
    "responsibilities",
    "description",
    "contact_info",
    "remote",
    "posting_date"
  ],
  "title": "JobAd",
  "type": "object"
}
```
```

#### Provider Details

##### openai

Error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: your_ope************here. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}

##### anthropic

Error: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}}

##### google

Error: Failed to get response from Google Vertex AI: File path/to/your/credentials.json was not found.

##### mistral

Error: Provider mistral not initialized
