from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

LAYA_VERSION = "1.0.0"
CARDI_OPTIONS: tuple[int, ...] = (3, 5, 8, 10, 12, 15, 20, 25, 30, 50)

SYSTEM_PROMPT_MENU = {
    "L2_domain": (
        "You are a routing classifier for a personal knowledge / OS assistant.\n"
        "Pick AT MOST 3 of the listed canonical domains (semantic) whose meanings cover the user request.\n"
        "Return JSON: {\"labels\": [\"<domain>\"...], \"confidence\": {\"<domain>\": 0..1}}.\n"
        "Use ONLY domains from the menu below; do not invent names."
    ),
    "L3_skill": (
        "You are a routing classifier. Pick AT MOST 3 of the listed canonical skill names.\n"
        "Return JSON: {\"labels\": [\"<skill>\"...], \"confidence\": {\"<skill>\": 0..1}}."
    ),
    "L4_task": (
        "You are a routing classifier. Describe the user's task in ONE short verb phrase\n"
        "(\"summarize\", \"find\", \"execute\", \"render\" etc.) PLUS at most 3 capability tags.\n"
        "Return JSON: {\"task\": \"<short_phrase>\", \"capabilities\": [\"<cap>\"]}."
    ),
    "L5_tool": (
        "You are a routing classifier. From the listed tool candidates, rank the top tools\n"
        "best matching the user's request.\n"
        "Return JSON: {\"ranking\": [{\"name\": \"<tool>\", \"score\": 0..1}, ...]}."
    ),
}


@dataclass(frozen=True, slots=True)
class LayaDecision:
    layer: str
    query: str
    selected: tuple[str, ...]
    raw_probabilities: dict[str, float] = field(default_factory=dict)
    calibrated_probabilities: dict[str, float] = field(default_factory=dict)
    reason_codes: tuple[str, ...] = ()
    latency_ms: float = 0.0
    provider_id: str = ""
    provider_model: str = ""
    abstained: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def _prompt(layer: str, menu: list[dict[str, Any]], query: str) -> list[dict[str, str]]:
    sys_msg = SYSTEM_PROMPT_MENU[layer] + "\n\nMenu:\n" + json.dumps(menu, ensure_ascii=False)
    user_msg = f"User request: {query}"
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]


def _clip(x: float) -> float:
    return max(0.0, min(x, 1.0))


def _platt(prob: float, *, a: float, b: float) -> float:
    if a == 0.0:
        return _clip(prob)
    logit = a * prob + b
    if logit >= 30.0:
        return 1.0
    if logit <= -30.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-logit))


def _llm_chat_json(
    *,
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    timeout_seconds: float,
) -> dict[str, Any]:
    from xninetzy.core.config import get_settings
    from xninetzy.interfaces.llm_chat_transport import post_json

    s = get_settings()
    base_url = ""
    api_key = ""
    if provider == "flaz":
        base_url = s.FLAZ_BASE_URL.rstrip("/") if s.FLAZ_BASE_URL else ""
        api_key = s.FLAZ_API_KEY or ""
        model = model or s.FLAZ_MODEL or ""
    elif provider == "openai":
        base_url = s.OPENAI_BASE_URL.rstrip("/") if s.OPENAI_BASE_URL else ""
        api_key = s.OPENAI_API_KEY or ""
        model = model or s.OPENAI_MODEL or ""
    else:
        raise ValueError(f"unsupported provider for Laya head: {provider}")
    if not base_url or not api_key:
        raise RuntimeError(f"provider {provider} missing base_url or api_key")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model or "",
        "messages": messages,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = post_json(url, payload, headers, timeout_seconds)
    content = (((body.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
    text = content.strip()
    if text.startswith("```"):
        first, _, rest = text.partition("```")
        if "json" in first.lower():
            text = rest.strip()
    try:
        return json.loads(text)
    except Exception:
        return {"labels": [], "confidence": {}, "_raw": text[:500]}


def invoke_laya(
    *,
    layer: str,
    query: str,
    menu: list[dict[str, Any]],
    provider_id: str | None = None,
    model: str | None = None,
    calibration: tuple[float, float] | None = None,
    timeout_seconds: float = 30.0,
) -> LayaDecision:
    from xninetzy.core.config import get_settings

    if layer not in SYSTEM_PROMPT_MENU:
        return LayaDecision(
            layer=layer,
            query=query,
            selected=(),
            reason_codes=("laya_invalid_layer",),
            abstained=True,
            metadata={"reason": f"unknown layer {layer}"},
        )
    bounded_menu = menu[: max(1, CARDI_OPTIONS[0 if len(menu) <= CARDI_OPTIONS[-1] else -1])]
    settings = get_settings()
    chosen_provider = provider_id or settings.LLM_DEFAULT_PROVIDER or "flaz"
    chosen_model = model or settings.FLAZ_MODEL or ""
    messages = _prompt(layer, bounded_menu, query)
    try:
        raw = _llm_chat_json(
            provider=chosen_provider,
            model=chosen_model,
            messages=messages,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        return LayaDecision(
            layer=layer,
            query=query,
            selected=(),
            reason_codes=("laya_unavailable", str(exc.__class__.__name__)),
            abstained=True,
            provider_id=chosen_provider,
            provider_model=chosen_model,
            metadata={"error": str(exc)[:300]},
        )
    if isinstance(raw, dict):
        labels_raw = raw.get("labels") or raw.get("selected") or raw.get("ranking") or []
    else:
        labels_raw = []
    if isinstance(labels_raw, list):
        labels: list[str] = []
        for x in labels_raw:
            if isinstance(x, str):
                labels.append(x)
            elif isinstance(x, dict):
                n = x.get("name") or x.get("label")
                if isinstance(n, str):
                    labels.append(n)
    else:
        labels = []
    confidence_map = raw.get("confidence") if isinstance(raw.get("confidence"), dict) else {}
    raw_probs: dict[str, float] = {}
    for k, v in confidence_map.items():
        if isinstance(v, (int, float)):
            raw_probs[str(k)] = _clip(float(v))
    calibrated = dict(raw_probs)
    if calibration is not None:
        a, b = calibration
        calibrated = {k: _clip(_platt(v, a=a, b=b)) for k, v in raw_probs.items()}
    abstained = not labels or (raw_probs and max(raw_probs.values()) < 0.4)
    selected = tuple(labels)
    return LayaDecision(
        layer=layer,
        query=query,
        selected=selected,
        raw_probabilities=raw_probs,
        calibrated_probabilities=calibrated,
        reason_codes=("laya_call_ok",) if labels else ("laya_parse_fallback",),
        provider_id=chosen_provider,
        provider_model=chosen_model,
        abstained=abstained,
        metadata={"menu_size": len(bounded_menu)},
    )


def _platt_fit_closed_form(probs: list[float], labels: list[int]) -> tuple[float, float]:
    pos = sum(1 for y in labels if y == 1)
    n = len(labels)
    a = 1.0 if 0 < pos < n else 0.0
    import math as _math

    base = max(1e-6, min(1.0 - 1e-6, max(probs) if probs else 0.5))
    b = -_math.log((1.0 - base) / base) if base > 0.0 and base < 1.0 else 0.0
    return (a, b)


def fit_platt(probs: list[float], labels: list[int]) -> tuple[float, float] | None:
    if not probs or len(probs) != len(labels):
        return None
    try:
        from sklearn.linear_model import LogisticRegression
    except Exception:
        try:
            return _platt_fit_closed_form(probs, labels)
        except Exception:
            return (1.0, 0.0)
    import math as _math

    feats = [_math.log(max(min(p, 1.0 - 1e-9), 1e-9)) for p in probs]
    clf = LogisticRegression(max_iter=1000, solver="lbfgs")
    clf.fit([[x] for x in feats], labels)
    a = float(clf.coef_[0][0])
    b = float(clf.intercept_[0])
    return (a, b)


def ece(probs: list[float], labels: list[int], *, n_bins: int = 10) -> float:
    if not probs or len(probs) != len(labels):
        return 0.0
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in zip(probs, labels):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))
    total = len(probs)
    out = 0.0
    for bucket in bins:
        if not bucket:
            continue
        acc = sum(y for _, y in bucket) / len(bucket)
        conf = sum(p for p, _ in bucket) / len(bucket)
        out += (len(bucket) / total) * abs(acc - conf)
    return out


def brier(probs: list[float], labels: list[int]) -> float:
    if not probs:
        return 0.0
    return sum((p - y) ** 2 for p, y in zip(probs, labels)) / len(probs)
