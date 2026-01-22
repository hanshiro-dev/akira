# Changelog

All notable changes to Akira.

## [Unreleased]

### Added
- Initial release of Akira LLM Security Testing Framework
- Interactive msfconsole-style console
- Attack modules:
  - `injection/basic_injection` - Prompt injection testing
  - `jailbreak/dan_jailbreak` - DAN-style jailbreak attacks
  - `extraction/system_prompt_leak` - System prompt extraction
  - `dos/magic_string` - Claude magic string DoS
- Target support:
  - OpenAI API
  - Anthropic Claude API
  - HuggingFace Inference API
  - AWS Bedrock
  - AWS SageMaker
  - Generic API (any LLM-powered endpoint)
- SQLite storage for:
  - Attack history persistence
  - Target profiles
  - Prompt cache
  - Response cache
- Fuzzy search for module discovery
- Rust extensions for performance (optional):
  - Payload fuzzing
  - Pattern matching
  - Response analysis
  - Fuzzy string matching
- CLI for non-interactive usage
- mdbook documentation

### Security
- All attack modules are for authorized testing only
- API keys stored locally in SQLite database
- No telemetry or data collection

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- MAJOR: Incompatible API changes
- MINOR: New functionality (backwards compatible)
- PATCH: Bug fixes (backwards compatible)

## Reporting Issues

Report bugs and feature requests at:
https://github.com/yourusername/akira/issues
