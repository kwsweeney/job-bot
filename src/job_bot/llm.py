"""Thin wrapper around the Gemini API."""
from __future__ import annotations

import json
import os
import re

DEFAULT_MODEL = "gemini-2.5-flash"


def extract_json(text: str):
    """Extract the first JSON value from model output (handles code fences)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                return decoder.raw_decode(text[i:])[0]
            except json.JSONDecodeError:
                continue
    raise ValueError("No JSON found in model response")


class Gemini:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        from google import genai

        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("Set GEMINI_API_KEY to use the Gemini API.")
        self._genai = genai
        self.client = genai.Client(api_key=key)
        self.model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

    def generate(self, prompt: str, pdf_bytes: bytes | None = None) -> str:
        from google.genai import types

        contents: list = []
        if pdf_bytes is not None:
            contents.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
        contents.append(prompt)
        return self.client.models.generate_content(model=self.model, contents=contents).text or ""

    def generate_json(self, prompt: str):
        return extract_json(self.generate(prompt))

    def search(self, prompt: str) -> str:
        """Generate with Google Search grounding enabled (web search)."""
        from google.genai import types

        cfg = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        resp = self.client.models.generate_content(model=self.model, contents=prompt, config=cfg)
        return resp.text or ""
