"""Target implementations for various LLM platforms"""

from akira.targets.api import GenericAPITarget
from akira.targets.openai import OpenAITarget
from akira.targets.anthropic import AnthropicTarget
from akira.targets.huggingface import HuggingFaceModelTarget, HuggingFaceInferenceTarget
from akira.targets.aws import BedrockTarget, SageMakerTarget
from akira.targets.factory import create_target

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
