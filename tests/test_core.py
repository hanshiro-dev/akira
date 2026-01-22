"""Tests for core module functionality"""

import pytest

from akira.core.module import Module, ModuleInfo, AttackCategory, Severity, AttackResult
from akira.core.target import Target, TargetConfig, TargetType
from akira.core.registry import ModuleRegistry


class MockTarget(Target):
    """Mock target for testing"""

    def __init__(self, responses: list[str] | None = None) -> None:
        super().__init__(TargetConfig())
        self._responses = responses or ["Mock response"]
        self._call_count = 0

    @property
    def target_type(self) -> TargetType:
        return TargetType.API_ENDPOINT

    async def validate(self) -> bool:
        self._validated = True
        return True

    async def send(self, payload: str) -> str:
        response = self._responses[self._call_count % len(self._responses)]
        self._call_count += 1
        return response

    async def send_batch(self, payloads: list[str]) -> list[str]:
        return [await self.send(p) for p in payloads]


class MockModule(Module):
    """Mock module for testing"""

    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="mock_module",
            description="A mock module for testing",
            author="Test",
            category=AttackCategory.INJECTION,
            severity=Severity.LOW,
        )

    def _setup_options(self) -> None:
        self.add_option("test_option", "A test option", default="default_value")

    async def check(self, target: Target) -> bool:
        return True

    async def run(self, target: Target) -> AttackResult:
        response = await target.send("test payload")
        return AttackResult(
            success=True,
            confidence=0.9,
            payload_used="test payload",
            response=response,
        )


class TestModule:
    def test_module_info(self) -> None:
        module = MockModule()
        assert module.info.name == "mock_module"
        assert module.info.category == AttackCategory.INJECTION

    def test_module_options(self) -> None:
        module = MockModule()
        assert module.get_option("test_option") == "default_value"

        module.set_option("test_option", "new_value")
        assert module.get_option("test_option") == "new_value"

    def test_module_validation(self) -> None:
        module = MockModule()
        module.add_option("required_opt", "Required", required=True)

        errors = module.validate_options()
        assert len(errors) == 1
        assert "required_opt" in errors[0]


class TestRegistry:
    def test_register_and_get(self) -> None:
        registry = ModuleRegistry()
        registry.register(MockModule)

        assert "injection/mock_module" in registry.list_all()
        assert registry.get("injection/mock_module") is MockModule

    def test_search(self) -> None:
        registry = ModuleRegistry()
        registry.register(MockModule)

        results = registry.search("mock")
        assert "injection/mock_module" in results

        results = registry.search("testing")
        assert "injection/mock_module" in results


@pytest.mark.asyncio
async def test_module_run() -> None:
    module = MockModule()
    target = MockTarget(responses=["Vulnerable response"])

    result = await module.run(target)

    assert result.success is True
    assert result.confidence == 0.9
    assert result.response == "Vulnerable response"
