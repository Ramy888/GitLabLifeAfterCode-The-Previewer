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
            need = need["job"] if isinstance(need, dict) else need
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
        assert any("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME" in r for r in rules)
        assert any("CI_COMMIT_MESSAGE" in r for r in rules)  # the release merge on the default branch
    assert "review:inputs" in cfg["package:stores"]["needs"]
    assert any("merge_request_event" in r["if"] for r in cfg["workflow"]["rules"])


def test_merging_a_release_mr_publishes_the_release():
    import re
    cfg = config()
    rule = cfg["release:gitlab"]["rules"][0]["if"]
    assert "$CI_DEFAULT_BRANCH" in rule
    regex = rule.split("=~", 1)[1].strip().strip("/").replace("\\/", "/")
    assert re.search(regex, "Merge branch 'store-review/2.1.1' into 'main'\n\nStore release 2.1.1")
    assert not re.search(regex, "Merge branch 'store-review-fix/and-targetsdk' into 'main'")
    release = cfg["release:gitlab"]["release"]
    assert release["tag_name"] == "v$RELEASE_VERSION" and release["ref"] == "$CI_COMMIT_SHA"
    assert {"package:stores", "review:scan"} <= {n if isinstance(n, str) else n["job"] for n in cfg["release:gitlab"]["needs"]}


def test_flow_branches_skip_push_pipelines():
    cfg = config()
    never = [r["if"] for r in cfg["workflow"]["rules"] if r.get("when") == "never"]
    assert any("store-review(-fix)?" in r for r in never)


def test_fixer_branches_do_not_trigger_release_jobs():
    import re
    cfg = config()
    for job in ("review:inputs", "package:stores"):
        pattern = next(r["if"] for r in cfg[job]["rules"] if "store-review" in r["if"])
        regex = pattern.split("=~", 1)[1].strip().strip("/").replace("\\/", "/")
        assert re.search(regex, "store-review/2.1.0")
        assert not re.search(regex, "store-review-fix/and-targetsdk")
        assert not re.search(regex, "store-review/fix-and-targetsdk")


def test_package_loop_distinguishes_blocked_from_broken():
    script = " ".join(config()["package:stores"]["script"])
    assert "broken" in script and "exit 1" in script and "exit 4" in script


def test_release_links_the_aab():
    links = config()["release:gitlab"]["release"]["assets"]["links"]
    assert any("app-release.aab" in link["url"] for link in links)


def test_deploy_and_release_are_never_auto_cancelled():
    # default: interruptible: true lets a new push cancel older pipelines; a half-done deploy or release must finish.
    cfg = config()
    assert cfg["default"]["interruptible"] is True
    for job in ("deploy:cloudrun", "release:gitlab"):
        assert cfg[job].get("interruptible") is False, job
