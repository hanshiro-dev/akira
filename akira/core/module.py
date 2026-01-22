"""Base module class for attack modules"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from akira.core.target import Target


class Severity(str, Enum):
    """Attack severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackCategory(str, Enum):
    """Categories of attacks"""
    DOS = "dos"
    INJECTION = "injection"
    JAILBREAK = "jailbreak"
    EXTRACTION = "extraction"
    EVASION = "evasion"
    POISONING = "poisoning"


@dataclass
class ModuleOption:
    """Configuration option for a module"""
    name: str
    description: str
    required: bool = False
    default: Any = None
    value: Any = None

    def get_value(self) -> Any:
        return self.value if self.value is not None else self.default


@dataclass
class ModuleInfo:
    """Metadata about an attack module"""
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
    """Result of an attack execution"""
    success: bool
    confidence: float  # 0.0 to 1.0
    payload_used: str
    response: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def is_vulnerable(self) -> bool:
        return self.success and self.confidence >= 0.7


class Module(ABC):
    """Base class for all attack modules"""

    def __init__(self) -> None:
        self._options: dict[str, ModuleOption] = {}
        self._target: Target | None = None
        self._setup_options()

    @property
    @abstractmethod
    def info(self) -> ModuleInfo:
        """Return module metadata"""
        ...

    @abstractmethod
    def _setup_options(self) -> None:
        """Define module options"""
        ...

    @abstractmethod
    async def check(self, target: Target) -> bool:
        """Check if target is potentially vulnerable (non-destructive)"""
        ...

    @abstractmethod
    async def run(self, target: Target) -> AttackResult:
        """Execute the attack against the target"""
        ...

    def add_option(
        self,
        name: str,
        description: str,
        required: bool = False,
        default: Any = None,
    ) -> None:
        """Add a configurable option to the module"""
        self._options[name] = ModuleOption(
            name=name,
            description=description,
            required=required,
            default=default,
        )

    def set_option(self, name: str, value: Any) -> None:
        """Set an option value"""
        if name not in self._options:
            raise ValueError(f"Unknown option: {name}")
        self._options[name].value = value

    def get_option(self, name: str) -> Any:
        """Get an option value"""
        if name not in self._options:
            raise ValueError(f"Unknown option: {name}")
        return self._options[name].get_value()

    @property
    def options(self) -> dict[str, ModuleOption]:
        """Get all options"""
        return self._options

    def validate_options(self) -> list[str]:
        """Validate all required options are set. Returns list of errors."""
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
