# Packaging and Distribution

Build is configured in pyproject.toml. To build the package, run:

```bash
python -m build
```

Commit, and tag. GitHub Actions will automatically build and publish the package to PyPI.

### Run locally (replace the correct version, duh)
```bash
pip install build
python -m build
pip install dist/pydantic_llm_tester-0.1.15-py3-none-any.whl
```

### Install for local development (uses local files)
```bash
python -m build
pip install -e .
```
