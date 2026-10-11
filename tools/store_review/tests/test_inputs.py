import json

from store_review.cli import main
from store_review.inputs import validate_inputs
from store_review.snapshot import load_snapshot

INPUTS = [
    {"key": "STORE_REVIEW_DEMO_LOGIN", "kind": "ci_variable", "ask": "a", "finding": "SHR-DEMO-LOGIN", "stores": ["ios", "android"]},
    {"key": "privacy_policy_url", "kind": "url", "ask": "b", "finding": "SHR-PRIVACY-URL", "stores": ["ios", "android"]},
    {"key": "account_deletion_url", "kind": "url", "ask": "c", "finding": "AND-DELETION-URL", "stores": ["android"]},
    {"key": "uses_non_exempt_encryption", "kind": "answer", "ask": "d", "finding": "IOS-ENCRYPTION-FLAG", "stores": ["ios"]},
]
LISTING = "privacy_policy_url: https://ex.com/privacy\naccount_deletion_url: https://ex.com/delete\n"
NOTES = "answers:\n  uses_non_exempt_encryption: 'no'\n"


def ok_fetch(url):
    return 200


def test_all_valid(make_app):
    snap = load_snapshot(make_app({"store/listing.yaml": LISTING, "store/review_notes.yaml": NOTES}),
                         env={"STORE_REVIEW_DEMO_LOGIN": "u:p"})
    assert validate_inputs(INPUTS, snap, ok_fetch) == []


def test_each_failure_is_reported_with_reason(make_app):
    snap = load_snapshot(make_app({"store/listing.yaml": "privacy_policy_url: https://ex.com/privacy\n"}), env={})
    fetch = lambda url: 404  # noqa: E731
    problems = {p["key"]: p["problem"] for p in validate_inputs(INPUTS, snap, fetch)}
    assert problems["STORE_REVIEW_DEMO_LOGIN"] == "CI/CD variable is not set"
    assert problems["privacy_policy_url"] == "https://ex.com/privacy returned HTTP 404"
    assert problems["account_deletion_url"] == "not set in store/listing.yaml"
    assert problems["uses_non_exempt_encryption"] == "no yes/no answer in store/review_notes.yaml"


def test_fetch_error_is_a_problem_not_a_crash(make_app):
    snap = load_snapshot(make_app({"store/listing.yaml": LISTING, "store/review_notes.yaml": NOTES}),
                         env={"STORE_REVIEW_DEMO_LOGIN": "u:p"})

    def boom(url):
        raise OSError("dns failure")

    problems = validate_inputs(INPUTS, snap, boom)
    assert {p["key"] for p in problems} == {"privacy_policy_url", "account_deletion_url"}
    assert "dns failure" in problems[0]["problem"]


def test_cli_exit_codes_and_narrowed_checklist(make_app, tmp_path, monkeypatch, capsys):
    app = make_app({"store/listing.yaml": LISTING, "store/review_notes.yaml": NOTES})
    findings = tmp_path / "handoff.json"
    findings.write_text(json.dumps({"inputs_required": INPUTS}))
    monkeypatch.setenv("STORE_REVIEW_DEMO_LOGIN", "u:p")
    monkeypatch.setattr("store_review.inputs.http_status", lambda url: 404 if "delete" in url else 200)
    assert main(["validate-inputs", "--findings", str(findings), "--app", str(app)]) == 3
    out = capsys.readouterr().out
    assert "account_deletion_url" in out and "HTTP 404" in out
    assert "privacy_policy_url" not in out and "u:p" not in out
    monkeypatch.setattr("store_review.inputs.http_status", ok_fetch)
    assert main(["validate-inputs", "--findings", str(findings), "--app", str(app)]) == 0


def test_http_status_returns_error_code(monkeypatch):
    import urllib.error

    from store_review import inputs

    def fake_urlopen(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(inputs.urllib.request, "urlopen", fake_urlopen)
    assert inputs.http_status("https://ex.com/missing") == 404


def test_required_inputs_derived_from_app_even_after_answers(make_app):
    from store_review.inputs import required_inputs

    auth = "name: demo\nversion: 1.0.0\ndependencies:\n  firebase_auth: ^5.0.0\n"
    files = {"pubspec.yaml": auth, "store/listing.yaml": LISTING,
             "android/app/src/main/AndroidManifest.xml": '<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application/></manifest>'}
    snap = load_snapshot(make_app(files), env={"STORE_REVIEW_DEMO_LOGIN": "u:p"})
    keys = {i["key"] for i in required_inputs(snap)}
    # Already provided, but still listed so their values get validated.
    assert keys == {"STORE_REVIEW_DEMO_LOGIN", "privacy_policy_url", "account_deletion_url"}
    assert snap.env["STORE_REVIEW_DEMO_LOGIN"] == "u:p"  # the caller's snapshot is not mutated


def test_cli_validate_inputs_without_findings_file(make_app, monkeypatch, capsys):
    auth = "name: demo\nversion: 1.0.0\ndependencies:\n  firebase_auth: ^5.0.0\n"
    app = make_app({"pubspec.yaml": auth, "store/listing.yaml": LISTING})
    monkeypatch.delenv("STORE_REVIEW_DEMO_LOGIN", raising=False)
    monkeypatch.setattr("store_review.inputs.http_status", ok_fetch)
    assert main(["validate-inputs", "--app", str(app)]) == 3
    assert "STORE_REVIEW_DEMO_LOGIN" in capsys.readouterr().out
    monkeypatch.setenv("STORE_REVIEW_DEMO_LOGIN", "u:p")
    assert main(["validate-inputs", "--app", str(app)]) == 0


def test_skip_ci_variables_for_flow_runtime(make_app, monkeypatch, capsys):
    auth = "name: demo\nversion: 1.0.0\ndependencies:\n  firebase_auth: ^5.0.0\n"
    app = make_app({"pubspec.yaml": auth, "store/listing.yaml": LISTING})
    monkeypatch.delenv("STORE_REVIEW_DEMO_LOGIN", raising=False)
    monkeypatch.setattr("store_review.inputs.http_status", ok_fetch)
    assert main(["validate-inputs", "--app", str(app), "--skip-ci-variables"]) == 0
    assert "checked by the release pipeline" in capsys.readouterr().out


def test_validate_inputs_retry_line_uses_the_configured_mention(make_app, monkeypatch, capsys):
    app = make_app({"pubspec.yaml": "name: demo\nversion: 1.0.0\n", "store/listing.yaml": ""})
    monkeypatch.setattr("store_review.inputs.http_status", ok_fetch)
    monkeypatch.setenv("STORE_REVIEW_MENTION", "@ai-from-env")
    assert main(["validate-inputs", "--app", str(app), "--skip-ci-variables"]) == 3
    out = capsys.readouterr().out
    assert "`@ai-from-env resume`" in out and "@store-review resume" not in out


def _unreachable(url):
    import urllib.error

    raise urllib.error.URLError("Tunnel connection failed: 403 Forbidden")


def test_flow_session_defers_unreachable_urls_to_the_release_pipeline(make_app, monkeypatch, capsys):
    # Duo flow sessions reach the internet through a proxy that may refuse the app's host.
    app = make_app({"pubspec.yaml": "name: demo\nversion: 1.0.0\n", "store/listing.yaml": LISTING})
    monkeypatch.setattr("store_review.inputs.http_status", _unreachable)
    assert main(["validate-inputs", "--app", str(app), "--skip-ci-variables"]) == 0
    out = capsys.readouterr().out
    assert "privacy_policy_url" in out and "could not reach" in out and "release pipeline" in out


def test_flow_session_still_fails_on_a_real_http_error(make_app, monkeypatch, capsys):
    app = make_app({"pubspec.yaml": "name: demo\nversion: 1.0.0\n", "store/listing.yaml": LISTING})
    monkeypatch.setattr("store_review.inputs.http_status", lambda url: 404)
    assert main(["validate-inputs", "--app", str(app), "--skip-ci-variables"]) == 3
    assert "HTTP 404" in capsys.readouterr().out


def test_pipeline_mode_fails_on_unreachable_urls(make_app, monkeypatch, capsys):
    app = make_app({"pubspec.yaml": "name: demo\nversion: 1.0.0\n", "store/listing.yaml": LISTING})
    monkeypatch.setattr("store_review.inputs.http_status", _unreachable)
    assert main(["validate-inputs", "--app", str(app)]) == 3
    assert "could not be fetched" in capsys.readouterr().out
