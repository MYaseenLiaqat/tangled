from openai import AsyncOpenAI
from ..config import settings

_client: AsyncOpenAI | None = None


def _c() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.llm_api_key or "missing", base_url=settings.llm_base_url,
                              timeout=settings.llm_timeout, max_retries=settings.llm_max_retries)
    return _client


async def chat(messages: list[dict], json_mode: bool = False, temperature: float = 0.2) -> str:
    kw = dict(model=settings.llm_model, messages=messages, temperature=temperature,
              max_tokens=settings.max_llm_output_tokens)
    if json_mode:
        kw["response_format"] = {"type": "json_object"}
    r = await _c().chat.completions.create(**kw)
    return r.choices[0].message.content or ""
