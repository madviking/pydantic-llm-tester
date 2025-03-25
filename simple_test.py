#!/usr/bin/env python3
"""
Simple test to check basic Python functionality
"""

import os
import json

# Test reading files
def test_file_reading():
    try:
        # Get the path to the tests directory
        tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "llm_tester", "tests", "cases", "job_ads")
        
        # Read a source file
        source_path = os.path.join(tests_dir, "sources", "simple.txt")
        if os.path.exists(source_path):
            with open(source_path, 'r') as f:
                source_content = f.read()
            print(f"Successfully read source file: {len(source_content)} characters")
        else:
            print(f"Source file not found: {source_path}")
        
        # Read an expected JSON file
        expected_path = os.path.join(tests_dir, "expected", "simple.json")
        if os.path.exists(expected_path):
            with open(expected_path, 'r') as f:
                expected_data = json.load(f)
            print(f"Successfully read expected JSON with {len(expected_data)} keys")
            print(f"Job title: {expected_data.get('title')}")
        else:
            print(f"Expected file not found: {expected_path}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Test module structure
def test_module_structure():
    try:
        print("\nChecking module structure:")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Check important directories exist
        dirs_to_check = [
            "llm_tester",
            "llm_tester/models",
            "llm_tester/models/job_ads",
            "llm_tester/tests",
            "llm_tester/tests/cases",
            "llm_tester/tests/cases/job_ads",
            "llm_tester/utils",
            "tests"
        ]
        
        for dir_path in dirs_to_check:
            full_path = os.path.join(base_dir, dir_path)
            if os.path.exists(full_path) and os.path.isdir(full_path):
                print(f"✅ {dir_path} exists")
            else:
                print(f"❌ {dir_path} MISSING")
                
        # Check important files exist
        files_to_check = [
            "llm_tester/__init__.py",
            "llm_tester/llm_tester.py",
            "llm_tester/cli.py",
            "llm_tester/models/job_ads/model.py",
            "llm_tester/utils/provider_manager.py",
            "llm_tester/utils/prompt_optimizer.py",
            "llm_tester/utils/report_generator.py",
            "tests/test_llm_tester.py",
            "tests/test_cli.py",
            "setup.py",
            "requirements.txt"
        ]
        
        for file_path in files_to_check:
            full_path = os.path.join(base_dir, file_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} MISSING")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running simple tests...")
    test_file_reading()
    test_module_structure()