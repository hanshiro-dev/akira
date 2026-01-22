"""Session management for Akira"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from akira.core.module import AttackResult, Module
from akira.core.target import Target


@dataclass
class AttackLog:
    """Log entry for an attack attempt"""
    timestamp: datetime
    module_name: str
    target_repr: str
    result: AttackResult
    options: dict[str, Any]


class Session:
    """Manages the current Akira session state"""

    def __init__(self) -> None:
        self._current_module: Module | None = None
        self._current_target: Target | None = None
        self._attack_history: list[AttackLog] = []
        self._global_options: dict[str, Any] = {
            "verbose": False,
            "timeout": 30,
            "max_retries": 3,
            "parallel_requests": 5,
        }
        self._started_at = datetime.now()

    @property
    def module(self) -> Module | None:
        return self._current_module

    @module.setter
    def module(self, value: Module) -> None:
        self._current_module = value

    @property
    def target(self) -> Target | None:
        return self._current_target

    @target.setter
    def target(self, value: Target) -> None:
        self._current_target = value
        if self._current_module:
            self._current_module.target = value

    def log_attack(self, module: Module, result: AttackResult) -> None:
        """Log an attack attempt"""
        self._attack_history.append(
            AttackLog(
                timestamp=datetime.now(),
                module_name=module.info.name,
                target_repr=repr(self._current_target) if self._current_target else "unknown",
                result=result,
                options={k: v.get_value() for k, v in module.options.items()},
            )
        )

    @property
    def history(self) -> list[AttackLog]:
        return self._attack_history

    def get_global(self, key: str) -> Any:
        return self._global_options.get(key)

    def set_global(self, key: str, value: Any) -> None:
        self._global_options[key] = value

    @property
    def stats(self) -> dict[str, Any]:
        """Get session statistics"""
        successful = sum(1 for log in self._attack_history if log.result.success)
        return {
            "started_at": self._started_at.isoformat(),
            "total_attacks": len(self._attack_history),
            "successful_attacks": successful,
            "failed_attacks": len(self._attack_history) - successful,
        }
