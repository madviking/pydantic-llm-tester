# Using Files with Pydantic LLM Tester

This guide explains how to use file upload capabilities within the Pydantic LLM Tester framework, allowing you to test LLM responses to multimodal inputs that include files like images.

## Overview

The framework has been enhanced to support passing file paths along with traditional text-based prompts and sources to LLM providers. This is particularly useful for:

-   Testing vision-capable models with image inputs.
-   Evaluating how LLMs extract information from content within files.
-   (Future) Testing LLMs with other file types like PDFs or audio.

## Core Concepts

### 1. `files` Parameter

The primary way files are introduced is through an optional `files` parameter in the provider's `get_response` method (and subsequently in `_call_llm_api`). This parameter expects a list of strings, where each string is a path to a file.

```python
# Example of how it's used internally (simplified)
response_text, usage_data = provider.get_response(
    prompt="Describe the content of the image.",
    source="Image context if any.", # Can be minimal if image is primary
    model_class=MyPydanticModel,
    files=["/path/to/your/image.png"] 
)
```

### 2. `supports_file_upload` Configuration

Each LLM provider has a configuration flag `supports_file_upload` (boolean) in its `config.json` file (located in `src/pydantic_llm_tester/llms/<provider_name>/config.json`).

-   If `true`, the provider is expected to have logic to handle the `files` parameter.
-   If `false` (or omitted, as it defaults to false), and files are passed to this provider via a test case, the `BaseLLM` class will raise a `NotImplementedError` before attempting to call the provider's API.

### 3. `model_class` for Schema Guidance

To ensure that LLMs (especially when processing images or complex inputs) attempt to return structured JSON, the Pydantic model class (e.g., `JobAd`) defining the desired output schema is now passed through the call chain to the provider's `_call_llm_api` method.

For most providers (OpenAI, Anthropic, Google, Mistral, OpenRouter), the system prompt is automatically enhanced with the JSON schema derived from this `model_class`. This significantly improves the reliability of getting schema-compliant JSON responses.

## Defining Test Cases with Files

When creating test cases within your `py_model` modules (e.g., in `src/pydantic_llm_tester/py_models/your_module/model.py`), you can include a `file_paths` key in the dictionaries returned by the `get_test_cases()` method.

-   `file_paths`: A list of strings, where each string is the path to a file to be included in the test. Paths should typically be relative to the `sources` directory of your `py_model`'s test data, or absolute paths.

**Example `get_test_cases()` in `your_module/model.py`:**

```python
import os
from typing import List, Dict, Any, Type
from pydantic import BaseModel

class YourPydanticModel(BaseModel):
    description: str
    # ... other fields

class TestSchema(BaseModel): # Assuming this is your main model for this py_model
    # ... fields ...
    image_analysis: Optional[str] = None # Example field for image content

    MODULE_NAME: ClassVar[str] = "your_module"
    TEST_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "tests")
    # ... other class vars and methods ...

    @classmethod
    def get_test_cases(cls: Type['TestSchema']) -> List[Dict[str, Any]]:
        test_cases = []
        sources_dir = os.path.join(cls.TEST_DIR, "sources")
        prompts_dir = os.path.join(cls.TEST_DIR, "prompts")
        expected_dir = os.path.join(cls.TEST_DIR, "expected")

        # Example of a text-only test case
        test_cases.append({
            'name': 'text_only_example',
            'model_class': cls,
            'source_path': os.path.join(sources_dir, 'some_text_source.txt'),
            'prompt_path': os.path.join(prompts_dir, 'some_text_prompt.txt'),
            'expected_path': os.path.join(expected_dir, 'some_text_expected.json'),
        })

        # Example of an image-based test case
        image_file_name = "example_image.png"
        image_file_full_path = os.path.join(sources_dir, image_file_name)
        
        if os.path.exists(image_file_full_path):
            test_cases.append({
                'name': 'image_example',
                'model_class': cls,
                'source_path': os.path.join(sources_dir, 'image_example_source.txt'), # Dummy or context text
                'prompt_path': os.path.join(prompts_dir, 'image_example_prompt.txt'), # Prompt for image analysis
                'expected_path': os.path.join(expected_dir, 'image_example_expected.json'),
                'file_paths': [image_file_full_path] # Path to the image
            })
        
        return test_cases
```

## Current Capabilities & Limitations

### Supported File Types (Initial Implementation)

-   **Images**: Common image formats (JPEG, PNG, GIF, WEBP) are currently supported for processing by:
    -   `OpenAIProvider`
    -   `AnthropicProvider`
    -   `GoogleProvider`
    These providers will attempt to read the image, encode it (usually to base64), and include it in the API request in their respective required formats.

-   **PDFs and Other Documents**: Direct processing of PDFs or other document types (e.g., DOCX, TXT as file inputs rather than source text) is **not yet implemented** in the provider-specific logic.
    -   If a path to a non-image file is provided to OpenAI, Anthropic, or Google providers, it will currently be skipped with a warning.
    -   Providers configured with `supports_file_upload: false` (e.g., Mistral, OpenRouter, PydanticAI) do not attempt any file processing.

### Provider-Specific Notes

-   **OpenAI**: Uses multipart message content, including text and base64-encoded image data URIs.
-   **Anthropic**: Uses a list of content blocks, including text blocks and image blocks with base64-encoded data.
-   **Google (Gemini)**: Uses a list of `Part` objects, where image data (raw bytes) is passed along with the text prompt.

### Important Considerations

-   **Model Capabilities**: Ensure the specific LLM model you are testing (e.g., `openai:gpt-4o`, `anthropic:claude-3-opus-20240229`, `google:gemini-1.5-pro`) actually supports vision/multimodal input. Using a non-vision model with image files will likely result in errors or the image being ignored.
-   **Prompting for Images**: When working with images, your prompt text (from `prompt_path`) should clearly instruct the LLM on how to use the image content (e.g., "Describe the objects in the provided image," "Extract text from the attached document image," "What is depicted in this picture?").
-   **Schema Adherence**: While schema injection helps, complex images or unclear prompts might still lead to LLM responses that don't perfectly match your Pydantic schema. Iterative prompt engineering is often necessary.

## Future Enhancements

-   Support for more file types (PDFs, plain text files as direct inputs).
-   More granular configuration for supported MIME types per LLM model (`ModelConfig`).
-   CLI options to pass files directly via the `llm-tester run` command.

This guide provides a starting point for using file inputs. As the framework evolves, these capabilities will be expanded.
