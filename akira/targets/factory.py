"""Factory for creating target instances"""

from akira.core.target import Target, TargetConfig, TargetType
from akira.targets.api import GenericAPITarget
from akira.targets.openai import OpenAITarget
from akira.targets.anthropic import AnthropicTarget
from akira.targets.huggingface import HuggingFaceModelTarget, HuggingFaceInferenceTarget
from akira.targets.aws import BedrockTarget, SageMakerTarget


TARGET_MAP: dict[TargetType, type[Target]] = {
    TargetType.API_ENDPOINT: GenericAPITarget,
    TargetType.OPENAI: OpenAITarget,
    TargetType.ANTHROPIC: AnthropicTarget,
    TargetType.HUGGINGFACE_MODEL: HuggingFaceModelTarget,
    TargetType.HUGGINGFACE_INFERENCE: HuggingFaceInferenceTarget,
    TargetType.AWS_BEDROCK: BedrockTarget,
    TargetType.AWS_SAGEMAKER: SageMakerTarget,
}


def create_target(
    target_type: TargetType | str,
    endpoint: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    region: str | None = None,
    **extra: object,
) -> Target:
    if isinstance(target_type, str):
        target_type = TargetType(target_type)

    target_class = TARGET_MAP.get(target_type)
    if not target_class:
        raise ValueError(f"Unknown target type: {target_type}")

    config = TargetConfig(
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        region=region,
        extra=dict(extra),
    )

    return target_class(config)
