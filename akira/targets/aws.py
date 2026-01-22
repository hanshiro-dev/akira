"""AWS AI service targets - Bedrock and SageMaker"""

import asyncio
import json
from typing import Any

from akira.core.target import Target, TargetConfig, TargetType


class BedrockTarget(Target):
    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._client = None
        self._runtime_client = None

    @property
    def target_type(self) -> TargetType:
        return TargetType.AWS_BEDROCK

    def _get_boto_clients(self) -> tuple[Any, Any]:
        if self._client is None:
            import boto3

            kwargs = {}
            if self.config.region:
                kwargs["region_name"] = self.config.region
            if self.config.extra.get("aws_access_key_id"):
                kwargs["aws_access_key_id"] = self.config.extra["aws_access_key_id"]
                kwargs["aws_secret_access_key"] = self.config.extra["aws_secret_access_key"]

            self._client = boto3.client("bedrock", **kwargs)
            self._runtime_client = boto3.client("bedrock-runtime", **kwargs)

        return self._client, self._runtime_client

    async def validate(self) -> bool:
        try:
            client, _ = self._get_boto_clients()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, client.list_foundation_models)
            self._validated = True
            return True
        except Exception as e:
            print(f"Bedrock validation failed: {e}")
            return False

    async def send(self, payload: str) -> str:
        _, runtime = self._get_boto_clients()
        model_id = self.config.model or "anthropic.claude-3-haiku-20240307-v1:0"

        if "anthropic" in model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.config.extra.get("max_tokens", 1024),
                "messages": [{"role": "user", "content": payload}],
            }
        elif "amazon" in model_id:
            body = {
                "inputText": payload,
                "textGenerationConfig": {"maxTokenCount": self.config.extra.get("max_tokens", 1024)},
            }
        elif "meta" in model_id:
            body = {"prompt": payload, "max_gen_len": self.config.extra.get("max_tokens", 1024)}
        else:
            body = {"prompt": payload}

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            ),
        )

        result = json.loads(response["body"].read())
        return self._extract_response(result, model_id)

    def _extract_response(self, result: dict[str, Any], model_id: str) -> str:
        if "anthropic" in model_id:
            content = result.get("content", [])
            return content[0].get("text", "") if content else ""
        elif "amazon" in model_id:
            results = result.get("results", [])
            return results[0].get("outputText", "") if results else ""
        elif "meta" in model_id:
            return result.get("generation", "")
        return str(result)

    async def send_batch(self, payloads: list[str]) -> list[str]:
        semaphore = asyncio.Semaphore(2)

        async def send_limited(p: str) -> str:
            async with semaphore:
                return await self.send(p)

        return list(await asyncio.gather(*[send_limited(p) for p in payloads]))

    async def close(self) -> None:
        self._client = None
        self._runtime_client = None


class SageMakerTarget(Target):
    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._client = None

    @property
    def target_type(self) -> TargetType:
        return TargetType.AWS_SAGEMAKER

    def _get_client(self) -> Any:
        if self._client is None:
            import boto3

            kwargs = {}
            if self.config.region:
                kwargs["region_name"] = self.config.region
            if self.config.extra.get("aws_access_key_id"):
                kwargs["aws_access_key_id"] = self.config.extra["aws_access_key_id"]
                kwargs["aws_secret_access_key"] = self.config.extra["aws_secret_access_key"]

            self._client = boto3.client("sagemaker-runtime", **kwargs)
        return self._client

    async def validate(self) -> bool:
        if not self.config.endpoint:
            return False
        try:
            import boto3
            sm_client = boto3.client("sagemaker", region_name=self.config.region or "us-east-1")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: sm_client.describe_endpoint(EndpointName=self.config.endpoint)
            )
            self._validated = True
            return True
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        if not self.config.endpoint:
            raise ValueError("No endpoint specified")

        client = self._get_client()
        body = json.dumps({"inputs": payload})

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.invoke_endpoint(
                EndpointName=self.config.endpoint,
                ContentType="application/json",
                Body=body,
            ),
        )

        result = json.loads(response["Body"].read())
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", str(result[0]))
        return str(result)

    async def send_batch(self, payloads: list[str]) -> list[str]:
        return [await self.send(p) for p in payloads]

    async def close(self) -> None:
        self._client = None
