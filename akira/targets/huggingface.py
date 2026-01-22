"""HuggingFace targets - local models and inference API"""

import asyncio
import os
from typing import Any

import httpx

from akira.core.target import Target, TargetConfig, TargetType


class HuggingFaceInferenceTarget(Target):
    """Target for HuggingFace Inference API"""

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
        """Check if the model exists and is accessible"""
        if not self.config.model:
            return False

        try:
            client = await self._get_client()
            # Check model info endpoint
            response = await client.get(
                f"https://huggingface.co/api/models/{self.config.model}"
            )
            self._validated = response.status_code == 200
            return self._validated
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        """Send a prompt to the model"""
        if not self.config.model:
            raise ValueError("No model specified")

        client = await self._get_client()
        url = f"{self.BASE_URL}/{self.config.model}"

        # Try chat format first, fall back to text generation
        data: dict[str, Any]
        if "chat" in self.config.model.lower() or "instruct" in self.config.model.lower():
            data = {
                "inputs": payload,
                "parameters": {
                    "max_new_tokens": self.config.extra.get("max_tokens", 256),
                    "return_full_text": False,
                },
            }
        else:
            data = {
                "inputs": payload,
                "parameters": {"max_new_tokens": self.config.extra.get("max_tokens", 256)},
            }

        response = await client.post(url, json=data)

        # Handle model loading
        if response.status_code == 503:
            # Model is loading, wait and retry
            await asyncio.sleep(20)
            response = await client.post(url, json=data)

        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        return str(result)

    async def send_batch(self, payloads: list[str]) -> list[str]:
        """Send multiple payloads"""
        # HF Inference API has strict rate limits
        results = []
        for p in payloads:
            results.append(await self.send(p))
            await asyncio.sleep(1)  # Rate limiting
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class HuggingFaceModelTarget(Target):
    """Target for local HuggingFace models via transformers"""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._model = None
        self._tokenizer = None

    @property
    def target_type(self) -> TargetType:
        return TargetType.HUGGINGFACE_MODEL

    async def validate(self) -> bool:
        """Load and validate the model"""
        if not self.config.model:
            return False

        try:
            # Lazy import to avoid requiring transformers for API-only usage
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.config.model)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.config.model,
                device_map="auto",
                torch_dtype="auto",
            )
            self._validated = True
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    async def send(self, payload: str) -> str:
        """Generate response from local model"""
        if not self._model or not self._tokenizer:
            raise RuntimeError("Model not loaded. Call validate() first.")

        # Run inference in thread pool to not block async
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate, payload)

    def _generate(self, payload: str) -> str:
        """Synchronous generation"""
        inputs = self._tokenizer(payload, return_tensors="pt")
        inputs = inputs.to(self._model.device)

        outputs = self._model.generate(
            **inputs,
            max_new_tokens=self.config.extra.get("max_tokens", 256),
            do_sample=True,
            temperature=0.7,
            pad_token_id=self._tokenizer.eos_token_id,
        )

        # Decode only the new tokens
        response = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        return response

    async def send_batch(self, payloads: list[str]) -> list[str]:
        """Process payloads sequentially (local model)"""
        return [await self.send(p) for p in payloads]

    async def close(self) -> None:
        """Unload model from memory"""
        if self._model:
            del self._model
            self._model = None
        if self._tokenizer:
            del self._tokenizer
            self._tokenizer = None
