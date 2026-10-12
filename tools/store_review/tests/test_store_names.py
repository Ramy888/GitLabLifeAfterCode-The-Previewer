"""Everything the product displays names the stores generically ("iOS store", "Android store").

The hackathon bans third-party trademarks in the demo video, and GitLab's advice (2026-10-13) was to use generic
wording. Store names reach the screen through the issue report, the Release notes, the email and the packages, so
this guards every displayed string the engine owns. Source URLs are links, not displayed text, and are not checked.
"""

import re
from pathlib import Path

from store_review.notify import render_release_email
from store_review.package import CONSOLE_STEPS
from store_review.report import STORES, build_document, render_handoff, render_markdown
from store_review.rules import all_rule_ids, rule_meta, run_checks
from store_review.snapshot import load_snapshot

BRANDS = re.compile(r"\b(Apple|Google|App Store|Play Store|Play Console|Play)\b")
REPO = Path(__file__).resolve().parents[3]


def displayed(meta: dict) -> list[str]:
    return [meta["guideline"], meta["fix"]["recipe"]]


def test_store_labels_are_generic():
    assert STORES == {"ios": "iOS store", "android": "Android store"}


def test_rule_packs_cite_guidelines_without_brand_names():
    hits = [(rid, text) for rid in all_rule_ids() for text in displayed(rule_meta(rid)[1]) if BRANDS.search(text)]
    assert hits == []


def test_console_steps_are_generic():
    assert [s for steps in CONSOLE_STEPS.values() for s in steps if BRANDS.search(s)] == []


def test_report_handoff_and_email_are_generic_for_every_rule_that_fires():
    # the live app plus every corpus case: between them every check fires, so every finding title is rendered
    apps = [REPO] + [case / "app" for case in sorted((REPO / "tools/store_review/corpus").iterdir()) if (case / "app").is_dir()]
    findings = [f for app in apps for f in run_checks(load_snapshot(app, env={}))]
    assert {f.id for f in findings} >= {rid for rid in all_rule_ids() if not rid.startswith("SHR-DEMO")}
    doc = build_document({"name": "Time Tracker", "version": "2.1.2"}, findings)
    subject, text, html = render_release_email(doc, "https://gitlab.com/g/p/-/releases/v2.1.2")
    for name, out in [("report", render_markdown(doc)), ("handoff", render_handoff(doc)),
                      ("subject", subject), ("text", text), ("html", html)]:
        assert not BRANDS.search(out), (name, BRANDS.search(out))
