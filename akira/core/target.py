"""Target definitions for different attack surfaces"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TargetType(str, Enum):
    API_ENDPOINT = "api"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE_MODEL = "hf"
    HUGGINGFACE_INFERENCE = "hf_inference"
    AWS_BEDROCK = "bedrock"
    AWS_SAGEMAKER = "sagemaker"
    AZURE_OPENAI = "azure"
    LOCAL_MODEL = "local"


@dataclass
class TargetConfig:
    endpoint: str | None = None
    api_key: str | None = None
    model: str | None = None
    region: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class Target(ABC):
    def __init__(self, config: TargetConfig) -> None:
        self.config = config
        self._validated = False

    @property
    @abstractmethod
    def target_type(self) -> TargetType:
        ...

    @abstractmethod
    async def validate(self) -> bool:
        ...

    @abstractmethod
    async def send(self, payload: str) -> str:
        ...

    @abstractmethod
    async def send_batch(self, payloads: list[str]) -> list[str]:
        ...

    @property
    def is_validated(self) -> bool:
        return self._validated

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.target_type.value})"
