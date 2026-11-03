"""LLM 客户端：统一走 OpenAI 兼容协议，可接入通义千问 / 智谱 GLM / DeepSeek / Kimi / GPT-4o 等。"""
from __future__ import annotations

from typing import List, Optional


class LLMClient:
    """轻量封装：available=False 时表示未配置 Key，上层将回退到本地规则引擎。"""

    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.6):
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "").strip()
        self.model = (model or "qwen-plus").strip()
        self.temperature = temperature
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url or None)
        return self._client

    def chat(
        self,
        system: str,
        user: str,
        history: Optional[List[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1600,
    ) -> str:
        messages = [{"role": "system", "content": system}]
        for h in (history or [])[-8:]:
            role = h.get("role", "user")
            content = h.get("content", "")
            if content:
                messages.append({"role": role, "content": content[:2000]})
        messages.append({"role": "user", "content": user})

        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
