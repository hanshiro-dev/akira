"""HuggingFace targets - Inference API and local models"""

import asyncio
import os
from typing import Any

import httpx

from akira.core.target import Target, TargetConfig, TargetType


class HuggingFaceInferenceTarget(Target):
    BASE_URL = "https://api-inference.huggingface.co/models"

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        if not self.config.api_key:
            self.config.api_key = os.environ.get("HF_TOKEN")

    @property
    def target_type(self) -> TargetType:
        return TargetType.HUGGINGFACE_INFERENCE

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._client = httpx.AsyncClient(headers=headers, timeout=120.0)
        return self._client

    async def validate(self) -> bool:
        if not self.config.model:
            return False
        try:
            client = await self._get_client()
            response = await client.get(f"https://huggingface.co/api/models/{self.config.model}")
            self._validated = response.status_code == 200
            return self._validated
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        if not self.config.model:
            raise ValueError("No model specified")

        client = await self._get_client()
        url = f"{self.BASE_URL}/{self.config.model}"

        data: dict[str, Any] = {
            "inputs": payload,
            "parameters": {
                "max_new_tokens": self.config.extra.get("max_tokens", 256),
                "return_full_text": False,
            },
        }

        response = await client.post(url, json=data)

        if response.status_code == 503:
            await asyncio.sleep(20)
            response = await client.post(url, json=data)

        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        return str(result)

    async def send_batch(self, payloads: list[str]) -> list[str]:
        results = []
        for p in payloads:
            results.append(await self.send(p))
            await asyncio.sleep(1)
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class HuggingFaceModelTarget(Target):
    """Local HuggingFace model via transformers"""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._model = None
        self._tokenizer = None

    @property
    def target_type(self) -> TargetType:
        return TargetType.HUGGINGFACE_MODEL

    async def validate(self) -> bool:
        if not self.config.model:
            return False
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.config.model)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.config.model, device_map="auto", torch_dtype="auto"
            )
            self._validated = True
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    async def send(self, payload: str) -> str:
        if not self._model or not self._tokenizer:
            raise RuntimeError("Model not loaded")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate, payload)

    def _generate(self, payload: str) -> str:
        inputs = self._tokenizer(payload, return_tensors="pt").to(self._model.device)

        outputs = self._model.generate(
            **inputs,
            max_new_tokens=self.config.extra.get("max_tokens", 256),
            do_sample=True,
            temperature=0.7,
            pad_token_id=self._tokenizer.eos_token_id,
        )

        return self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )

    async def send_batch(self, payloads: list[str]) -> list[str]:
        return [await self.send(p) for p in payloads]

    async def close(self) -> None:
        if self._model:
            del self._model
            self._model = None
        if self._tokenizer:
            del self._tokenizer
            self._tokenizer = None
