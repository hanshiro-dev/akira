<div align="center">
  <img src="docs/logo.png" alt="Akira Logo" width="800"/>
  
  **Verify your AI deployments against known attacks**
  
  [![Build Status](https://github.com/hanshiro-dev/hanshirodb/workflows/CI/badge.svg)](https://github.com/hanshiro-dev/hanshirodb/actions)
  [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
</div>


Akira is a CLI tool for testing LLM and AI Infrastructure Security. It provides an interactive console and attack modules for testing prompt injection, jailbreaks, data extraction, and denial-of-service vulnerabilities.

## Features

- **Interactive Console** - msfconsole-style interface with tab completion
- **Multiple Targets** - OpenAI, Anthropic, HuggingFace, AWS Bedrock/SageMaker, custom APIs
- **Attack Modules** - Prompt injection, jailbreaks, system prompt extraction, DoS
- **Attack Repository** - Pull attacks from remote git repositories
- **High Performance** - Rust-powered payload fuzzing and response analysis

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Build Rust extension (optional, for fuzzing features)
cd rust && maturin develop && cd ..

# Launch console
akira
```

## Console Usage

```
akira > use injection/basic_injection
akira(basic_injection) > target openai https://api.openai.com/v1/chat/completions --key $OPENAI_API_KEY
akira(basic_injection) > set canary INJECTION_TEST
akira(basic_injection) > run

[*] Executing basic_injection...
[+] VULNERABLE (confidence: 95%)
```

## Available Commands

| Command | Description |
|---------|-------------|
| `use <module>` | Select an attack module |
| `info` | Show module details |
| `show modules` | List all modules |
| `search <term>` | Search modules |
| `target <type> <endpoint>` | Set target |
| `set <option> <value>` | Configure module |
| `run` | Execute attack |
| `check` | Quick vulnerability probe |

## Target Types

- `openai` - OpenAI API
- `anthropic` - Anthropic Claude API
- `hf_inference` - HuggingFace Inference API
- `hf` - Local HuggingFace model
- `bedrock` - AWS Bedrock
- `sagemaker` - AWS SageMaker
- `api` - Generic REST endpoint


## License

MIT
