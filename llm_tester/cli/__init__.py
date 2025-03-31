# Init file for the cli package

# Import the main Typer app object to make it accessible at the package level
# This helps with entry point resolution in setup.py
from .main import app

__all__ = ["app"]
