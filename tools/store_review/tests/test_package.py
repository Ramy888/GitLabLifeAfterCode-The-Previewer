import json

from store_review.cli import main

LISTING = """privacy_policy_url: https://ex.com/privacy
account_deletion_url: https://ex.com/delete
ios:
  name: Time Tracker
  subtitle: Track jobs and hours
  description: Track the time you spend on each job.
android:
  name: Time Tracker
  short_description: Track jobs and hours
  description: Track the time you spend on each job.
"""
NOTES = "account_deletion_path: Account > Delete account\nanswers:\n  uses_non_exempt_encryption: 'no'\n"
FILES = ("metadata.json", "reviewer-notes.md", "privacy-answers.json", "release-notes.en.md", "release-notes.ar.md", "checklist.md")


def findings_doc(status):
    scores = {s: {"status": status, "readiness": 40 if status == "blocked" else 88, "low": 80, "high": 90,
                  "blockers": 1 if status == "blocked" else 0, "warnings": 1} for s in ("ios", "android")}
    return {"schema": "store-review/findings@1", "app": {"name": "demo", "version": "2.1.0"}, "findings": [],
            "inputs_required": [], "scores": scores, "benchmark": None}


def run(make_app, tmp_path, store, status="ready", extra=None):
    app = make_app({"store/listing.yaml": LISTING, "store/review_notes.yaml": NOTES, **(extra or {})})
    fj = tmp_path / "findings.json"
    fj.write_text(json.dumps(findings_doc(status)))
    out = tmp_path / "dist"
    code = main(["package", "--store", store, "--findings", str(fj), "--app", str(app), "--out", str(out)])
    return code, out / store


def test_ios_package_files(make_app, tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_REVIEW_DEMO_LOGIN", "reviewer@ex.com:s3cret-pass")
    code, d = run(make_app, tmp_path, "ios")
    assert code == 0
    assert all((d / f).is_file() for f in FILES)
    meta = json.loads((d / "metadata.json").read_text())
    assert meta["name"] == "Time Tracker" and meta["version"] == "2.1.0" and meta["privacy_policy_url"].endswith("/privacy")
    notes = (d / "reviewer-notes.md").read_text()
    assert "Account > Delete account" in notes and "STORE_REVIEW_DEMO_LOGIN" in notes
    for f in FILES:
        assert "s3cret-pass" not in (d / f).read_text()
    assert "App Store Connect" in (d / "checklist.md").read_text()


def test_android_package_has_deletion_url_and_data_safety(make_app, tmp_path):
    code, d = run(make_app, tmp_path, "android",
                  extra={"store/data_safety.yaml": "declared_permissions:\n  - android.permission.CAMERA\n"})
    assert code == 0
    assert json.loads((d / "metadata.json").read_text())["account_deletion_url"].endswith("/delete")
    assert "android.permission.CAMERA" in (d / "privacy-answers.json").read_text()
    assert "Play Console" in (d / "checklist.md").read_text()


def test_release_notes_from_repo_when_present(make_app, tmp_path):
    code, d = run(make_app, tmp_path, "ios", extra={"store/release_notes/2.1.0.en.md": "New: weekly report\n",
                                                    "store/release_notes/2.1.0.ar.md": "جديد: تقرير أسبوعي\n"})
    assert (d / "release-notes.en.md").read_text() == "New: weekly report\n"
    assert "تقرير أسبوعي" in (d / "release-notes.ar.md").read_text()


def test_refuses_while_blocked(make_app, tmp_path, capsys):
    code, d = run(make_app, tmp_path, "android", status="blocked")
    assert code == 4 and not d.exists()
    assert "blocker" in capsys.readouterr().err
