"""OpenAI API target"""

import asyncio
import os

import httpx

from akira.core.target import Target, TargetConfig, TargetType


class OpenAITarget(Target):
    """Target for OpenAI API"""

    BASE_URL = "https://api.openai.com/v1"

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        # Use environment variable if no API key provided
        if not self.config.api_key:
            self.config.api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def target_type(self) -> TargetType:
        return TargetType.OPENAI

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint or self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def validate(self) -> bool:
        """Validate API key by listing models"""
        if not self.config.api_key:
            return False

        try:
            client = await self._get_client()
            response = await client.get("/models")
            self._validated = response.status_code == 200
            return self._validated
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        """Send a prompt to OpenAI"""
        client = await self._get_client()

        data = {
            "model": self.config.model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": payload}],
            "max_tokens": self.config.extra.get("max_tokens", 1024),
        }

        # Add system prompt if configured
        if system_prompt := self.config.extra.get("system_prompt"):
            data["messages"].insert(0, {"role": "system", "content": system_prompt})

        response = await client.post("/chat/completions", json=data)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def send_batch(self, payloads: list[str]) -> list[str]:
        """Send multiple payloads with rate limiting"""
        results = []
        # Simple rate limiting - 3 concurrent requests
        semaphore = asyncio.Semaphore(3)

        async def send_with_limit(p: str) -> str:
            async with semaphore:
                return await self.send(p)

        tasks = [send_with_limit(p) for p in payloads]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
