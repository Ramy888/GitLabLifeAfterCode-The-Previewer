import json

from store_review.cli import main
from store_review.notify import render_release_email


def doc(ios_status="ready", ios_blockers=0, extra=()):
    finding = {"id": "LLM-IOS-SUPPORT", "store": "ios", "layer": "reviewer", "guideline": "Apple 1.5",
               "title": "Only contact is <a GitLab issue>", "severity": "warning", "weight": 6, "source": "llm",
               "confidence": 0.8, "evidence": [{"path": "deploy/legal/privacy.html"}], "fix": {"kind": "manual", "recipe": "x"}}
    return {"schema": "findings@1", "app": {"name": "Time Tracker", "version": "2.1.1"},
            "scores": {"ios": {"status": ios_status, "readiness": 95 if ios_status == "ready" else 40, "low": 91, "high": 100,
                               "blockers": ios_blockers, "warnings": 2},
                       "android": {"status": "ready", "readiness": 91, "low": 84, "high": 100, "blockers": 0, "warnings": 4}},
            "benchmark": {"cases": 42, "precision": 0.971, "recall": 0.971},
            "findings": [finding, *extra]}


URL = "https://gitlab.com/g/p/-/releases/v2.1.1"


def test_subject_and_text_carry_the_outcome():
    subject, text, _ = render_release_email(doc(), URL)
    assert subject == "Time Tracker v2.1.1 is ready to submit · iOS 95 · Android 91"
    assert "Apple App Store: ready, readiness 95 (91–100), 0 blockers, 2 warnings" in text
    assert URL in text and "Nothing was uploaded to any store" in text


def test_html_shows_both_stores_the_release_button_and_escapes_findings():
    _, _, html = render_release_email(doc(), URL)
    for needle in ("Apple App Store", "Google Play", ">95<", ">91<", "91–100", "84–100", f'href="{URL}"', "Ready to submit"):
        assert needle in html, needle
    assert "&lt;a GitLab issue&gt;" in html and "<a GitLab issue>" not in html
    assert "<table" in html and "<style" not in html  # inline styles only: Gmail strips style blocks
    assert '<meta charset="utf-8">' in html  # the copy uses · and – ; without it clients guess Latin-1


def test_a_blocked_store_changes_the_headline():
    subject, _, html = render_release_email(doc(ios_status="blocked", ios_blockers=1), URL)
    assert subject.startswith("Time Tracker v2.1.1 needs work")
    assert "Blocked" in html and "Ready to submit" not in html


def test_lists_at_most_five_findings_most_severe_first():
    extra = [dict(doc()["findings"][0], id=f"W{i}", severity="warning") for i in range(6)]
    extra.append(dict(doc()["findings"][0], id="B1", severity="blocker"))
    _, _, html = render_release_email(doc(extra=extra), URL)
    assert html.index("B1") < html.index("W0")
    assert sum(html.count(f"W{i}") for i in range(6)) + html.count("LLM-IOS-SUPPORT") == 4
    assert "and 3 more in the report" in html


def test_cli_writes_a_preview_without_sending(tmp_path, monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_EMAIL_TOKEN", raising=False)
    findings = tmp_path / "findings.json"
    findings.write_text(json.dumps(doc()))
    out = tmp_path / "email.html"
    assert main(["notify", "--findings", str(findings), "--release-url", URL, "--html-out", str(out)]) == 0
    assert "Google Play" in out.read_text()
