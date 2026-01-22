# Contributing

Guidelines for contributing to Akira.

## Getting Started

### Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/akira.git
cd akira
```

### Development Setup

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

## Code Style

### Python

- Use type hints for all functions
- Follow existing code patterns
- Minimal comments - code should be self-documenting
- No obvious comments explaining what code does

```python
# Good
def calculate_confidence(matches: int, total: int) -> float:
    return matches / total if total > 0 else 0.0

# Bad
def calculate_confidence(matches: int, total: int) -> float:
    # Calculate the confidence by dividing matches by total
    # If total is zero, return 0.0 to avoid division by zero
    if total > 0:
        return matches / total
    else:
        return 0.0
```

### Linting

```bash
ruff check akira/
mypy akira/
```

### Formatting

```bash
ruff format akira/
```

## Pull Request Process

### 1. Create Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

### 2. Make Changes

- Write code
- Add tests
- Update docs if needed

### 3. Test

```bash
pytest tests/
ruff check akira/
mypy akira/
```

### 4. Commit

```bash
git add .
git commit -m "Add feature X"
```

### 5. Push and PR

```bash
git push origin feature/my-feature
```

Then open a Pull Request on GitHub.

## Adding Attack Modules

1. Create module in `akira/modules/<category>/`
2. Follow the [Writing Modules](./writing-modules.md) guide
3. Add tests in `tests/`
4. Document in `docs/src/modules/`

### Module Checklist

- [ ] Implements `info` property with complete metadata
- [ ] Implements `check()` for quick probe
- [ ] Implements `run()` for full attack
- [ ] Has configurable options where appropriate
- [ ] Handles errors gracefully
- [ ] Returns meaningful confidence scores
- [ ] Includes references to research/CVEs
- [ ] Has appropriate tags for searchability
- [ ] Unit tests pass

## Adding Targets

1. Create target in `akira/targets/`
2. Follow the [Writing Targets](./writing-targets.md) guide
3. Register in `factory.py`
4. Add documentation

### Target Checklist

- [ ] Implements required interface methods
- [ ] Handles authentication properly
- [ ] Has informative error messages
- [ ] Supports async operations
- [ ] Unit tests pass

## Documentation

Documentation uses mdbook. To preview:

```bash
cd docs
mdbook serve
```

### Adding Pages

1. Create `.md` file in `docs/src/`
2. Add to `SUMMARY.md`

## Reporting Issues

### Bug Reports

Include:
- Akira version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/tracebacks

### Feature Requests

Describe:
- Use case
- Proposed solution
- Alternatives considered

## Security Issues

For security vulnerabilities, please email security@example.com instead of opening a public issue.

## Code of Conduct

- Be respectful
- Provide constructive feedback
- Help others learn
- Focus on the code, not the person
