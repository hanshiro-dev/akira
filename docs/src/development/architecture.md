# Architecture

Overview of Akira's internal architecture.

## Directory Structure

```
akira/
├── akira/
│   ├── cli/              # Command-line interface
│   │   ├── console.py    # Interactive console
│   │   └── main.py       # CLI entry points
│   ├── core/             # Core framework
│   │   ├── module.py     # Base module classes
│   │   ├── target.py     # Base target class
│   │   ├── session.py    # Session management
│   │   ├── registry.py   # Module discovery
│   │   ├── storage.py    # SQLite persistence
│   │   └── fuzzy.py      # Fuzzy search
│   ├── modules/          # Attack modules
│   │   ├── dos/
│   │   ├── extraction/
│   │   ├── injection/
│   │   └── jailbreak/
│   ├── targets/          # Target implementations
│   │   ├── api.py
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── ...
│   └── repository/       # Attack repository management
├── rust/                 # Rust extensions
│   └── src/
│       ├── lib.rs
│       ├── fuzzer.rs
│       ├── matcher.rs
│       ├── analyzer.rs
│       └── fuzzy.rs
├── tests/
└── docs/
```

## Core Components

### Module System

```
┌─────────────────────────────────────────────────────────┐
│                      Registry                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ dos/magic   │  │ injection/  │  │ jailbreak/  │     │
│  │   _string   │  │   basic     │  │    dan      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                       Module                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────────┐       │
│  │   info    │  │  options  │  │ check() / run()│       │
│  └───────────┘  └───────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Target System

```
┌─────────────────────────────────────────────────────────┐
│                    Target (Base)                         │
│  ┌───────────────┐  ┌───────────────┐                   │
│  │  validate()   │  │    send()     │                   │
│  └───────────────┘  └───────────────┘                   │
└─────────────────────────────────────────────────────────┘
           │
           ├──────────────┬──────────────┬────────────────┐
           ▼              ▼              ▼                ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  OpenAI  │   │Anthropic │   │   API    │   │ Bedrock  │
    └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Session & Storage

```
┌─────────────────────────────────────────────────────────┐
│                       Session                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   module    │  │   target    │  │   history   │     │
│  └─────────────┘  └─────────────┘  └──────┬──────┘     │
└──────────────────────────────────────────│─────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Storage (SQLite)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   history   │  │  profiles   │  │    cache    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Attack Execution

```
User Input → Console → Session → Module → Target → LLM API
                                    │
                                    ▼
                              AttackResult
                                    │
                                    ▼
                    Session → Storage (persist)
                                    │
                                    ▼
                              Console (display)
```

### Module Discovery

```
registry.load_builtin_modules()
         │
         ▼
    Scan akira/modules/*/
         │
         ▼
    Import Python modules
         │
         ▼
    Find Module subclasses
         │
         ▼
    Register in _modules dict
```

## Key Classes

### Module

```python
class Module(ABC):
    @property
    @abstractmethod
    def info(self) -> ModuleInfo: ...

    @abstractmethod
    async def check(self, target: Target) -> bool: ...

    @abstractmethod
    async def run(self, target: Target) -> AttackResult: ...
```

### Target

```python
class Target(ABC):
    @property
    @abstractmethod
    def target_type(self) -> TargetType: ...

    @abstractmethod
    async def validate(self) -> bool: ...

    @abstractmethod
    async def send(self, payload: str) -> str: ...
```

### AttackResult

```python
@dataclass
class AttackResult:
    success: bool
    confidence: float
    payload_used: str
    response: str
    details: dict[str, Any]
    error: str | None = None
```

## Rust Extensions

Optional high-performance components:

| Module | Purpose |
|--------|---------|
| `fuzzer.rs` | Payload mutation |
| `matcher.rs` | Pattern matching (Aho-Corasick) |
| `analyzer.rs` | Parallel response analysis |
| `fuzzy.rs` | Fuzzy string matching |

Python fallbacks exist for all Rust functionality.
