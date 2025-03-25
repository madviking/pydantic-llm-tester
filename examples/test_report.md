# LLM Tester Report - 2025-03-25 10:44:51

## Standard Performance Report

### Test: job_ads/complex

#### Performance Summary

| Provider | Model | Accuracy |
|----------|-------|----------|
| openai | gpt-4-turbo | 0.00% |
| anthropic | claude-3-haiku-20240307 | 0.00% |
| google | gemini-1.5-pro | 0.00% |
| mistral | mistral-medium | 0.00% |

#### Provider Details

##### openai

Validation failed: 8 validation errors for JobAd
title
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
company
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
salary
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
experience
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
responsibilities
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
description
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
contact_info
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
remote
  Field required [type=missing, input_value={'job_title': 'Senior Mac...ing_date': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing

##### anthropic

Validation failed: 9 validation errors for JobAd
title
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
company
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
employment_type
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
required_skills
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
education
  Input should be a valid list [type=list_type, input_value={'degree': "Master's", 'f...ning or related field'}}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/list_type
description
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
contact_info
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
remote
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
posting_date
  Field required [type=missing, input_value={'jobTitle': 'Senior Mach...tingDate': '2025-03-15'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing

##### google

Error: Provider google not initialized

##### mistral

Error: Provider mistral not initialized

### Test: job_ads/simple

#### Performance Summary

| Provider | Model | Accuracy |
|----------|-------|----------|
| openai | gpt-4-turbo | 0.00% |
| anthropic | claude-3-haiku-20240307 | 0.00% |
| google | gemini-1.5-pro | 0.00% |
| mistral | mistral-medium | 0.00% |

#### Provider Details

##### openai

Validation failed: 11 validation errors for JobAd
title
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
company
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
location
  Input should be a valid dictionary [type=dict_type, input_value='Austin, Texas, United States', input_type=str]
    For further information visit https://errors.pydantic.dev/2.10/v/dict_type
salary
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
employment_type
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
experience
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
responsibilities
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
description
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
contact_info
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
remote
  Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='Hybrid (2-3 days in office)', input_type=str]
    For further information visit https://errors.pydantic.dev/2.10/v/bool_parsing
posting_date
  Field required [type=missing, input_value={'job_title': 'Full Stack...d (2-3 days in office)'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing

##### anthropic

Validation failed: 13 validation errors for JobAd
title
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
company
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
location
  Input should be a valid dictionary [type=dict_type, input_value='Austin, Texas, United States', input_type=str]
    For further information visit https://errors.pydantic.dev/2.10/v/dict_type
salary
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
employment_type
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
experience
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
required_skills
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
education
  Input should be a valid list [type=list_type, input_value="Bachelor's degree in Com...cience or related field", input_type=str]
    For further information visit https://errors.pydantic.dev/2.10/v/list_type
responsibilities
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
description
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
contact_info
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
remote
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
posting_date
  Field required [type=missing, input_value={'jobTitle': 'Full Stack ...am or client meetings.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing

##### google

Error: Provider google not initialized

##### mistral

Error: Provider mistral not initialized
