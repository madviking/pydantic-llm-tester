# Plan: File Upload Support for LLM Providers

This document outlines the architecture and step-by-step tasks required to add file upload support to the pydantic-llm-tester provider system, following a TDD-first approach. Each task is designed to be reviewed and approved before implementation.

---

## **Overview**

Goal:  
Enable LLM providers (and the provider abstraction) to support file uploads, so that users can pass files (e.g., PDFs, text, images) to LLM APIs that support this feature. The design must be provider-agnostic, extensible, and backward-compatible.

---

## **Task Breakdown**

### **1. Write Tests First (TDD)**

- Design and implement tests for the provider interface and file upload integration.
    - Test provider usage with and without file uploads.
    - Test correct behavior for providers that do/do not support file uploads.
    - Test error handling for unsupported file uploads.
    - Test backward compatibility (prompt-only usage).
- Add or update tests for the provider factory and registry to ensure file upload capability is correctly exposed.

---

### **2. Design Provider Interface Changes**

- Extend `BaseLLM` and all provider interfaces to accept an optional `files` parameter in `get_response` and `_call_llm_api`.
- Document the expected type and semantics of `files` (e.g., list of file paths, file-like objects, or provider-specific descriptors).
- Ensure the default implementation in `BaseLLM` raises a clear error if files are provided but not supported.

---

### **3. Update Provider Implementations**

- For each provider (OpenAI, Anthropic, Google, etc.):
    - Update the provider class to accept and process the `files` parameter if the underlying API supports file uploads.
    - If not supported, raise `NotImplementedError` or ignore the parameter.
    - Add a `supports_file_upload` property or config flag for introspection.

---

### **4. Update Provider Factory and Registry**

- Ensure the provider factory and registry can instantiate providers with file upload support and expose the `supports_file_upload` capability.

---

### **5. Update CLI and API Usage (Optional)**

- If relevant, update CLI commands and Python API examples to demonstrate file upload usage.
- Add documentation and usage examples for file uploads.

---

### **6. Testing and Validation**

- Run all new and existing tests to ensure correctness and backward compatibility.
- Add integration tests for end-to-end provider usage with file uploads.

---

### **7. Documentation**

- Update developer and user documentation to:
    - List which providers support file uploads.
    - Show how to use the new `files` parameter in both CLI and API.
    - Document limitations and error handling.

---

## **Task List (Checklist)**

**Status as of 2025-05-10:**
The initial phase focusing on interface changes, basic image file processing for key providers (OpenAI, Anthropic, Google), and schema injection for better JSON conformance is largely complete.

- [x] 1. Write tests for provider and file upload integration (TDD-first).
    - Basic tests for `MockProvider` handling `files` parameter and `supports_file_upload` flag are implemented.
    - Tests for `BaseLLM` behavior with `model_class` and `files` parameters in `get_response` are covered by updates to existing provider tests.
    - *Further integration tests for actual file content processing by providers are pending full implementation in each provider.*
- [x] 2. Design and document provider interface changes for file upload.
    - `BaseLLM`, `ProviderManager`, `LLMTester` and all provider interfaces now accept an optional `files: List[str]` parameter.
    - `BaseLLM`, `ProviderManager`, `LLMTester` and all provider interfaces now accept `model_class: Type[BaseModel]` for schema guidance.
    - `BaseLLM` raises `NotImplementedError` if files are provided to a provider that has `supports_file_upload=False`.
- [x] 3. Update all provider implementations for file upload support.
    - All provider `_call_llm_api` methods updated to accept `files` and `model_class`.
    - OpenAI, Anthropic, and Google providers now include logic to process common image types (JPEG, PNG, GIF, WEBP) from file paths, encode them, and include them in API requests. PDF and other file types are not yet supported.
    - OpenAI, Anthropic, Google, Mistral, OpenRouter providers now inject the Pydantic model's JSON schema into the system prompt to improve structured JSON output. (PydanticAI provider relies on its library's internal schema handling).
    - *TODOs remain in provider code for more advanced file handling (e.g., non-image files, error handling for large files, specific model capabilities).*
- [x] 4. Add `supports_file_upload` capability to provider config/classes.
    - `ProviderConfig` in `base.py` includes `supports_file_upload: bool`.
    - All provider `config.json` files updated with this flag.
    - `BaseLLM` instances now have a `self.supports_file_upload` attribute.
- [ ] 5. Update provider factory/registry for file upload awareness.
    - No direct changes made as `ProviderFactory` loads `ProviderConfig` which now includes `supports_file_upload`. Provider instances will have the attribute. Further exposure via registry methods can be a future enhancement if needed.
- [x] 6. Update CLI/API usage and documentation (if needed).
    - `LLMTester` and `ProviderManager` Python APIs updated to handle `files` and `model_class` parameters.
    - CLI test name filtering (`-f` / `--filter` option) is now implemented and functional.
    - *CLI (`llm-tester run`) has not yet been updated with a `--files` option (for passing file arguments directly in the run command).*
- [x] 7. Add integration and validation tests.
    - One integration test case using an image file (`job_ad_pic.png`) has been added to the `job_ads` py_model.
    - *More comprehensive integration tests covering various file types and providers are needed as full file processing logic is implemented.*
- [ ] 9. Update scaffolding templates.
    - *Make sure templates have the file handling.*
- [ ] 8. Update user/developer documentation.
    - *This is part of the current handover task.*
    

---

**Next Steps (Beyond Current Scope):**
- Implement full, robust file processing (various types like PDF, other document formats) in each provider's `_call_llm_api` where `supports_file_upload` is true.
- Add capability to specify supported file MIME types per LLM model in `ModelConfig`.
- Enhance CLI to accept file arguments for tests.
- Write comprehensive documentation for using file uploads (guide, API docs).
- Add more detailed integration tests for various file types and error conditions.

---

**Please review and approve or suggest changes to this plan before any code changes are made.**
