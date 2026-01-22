"""Anthropic API target"""

import asyncio
import os

import httpx

from akira.core.target import Target, TargetConfig, TargetType


class AnthropicTarget(Target):
    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        if not self.config.api_key:
            self.config.api_key = os.environ.get("ANTHROPIC_API_KEY")

    @property
    def target_type(self) -> TargetType:
        return TargetType.ANTHROPIC

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint or self.BASE_URL,
                headers={
                    "x-api-key": self.config.api_key or "",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                timeout=60.0,
            )
        return self._client

    async def validate(self) -> bool:
        if not self.config.api_key:
            return False
        try:
            client = await self._get_client()
            response = await client.post(
                "/messages",
                json={
                    "model": self.config.model or "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
            self._validated = response.status_code == 200
            return self._validated
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        client = await self._get_client()

        data = {
            "model": self.config.model or "claude-sonnet-4-20250514",
            "max_tokens": self.config.extra.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": payload}],
        }

        if system_prompt := self.config.extra.get("system_prompt"):
            data["system"] = system_prompt

        response = await client.post("/messages", json=data)
        response.raise_for_status()

        content = response.json().get("content", [])
        return content[0].get("text", "") if content else ""

    async def send_batch(self, payloads: list[str]) -> list[str]:
        semaphore = asyncio.Semaphore(2)

        async def send_with_limit(p: str) -> str:
            async with semaphore:
                result = await self.send(p)
                await asyncio.sleep(0.5)
                return result

        return list(await asyncio.gather(*[send_with_limit(p) for p in payloads]))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
