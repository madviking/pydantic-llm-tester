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

- [ ] 1. Write tests for provider and file upload integration (TDD-first).
- [ ] 2. Design and document provider interface changes for file upload.
- [ ] 3. Update all provider implementations for file upload support.
- [ ] 4. Add `supports_file_upload` capability to provider config/classes.
- [ ] 5. Update provider factory/registry for file upload awareness.
- [ ] 6. Update CLI/API usage and documentation (if needed).
- [ ] 7. Add integration and validation tests.
- [ ] 8. Update user/developer documentation.

---

**Please review and approve or suggest changes to this plan before any code changes are made.**
