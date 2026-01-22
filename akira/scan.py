"""High-level scanning API for programmatic use"""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field

from akira.core.module import AttackCategory, AttackResult
from akira.core.registry import registry
from akira.core.target import Target


@dataclass
class ScanResult:
    target: str
    total: int
    vulnerable: int
    results: dict[str, AttackResult] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        return self.vulnerable / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "total": self.total,
            "vulnerable": self.vulnerable,
            "success_rate": self.success_rate,
            "results": {
                name: {
                    "success": r.success,
                    "confidence": r.confidence,
                    "payload": r.payload_used,
                    "response": r.response[:500] if r.response else "",
                    "error": r.error,
                    "details": r.details,
                }
                for name, r in self.results.items()
            },
        }


async def scan(
    target: Target,
    attacks: Sequence[str] | None = None,
    category: str | None = None,
    exclude: Sequence[str] | None = None,
    stop_on_first: bool = False,
) -> ScanResult:
    """
    Run attacks against a target.

    Args:
        target: Target instance to scan
        attacks: Specific attack names to run (None = all)
        category: Filter by category (dos, injection, etc.)
        exclude: Attack names to skip
        stop_on_first: Stop after first successful attack

    Returns:
        ScanResult with all findings

    Example:
        from akira import scan
        from akira.targets import create_target

        target = create_target("anthropic", api_key="...", model="claude-sonnet-4-20250514")
        result = await scan(target, category="dos")
        print(f"Found {result.vulnerable} vulnerabilities")
    """
    registry.load_builtin_attacks()
    exclude = set(exclude or [])

    # Determine which attacks to run
    if attacks:
        attack_names = [a for a in attacks if a not in exclude]
    elif category:
        try:
            cat = AttackCategory(category)
            attack_names = [a for a in registry.list_by_category(cat) if a not in exclude]
        except ValueError:
            attack_names = []
    else:
        attack_names = [a for a in registry.list_all() if a not in exclude]

    # Validate target
    if not target.is_validated:
        await target.validate()

    results: dict[str, AttackResult] = {}
    vulnerable_count = 0

    for name in attack_names:
        module_cls = registry.get(name)
        if not module_cls:
            continue

        module = module_cls()
        try:
            result = await module.run(target)
            results[name] = result
            if result.success:
                vulnerable_count += 1
                if stop_on_first:
                    break
        except Exception as e:
            results[name] = AttackResult(
                success=False,
                confidence=0.0,
                payload_used="",
                response="",
                error=str(e),
            )

    return ScanResult(
        target=str(target),
        total=len(results),
        vulnerable=vulnerable_count,
        results=results,
    )


def scan_sync(
    target: Target,
    attacks: Sequence[str] | None = None,
    category: str | None = None,
    exclude: Sequence[str] | None = None,
    stop_on_first: bool = False,
) -> ScanResult:
    """Synchronous wrapper for scan()"""
    return asyncio.run(scan(target, attacks, category, exclude, stop_on_first))
