"""SPEC criterion 11: static checks of the Duo flow against Flow Registry v1 rules (docs/flow_registry/v1.md)."""

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
FLOW = REPO / ".gitlab/duo/flows/store-review.yaml"
AGENT_CONFIG = REPO / ".gitlab/duo/agent-config.yml"
# Tool names copied from ai-assist duo_workflow_service/tools/*.py (2026-10-10).
KNOWN_TOOLS = {
    "run_command", "read_file", "read_files", "create_file_with_contents", "find_files", "mkdir", "edit_file", "list_dir",
    "list_commits", "get_commit", "get_commit_diff", "create_commit", "create_issue", "list_issues", "get_issue",
    "update_issue", "create_issue_note", "list_issue_notes", "get_issue_note", "create_merge_request",
    "get_merge_request", "list_merge_request_diffs", "update_merge_request", "get_pipeline_failing_jobs", "get_job_logs",
    "create_branch",
}
COMPONENT_TYPES = {"AgentComponent", "DeterministicStepComponent", "OneOffComponent", "HumanInputComponent"}
NAME = re.compile(r"^[A-Za-z0-9_]+$")


def flow():
    return yaml.safe_load(FLOW.read_text())


def test_top_level_shape():
    f = flow()
    assert f["version"] == "v1" and f["environment"] == "ambient"
    assert {"components", "prompts", "routers", "flow"} <= set(f)
    assert not {"name", "description", "product_group"} & set(f)  # not allowed for custom flows


def test_components_prompts_and_tools():
    f = flow()
    prompt_ids = {p["prompt_id"] for p in f["prompts"]}
    names = {c["name"] for c in f["components"]}
    for c in f["components"]:
        assert NAME.match(c["name"]), c["name"]
        assert c["type"] in COMPONENT_TYPES
        if c["type"] == "AgentComponent":
            assert c["prompt_id"] in prompt_ids
            assert "response_schema_id" not in c
            for tool in c.get("toolset", []):
                tool_name = tool if isinstance(tool, str) else next(iter(tool))
                assert tool_name in KNOWN_TOOLS, tool_name
            for sub in c.get("subagents", []):
                assert sub["name"] in names
                (owned,) = [x for x in f["components"] if x["name"] == sub["name"]]
                assert owned.get("description"), f"sub-agent {sub['name']} needs a description"


def test_prompts_follow_restrictions():
    for p in flow()["prompts"]:
        assert "model" not in p
        assert "stop" not in p.get("params", {})
        assert p["prompt_template"]["system"].strip() and p["prompt_template"]["user"].strip()


def test_routing_reaches_end_from_entry():
    f = flow()
    names = {c["name"] for c in f["components"]}
    managed = {s["name"] for c in f["components"] for s in c.get("subagents", [])}
    assert f["flow"]["entry_point"] in names - managed
    for r in f["routers"]:
        assert r["from"] in names
        targets = [r["to"]] if "to" in r else list(r["condition"]["routes"].values())
        assert all(t == "end" or t in names for t in targets)
    assert any(r.get("to") == "end" for r in f["routers"])


def test_prompts_never_ask_for_secrets_in_comments():
    text = FLOW.read_text().lower()
    assert "never paste" in text or "never ask" in text
    assert "store_review_demo_login" in text


def test_agent_config_installs_the_engine():
    cfg = yaml.safe_load(AGENT_CONFIG.read_text())
    script = "\n".join(cfg["setup_script"])
    assert "uv" in script and "tools/store_review" in script
