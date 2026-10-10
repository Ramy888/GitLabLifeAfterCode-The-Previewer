import json

import pytest

from store_review.cli import main

AUTH = "name: demo\nversion: 2.1.0\ndependencies:\n  firebase_auth: ^5.0.0\n"
SECRET = "hunter2-very-secret"


@pytest.fixture
def app(make_app):
    return make_app({
        "pubspec.yaml": AUTH,
        "android/app/build.gradle": "targetSdk = 34\n",
        "android/app/src/main/AndroidManifest.xml": '<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application/></manifest>',
        "lib/profile.dart": "ProfileScreen(providers: p);\n",
    })


def scan(app, tmp_path, monkeypatch, env=None):
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    out = tmp_path / "findings.json"
    assert main(["scan", "--app", str(app), "--out", str(out), "--report", str(tmp_path / "report.md")]) == 0
    return out, json.loads(out.read_text())


def test_scan_writes_schema_scores_and_inputs(app, tmp_path, monkeypatch):
    monkeypatch.delenv("STORE_REVIEW_DEMO_LOGIN", raising=False)
    _, doc = scan(app, tmp_path, monkeypatch)
    assert doc["schema"] == "store-review/findings@1"
    assert doc["app"] == {"name": "demo", "version": "2.1.0"}
    assert {f["id"] for f in doc["findings"]} >= {"AND-TARGETSDK", "SHR-DEMO-LOGIN", "SHR-PRIVACY-URL", "AND-DELETION-URL"}
    assert doc["scores"]["android"]["status"] == "blocked" and doc["scores"]["ios"]["status"] == "blocked"
    keys = {i["key"] for i in doc["inputs_required"]}
    assert keys == {"STORE_REVIEW_DEMO_LOGIN", "privacy_policy_url", "account_deletion_url"}
    report = (tmp_path / "report.md").read_text()
    assert "AND-TARGETSDK" in report and "Readiness 40" in report


def test_no_secret_value_anywhere(app, tmp_path, monkeypatch, capsys):
    out, doc = scan(app, tmp_path, monkeypatch, env={"STORE_REVIEW_DEMO_LOGIN": SECRET})
    assert "SHR-DEMO-LOGIN" not in {f["id"] for f in doc["findings"]}
    assert main(["handoff", "--findings", str(out)]) == 0
    printed = capsys.readouterr().out
    for text in (out.read_text(), (tmp_path / "report.md").read_text(), printed):
        assert SECRET not in text


def test_handoff_lists_only_handoff_items(app, tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("STORE_REVIEW_DEMO_LOGIN", raising=False)
    out, _ = scan(app, tmp_path, monkeypatch)
    capsys.readouterr()
    assert main(["handoff", "--findings", str(out)]) == 0
    text = capsys.readouterr().out
    assert "STORE_REVIEW_DEMO_LOGIN" in text and "privacy_policy_url" in text
    assert "AND-TARGETSDK" not in text  # auto-fixable, not a human input
    assert "@store-review resume" in text


def llm_finding(**over):
    d = {"id": "LLM-4.2", "store": "ios", "layer": "reviewer", "guideline": "Apple 4.2 Minimum Functionality",
         "title": "Thin feature set", "severity": "warning", "weight": 8, "source": "llm", "confidence": 0.5,
         "evidence": [{"path": "lib/src/app.dart", "line": 1, "detail": "two screens"}],
         "fix": {"kind": "manual", "recipe": "Explain the value in reviewer notes"}}
    d.update(over)
    return d


def test_merge_adds_llm_findings_and_rescores(app, tmp_path, monkeypatch):
    out, before = scan(app, tmp_path, monkeypatch, env={"STORE_REVIEW_DEMO_LOGIN": "x"})
    llm = tmp_path / "llm.json"
    llm.write_text(json.dumps({"findings": [llm_finding()]}))
    assert main(["merge", "--findings", str(out), "--llm", str(llm)]) == 0
    after = json.loads(out.read_text())
    assert len(after["findings"]) == len(before["findings"]) + 1


def test_merge_rejects_missing_evidence(app, tmp_path, monkeypatch):
    out, _ = scan(app, tmp_path, monkeypatch)
    llm = tmp_path / "llm.json"
    llm.write_text(json.dumps({"findings": [llm_finding(evidence=[])]}))
    assert main(["merge", "--findings", str(out), "--llm", str(llm)]) == 2


def test_merge_rejects_non_llm_source(app, tmp_path, monkeypatch):
    out, _ = scan(app, tmp_path, monkeypatch)
    llm = tmp_path / "llm.json"
    llm.write_text(json.dumps({"findings": [llm_finding(source="deterministic")]}))
    assert main(["merge", "--findings", str(out), "--llm", str(llm)]) == 2
