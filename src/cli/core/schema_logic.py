import os
import logging
from typing import List

# Use absolute imports
from src.cli.core.common import get_llm_tester_dir

logger = logging.getLogger(__name__)

def get_discovered_schemas() -> List[str]:
    """
    Discovers available extraction schemas (test modules) based on directories
    in src/py_models/.
    """
    models_dir = os.path.join(get_llm_tester_dir(), 'py_models')
    discovered = []
    try:
        if not os.path.isdir(models_dir):
            logger.warning(f"Extraction schemas directory not found at: {models_dir}")
            return []
        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            # Check if it's a directory, not starting with '__', and contains 'model.py'
            if os.path.isdir(item_path) and not item.startswith('__'):
                if os.path.exists(os.path.join(item_path, 'model.py')):
                    discovered.append(item)
                else:
                     logger.debug(f"Directory '{item}' in '{models_dir}' lacks model.py, skipping.")

    except Exception as e:
        logger.error(f"Error discovering schemas in '{models_dir}': {e}", exc_info=True)
        return []

    return sorted(discovered)
