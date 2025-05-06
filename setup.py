from setuptools import setup, find_packages

from pathlib import Path

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pydantic-llm-tester", # Corrected package name for PyPI
    version="0.1.0",
    description="A framework for testing LLM performance using pydanticAI",
    long_description=long_description,
    long_description_content_type="text/markdown", # Specify content type as Markdown
    author="",
    author_email="",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "anthropic>=0.5.0",
        "mistralai>=0.0.1",
        "google-cloud-aiplatform>=1.36.0",
        "vertexai>=0.0.1",
        "python-dotenv>=1.0.0",
        "typer[all]>=0.9.0", # Added Typer dependency
        "pydantic-ai>=0.0.44", # Added pydantic-ai dependency
        "rapidfuzz>=3.0.0",
        "requests>=2.20.0",
        "google-generativeai>=0.8.5",
    ],
    entry_points={
        "console_scripts": [
            "llm-tester=src.cli.main:app", # Point to the app object in cli/main.py
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
