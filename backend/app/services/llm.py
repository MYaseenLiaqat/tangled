from openai import AsyncOpenAI, APIError
from ..config import settings

_client: AsyncOpenAI | None = None
_json_mode_supported: bool | None = None


def _c() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.llm_api_key or "missing", base_url=settings.llm_base_url,
                              timeout=settings.llm_timeout, max_retries=settings.llm_max_retries)
    return _client


async def chat(messages: list[dict], json_mode: bool = False, temperature: float = 0.2) -> str:
    global _json_mode_supported
    kw = dict(model=settings.llm_model, messages=messages, temperature=temperature,
              max_tokens=settings.max_llm_output_tokens)
    if json_mode and settings.llm_json_mode != "off" and _json_mode_supported is not False:
        kw["response_format"] = {"type": "json_object"}
    if json_mode and (settings.llm_json_mode == "off" or _json_mode_supported is False):
        kw["messages"] = [*messages, {"role": "user", "content": "Return only one valid JSON object."}]
    try:
        r = await _c().chat.completions.create(**kw)
        if json_mode and "response_format" in kw:
            _json_mode_supported = True
    except APIError:
        if not json_mode or settings.llm_json_mode == "on" or _json_mode_supported is False:
            raise
        _json_mode_supported = False
        kw.pop("response_format", None)
        kw["messages"] = [*messages, {"role": "user", "content": "Return only one valid JSON object."}]
        r = await _c().chat.completions.create(**kw)
    return r.choices[0].message.content or ""
