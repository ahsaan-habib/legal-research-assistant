from __future__ import annotations

import httpx

from . import config


def chat(messages: list[dict], fmt: str | dict | None = None) -> str:
    body = {"model": config.MODEL, "messages": messages, "stream": False, "think": False,
            "options": {"temperature": 0.0}}
    if fmt is not None:
        body["format"] = fmt
    r = httpx.post(f"{config.OLLAMA_URL}/api/chat", json=body, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"]
