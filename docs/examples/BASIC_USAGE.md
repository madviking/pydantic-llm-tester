# Basic Usage Examples

This document provides basic usage examples for the LLM Tester framework.

## Command-Line Usage

### Running Tests with Default Settings

```bash
# Run the interactive interface
./runner.py

# Run with non-interactive mode
./runner.py -n

# Run the test command
./runner.py test
```

### Testing Specific Providers

```bash
# Test OpenAI and Anthropic
./runner.py test -p openai -p anthropic

# Test with specific models
./runner.py test -p openai --model openai:gpt-4-turbo
```

### Testing Specific Modules

```bash
# Test job_ads module
./runner.py test -m job_ads

# Test multiple modules
./runner.py test -m job_ads -m product_descriptions
```

### Running Optimized Tests

```bash
# Run optimized tests
./runner.py test -o

# Run optimized tests for specific providers and modules
./runner.py test -o -p openai -m job_ads
```

### Using Mock Providers

```bash
# Test with mock provider
./runner.py test -p mock_provider
```

## Python API Usage

### Basic Usage

```python
from llm_tester import LLMTester

# Initialize tester with providers
tester = LLMTester(providers=["openai", "anthropic"])

# Run tests
results = tester.run_tests()

# Generate report
report = tester.generate_report(results)
print(report)
```

### Running Tests with Model Overrides

```python
from llm_tester import LLMTester

# Initialize tester
tester = LLMTester(providers=["openai", "anthropic"])

# Define model overrides
model_overrides = {
    "openai": "gpt-4-turbo",
    "anthropic": "claude-3-opus-20240229"
}

# Run tests with model overrides
results = tester.run_tests(model_overrides=model_overrides)

# Generate report
report = tester.generate_report(results)
print(report)
```

### Running Tests for Specific Modules

```python
from llm_tester import LLMTester

# Initialize tester
tester = LLMTester(providers=["openai", "anthropic"])

# Run tests for specific modules
results = tester.run_tests(modules=["job_ads"])

# Generate report
report = tester.generate_report(results)
print(report)
```

### Running Optimized Tests

```python
from llm_tester import LLMTester

# Initialize tester
tester = LLMTester(providers=["openai", "anthropic"])

# Run optimized tests
optimized_results = tester.run_optimized_tests()

# Generate report
optimized_report = tester.generate_report(optimized_results, optimized=True)
print(optimized_report)
```

### Progress Tracking

```python
from llm_tester import LLMTester

# Initialize tester
tester = LLMTester(providers=["openai", "anthropic"])

# Define progress callback
def progress_callback(message):
    print(f"Progress: {message}")

# Run tests with progress tracking
results = tester.run_tests(progress_callback=progress_callback)
```

### Saving Reports

```python
from llm_tester import LLMTester

# Initialize tester
tester = LLMTester(providers=["openai", "anthropic"])

# Run tests
results = tester.run_tests()

# Generate report
report = tester.generate_report(results)

# Save report to file
output_dir = "my_results"
import os
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, "report.md"), "w") as f:
    f.write(report)

# Save cost report
cost_report_paths = tester.save_cost_report(output_dir)
print(f"Cost report saved to: {cost_report_paths}")
```

## Provider-Specific Examples

### OpenAI

```python
from llm_tester import LLMTester

# Initialize tester with OpenAI
tester = LLMTester(providers=["openai"])

# Run tests with OpenAI's GPT-4 Turbo
results = tester.run_tests(model_overrides={"openai": "gpt-4-turbo"})
```

### Anthropic

```python
from llm_tester import LLMTester

# Initialize tester with Anthropic
tester = LLMTester(providers=["anthropic"])

# Run tests with Anthropic's Claude 3 Opus
results = tester.run_tests(model_overrides={"anthropic": "claude-3-opus-20240229"})
```

### Mistral

```python
from llm_tester import LLMTester

# Initialize tester with Mistral
tester = LLMTester(providers=["mistral"])

# Run tests with Mistral's Large model
results = tester.run_tests(model_overrides={"mistral": "mistral-large-latest"})
```

### Google

```python
from llm_tester import LLMTester

# Initialize tester with Google
tester = LLMTester(providers=["google"])

# Run tests with Google's Gemini Pro
results = tester.run_tests(model_overrides={"google": "gemini-1.5-pro"})
```

### PydanticAI

```python
from llm_tester import LLMTester

# Initialize tester with PydanticAI
tester = LLMTester(providers=["pydantic_ai"])

# Run tests with PydanticAI using OpenAI's model
results = tester.run_tests(model_overrides={"pydantic_ai": "openai:gpt-4"})
```

### Mock Provider

```python
from llm_tester import LLMTester

# Initialize tester with Mock provider
tester = LLMTester(providers=["mock_provider"])

# Run tests with Mock provider
results = tester.run_tests()
```

## Analyzing Results

```python
from llm_tester import LLMTester

# Initialize tester
tester = LLMTester(providers=["openai", "anthropic"])

# Run tests
results = tester.run_tests()

# Analyze results
for test_id, test_results in results.items():
    print(f"Test: {test_id}")
    
    for provider, provider_results in test_results.items():
        if "error" in provider_results:
            print(f"  {provider}: Error - {provider_results['error']}")
            continue
            
        validation = provider_results.get("validation", {})
        accuracy = validation.get("accuracy", 0.0) if validation.get("success", False) else 0.0
        
        print(f"  {provider}: Accuracy - {accuracy:.2f}%")
        
        usage = provider_results.get("usage", {})
        if usage:
            total_tokens = usage.get("total_tokens", 0)
            total_cost = usage.get("total_cost", 0)
            print(f"    Tokens: {total_tokens}, Cost: ${total_cost:.6f}")
```

## Advanced Usage Examples

See the [ADVANCED_USAGE.md](ADVANCED_USAGE.md) document for more sophisticated usage examples, including:

- Custom model implementation
- Custom provider implementation
- Advanced prompt optimization
- Integration with other systems
- Automated workflows