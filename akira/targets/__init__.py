"""Target implementations for various LLM platforms"""

from akira.targets.anthropic import AnthropicTarget
from akira.targets.api import GenericAPITarget
from akira.targets.aws import BedrockTarget, SageMakerTarget
from akira.targets.factory import create_target
from akira.targets.huggingface import HuggingFaceInferenceTarget, HuggingFaceModelTarget
from akira.targets.openai import OpenAITarget

__all__ = [
    "GenericAPITarget",
    "OpenAITarget",
    "AnthropicTarget",
    "HuggingFaceModelTarget",
    "HuggingFaceInferenceTarget",
    "BedrockTarget",
    "SageMakerTarget",
    "create_target",
]
