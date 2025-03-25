#!/usr/bin/env python3
"""
Interactive Runner for LLM Tester

This script provides an interactive interface for running LLM tests,
managing test cases, and viewing results.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from unittest.mock import patch
import importlib

# Add the parent directory to the path to import llm_tester
sys.path.append(str(Path(__file__).parent))

from llm_tester import LLMTester

# Default model configurations for each provider
DEFAULT_MODELS = {
    "openai": "gpt-4",
    "anthropic": "claude-3-opus-20240229",
    "mistral": "mistral-large-latest",
    "google": "gemini-pro"
}

# Mock responses for testing without API keys
MOCK_RESPONSES = {
    "job_ads": """
    {
      "title": "SENIOR MACHINE LEARNING ENGINEER",
      "company": "DataVision Analytics",
      "department": "AI Research Division",
      "location": {
        "city": "Boston",
        "state": "Massachusetts",
        "country": "United States"
      },
      "salary": {
        "range": "$150,000 - $190,000",
        "currency": "USD",
        "period": "annually"
      },
      "employment_type": "Full-time",
      "experience": {
        "years": "5+ years",
        "level": "Senior"
      },
      "required_skills": [
        "Python",
        "TensorFlow/PyTorch",
        "computer vision or NLP algorithms",
        "distributed computing",
        "data preprocessing",
        "feature engineering"
      ],
      "preferred_skills": [
        "GPT models",
        "fine-tuning",
        "edge deployment"
      ],
      "education": [
        {
          "degree": "Master's degree",
          "field": "Computer Science, AI, or related field",
          "required": true
        },
        {
          "degree": "PhD",
          "field": "Machine Learning or related field",
          "required": false
        }
      ],
      "responsibilities": [
        "Design and implement novel ML architectures for complex problems",
        "Lead research projects exploring state-of-the-art approaches",
        "Mentor junior team members on ML best practices"
      ],
      "benefits": [
        {
          "name": "Comprehensive health, dental, and vision insurance",
          "description": "Includes coverage for dependents and domestic partners"
        },
        {
          "name": "401(k) matching program",
          "description": "Up to 5% match with immediate vesting"
        }
      ],
      "description": "As a Senior ML Engineer, you will be at the forefront of our AI research initiatives.",
      "application_deadline": "2025-04-30",
      "contact_info": {
        "name": "Dr. Sarah Chen",
        "email": "ml-recruiting@datavisionanalytics.com",
        "phone": "(617) 555-9876",
        "website": "https://careers.datavisionanalytics.com/ml-engineer"
      },
      "remote": true,
      "travel_required": "Occasional travel (10-15%) for conferences, team off-sites, and client meetings",
      "posting_date": "2025-03-15"
    }
    """,
    "product_descriptions": """
    {
      "id": "WE-X1-BLK",
      "name": "Wireless Earbuds X1",
      "brand": "TechGear",
      "category": "Audio Accessories",
      "price": {
        "amount": 79.99,
        "currency": "USD",
        "discount_percentage": 20.0,
        "original_amount": 99.99
      },
      "description": "Experience true wireless freedom with our X1 Wireless Earbuds.",
      "features": [
        "True wireless design",
        "Bluetooth 5.2 connectivity",
        "8-hour battery life (30 hours with charging case)",
        "Active noise cancellation"
      ],
      "specifications": [
        {
          "name": "Driver Size",
          "value": "10",
          "unit": "mm"
        },
        {
          "name": "Frequency Response",
          "value": "20Hz-20KHz"
        }
      ],
      "dimensions": {
        "length": 2.1,
        "width": 1.8,
        "height": 2.5,
        "unit": "cm"
      },
      "weight": {
        "value": 5.6,
        "unit": "g"
      },
      "colors": [
        "Midnight Black",
        "Arctic White",
        "Navy Blue"
      ],
      "images": [
        "https://techgear.com/images/wireless-earbuds-x1-black.jpg",
        "https://techgear.com/images/wireless-earbuds-x1-case.jpg"
      ],
      "shipping_info": {
        "ships_within": "1 business day",
        "shipping_type": "Free standard shipping"
      },
      "warranty": "1-year limited warranty",
      "return_policy": "30-day money-back guarantee",
      "reviews": {
        "rating": 4.6,
        "count": 352
      },
      "release_date": "2025-01-15",
      "is_bestseller": true,
      "related_products": [
        "WE-X1-TIPS",
        "WE-X1-CASE",
        "BT-SPK-10"
      ]
    }
    """
}

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header"""
    width = 80
    print("=" * width)
    print(f"{title.center(width)}")
    print("=" * width)
    print()

def print_menu(options: List[Tuple[str, str]]):
    """Print a menu with options and descriptions"""
    for i, (key, desc) in enumerate(options, 1):
        print(f"{i}. {key:<25} - {desc}")
    print("q. Quit")
    print()

def get_user_choice(max_option: int) -> str:
    """Get user choice from input"""
    while True:
        choice = input("Enter your choice: ").strip().lower()
        if choice == 'q':
            return choice
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= max_option:
                return choice_num
        except ValueError:
            pass
        
        print(f"Invalid choice. Please enter a number between 1 and {max_option} or 'q' to quit.")

def load_env_file(env_path: str = None):
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            default_paths = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    load_dotenv(dotenv_path=path)
                    print(f"Loaded environment variables from {path}")
                    return True
            
            print("No .env file found. Please set up API keys manually.")
            return False
    except ImportError:
        print("python-dotenv package not installed. Cannot load .env file.")
        return False

def check_api_keys() -> Dict[str, Dict[str, Any]]:
    """Check which API keys are available"""
    results = {
        "openai": {
            "available": bool(os.environ.get("OPENAI_API_KEY")),
            "key_name": "OPENAI_API_KEY",
            "value": os.environ.get("OPENAI_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "anthropic": {
            "available": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "key_name": "ANTHROPIC_API_KEY",
            "value": os.environ.get("ANTHROPIC_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "mistral": {
            "available": bool(os.environ.get("MISTRAL_API_KEY")),
            "key_name": "MISTRAL_API_KEY", 
            "value": os.environ.get("MISTRAL_API_KEY", ""),
            "missing": [],
            "status": "valid"
        },
        "google": {
            "available": False,
            "missing": [],
            "keys": {
                "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
                "GOOGLE_PROJECT_ID": os.environ.get("GOOGLE_PROJECT_ID", "")
            },
            "status": "valid"
        }
    }
    
    # Check Google specifically since it needs multiple keys
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    google_project = os.environ.get("GOOGLE_PROJECT_ID")
    
    if not google_creds:
        results["google"]["missing"].append("GOOGLE_APPLICATION_CREDENTIALS")
    elif not os.path.exists(google_creds):
        results["google"]["status"] = "invalid"
        results["google"]["error"] = f"Credentials file not found: {google_creds}"
    
    if not google_project:
        results["google"]["missing"].append("GOOGLE_PROJECT_ID")
    
    results["google"]["available"] = (
        bool(google_creds) and
        bool(google_project) and
        results["google"]["status"] == "valid"
    )
    
    # Check other providers
    for provider in ["openai", "anthropic", "mistral"]:
        key_name = results[provider]["key_name"]
        if not results[provider]["value"]:
            results[provider]["missing"].append(key_name)
            results[provider]["status"] = "missing"
    
    return results

def list_test_cases(tester: LLMTester):
    """List all available test cases"""
    clear_screen()
    print_header("Available Test Cases")
    
    test_cases = tester.discover_test_cases()
    
    if not test_cases:
        print("No test cases found.")
        return
    
    # Group by module
    grouped_cases = {}
    for test_case in test_cases:
        module = test_case['module']
        if module not in grouped_cases:
            grouped_cases[module] = []
        grouped_cases[module].append(test_case)
    
    for module, cases in grouped_cases.items():
        print(f"\n[{module}]")
        for i, case in enumerate(cases, 1):
            print(f"  {i}. {case['name']}")
    
    print("\nTotal test cases: ", len(test_cases))
    input("\nPress Enter to return to the main menu...")

def setup_providers() -> List[str]:
    """Setup which providers to use"""
    clear_screen()
    print_header("Setup Providers")
    
    api_keys = check_api_keys()
    
    print("Available providers:")
    for provider, info in api_keys.items():
        if info["available"]:
            status = "✓ (API key found and valid)"
        else:
            if provider == "google" and info["missing"]:
                status = f"✗ (Missing: {', '.join(info['missing'])})"
            elif provider == "google" and info["status"] == "invalid":
                status = f"✗ ({info.get('error', 'Invalid configuration')})"
            else:
                status = "✗ (API key missing)"
        print(f"  {provider:<10} - {status}")
    
    print("\nChoose providers to use:")
    print("1. All available providers")
    print("2. OpenAI only")
    print("3. Anthropic only")
    print("4. Mock (no API keys needed)")
    print("5. Custom selection")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    available_providers = [p for p, info in api_keys.items() if info["available"]]
    
    if choice == '1':
        if not available_providers:
            print("\nNo valid API keys found. Defaulting to mock provider.")
            return ["mock_provider"]
        return available_providers
    elif choice == '2':
        if api_keys["openai"]["available"]:
            return ["openai"]
        else:
            print("\nOpenAI API key not available. Using mock instead.")
            return ["mock_openai"]
    elif choice == '3':
        if api_keys["anthropic"]["available"]:
            return ["anthropic"]
        else:
            print("\nAnthropic API key not available. Using mock instead.")
            return ["mock_anthropic"]
    elif choice == '4':
        return ["mock_provider"]
    elif choice == '5':
        providers_input = input("Enter providers (comma-separated, e.g., 'openai,anthropic'): ")
        selected = [p.strip() for p in providers_input.split(',') if p.strip()]
        
        # Verify selected providers have API keys
        missing_providers = []
        for provider in selected:
            if provider in api_keys and not api_keys[provider]["available"]:
                missing_providers.append(provider)
        
        if missing_providers:
            print(f"\nWarning: Missing API keys for: {', '.join(missing_providers)}")
            use_anyway = input("Do you want to use these providers anyway? (y/n): ").strip().lower()
            if use_anyway != 'y':
                print("Removing providers with missing API keys.")
                selected = [p for p in selected if p not in missing_providers]
        
        if not selected:
            print("No valid providers selected. Defaulting to mock provider.")
            return ["mock_provider"]
        
        return selected
    else:
        print("Invalid choice. Using all available providers.")
        if not available_providers:
            print("No valid API keys found. Defaulting to mock provider.")
            return ["mock_provider"]
        return available_providers

def setup_models(providers: List[str]) -> Dict[str, str]:
    """Setup which models to use for each provider"""
    clear_screen()
    print_header("Setup Models")
    
    models = {}
    
    print("Current providers:")
    for provider in providers:
        default_model = DEFAULT_MODELS.get(provider, "default")
        print(f"  {provider:<10} - Default model: {default_model}")
    
    customize = input("\nDo you want to customize the models? (y/n): ").strip().lower()
    
    if customize != 'y':
        return models
    
    for provider in providers:
        default_model = DEFAULT_MODELS.get(provider, "default")
        model = input(f"Enter model for {provider} (default: {default_model}): ").strip()
        
        if model:
            models[provider] = model
    
    return models

def run_tests(tester: LLMTester, providers: List[str], models: Dict[str, str] = None, optimize: bool = False):
    """Run tests with the given configuration"""
    clear_screen()
    print_header("Running Tests" + (" (Optimized)" if optimize else ""))
    
    # Check if we're using mock providers
    using_mock = any(p.startswith("mock_") for p in providers)
    
    # If using mock, set up the mock function
    if using_mock:
        print("Using mock providers. No API calls will be made.")
        
        def mock_get_response(self, provider, prompt, source, model_name=None):
            # Determine which mock response to use based on source content
            if "job" in source.lower() or "software engineer" in source.lower() or "developer" in source.lower():
                mock_data = json.loads(MOCK_RESPONSES["job_ads"])
                # Customize the response based on the source
                if "FULL STACK" in source:
                    mock_data["title"] = "FULL STACK DEVELOPER"
                    mock_data["company"] = "TechInnovate Solutions"
                return json.dumps(mock_data)
            else:
                mock_data = json.loads(MOCK_RESPONSES["product_descriptions"])
                # Customize the response based on the source
                if "ULTRABOOK" in source:
                    mock_data["name"] = "UltraBook Pro X15 Laptop"
                    mock_data["brand"] = "TechVantage"
                return json.dumps(mock_data)
        
        # Patch the get_response method
        with patch('llm_tester.utils.provider_manager.ProviderManager.get_response', mock_get_response):
            if optimize:
                results = tester.run_optimized_tests(model_overrides=models)
            else:
                results = tester.run_tests(model_overrides=models)
    else:
        # Run with real providers
        if optimize:
            results = tester.run_optimized_tests(model_overrides=models)
        else:
            results = tester.run_tests(model_overrides=models)
    
    # Generate report
    report = tester.generate_report(results, optimized=optimize)
    
    # Create output directory
    os.makedirs("test_results", exist_ok=True)
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"test_results/report_{timestamp}{'_optimized' if optimize else ''}.md"
    
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\nReport saved to {report_path}")
    
    # Print summary
    print("\nTest Summary:")
    for test_name, test_results in results.items():
        print(f"  {test_name}:")
        for provider, provider_result in test_results.items():
            if 'validation' in provider_result:
                validation = provider_result.get('validation', {})
                accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                model = provider_result.get('model', 'default')
                print(f"    {provider} ({model}): {accuracy:.2f}%")
            else:
                print(f"    {provider}: Results available in full report")
    
    input("\nPress Enter to return to the main menu...")

def check_setup():
    """Check if the environment is properly set up"""
    clear_screen()
    print_header("Environment Setup Check")
    
    # Check for required packages
    print("Checking required packages...")
    required_packages = ['pydantic', 'dotenv', 'openai', 'anthropic', 'mistralai']
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ✗ {package} - not found")
    
    if missing_packages:
        print("\n📦 Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        
        install = input("\nDo you want to install the missing packages? (y/n): ").strip().lower()
        if install == 'y':
            for package in missing_packages:
                os.system(f"pip install {package}")
                print(f"Installed {package}")
    
    # Load environment variables
    print("\nChecking environment variables...")
    loaded = load_env_file()
    
    # Check API keys
    api_keys = check_api_keys()
    available_providers = [provider for provider, info in api_keys.items() if info["available"]]
    
    print("\n🔑 API Key Status:")
    for provider, info in api_keys.items():
        if info["available"]:
            print(f"  ✓ {provider:<10} - API key found and valid")
        else:
            if provider == "google":
                if info["missing"]:
                    print(f"  ✗ {provider:<10} - Missing: {', '.join(info['missing'])}")
                elif info["status"] == "invalid":
                    print(f"  ✗ {provider:<10} - Error: {info.get('error', 'Invalid configuration')}")
            else:
                print(f"  ✗ {provider:<10} - API key missing")
    
    print("\n📝 Summary:")
    if not available_providers:
        print("  - No API keys found. You can still use the mock provider for testing.")
        print("  - To use real providers, add your API keys to a .env file in the project root.")
        print("\nRequired environment variables:")
        print("  OPENAI_API_KEY=your_openai_key")
        print("  ANTHROPIC_API_KEY=your_anthropic_key")
        print("  MISTRAL_API_KEY=your_mistral_key")
        print("  GOOGLE_PROJECT_ID=your_google_project_id")
        print("  GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json")
    else:
        print(f"  - {len(available_providers)} of {len(api_keys)} providers configured correctly")
        print(f"  - Available providers: {', '.join(available_providers)}")
        
        if len(available_providers) < len(api_keys):
            print("\nMissing API keys:")
            for provider, info in api_keys.items():
                if not info["available"]:
                    if provider == "google":
                        for key in info["missing"]:
                            print(f"  {key}=your_{key.lower()}")
                    else:
                        print(f"  {info['key_name']}=your_{provider.lower()}_key")
    
    input("\nPress Enter to continue...")

def main(args=None):
    """Main function for the interactive runner"""
    parser = argparse.ArgumentParser(description="Interactive LLM Tester Runner")
    parser.add_argument(
        "--env", 
        type=str, 
        help="Path to .env file with API keys"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check setup and exit"
    )
    
    parsed_args = parser.parse_args(args)
    
    # Load environment variables
    if parsed_args.env:
        load_env_file(parsed_args.env)
    else:
        load_env_file()
    
    # Only check setup if requested
    if parsed_args.check_only:
        check_setup()
        return 0
    
    # Initialize tester
    tester = LLMTester(providers=[])
    
    # Main menu loop
    while True:
        clear_screen()
        print_header("LLM Tester Interactive Runner")
        
        options = [
            ("Check Setup", "Verify environment and dependencies"),
            ("List Test Cases", "Show all available test cases"),
            ("Run Tests", "Run tests with current settings"),
            ("Run Optimized Tests", "Run tests with prompt optimization"),
            ("Setup Providers", "Choose which LLM providers to use"),
            ("Setup Models", "Configure which models to use for each provider")
        ]
        
        print_menu(options)
        
        choice = get_user_choice(len(options))
        
        if choice == 'q':
            print("Exiting LLM Tester.")
            break
        
        if choice == 1:
            check_setup()
        elif choice == 2:
            list_test_cases(tester)
        elif choice == 3:
            providers = getattr(tester, 'providers', [])
            if not providers:
                providers = setup_providers()
                tester = LLMTester(providers=providers)
            models = setup_models(providers)
            run_tests(tester, providers, models)
        elif choice == 4:
            providers = getattr(tester, 'providers', [])
            if not providers:
                providers = setup_providers()
                tester = LLMTester(providers=providers)
            models = setup_models(providers)
            run_tests(tester, providers, models, optimize=True)
        elif choice == 5:
            providers = setup_providers()
            tester = LLMTester(providers=providers)
        elif choice == 6:
            providers = getattr(tester, 'providers', [])
            if not providers:
                providers = setup_providers()
                tester = LLMTester(providers=providers)
            setup_models(providers)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())