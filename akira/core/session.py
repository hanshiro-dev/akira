"""Session management for Akira"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from akira.core.module import AttackResult, Module
from akira.core.target import Target
from akira.core.storage import get_storage


@dataclass
class AttackLog:
    timestamp: datetime
    module_name: str
    target_repr: str
    result: AttackResult
    options: dict[str, Any]
    db_id: int | None = None


class Session:
    def __init__(self, persist_history: bool = True) -> None:
        self._current_module: Module | None = None
        self._current_target: Target | None = None
        self._attack_history: list[AttackLog] = []
        self._persist_history = persist_history
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
        target = self._current_target
        target_type = target.target_type.value if target else "unknown"
        target_url = getattr(target, "url", "") or getattr(target, "endpoint", "") or "unknown"

        db_id = None
        if self._persist_history:
            db_id = get_storage().save_history(
                module=f"{module.info.category.value}/{module.info.name}",
                target_type=target_type,
                target_url=str(target_url),
                success=result.success,
                confidence=result.confidence,
                payload=result.payload_used or "",
                response=result.response or "",
                details=result.details,
            )

        self._attack_history.append(
            AttackLog(
                timestamp=datetime.now(),
                module_name=module.info.name,
                target_repr=repr(target) if target else "unknown",
                result=result,
                options={k: v.get_value() for k, v in module.options.items()},
                db_id=db_id,
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
        successful = sum(1 for log in self._attack_history if log.result.success)
        return {
            "started_at": self._started_at.isoformat(),
            "total_attacks": len(self._attack_history),
            "successful_attacks": successful,
            "failed_attacks": len(self._attack_history) - successful,
        }
