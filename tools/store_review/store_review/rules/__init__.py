"""Rule packs and the check runner."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import cache
from importlib import resources

import yaml

from store_review.model import Evidence, Finding, Fix
from store_review.snapshot import AppSnapshot

PACKS = ("ios", "android", "shared")


@dataclass(frozen=True)
class Hit:
    """One rule violation found by a check, before rule-pack metadata is attached."""

    title: str
    evidence: list[Evidence]
    params: dict = field(default_factory=dict)


Check = Callable[[AppSnapshot, dict], Iterator[Hit]]
_CHECKS: dict[str, Check] = {}


def check(rule_id: str) -> Callable[[Check], Check]:
    def register(fn: Check) -> Check:
        _CHECKS[rule_id] = fn
        return fn

    return register


@cache
def load_pack(name: str) -> dict:
    return yaml.safe_load(resources.files("store_review.rules").joinpath(f"{name}.yaml").read_text())


def rule_meta(rule_id: str) -> tuple[str, dict]:
    for name in PACKS:
        pack = load_pack(name)
        if rule_id in pack["rules"]:
            return pack["store"], pack["rules"][rule_id]
    raise KeyError(rule_id)


def all_rule_ids() -> list[str]:
    return [rid for name in PACKS for rid in load_pack(name)["rules"]]


def _finding(rule_id: str, hit: Hit) -> Finding:
    store, meta = rule_meta(rule_id)
    return Finding(
        id=rule_id,
        store=store,
        layer=meta["layer"],
        guideline=meta["guideline"],
        title=hit.title,
        severity=meta["severity"],
        weight=meta["weight"],
        source="deterministic",
        confidence=1.0,
        evidence=tuple(hit.evidence),
        fix=Fix(meta["fix"]["kind"], meta["fix"]["recipe"].format(**hit.params)),
    )


def run_checks(snap: AppSnapshot) -> list[Finding]:
    from store_review.checks import android, ios, shared  # noqa: F401  (registers checks)

    findings = []
    for rule_id in all_rule_ids():
        store, _ = rule_meta(rule_id)
        pack = load_pack(store)
        findings.extend(_finding(rule_id, hit) for hit in _CHECKS[rule_id](snap, pack))
    return findings
