from setuptools import setup, find_packages

setup(
    name="llm_tester",
    version="0.1.0",
    description="A framework for testing LLM performance using pydanticAI",
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
    ],
    entry_points={
        "console_scripts": [
            "llm-tester=llm_tester.cli:app", # Point to the app object in the package __init__
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
