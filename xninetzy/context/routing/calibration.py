from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CALIBRATION_VERSION = "1.0.0"
CALIBRATION_MIN_SAMPLES = 100
DEFAULT_REJECT_THRESHOLD = 0.05


@dataclass(frozen=True, slots=True)
class CalibrationRecord:
    layer: str
    domain: str
    coefficients: tuple[float, float]
    n_samples: int
    ece: float
    brier: float
    trained_at: str
    train_split_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "domain": self.domain,
            "a": self.coefficients[0],
            "b": self.coefficients[1],
            "n_samples": self.n_samples,
            "ece": round(self.ece, 6),
            "brier": round(self.brier, 6),
            "trained_at": self.trained_at,
            "train_split_hash": self.train_split_hash,
            "version": CALIBRATION_VERSION,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CalibrationRecord":
        return cls(
            layer=str(payload.get("layer", "")),
            domain=str(payload.get("domain", "")),
            coefficients=(float(payload.get("a", 1.0)), float(payload.get("b", 0.0))),
            n_samples=int(payload.get("n_samples", 0)),
            ece=float(payload.get("ece", 0.0)),
            brier=float(payload.get("brier", 0.0)),
            trained_at=str(payload.get("trained_at", "")),
            train_split_hash=str(payload.get("train_split_hash", "")),
        )


class CalibrationRegistry:
    def __init__(self, storage_dir: str | Path = "data/routing_calibration") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[tuple[str, str], CalibrationRecord] = {}

    def _key(self, layer: str, domain: str) -> tuple[str, str]:
        return (layer, domain)

    def register(self, record: CalibrationRecord) -> None:
        key = self._key(record.layer, record.domain)
        self._cache[key] = record
        path = self.storage_dir / f"{record.layer}__{record.domain}.json"
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True), encoding="utf-8")

    def lookup(self, layer: str, domain: str) -> CalibrationRecord | None:
        key = self._key(layer, domain)
        if key in self._cache:
            return self._cache[key]
        path = self.storage_dir / f"{layer}__{domain}.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        rec = CalibrationRecord.from_dict(payload)
        self._cache[key] = rec
        return rec

    def is_acceptable(self, record: CalibrationRecord) -> bool:
        if record.n_samples < CALIBRATION_MIN_SAMPLES:
            return False
        return record.ece <= DEFAULT_REJECT_THRESHOLD


def _split_hash(rows: list[dict[str, Any]]) -> str:
    raw = json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def ece(probs: list[float], labels: list[int], *, n_bins: int = 10) -> float:
    if not probs or len(probs) != len(labels):
        return 0.0
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, label in zip(probs, labels):
        idx = min(max(int(p * n_bins), 0), n_bins - 1)
        bins[idx].append((p, label))
    total = len(probs)
    score = 0.0
    for bucket in bins:
        if not bucket:
            continue
        acc = sum(label for _, label in bucket) / len(bucket)
        conf = sum(p for p, _ in bucket) / len(bucket)
        score += (len(bucket) / total) * abs(acc - conf)
    return score


def brier(probs: list[float], labels: list[int]) -> float:
    if not probs:
        return 0.0
    return sum((p - label) ** 2 for p, label in zip(probs, labels)) / len(probs)


def fit_platt(probs: list[float], labels: list[int]) -> tuple[float, float]:
    if len(probs) < 3 or len(set(labels)) < 2:
        return (1.0, 0.0)
    try:
        from sklearn.linear_model import LogisticRegression
        import math as _math

        feats = [_math.log(max(min(p, 1.0 - 1e-9), 1e-9)) for p in probs]
        clf = LogisticRegression(max_iter=1000, solver="lbfgs")
        clf.fit([[x] for x in feats], list(labels))
        return (float(clf.coef_[0][0]), float(clf.intercept_[0]))
    except Exception:
        return (1.0, 0.0)


def apply_calibration(probs: dict[str, float], coefficients: tuple[float, float]) -> dict[str, float]:
    a, b = coefficients
    out: dict[str, float] = {}
    for k, p in probs.items():
        logit = a * p + b
        if logit >= 30.0:
            out[k] = 1.0
        elif logit <= -30.0:
            out[k] = 0.0
        else:
            out[k] = 1.0 / (1.0 + math.exp(-logit))
        out[k] = max(0.0, min(1.0, out[k]))
    return out


def health_snapshot(registry: CalibrationRegistry) -> dict[str, Any]:
    layer_domain_records: dict[str, dict[str, dict[str, Any]]] = {}
    n_acceptable = 0
    for layer in ("L2_domain", "L3_skill", "L4_task", "L5_capability", "L5_tool"):
        for domain in ("learning", "research", "career", "academic", "media", "security", "knowledge"):
            rec = registry.lookup(layer, domain)
            if rec is None:
                continue
            layer_domain_records.setdefault(layer, {})[domain] = rec.to_dict()
            if registry.is_acceptable(rec):
                n_acceptable += 1
    return {
        "version": CALIBRATION_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "registries": layer_domain_records,
        "acceptable_count": n_acceptable,
        "min_samples_required": CALIBRATION_MIN_SAMPLES,
        "ece_reject_threshold": DEFAULT_REJECT_THRESHOLD,
    }
