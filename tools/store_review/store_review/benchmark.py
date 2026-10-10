"""Precision and recall of the deterministic rules over the Rejection Corpus."""

from __future__ import annotations

from pathlib import Path

import yaml

from store_review.rules import run_checks
from store_review.snapshot import load_snapshot


def _ratio(num: int, den: int) -> float:
    return round(num / den, 3) if den else 1.0


def run_benchmark(corpus: Path | str) -> dict:
    tp = fp = fn = 0
    misses, n = [], 0
    for case_dir in sorted(Path(corpus).iterdir()):
        meta_path = case_dir / "case.yaml"
        if not meta_path.is_file():
            continue
        n += 1
        meta = yaml.safe_load(meta_path.read_text())
        expected = set(meta.get("expected") or [])
        found = {f.id for f in run_checks(load_snapshot(case_dir / "app", env=meta.get("env") or {}))}
        tp += len(found & expected)
        fp += len(found - expected)
        fn += len(expected - found)
        if found != expected:
            misses.append({"case": case_dir.name, "missed": sorted(expected - found), "extra": sorted(found - expected)})
    return {"cases": n, "precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn),
            "tp": tp, "fp": fp, "fn": fn, "misses": misses}
