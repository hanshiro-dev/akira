"""Target definitions for different attack surfaces"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TargetType(str, Enum):
    """Types of targets Akira can attack"""
    API_ENDPOINT = "api"           # Generic LLM API endpoint
    OPENAI = "openai"              # OpenAI API
    ANTHROPIC = "anthropic"        # Anthropic API
    HUGGINGFACE_MODEL = "hf"       # HuggingFace model
    HUGGINGFACE_INFERENCE = "hf_inference"  # HuggingFace Inference API
    AWS_BEDROCK = "bedrock"        # AWS Bedrock
    AWS_SAGEMAKER = "sagemaker"    # AWS SageMaker
    AZURE_OPENAI = "azure"         # Azure OpenAI
    LOCAL_MODEL = "local"          # Local model (Ollama, vLLM, etc.)


@dataclass
class TargetConfig:
    """Configuration for connecting to a target"""
    endpoint: str | None = None
    api_key: str | None = None
    model: str | None = None
    region: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class Target(ABC):
    """Base class for all targets"""

    def __init__(self, config: TargetConfig) -> None:
        self.config = config
        self._validated = False

    @property
    @abstractmethod
    def target_type(self) -> TargetType:
        """Return the target type"""
        ...

    @abstractmethod
    async def validate(self) -> bool:
        """Validate the target is reachable and credentials work"""
        ...

    @abstractmethod
    async def send(self, payload: str) -> str:
        """Send a payload to the target and return the response"""
        ...

    @abstractmethod
    async def send_batch(self, payloads: list[str]) -> list[str]:
        """Send multiple payloads (for efficiency)"""
        ...

    @property
    def is_validated(self) -> bool:
        return self._validated

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.target_type.value})"
