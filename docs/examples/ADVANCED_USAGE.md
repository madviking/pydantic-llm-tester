# Advanced Usage Examples

This document provides advanced usage examples for the LLM Tester framework.

## Custom Model Implementation

Creating a custom model for extracting structured data from news articles:

```python
# news_article.py
import os
import json
from typing import List, Optional, Dict, Any, ClassVar
from pydantic import BaseModel, Field
from datetime import date


class NewsArticle(BaseModel):
    """
    Model for extracting structured information from news articles
    """
    
    # Class variables for module configuration
    MODULE_NAME: ClassVar[str] = "news_articles"
    TEST_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "tests")
    REPORT_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "reports")
    
    # Define model fields
    headline: str = Field(..., description="Article headline")
    publication_date: date = Field(..., description="Publication date")
    author: str = Field(..., description="Article author")
    source: str = Field(..., description="News source")
    content_summary: str = Field(..., description="Summary of the article content")
    categories: List[str] = Field(default_factory=list, description="Article categories")
    location: Optional[str] = Field(None, description="Location mentioned in the article")
    people_mentioned: List[str] = Field(default_factory=list, description="People mentioned in the article")
    organizations_mentioned: List[str] = Field(default_factory=list, description="Organizations mentioned in the article")
    
    @classmethod
    def get_test_cases(cls) -> List[Dict[str, Any]]:
        """Discover test cases for this module"""
        # Implementation as in ADDING_MODELS.md
        # ...
    
    @classmethod
    def save_module_report(cls, results: Dict[str, Any], run_id: str) -> str:
        """Save a report specifically for this module"""
        # Implementation as in ADDING_MODELS.md
        # ...
    
    @classmethod
    def save_module_cost_report(cls, cost_data: Dict[str, Any], run_id: str) -> str:
        """Save a cost report specifically for this module"""
        # Implementation as in ADDING_MODELS.md
        # ...
```

Using the custom model:

```python
# Copy the file to the models directory
import shutil
import os

# Create module directory structure
os.makedirs("llm_tester/models/news_articles/tests/sources", exist_ok=True)
os.makedirs("llm_tester/models/news_articles/tests/prompts", exist_ok=True)
os.makedirs("llm_tester/models/news_articles/tests/expected", exist_ok=True)
os.makedirs("llm_tester/models/news_articles/reports", exist_ok=True)

# Copy the model file
shutil.copy("news_article.py", "llm_tester/models/news_articles/model.py")

# Create __init__.py
with open("llm_tester/models/news_articles/__init__.py", "w") as f:
    f.write('''"""News article extraction model"""

from .model import NewsArticle

__all__ = ["NewsArticle"]
''')

# Create __init__.py for tests
with open("llm_tester/models/news_articles/tests/__init__.py", "w") as f:
    f.write('"""Test cases for news article extraction"""')

# Test the model
from llm_tester import LLMTester
tester = LLMTester(providers=["openai"])
tester.run_tests(modules=["news_articles"])
```

## Custom Provider Implementation

Creating a custom provider for a new LLM API:

```python
# custom_provider.py
"""Custom provider implementation"""

import logging
import json
import os
import requests
from typing import Dict, Any, Tuple, Optional, List, Union

from llm_tester.llms.base import BaseLLM, ModelConfig
from llm_tester.utils.cost_manager import UsageData


class CustomProvider(BaseLLM):
    """Provider implementation for a custom LLM API"""
    
    def __init__(self, config=None):
        """Initialize the provider"""
        super().__init__(config)
        
        # Get API key
        api_key = self.get_api_key()
        if not api_key:
            self.logger.warning(f"No API key found. Set the {self.config.env_key if self.config else 'CUSTOM_API_KEY'} environment variable.")
            self.client = None
            return
            
        # Initialize client - using requests directly in this example
        self.api_key = api_key
        self.api_base = os.environ.get("CUSTOM_API_BASE", "https://api.example.com")
        self.logger.info("Custom provider initialized")
        
    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        """Implementation-specific API call
        
        Args:
            prompt: The full prompt text to send
            system_prompt: System prompt from config
            model_name: Clean model name (without provider prefix)
            model_config: Model configuration
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if not self.api_key:
            self.logger.error("API key not initialized")
            raise ValueError("API key not initialized")
            
        # Calculate max tokens based on model config
        max_tokens = min(model_config.max_output_tokens, 4096)
        
        # Ensure we have a valid system prompt
        if not system_prompt:
            system_prompt = "Extract the requested information from the provided text as accurate JSON."
        
        # Make the API call
        self.logger.info(f"Sending request to custom model {model_name}")
        
        try:
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
            
            # Send the request
            response = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Extract response text
            response_text = result["choices"][0]["message"]["content"]
            
            # Create usage data
            usage_data = {
                "prompt_tokens": result["usage"]["prompt_tokens"],
                "completion_tokens": result["usage"]["completion_tokens"],
                "total_tokens": result["usage"]["total_tokens"]
            }
            
            return response_text, usage_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling API: {str(e)}")
            raise ValueError(f"Error calling API: {str(e)}")
```

Creating the provider configuration:

```json
{
  "name": "custom",
  "provider_type": "custom",
  "env_key": "CUSTOM_API_KEY",
  "env_key_secret": "",
  "system_prompt": "Extract the requested information from the provided text as accurate JSON.",
  "models": [
    {
      "name": "custom-model-1",
      "default": true,
      "preferred": true,
      "cost_input": 1.0,
      "cost_output": 2.0,
      "cost_category": "standard",
      "max_input_tokens": 8000,
      "max_output_tokens": 4000
    }
  ]
}
```

Using the custom provider:

```python
# Create provider directory
import os
os.makedirs("llm_tester/llms/custom", exist_ok=True)

# Copy the provider file
import shutil
shutil.copy("custom_provider.py", "llm_tester/llms/custom/provider.py")

# Create __init__.py
with open("llm_tester/llms/custom/__init__.py", "w") as f:
    f.write('"""Custom provider implementation"""')

# Save config.json
with open("llm_tester/llms/custom/config.json", "w") as f:
    f.write('''
{
  "name": "custom",
  "provider_type": "custom",
  "env_key": "CUSTOM_API_KEY",
  "env_key_secret": "",
  "system_prompt": "Extract the requested information from the provided text as accurate JSON.",
  "models": [
    {
      "name": "custom-model-1",
      "default": true,
      "preferred": true,
      "cost_input": 1.0,
      "cost_output": 2.0,
      "cost_category": "standard",
      "max_input_tokens": 8000,
      "max_output_tokens": 4000
    }
  ]
}
''')

# Add to models_pricing.json
import json
with open("models_pricing.json", "r") as f:
    pricing = json.load(f)

pricing["custom"] = {
    "custom-model-1": {
        "input": 1.0,
        "output": 2.0
    }
}

with open("models_pricing.json", "w") as f:
    json.dump(pricing, f, indent=2)

# Set environment variables
import os
os.environ["CUSTOM_API_KEY"] = "your-api-key"
os.environ["CUSTOM_API_BASE"] = "https://api.example.com"

# Reset provider caches
from llm_tester.llms import reset_caches, reset_provider_cache
reset_caches()
reset_provider_cache()

# Test the provider
from llm_tester import LLMTester
tester = LLMTester(providers=["custom"])
results = tester.run_tests()
```

## Advanced Prompt Optimization

Creating a custom prompt optimization strategy:

```python
# In a new file: custom_optimizer.py
from llm_tester.utils.prompt_optimizer import PromptOptimizer
from typing import Dict, Any, List, Type, Optional
from pydantic import BaseModel


class EnhancedPromptOptimizer(PromptOptimizer):
    """Enhanced prompt optimizer with advanced strategies"""
    
    def __init__(self):
        super().__init__()
        
    def optimize_prompt(self, original_prompt: str, source: str, model_class: Type[BaseModel], 
                        expected_data: Dict[str, Any], initial_results: Dict[str, Any],
                        save_to_file: bool = True, original_prompt_path: Optional[str] = None) -> str:
        """
        Apply advanced optimization strategies to improve the prompt
        """
        # Start with a basic analysis
        issues = self._analyze_results(initial_results, expected_data)
        
        # Get field descriptions from the model
        field_descriptions = {}
        for field_name, field in model_class.__fields__.items():
            field_descriptions[field_name] = field.field_info.description
        
        # Build enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(
            original_prompt=original_prompt,
            issues=issues,
            field_descriptions=field_descriptions,
            expected_data=expected_data,
            source=source
        )
        
        # Save the optimized prompt if requested
        if save_to_file and original_prompt_path:
            self._save_optimized_prompt(enhanced_prompt, original_prompt_path)
            
        return enhanced_prompt
    
    def _analyze_results(self, initial_results: Dict[str, Any], expected_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze initial results to find issues"""
        issues = []
        
        for provider, results in initial_results.items():
            if "error" in results:
                issues.append({
                    "type": "provider_error",
                    "provider": provider,
                    "message": results["error"]
                })
                continue
                
            if "validation" not in results:
                continue
                
            validation = results["validation"]
            if not validation.get("success", False):
                issues.append({
                    "type": "validation_failure",
                    "provider": provider,
                    "message": validation.get("error", "Unknown validation error")
                })
                continue
                
            # Compare fields
            if "validated_data" in validation:
                actual_data = validation["validated_data"]
                
                for field, expected_value in expected_data.items():
                    if field not in actual_data:
                        issues.append({
                            "type": "missing_field",
                            "field": field,
                            "provider": provider
                        })
                    elif actual_data[field] != expected_value:
                        issues.append({
                            "type": "incorrect_value",
                            "field": field,
                            "provider": provider,
                            "expected": expected_value,
                            "actual": actual_data[field]
                        })
        
        return issues
    
    def _build_enhanced_prompt(self, original_prompt: str, issues: List[Dict[str, Any]], 
                             field_descriptions: Dict[str, str], expected_data: Dict[str, Any],
                             source: str) -> str:
        """Build an enhanced prompt based on issues found"""
        
        # Start with the original prompt
        enhanced_prompt = original_prompt
        
        # Add field-specific instructions for problem areas
        field_instructions = []
        
        for issue in issues:
            if issue["type"] in ["missing_field", "incorrect_value"]:
                field = issue["field"]
                if field in field_descriptions:
                    field_instructions.append(f"- {field}: {field_descriptions[field]}")
        
        if field_instructions:
            enhanced_prompt += "\n\nPay special attention to these fields:\n"
            enhanced_prompt += "\n".join(field_instructions)
        
        # Add examples for fields with issues
        examples = {}
        for issue in issues:
            if issue["type"] == "incorrect_value":
                field = issue["field"]
                if field in expected_data and field not in examples:
                    examples[field] = expected_data[field]
        
        if examples:
            enhanced_prompt += "\n\nHere are examples of correct values for some fields:\n"
            for field, value in examples.items():
                enhanced_prompt += f"- {field}: {value}\n"
        
        # Add reminder about JSON format
        enhanced_prompt += "\n\nMake sure to return valid JSON that conforms exactly to the schema. Do not include any explanatory text outside the JSON."
        
        return enhanced_prompt
```

Using the custom optimizer:

```python
# Use the custom optimizer
from custom_optimizer import EnhancedPromptOptimizer

# Initialize tester
from llm_tester import LLMTester
tester = LLMTester(providers=["openai"])

# Replace the default optimizer with our enhanced version
tester.prompt_optimizer = EnhancedPromptOptimizer()

# Run optimized tests
optimized_results = tester.run_optimized_tests()
```

## Integration with External Systems

### Slack Notifications

```python
# slack_notifier.py
import requests
import json
from typing import Dict, Any

class SlackNotifier:
    """Send notifications to Slack about test results"""
    
    def __init__(self, webhook_url: str):
        """Initialize with Slack webhook URL"""
        self.webhook_url = webhook_url
        
    def notify_test_complete(self, results: Dict[str, Any], run_id: str) -> None:
        """Send notification about completed tests"""
        summary = self._generate_summary(results)
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "LLM Test Results"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Run ID:* {run_id}\n*Tests:* {len(results)}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": summary
                    }
                }
            ]
        }
        
        requests.post(
            self.webhook_url,
            data=json.dumps(message),
            headers={"Content-Type": "application/json"}
        )
        
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate a summary of test results"""
        summary = "*Provider Performance*\n"
        
        provider_stats = {}
        for test_id, test_results in results.items():
            for provider, provider_result in test_results.items():
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        "success": 0,
                        "error": 0,
                        "total": 0,
                        "accuracy_sum": 0,
                        "tests_with_accuracy": 0
                    }
                
                stats = provider_stats[provider]
                stats["total"] += 1
                
                if "error" in provider_result:
                    stats["error"] += 1
                    continue
                    
                validation = provider_result.get("validation", {})
                if validation.get("success", False):
                    stats["success"] += 1
                    accuracy = validation.get("accuracy", 0.0)
                    stats["accuracy_sum"] += accuracy
                    stats["tests_with_accuracy"] += 1
                else:
                    stats["error"] += 1
        
        # Create summary
        for provider, stats in provider_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            avg_accuracy = stats["accuracy_sum"] / stats["tests_with_accuracy"] if stats["tests_with_accuracy"] > 0 else 0
            
            summary += f"*{provider}*: "
            summary += f"{success_rate:.1f}% success rate, "
            summary += f"{avg_accuracy:.1f}% avg accuracy "
            summary += f"({stats['success']}/{stats['total']} tests)\n"
        
        return summary
```

Using the Slack notifier:

```python
# Initialize Slack notifier
from slack_notifier import SlackNotifier
notifier = SlackNotifier("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")

# Run tests
from llm_tester import LLMTester
tester = LLMTester(providers=["openai", "anthropic"])
results = tester.run_tests()

# Send notification
notifier.notify_test_complete(results, tester.run_id)
```

### Integration with CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
# .github/workflows/llm-tests.yml
name: LLM Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Run LLM tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        ./runner.py test -p openai -p anthropic --output test_results
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: test_results/
```

## Custom Reporting Integration

Creating a custom report format:

```python
# custom_reporter.py
from typing import Dict, Any
import json
import os
import matplotlib.pyplot as plt
import pandas as pd

class CustomReporter:
    """Generate custom reports for LLM test results"""
    
    def __init__(self, output_dir: str):
        """Initialize with output directory"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_report(self, results: Dict[str, Any], run_id: str) -> None:
        """Generate custom reports"""
        # Create comparison charts
        self._create_accuracy_chart(results, run_id)
        
        # Create detailed CSV report
        self._create_csv_report(results, run_id)
        
        # Create JSON summary
        self._create_json_summary(results, run_id)
    
    def _create_accuracy_chart(self, results: Dict[str, Any], run_id: str) -> None:
        """Create accuracy comparison chart"""
        # Extract accuracy data
        provider_data = {}
        
        for test_id, test_results in results.items():
            test_name = test_id.split('/')[-1]
            
            for provider, provider_result in test_results.items():
                if provider not in provider_data:
                    provider_data[provider] = []
                
                if "error" in provider_result:
                    provider_data[provider].append((test_name, 0))
                    continue
                    
                validation = provider_result.get("validation", {})
                accuracy = validation.get("accuracy", 0.0) if validation.get("success", False) else 0.0
                provider_data[provider].append((test_name, accuracy))
        
        # Create DataFrame
        data = []
        for provider, values in provider_data.items():
            for test_name, accuracy in values:
                data.append({
                    "Provider": provider,
                    "Test": test_name,
                    "Accuracy": accuracy
                })
        
        df = pd.DataFrame(data)
        
        # Create chart
        plt.figure(figsize=(12, 6))
        chart = df.pivot(index="Test", columns="Provider", values="Accuracy").plot(
            kind="bar",
            title="Accuracy Comparison by Provider",
            ylabel="Accuracy (%)",
            rot=45
        )
        
        # Save chart
        chart_path = os.path.join(self.output_dir, f"accuracy_chart_{run_id}.png")
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()
    
    def _create_csv_report(self, results: Dict[str, Any], run_id: str) -> None:
        """Create detailed CSV report"""
        data = []
        
        for test_id, test_results in results.items():
            module, test_name = test_id.split('/')
            
            for provider, provider_result in test_results.items():
                if "error" in provider_result:
                    data.append({
                        "Module": module,
                        "Test": test_name,
                        "Provider": provider,
                        "Model": provider_result.get("model", "unknown"),
                        "Success": False,
                        "Error": provider_result["error"],
                        "Accuracy": 0,
                        "PromptTokens": 0,
                        "CompletionTokens": 0,
                        "TotalTokens": 0,
                        "Cost": 0
                    })
                    continue
                
                validation = provider_result.get("validation", {})
                success = validation.get("success", False)
                accuracy = validation.get("accuracy", 0.0) if success else 0.0
                
                usage = provider_result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                total_cost = usage.get("total_cost", 0)
                
                data.append({
                    "Module": module,
                    "Test": test_name,
                    "Provider": provider,
                    "Model": provider_result.get("model", "unknown"),
                    "Success": success,
                    "Error": validation.get("error", "") if not success else "",
                    "Accuracy": accuracy,
                    "PromptTokens": prompt_tokens,
                    "CompletionTokens": completion_tokens,
                    "TotalTokens": total_tokens,
                    "Cost": total_cost
                })
        
        # Create DataFrame and save CSV
        df = pd.DataFrame(data)
        csv_path = os.path.join(self.output_dir, f"detailed_report_{run_id}.csv")
        df.to_csv(csv_path, index=False)
    
    def _create_json_summary(self, results: Dict[str, Any], run_id: str) -> None:
        """Create JSON summary"""
        # Calculate provider summaries
        provider_summary = {}
        
        for test_id, test_results in results.items():
            for provider, provider_result in test_results.items():
                if provider not in provider_summary:
                    provider_summary[provider] = {
                        "total_tests": 0,
                        "successful_tests": 0,
                        "error_tests": 0,
                        "total_accuracy": 0,
                        "avg_accuracy": 0,
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_cost": 0
                    }
                
                summary = provider_summary[provider]
                summary["total_tests"] += 1
                
                if "error" in provider_result:
                    summary["error_tests"] += 1
                    continue
                
                validation = provider_result.get("validation", {})
                if validation.get("success", False):
                    summary["successful_tests"] += 1
                    accuracy = validation.get("accuracy", 0.0)
                    summary["total_accuracy"] += accuracy
                else:
                    summary["error_tests"] += 1
                
                usage = provider_result.get("usage", {})
                summary["total_tokens"] += usage.get("total_tokens", 0)
                summary["prompt_tokens"] += usage.get("prompt_tokens", 0)
                summary["completion_tokens"] += usage.get("completion_tokens", 0)
                summary["total_cost"] += usage.get("total_cost", 0)
        
        # Calculate averages
        for provider, summary in provider_summary.items():
            if summary["successful_tests"] > 0:
                summary["avg_accuracy"] = summary["total_accuracy"] / summary["successful_tests"]
        
        # Create summary JSON
        summary = {
            "run_id": run_id,
            "total_tests": len(results),
            "providers": provider_summary
        }
        
        # Save JSON
        json_path = os.path.join(self.output_dir, f"summary_{run_id}.json")
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2)
```

Using the custom reporter:

```python
# Initialize custom reporter
from custom_reporter import CustomReporter
reporter = CustomReporter("custom_reports")

# Run tests
from llm_tester import LLMTester
tester = LLMTester(providers=["openai", "anthropic"])
results = tester.run_tests()

# Generate custom reports
reporter.generate_report(results, tester.run_id)
```