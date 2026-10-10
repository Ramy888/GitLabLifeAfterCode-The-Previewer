"""SPEC criterion 10: the pipeline defines the jobs the flow relies on."""

from pathlib import Path

import yaml

CI = Path(__file__).resolve().parents[3] / ".gitlab-ci.yml"
REQUIRED = {"engine:test", "flutter:test", "build:web", "build:android", "review:scan", "review:benchmark",
            "review:inputs", "package:stores", "deploy:cloudrun"}


def config():
    return yaml.safe_load(CI.read_text())


def test_required_jobs_exist():
    assert REQUIRED <= set(config())


def test_every_job_stage_is_declared_and_needs_exist():
    cfg = config()
    stages = set(cfg["stages"])
    jobs = {k: v for k, v in cfg.items() if isinstance(v, dict) and "script" in v and not k.startswith(".")}
    for name, job in jobs.items():
        assert job.get("stage") in stages, name
        for need in job.get("needs", []):
            assert need in jobs, f"{name} needs missing job {need}"


def test_review_artifacts_and_manual_protected_deploy():
    cfg = config()
    assert {"findings.json", "review-report.md", "handoff.md"} <= set(cfg["review:scan"]["artifacts"]["paths"])
    assert cfg["review:benchmark"]["artifacts"]["paths"] == ["benchmark.json"]
    (rule,) = cfg["deploy:cloudrun"]["rules"]
    assert rule["when"] == "manual" and "CI_DEFAULT_BRANCH" in rule["if"]


def test_no_secret_values_in_pipeline():
    text = CI.read_text()
    for marker in ("password=", "BEGIN PRIVATE KEY", "apiKey:"):
        assert marker not in text


def test_release_branches_validate_inputs_then_package():
    cfg = config()
    for job in ("review:inputs", "package:stores"):
        rules = [r["if"] for r in cfg[job]["rules"]]
        assert any("store-review" in r for r in rules) and any("CI_COMMIT_TAG" in r for r in rules)
    assert "review:inputs" in cfg["package:stores"]["needs"]
    assert any("merge_request_event" in r["if"] for r in cfg["workflow"]["rules"])
