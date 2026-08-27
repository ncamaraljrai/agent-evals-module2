from __future__ import annotations
import os, time
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()
import anthropic

AGENT_MODEL = os.getenv("EVAL_AGENT_MODEL", "claude-haiku-4-5")

@dataclass
class CallResult:
    response: object
    latency_ms: float

def _client():
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY missing. Copy .env.example to .env and add your key.")
    return anthropic.Anthropic()

def complete(*, messages, system=None, tools=None, temperature=0.0, max_tokens=700):
    req = {"model": AGENT_MODEL, "max_tokens": max_tokens,
           "temperature": temperature, "messages": messages}
    if system: req["system"] = system
    if tools: req["tools"] = tools
    started = time.perf_counter()
    response = _client().messages.create(**req)
    return CallResult(response, (time.perf_counter()-started)*1000)

def text_from_response(response):
    return "\n".join(b.text for b in response.content
                     if getattr(b, "type", None) == "text").strip()
