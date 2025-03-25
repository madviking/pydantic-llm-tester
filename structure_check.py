#!/usr/bin/env python3
"""
Simple structure check for the LLM Tester project
Doesn't require pydantic or any other dependencies
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(path):
    """Check if a file exists and print status"""
    if os.path.exists(path):
        print(f"✅ {path} exists")
        return True
    else:
        print(f"❌ {path} does not exist")
        return False

def check_critical_files():
    """Check if critical files exist"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of critical files and directories
    critical_paths = [
        # Core files
        "llm_tester/__init__.py",
        "llm_tester/llm_tester.py",
        "llm_tester/cli.py",
        
        # Models
        "llm_tester/models/__init__.py",
        "llm_tester/models/job_ads/__init__.py",
        "llm_tester/models/job_ads/model.py",
        
        # Utils
        "llm_tester/utils/__init__.py",
        "llm_tester/utils/provider_manager.py",
        "llm_tester/utils/prompt_optimizer.py",
        "llm_tester/utils/report_generator.py",
        
        # Tests
        "llm_tester/tests/cases/job_ads/sources/simple.txt",
        "llm_tester/tests/cases/job_ads/sources/complex.txt",
        "llm_tester/tests/cases/job_ads/prompts/simple.txt",
        "llm_tester/tests/cases/job_ads/prompts/complex.txt",
        "llm_tester/tests/cases/job_ads/expected/simple.json",
        "llm_tester/tests/cases/job_ads/expected/complex.json",
        
        # Configuration
        "llm_tester/.env.example",
        "requirements.txt",
        "setup.py",
        "LICENSE",
        "README.md",
    ]
    
    all_exists = True
    for path in critical_paths:
        full_path = os.path.join(base_dir, path)
        if not check_file_exists(full_path):
            all_exists = False
    
    return all_exists

def check_json_files():
    """Check if JSON files are valid"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    json_paths = [
        "llm_tester/tests/cases/job_ads/expected/simple.json",
        "llm_tester/tests/cases/job_ads/expected/complex.json",
    ]
    
    all_valid = True
    for path in json_paths:
        full_path = os.path.join(base_dir, path)
        
        try:
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    data = json.load(f)
                print(f"✅ {path} is valid JSON with {len(data)} keys")
            else:
                print(f"❌ {path} does not exist")
                all_valid = False
        except json.JSONDecodeError as e:
            print(f"❌ {path} contains invalid JSON: {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ Error reading {path}: {e}")
            all_valid = False
    
    return all_valid

def count_files_by_type():
    """Count files by extension"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    extensions = {'.py': 0, '.json': 0, '.txt': 0, '.md': 0}
    
    for root, dirs, files in os.walk(base_dir):
        # Skip git directory
        if '.git' in dirs:
            dirs.remove('.git')
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions:
                extensions[ext] += 1
    
    print("\nFile count by type:")
    for ext, count in extensions.items():
        print(f"  {ext}: {count} files")
    
    total = sum(extensions.values())
    print(f"  Total: {total} files")

def main():
    """Main function"""
    print("LLM Tester Project Structure Check")
    print("=================================")
    
    print("\nChecking for critical files...")
    critical_files_exist = check_critical_files()
    
    print("\nValidating JSON files...")
    json_valid = check_json_files()
    
    count_files_by_type()
    
    print("\nSummary:")
    if critical_files_exist and json_valid:
        print("✅ All checks passed! The project structure looks good.")
    else:
        if not critical_files_exist:
            print("❌ Some critical files are missing.")
        if not json_valid:
            print("❌ Some JSON files are invalid.")

if __name__ == "__main__":
    main()