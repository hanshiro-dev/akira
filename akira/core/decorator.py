"""Decorator-based attack definition API"""

import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from akira.core.module import (
    AttackCategory,
    AttackResult,
    Module,
    ModuleInfo,
    Severity,
)
from akira.core.target import Target


@dataclass
class Option:
    """Declare an attack option via function parameter default"""
    description: str
    default: Any = None
    required: bool = False


def attack(
    name: str,
    description: str,
    category: str,
    severity: str = "medium",
    author: str = "anonymous",
    references: list[str] | None = None,
    tags: list[str] | None = None,
) -> Callable:
    """
    Decorator to define an attack module from a simple async function.

    Usage:
        @attack(
            name="my_attack",
            description="Does something bad",
            category="injection",
            severity="high",
            author="hacker",
        )
        async def my_attack(target, payload: Option("The payload", default="test") = None):
            resp = await target.send(payload)
            return resp.success

    The decorated function receives:
        - target: Target instance
        - **options: Any Option() parameters become configurable options

    Return value:
        - bool: True = vulnerable, False = not vulnerable
        - dict: {"vulnerable": bool, "confidence": float, ...} for detailed results
        - AttackResult: Full control over the result
    """
    def decorator(fn: Callable[..., Coroutine[Any, Any, Any]]) -> type[Module]:
        # Extract options from function signature (check both annotation and default)
        sig = inspect.signature(fn)
        hints = getattr(fn, '__annotations__', {})
        options: dict[str, Option] = {}

        for param_name, param in sig.parameters.items():
            if param_name == "target":
                continue
            # Check annotation first (location: Option(...) = None style)
            if param_name in hints and isinstance(hints[param_name], Option):
                options[param_name] = hints[param_name]
            # Then check default (location = Option(...) style)
            elif isinstance(param.default, Option):
                options[param_name] = param.default

        class DecoratedAttack(Module):
            @property
            def info(self) -> ModuleInfo:
                return ModuleInfo(
                    name=name,
                    description=description,
                    author=author,
                    category=AttackCategory(category),
                    severity=Severity(severity),
                    references=references or [],
                    tags=tags or [],
                )

            def _setup_options(self) -> None:
                for opt_name, opt in options.items():
                    self.add_option(opt_name, opt.description, opt.required, opt.default)

            async def check(self, target: Target) -> bool:
                # Quick check - just run with defaults and see if vulnerable
                try:
                    result = await self.run(target)
                    return result.success
                except Exception:
                    return False

            async def run(self, target: Target) -> AttackResult:
                # Build kwargs from options
                kwargs = {}
                for opt_name in options:
                    kwargs[opt_name] = self.get_option(opt_name)

                try:
                    result = await fn(target, **kwargs)
                except Exception as e:
                    return AttackResult(
                        success=False,
                        confidence=0.0,
                        payload_used="",
                        response="",
                        error=str(e),
                    )

                return _normalize_result(result)

        DecoratedAttack.__name__ = fn.__name__
        DecoratedAttack.__qualname__ = fn.__name__
        DecoratedAttack.__module__ = fn.__module__

        return DecoratedAttack

    return decorator


def _normalize_result(result: Any) -> AttackResult:
    """Convert various return types to AttackResult"""
    if isinstance(result, AttackResult):
        return result

    if isinstance(result, bool):
        return AttackResult(
            success=result,
            confidence=1.0 if result else 0.0,
            payload_used="",
            response="",
        )

    if isinstance(result, dict):
        return AttackResult(
            success=result.get("vulnerable", result.get("success", False)),
            confidence=result.get("confidence", 1.0 if result.get("vulnerable") else 0.0),
            payload_used=result.get("payload", ""),
            response=result.get("response", ""),
            details={k: v for k, v in result.items() if k not in (
                "vulnerable", "success", "confidence", "payload", "response", "error"
            )},
            error=result.get("error"),
        )

    # Fallback - truthy = vulnerable
    return AttackResult(
        success=bool(result),
        confidence=1.0 if result else 0.0,
        payload_used="",
        response=str(result) if result else "",
    )
