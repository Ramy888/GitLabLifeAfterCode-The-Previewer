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
    assert "@<flow service account> resume" in text


def test_handoff_mention_from_flag_and_env(app, tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("STORE_REVIEW_DEMO_LOGIN", raising=False)
    out, _ = scan(app, tmp_path, monkeypatch)
    capsys.readouterr()
    assert main(["handoff", "--findings", str(out), "--mention", "@ai-store-review-acme"]) == 0
    assert "`@ai-store-review-acme resume`" in capsys.readouterr().out
    monkeypatch.setenv("STORE_REVIEW_MENTION", "@ai-from-env")
    assert main(["handoff", "--findings", str(out)]) == 0
    assert "`@ai-from-env resume`" in capsys.readouterr().out


def test_handoff_lists_manual_blockers_with_recipes(make_app, tmp_path, monkeypatch, capsys):
    root = make_app({"android/app/build.gradle": "android {\n  buildTypes {\n    release {\n      signingConfig = signingConfigs.debug\n    }\n  }\n}\n",
                     "store/listing.yaml": "privacy_policy_url: https://e.com/p\n"})
    out, _ = scan(root, tmp_path, monkeypatch)
    capsys.readouterr()
    assert main(["handoff", "--findings", str(out)]) == 0
    text = capsys.readouterr().out
    assert "Fixes only you can make" in text and "AND-DEBUG-SIGNING" in text and "upload key" in text


def test_headline_pluralises(app, tmp_path, monkeypatch):
    from store_review.report import headline
    doc = {"scores": {"ios": {"status": "ready", "readiness": 96, "low": 96, "high": 96, "blockers": 0, "warnings": 1}},
           "benchmark": None}
    assert "1 warning ·" in headline("ios", doc) and "0 blockers" in headline("ios", doc)


def app_version(app):
    from store_review.snapshot import load_snapshot

    return load_snapshot(app).version


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


def test_merge_is_idempotent(app, tmp_path, monkeypatch):
    out, before = scan(app, tmp_path, monkeypatch, env={"STORE_REVIEW_DEMO_LOGIN": "x"})
    llm = tmp_path / "llm.json"
    llm.write_text(json.dumps({"findings": [llm_finding()]}))
    for _ in range(2):
        assert main(["merge", "--findings", str(out), "--llm", str(llm)]) == 0
    after = json.loads(out.read_text())
    assert [f["id"] for f in after["findings"]].count("LLM-4.2") == 1


def test_merge_bad_json_returns_schema_exit(app, tmp_path, monkeypatch):
    out, _ = scan(app, tmp_path, monkeypatch)
    llm = tmp_path / "llm.json"
    llm.write_text("{not json")
    assert main(["merge", "--findings", str(out), "--llm", str(llm)]) == 2


def test_handoff_asks_to_confirm_ci_variables_instead_of_calling_them_missing(app, tmp_path, monkeypatch, capsys):
    # A flow session cannot see CI/CD variables, so the handoff must not claim one is missing.
    out, _ = scan(app, tmp_path, monkeypatch)
    capsys.readouterr()
    assert main(["handoff", "--findings", str(out)]) == 0
    text = capsys.readouterr().out
    demo = next(line for line in text.splitlines() if "STORE_REVIEW_DEMO_LOGIN" in line)
    assert "already set" in demo and "Put it in" not in demo
    privacy = next(line for line in text.splitlines() if "**privacy_policy_url**" in line)
    assert "Put it in `store/listing.yaml`" in privacy


def test_scan_merges_committed_judgement_into_scores_and_report(app, tmp_path, monkeypatch):
    # The release MR carries the reviewer agents' judgement, so CI scores include it.
    _, before = scan(app, tmp_path, monkeypatch, env={"STORE_REVIEW_DEMO_LOGIN": "x"})
    review = app / "store/review"
    review.mkdir(parents=True)
    blocker = llm_finding(id="LLM-IOS-FOREIGN-ID", severity="blocker", confidence=0.8, title="Foreign App Store ID")
    (review / "judgement.ios.json").write_text(json.dumps({"version": app_version(app), "findings": [blocker]}))
    _, after = scan(app, tmp_path, monkeypatch, env={"STORE_REVIEW_DEMO_LOGIN": "x"})
    assert "LLM-IOS-FOREIGN-ID" in [f["id"] for f in after["findings"]]
    assert after["scores"]["ios"]["blockers"] == before["scores"]["ios"]["blockers"] + 1
    assert after["scores"]["ios"]["status"] == "blocked"
    assert "LLM-IOS-FOREIGN-ID" in (tmp_path / "report.md").read_text()


def test_scan_rejects_a_malformed_judgement_file(app, tmp_path, monkeypatch, capsys):
    review = app / "store/review"
    review.mkdir(parents=True)
    bad = {"version": app_version(app), "findings": [llm_finding(source="rule")]}
    (review / "judgement.android.json").write_text(json.dumps(bad))
    out = tmp_path / "findings.json"
    assert main(["scan", "--app", str(app), "--out", str(out)]) == 2
    assert "judgement.android.json" in capsys.readouterr().err


def test_scan_ignores_judgement_left_from_another_release(app, tmp_path, monkeypatch, capsys):
    # After a release merges, its judgement stays on main; the next version must not inherit it.
    review = app / "store/review"
    review.mkdir(parents=True)
    old = llm_finding(id="LLM-OLD-RELEASE", severity="blocker")
    (review / "judgement.ios.json").write_text(json.dumps({"version": "0.9.0", "findings": [old]}))
    (review / "judgement.android.json").write_text(json.dumps({"findings": [old]}))  # no version: unknown origin
    _, doc = scan(app, tmp_path, monkeypatch, env={"STORE_REVIEW_DEMO_LOGIN": "x"})
    assert "LLM-OLD-RELEASE" not in [f["id"] for f in doc["findings"]]
    out = capsys.readouterr().out
    assert f"skipped store/review/judgement.ios.json (version 0.9.0, app is {app_version(app)})" in out
    assert f"skipped store/review/judgement.android.json (version none, app is {app_version(app)})" in out


def test_scan_matches_judgement_version_without_build_number(make_app, tmp_path, monkeypatch):
    app = make_app({"pubspec.yaml": "name: demo\nversion: 2.1.1+7\n"})
    review = app / "store/review"
    review.mkdir(parents=True)
    (review / "judgement.ios.json").write_text(json.dumps({"version": "2.1.1", "findings": [llm_finding()]}))
    _, doc = scan(app, tmp_path, monkeypatch)
    assert "LLM-4.2" in [f["id"] for f in doc["findings"]]


def test_report_title_uses_the_store_listing_name(make_app, tmp_path, monkeypatch):
    # The Dart package name (pubspec) is not what reviewers or users see; the listing name is.
    app = make_app({"pubspec.yaml": "name: starter_architecture_flutter_firebase\nversion: 2.1.1\n",
                    "store/listing.yaml": "ios:\n  name: Time Tracker\nandroid:\n  name: Time Tracker\n"})
    _, doc = scan(app, tmp_path, monkeypatch)
    assert doc["app"]["name"] == "Time Tracker"
    assert (tmp_path / "report.md").read_text().startswith("# Store review: Time Tracker 2.1.1")


def test_report_title_falls_back_to_the_package_name(make_app, tmp_path, monkeypatch):
    app = make_app({"pubspec.yaml": "name: demo_app\nversion: 1.0.0\n"})
    _, doc = scan(app, tmp_path, monkeypatch)
    assert doc["app"]["name"] == "demo_app"
