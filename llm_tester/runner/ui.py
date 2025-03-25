"""UI utilities for the interactive runner"""

import os
import logging
from typing import List, Tuple

# Configure logging
def setup_logging():
    """Set up and configure logging"""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Default level is INFO
    
    # Remove any existing handlers to avoid duplicates when rerunning
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Create console handler and set level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    
    return logger

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
