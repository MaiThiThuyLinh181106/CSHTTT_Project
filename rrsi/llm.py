from __future__ import annotations

import os
import re
import time
# pyrefly: ignore [missing-import]
import litellm

MODEL = os.environ.get("RRSI_SEARCH_MODEL", "gemini/gemini-3.5-flash-lite")
MAX_TOKENS = 20_000

_JSON_SUFFIX = (
    "\n\nOutput ONLY a single valid JSON object. No prose before or "
    "after, no markdown fences."
)


def extract_json(text: str) -> str:
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    if not t.startswith("{") and not t.startswith("["):
        start = min([i for i in (t.find("{"), t.find("[")) if i != -1], default=-1)
        if start != -1:
            t = t[start:]
    if t and t[0] == "{" and not t.endswith("}"):
        end = t.rfind("}")
        if end != -1:
            t = t[: end + 1]
    if t and t[0] == "[" and not t.endswith("]"):
        end = t.rfind("]")
        if end != -1:
            t = t[: end + 1]
    return t


def generate(
    prompt: str,
    system: str | None = None,
    max_retries: int = 8,
    json_only: bool = False,
    model: str | None = None,
    max_tokens: int = MAX_TOKENS,
    cache_prefix: str | None = None,
) -> str:
    mdl = "gemini/gemini-3.5-flash-lite"

    sys_prompt = (system or "") + (_JSON_SUFFIX if json_only else "")
    full_user_prompt = f"{cache_prefix}\n\n{prompt}" if cache_prefix else prompt

    messages = []
    if sys_prompt:
        messages.append({"role": "system", "content": sys_prompt})
    messages.append({"role": "user", "content": full_user_prompt})

    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            # Nghỉ 4 giây trước mỗi lần gọi để giữ tốc độ <= 15 requests/phút
            time.sleep(4)
            resp = litellm.completion(
                model=mdl,
                messages=messages,
                max_tokens=max_tokens,
            )
            text = resp.choices[0].message.content or ""
            if text.strip():
                return extract_json(text) if json_only else text
            last_err = RuntimeError("empty response")
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "RateLimit" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"[llm] Rate limit 429 reached, waiting 60s for quota recovery (attempt {attempt + 1}/{max_retries})...")
                time.sleep(60)
            else:
                time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"generate failed after {max_retries} tries: {last_err}")
    
if __name__ == "__main__":
    print(generate("Reply with exactly: OK", max_tokens=16))