# Changelog

All notable changes to the LLM Tester project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Created a centralized configuration manager in `utils/config_manager.py`
- Added comprehensive test cases for configuration management
- Created a standardized mock response system with template-based responses
- Added dynamic content customization for mock responses
- Created a detailed development guide in `docs/DEVELOPMENT.md`

### Changed
- Refactored duplicate test running logic in `LLMTester` class
- Improved prompt optimization directory handling
- Enhanced mock response selection based on source text content
- Updated README with new features

### Fixed
- Fixed optimized prompts directory creation issue
- Added proper error handling for file operations
- Improved logging throughout the codebase

## [0.1.0] - 2024-03-25

### Added
- Initial release of LLM Tester
- Support for multiple LLM providers (OpenAI, Anthropic, Mistral, Google)
- Support for job advertisement and product description models
- Prompt optimization capabilities
- Test report generation
- Interactive CLI tool