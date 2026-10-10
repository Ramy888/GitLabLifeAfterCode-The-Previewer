from store_review.model import Evidence, Finding, Fix
from store_review.score import score_store

EV = (Evidence("x", 1, "y"),)


def f(severity="warning", weight=0, source="deterministic", confidence=1.0, store="ios", rid="R"):
    return Finding(rid, store, "automated", "g", "t", severity, weight, source, confidence, EV, Fix("manual", "r"))


def test_no_findings_is_ready_100():
    assert score_store([], "ios") == {"status": "ready", "readiness": 100, "low": 100, "high": 100, "blockers": 0, "warnings": 0}


def test_blocker_caps_at_40():
    s = score_store([f("blocker"), f("warning", 5)], "ios")
    assert s["status"] == "blocked" and s["readiness"] == 40 and s["high"] == 40 and s["low"] <= 40
    assert s["blockers"] == 1


def test_warnings_exact_arithmetic():
    s = score_store([f("warning", 5), f("warning", 4), f("info", 9)], "ios")
    assert (s["readiness"], s["low"], s["high"], s["status"]) == (91, 91, 91, "ready")


def test_llm_confidence_makes_band():
    s = score_store([f("warning", 4), f("warning", 10, "llm", 0.5)], "ios")
    assert (s["readiness"], s["low"], s["high"]) == (91, 86, 96)


def test_needs_work_below_80():
    s = score_store([f("warning", 8)] * 3, "ios")
    assert (s["readiness"], s["status"]) == (76, "needs-work")


def test_shared_findings_count_for_both_stores_and_other_store_ignored():
    findings = [f("blocker", store="shared"), f("warning", 5, store="android")]
    assert score_store(findings, "ios")["blockers"] == 1
    assert score_store(findings, "ios")["warnings"] == 0
    assert score_store(findings, "android")["warnings"] == 1


def test_llm_blocker_also_blocks():
    assert score_store([f("blocker", source="llm", confidence=0.6, store="android")], "android")["status"] == "blocked"


def test_clamped_at_zero():
    assert score_store([f("warning", 8)] * 20, "ios")["low"] == 0
