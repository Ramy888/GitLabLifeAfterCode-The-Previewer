"""Finding model and the store-review/findings@1 schema checks."""

from __future__ import annotations

from dataclasses import dataclass

SCHEMA = "store-review/findings@1"
STORES = ("ios", "android", "shared")
LAYERS = ("automated", "reviewer")
SEVERITIES = ("blocker", "warning", "info")
SOURCES = ("deterministic", "llm")
FIX_KINDS = ("auto", "manual", "handoff")
REQUIRED_KEYS = ("id", "store", "layer", "guideline", "title", "severity", "weight", "source", "confidence", "evidence", "fix")


class SchemaError(ValueError):
    """A finding does not match the findings@1 schema."""


@dataclass(frozen=True)
class Evidence:
    path: str
    line: int | None
    detail: str


@dataclass(frozen=True)
class Fix:
    kind: str
    recipe: str


@dataclass(frozen=True)
class Finding:
    id: str
    store: str
    layer: str
    guideline: str
    title: str
    severity: str
    weight: float
    source: str
    confidence: float
    evidence: tuple[Evidence, ...]
    fix: Fix

    def applies_to(self, store: str) -> bool:
        return self.store == store or self.store == "shared"


def _require_choice(d: dict, key: str, choices: tuple[str, ...]) -> None:
    if d[key] not in choices:
        raise SchemaError(f"{key} must be one of {choices}, got {d[key]!r}")


def _number(d: dict, key: str) -> float:
    value = d[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError(f"{key} must be a number, got {value!r}")
    return value


def finding_from_dict(d: dict) -> Finding:
    try:
        return _finding_from_dict(d)
    except (KeyError, TypeError, AttributeError) as err:
        raise SchemaError(f"malformed finding {d.get('id', '?') if isinstance(d, dict) else d!r}: {err!r}") from err


def _finding_from_dict(d: dict) -> Finding:
    missing = [k for k in REQUIRED_KEYS if k not in d]
    if missing:
        raise SchemaError(f"missing keys: {', '.join(missing)}")
    _require_choice(d, "store", STORES)
    _require_choice(d, "layer", LAYERS)
    _require_choice(d, "severity", SEVERITIES)
    _require_choice(d, "source", SOURCES)
    confidence, weight = _number(d, "confidence"), _number(d, "weight")
    if not 0 <= confidence <= 1:
        raise SchemaError(f"confidence must be within 0..1, got {confidence!r}")
    if weight < 0:
        raise SchemaError(f"weight must be >= 0, got {weight!r}")
    if not isinstance(d["evidence"], list) or not d["evidence"]:
        raise SchemaError("evidence must list at least one item")
    evidence = tuple(Evidence(e["path"], e.get("line"), e["detail"]) for e in d["evidence"])
    fix = d["fix"]
    _require_choice(fix, "kind", FIX_KINDS)
    return Finding(
        id=d["id"],
        store=d["store"],
        layer=d["layer"],
        guideline=d["guideline"],
        title=d["title"],
        severity=d["severity"],
        weight=weight,
        source=d["source"],
        confidence=confidence,
        evidence=evidence,
        fix=Fix(fix["kind"], fix["recipe"]),
    )


def finding_to_dict(f: Finding) -> dict:
    return {
        "id": f.id,
        "store": f.store,
        "layer": f.layer,
        "guideline": f.guideline,
        "title": f.title,
        "severity": f.severity,
        "weight": f.weight,
        "source": f.source,
        "confidence": f.confidence,
        "evidence": [{"path": e.path, "line": e.line, "detail": e.detail} for e in f.evidence],
        "fix": {"kind": f.fix.kind, "recipe": f.fix.recipe},
    }
