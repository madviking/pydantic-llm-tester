"""Non-interactive runner functions"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

from llm_tester import LLMTester
from .config import load_config, save_config

def run_with_defaults(
    providers: Optional[List[str]] = None, 
    models: Optional[Dict[str, str]] = None, 
    modules: Optional[List[str]] = None, 
    optimize: bool = False, 
    output_dir: Optional[str] = None
) -> int:
    """Run tests with default settings without interactive prompts"""
    logger = logging.getLogger(__name__)
    logger.info("Running with default settings (non-interactive mode)")
    
    # Load configuration
    config = load_config()
    
    # Get providers if not specified
    if providers is None:
        providers = [p for p, conf in config.get("providers", {}).items() 
                    if conf.get("enabled", False)]
        
        if not providers:
            logger.warning("No providers enabled in config, defaulting to mock_provider")
            providers = ["mock_provider"]
            
    # Initialize tester
    tester = LLMTester(providers=providers)
    
    # Get models if not specified
    if models is None:
        models = {}
        for provider in providers:
            provider_config = config.get("providers", {}).get(provider, {})
            if "default_model" in provider_config:
                models[provider] = provider_config["default_model"]
    
    # Get output directory if not specified
    if output_dir is None:
        test_settings = config.get("test_settings", {})
        output_dir = test_settings.get("output_dir", "test_results")
    
    # Create timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}{'_optimized' if optimize else ''}.md"
    
    # Run tests
    logger.info(f"Starting test run with {'optimized' if optimize else 'standard'} prompts")
    logger.info(f"Providers: {', '.join(providers)}")
    
    for provider, model in models.items():
        logger.info(f"Using model for {provider}: {model}")
    
    if modules:
        logger.info(f"Testing modules: {', '.join(modules)}")
    else:
        logger.info("Testing all available modules")
    
    # Prepare progress callback
    def progress_callback(message):
        logger.info(message)
    
    # Run tests
    if optimize:
        # Get save_optimized_prompts setting from config
        test_settings = config.get("test_settings", {})
        save_optimized_prompts = test_settings.get("save_optimized_prompts", True)
        
        results = tester.run_optimized_tests(
            model_overrides=models,
            save_optimized_prompts=save_optimized_prompts,
            modules=modules,
            progress_callback=progress_callback
        )
    else:
        results = tester.run_tests(
            model_overrides=models, 
            modules=modules,
            progress_callback=progress_callback
        )
    
    # Generate report
    logger.info("Generating report...")
    report_dict = tester.generate_report(results, optimized=optimize)
    
    # Extract main report
    if isinstance(report_dict, dict):
        report = report_dict.get('main', '')
    else:
        # If generate_report returned a string directly, use that
        report = report_dict
    
    # Save report
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, filename)
    
    with open(report_path, "w") as f:
        f.write(report)
    
    logger.info(f"Report saved to {report_path}")
    
    # Save cost report
    cost_report_path = tester.save_cost_report(output_dir)
    if cost_report_path:
        logger.info(f"Cost report saved to {cost_report_path}")
    
    # Print summary
    logger.info("Test Summary:")
    for test_name, test_results in results.items():
        logger.info(f"  {test_name}:")
        for provider, provider_result in test_results.items():
            if isinstance(provider_result, dict) and 'validation' in provider_result:
                validation = provider_result.get('validation', {})
                accuracy = validation.get('accuracy', 0.0) if validation.get('success', False) else 0.0
                model = provider_result.get('model', 'default')
                logger.info(f"    {provider} ({model}): {accuracy:.2f}%")
            else:
                logger.info(f"    {provider}: Results available in full report")
    
    return 0
