"""Generic API target for any LLM-powered endpoint"""

import asyncio
import json
from string import Template
from typing import Any

import httpx

from akira.core.target import Target, TargetConfig, TargetType


class GenericAPITarget(Target):
    """Flexible target for any API endpoint using an LLM behind the scenes.

    Config options (via extra dict):
        request_template: JSON with $payload placeholder
        response_path: Dot-notation path (e.g., "data.reply.text")
        auth_type: bearer | header | query | basic
        auth_header: Custom header name (default: Authorization)
        method: HTTP method (default: POST)
    """

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    @property
    def target_type(self) -> TargetType:
        return TargetType.API_ENDPOINT

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = self._build_headers()
            timeout = float(self.config.extra.get("timeout", 60))
            self._client = httpx.AsyncClient(headers=headers, timeout=timeout)
        return self._client

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": self.config.extra.get("content_type", "application/json")
        }
        headers.update(self.config.extra.get("headers", {}))

        if self.config.api_key:
            auth_type = self.config.extra.get("auth_type", "bearer")
            auth_header = self.config.extra.get("auth_header", "Authorization")

            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            elif auth_type == "header":
                headers[auth_header] = self.config.api_key
            elif auth_type == "basic":
                import base64
                creds = base64.b64encode(self.config.api_key.encode()).decode()
                headers["Authorization"] = f"Basic {creds}"

        return headers

    def _build_request_body(self, payload: str) -> dict[str, Any] | str:
        template_str = self.config.extra.get("request_template")

        if template_str:
            escaped_payload = json.dumps(payload)[1:-1]
            filled = Template(template_str).safe_substitute(payload=escaped_payload)
            try:
                return json.loads(filled)
            except json.JSONDecodeError:
                return filled

        request_format = self.config.extra.get("request_format", "auto")
        formats = {
            "openai": {"model": self.config.model or "gpt-3.5-turbo", "messages": [{"role": "user", "content": payload}]},
            "anthropic": {"model": self.config.model or "claude-3-haiku-20240307", "max_tokens": 1024, "messages": [{"role": "user", "content": payload}]},
            "simple": {"prompt": payload},
            "message": {"message": payload},
            "query": {"query": payload},
            "input": {"input": payload},
            "text": {"text": payload},
        }

        return formats.get(request_format, {"message": payload, "prompt": payload, "input": payload})

    def _extract_response(self, result: Any) -> str:
        response_path = self.config.extra.get("response_path")
        if response_path:
            return self._get_nested_value(result, response_path)

        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            paths = [
                "response", "reply", "answer", "text", "content", "message", "output", "result",
                "data.response", "data.reply", "data.text", "data.message",
                "choices.0.message.content", "choices.0.text", "content.0.text", "generated_text",
            ]
            for path in paths:
                try:
                    value = self._get_nested_value(result, path)
                    if value and isinstance(value, str):
                        return value
                except (KeyError, IndexError, TypeError):
                    continue
            return json.dumps(result)

        return str(result)

    def _get_nested_value(self, obj: Any, path: str) -> str:
        current = obj
        for part in path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return ""
            else:
                return ""
            if current is None:
                return ""
        return str(current) if current is not None else ""

    async def validate(self) -> bool:
        if not self.config.endpoint:
            return False

        try:
            client = await self._get_client()
            try:
                response = await client.options(self.config.endpoint)
                if response.status_code < 500:
                    self._validated = True
                    return True
            except Exception:
                pass

            try:
                response = await client.post(
                    self.config.endpoint,
                    json=self._build_request_body("test"),
                    timeout=10.0,
                )
                self._validated = response.status_code < 500
                return self._validated
            except httpx.HTTPStatusError:
                self._validated = True
                return True
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        if not self.config.endpoint:
            raise ValueError("No endpoint configured")

        client = await self._get_client()
        method = self.config.extra.get("method", "POST").upper()

        url = self.config.endpoint
        if self.config.api_key and self.config.extra.get("auth_type") == "query":
            param_name = self.config.extra.get("auth_param", "api_key")
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{param_name}={self.config.api_key}"

        body = self._build_request_body(payload)

        if method == "GET":
            params = body if isinstance(body, dict) else {"payload": payload}
            response = await client.get(url, params=params)
        else:
            if isinstance(body, dict):
                response = await client.request(method, url, json=body)
            else:
                response = await client.request(method, url, content=body)

        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return self._extract_response(response.json())
        return response.text

    async def send_batch(self, payloads: list[str]) -> list[str]:
        max_concurrent = int(self.config.extra.get("max_concurrent", 5))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_limited(p: str) -> str:
            async with semaphore:
                return await self.send(p)

        tasks = [send_limited(p) for p in payloads]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
