"""Gated readiness score per store (see SPEC.md, 'Readiness score')."""

from __future__ import annotations

from store_review.model import Finding

BLOCKED_CAP = 40
READY_AT = 80


def _clamp(x: float) -> int:
    return int(round(max(0.0, min(100.0, x))))


def score_store(findings: list[Finding], store: str) -> dict:
    mine = [f for f in findings if f.applies_to(store)]
    blockers = [f for f in mine if f.severity == "blocker"]
    warnings = [f for f in mine if f.severity == "warning"]
    det = sum(f.weight for f in warnings if f.source == "deterministic")
    llm_expected = sum(f.weight * f.confidence for f in warnings if f.source == "llm")
    llm_worst = sum(f.weight for f in warnings if f.source == "llm")
    readiness, low, high = _clamp(100 - det - llm_expected), _clamp(100 - det - llm_worst), _clamp(100 - det)
    if blockers:
        status = "blocked"
        readiness, low, high = (min(v, BLOCKED_CAP) for v in (readiness, low, high))
    else:
        status = "ready" if readiness >= READY_AT else "needs-work"
    return {"status": status, "readiness": readiness, "low": low, "high": high,
            "blockers": len(blockers), "warnings": len(warnings)}
