# Running Tests with LLM Tester

This guide explains how to run tests using the LLM Tester framework. LLM Tester provides multiple ways to run tests, from command-line options to an interactive interface.

## Test Modes

LLM Tester supports three main testing modes:

1. **Standard Tests**: Run tests with standard prompts
2. **Optimized Tests**: Run tests with automatically optimized prompts
3. **Mock Tests**: Run tests with mock responses (no API calls)

## Command-Line Interface

The improved command-line interface provides several ways to run tests:

### Quick Test Command

The `test` command provides a straightforward way to run tests:

```bash
# Run tests with default settings
./runner.py test

# Test specific providers
./runner.py test -p openai -p anthropic

# Test specific modules
./runner.py test -m job_ads -m product_descriptions

# Run optimized tests
./runner.py test -o

# Specify models to use
./runner.py test -p openai --model openai:gpt-4-turbo

# Save results to a specific directory
./runner.py test --output ./my_results
```

### Non-Interactive Mode (Legacy)

For backward compatibility, you can also use the non-interactive flag:

```bash
# Run with default settings
./runner.py -n

# Run with specific providers
./runner.py -n -p openai -p anthropic

# Run optimized tests
./runner.py -n -o
```

## Interactive Interface

The interactive interface provides a menu-driven experience:

```bash
# Start the interactive interface
./runner.py interactive
```

The interactive interface offers these options:

1. **Check Setup**: Verify environment and dependencies
2. **List Test Cases**: Show all available test cases
3. **Run Tests**: Run tests with current settings
4. **Run Optimized Tests**: Run tests with prompt optimization
5. **Run Default Tests**: Run tests with default settings
6. **Setup Providers**: Choose which LLM providers to use
7. **Setup Models**: Configure which models to use for each provider
8. **Edit Configuration**: Edit test settings
9. **Create New Model**: Generate scaffolding for a new model

## Verify Provider Setup

Before running tests, you can verify your provider setup:

```bash
./runner.py verify
```

This shows which providers are discovered and configured properly.

## Running Tests with Specific Models

You can specify which models to use for each provider:

```bash
# Command-line
./runner.py test -p openai --model openai:gpt-4-turbo -p anthropic --model anthropic:claude-3-sonnet-20240229

# Interactive
# Choose "Setup Models" from the menu
```

## Running Optimized Tests

Optimized tests automatically refine prompts based on initial results:

```bash
# Command-line
./runner.py test -o

# Interactive
# Choose "Run Optimized Tests" from the menu
```

The optimization process:
1. Runs tests with standard prompts
2. Analyzes results to identify improvement areas
3. Generates optimized prompts
4. Runs tests again with the optimized prompts
5. Compares and reports the improvement

## Running Mock Tests

Mock tests simulate responses without making API calls:

```bash
# Command-line
./runner.py test -p mock_provider

# Interactive
# Choose "Setup Providers" from the menu and select "Mock"
```

## Analyzing Test Results

After running tests, LLM Tester will:

1. Display a summary of results
2. Save detailed reports to the output directory
3. Generate cost reports for token usage analysis

Reports include:
- Overall accuracy per provider and model
- Detailed field-by-field accuracy
- Token usage and cost information
- Comparison between standard and optimized prompts (for optimized tests)

## Configuring Test Settings

Test settings can be configured through the interactive interface or by editing the `config.json` file:

```bash
# Interactive
# Choose "Edit Configuration" from the menu

# Manual
# Edit config.json directly
```

Key settings include:
- Output directory for reports
- Default providers and models
- Whether to save optimized prompts
- Default modules to test

## Best Practices

1. **Start with Verification**: Use `./runner.py verify` to check your setup
2. **Use Mock Tests First**: Test with mock providers before using real APIs
3. **Compare Providers**: Test with multiple providers to compare performance
4. **Optimize Prompts**: Use optimized tests to improve accuracy
5. **Analyze Costs**: Review cost reports to optimize for performance/cost ratio