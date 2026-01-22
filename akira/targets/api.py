"""Generic API target for custom LLM endpoints"""

import asyncio
from typing import Any

import httpx

from akira.core.target import Target, TargetConfig, TargetType


class GenericAPITarget(Target):
    """Target for generic LLM API endpoints"""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    @property
    def target_type(self) -> TargetType:
        return TargetType.API_ENDPOINT

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def validate(self) -> bool:
        """Validate the endpoint is reachable"""
        if not self.config.endpoint:
            return False

        try:
            client = await self._get_client()
            # Try a simple request to check connectivity
            response = await client.get(self.config.endpoint)
            self._validated = response.status_code < 500
            return self._validated
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        """Send a payload to the API endpoint"""
        if not self.config.endpoint:
            raise ValueError("No endpoint configured")

        client = await self._get_client()

        # Default request format - can be customized via config.extra
        request_format = self.config.extra.get("request_format", "openai")

        if request_format == "openai":
            data = {
                "model": self.config.model or "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": payload}],
            }
        else:
            # Raw format - just send the payload
            data = {"prompt": payload}

        response = await client.post(self.config.endpoint, json=data)
        response.raise_for_status()

        result = response.json()
        return self._extract_response(result, request_format)

    def _extract_response(self, result: dict[str, Any], format: str) -> str:
        """Extract the text response from API result"""
        if format == "openai":
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return result.get("response", result.get("text", str(result)))

    async def send_batch(self, payloads: list[str]) -> list[str]:
        """Send multiple payloads concurrently"""
        tasks = [self.send(p) for p in payloads]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def close(self) -> None:
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
