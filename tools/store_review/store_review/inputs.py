"""Validate the human's handoff inputs before the review resumes. Never reads or prints secret values beyond presence."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable

from store_review.snapshot import AppSnapshot

Fetch = Callable[[str], int]
ANSWERS = {"yes", "no", "true", "false"}


def http_status(url: str) -> int:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "store-review/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (URL comes from the repo's own listing)
            return resp.status
    except urllib.error.HTTPError as err:
        return err.code


def _check(item: dict, snap: AppSnapshot, fetch: Fetch) -> str | None:
    key, kind = item["key"], item["kind"]
    if kind == "ci_variable":
        return None if snap.env.get(key) else "CI/CD variable is not set"
    if kind == "url":
        url = snap.store["listing"].get(key)
        if not url:
            return "not set in store/listing.yaml"
        try:
            status = fetch(url)
        except Exception as err:  # network errors become a reported problem, not a crash
            return f"{url} could not be fetched ({err})"
        return None if status == 200 else f"{url} returned HTTP {status}"
    answer = str((snap.store["review_notes"].get("answers") or {}).get(key, "")).strip().lower()
    return None if answer in ANSWERS else "no yes/no answer in store/review_notes.yaml"


def validate_inputs(items: list[dict], snap: AppSnapshot, fetch: Fetch | None = None) -> list[dict]:
    fetch = fetch or http_status
    problems = []
    for item in items:
        problem = _check(item, snap, fetch)
        if problem:
            problems.append({**item, "problem": problem})
    return problems
