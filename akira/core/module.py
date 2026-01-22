"""Base module class for attack modules"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from akira.core.target import Target


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackCategory(str, Enum):
    DOS = "dos"
    INJECTION = "injection"
    JAILBREAK = "jailbreak"
    EXTRACTION = "extraction"
    EVASION = "evasion"
    POISONING = "poisoning"
    MULTITURN = "multiturn"
    TOOL_ABUSE = "tool_abuse"
    RAG_POISON = "rag_poison"
    AGENT_HIJACK = "agent_hijack"


@dataclass
class ModuleOption:
    name: str
    description: str
    required: bool = False
    default: Any = None
    value: Any = None

    def get_value(self) -> Any:
        return self.value if self.value is not None else self.default


@dataclass
class ModuleInfo:
    name: str
    description: str
    author: str
    category: AttackCategory
    severity: Severity
    references: list[str] = field(default_factory=list)
    cve: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class AttackResult:
    success: bool
    confidence: float
    payload_used: str
    response: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def is_vulnerable(self) -> bool:
        return self.success and self.confidence >= 0.7


class Module(ABC):
    def __init__(self) -> None:
        self._options: dict[str, ModuleOption] = {}
        self._target: Target | None = None
        self._setup_options()

    @property
    @abstractmethod
    def info(self) -> ModuleInfo:
        ...

    @abstractmethod
    def _setup_options(self) -> None:
        ...

    @abstractmethod
    async def check(self, target: Target) -> bool:
        """Non-destructive vulnerability probe"""
        ...

    @abstractmethod
    async def run(self, target: Target) -> AttackResult:
        ...

    def add_option(
        self,
        name: str,
        description: str,
        required: bool = False,
        default: Any = None,
    ) -> None:
        self._options[name] = ModuleOption(
            name=name,
            description=description,
            required=required,
            default=default,
        )

    def set_option(self, name: str, value: Any) -> None:
        if name not in self._options:
            raise ValueError(f"Unknown option: {name}")
        self._options[name].value = value

    def get_option(self, name: str) -> Any:
        if name not in self._options:
            raise ValueError(f"Unknown option: {name}")
        return self._options[name].get_value()

    @property
    def options(self) -> dict[str, ModuleOption]:
        return self._options

    def validate_options(self) -> list[str]:
        errors = []
        for name, opt in self._options.items():
            if opt.required and opt.get_value() is None:
                errors.append(f"Required option '{name}' is not set")
        return errors

    @property
    def target(self) -> Target | None:
        return self._target

    @target.setter
    def target(self, value: Target) -> None:
        self._target = value
