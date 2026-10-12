"""findings.json document, Markdown report and the human handoff checklist."""

from __future__ import annotations

from datetime import datetime, timezone

from store_review.model import SCHEMA, SchemaError, Finding, finding_from_dict, finding_to_dict
from store_review.rules import rule_meta
from store_review.score import score_store
from store_review.snapshot import AppSnapshot

STORES = {"ios": "Apple App Store", "android": "Google Play"}
DEFAULT_MENTION = "@<flow service account>"


def _input_for(f: Finding) -> dict | None:
    if f.fix.kind != "handoff":
        return None
    try:
        spec = rule_meta(f.id)[1].get("input")
    except KeyError:
        spec = None
    spec = spec or {"key": f.id, "kind": "answer", "ask": f.fix.recipe}
    stores = ["ios", "android"] if f.store == "shared" else [f.store]
    return {**spec, "finding": f.id, "stores": stores}


def inputs_required(findings: list[Finding]) -> list[dict]:
    seen, out = set(), []
    for f in findings:
        item = _input_for(f)
        if item and item["key"] not in seen:
            seen.add(item["key"])
            out.append(item)
    return out


def build_document(app: dict, findings: list[Finding], benchmark: dict | None = None) -> dict:
    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "app": app,
        "findings": [finding_to_dict(f) for f in findings],
        "inputs_required": inputs_required(findings),
        "scores": {store: score_store(findings, store) for store in STORES},
        "benchmark": benchmark,
    }


def app_info(snap: AppSnapshot) -> dict:
    """The name reviewers and users see: the store listing's, falling back to the pubspec package name."""
    listing = snap.store["listing"]
    listed = [(listing.get(store) or {}).get("name") for store in ("ios", "android")]
    return {"name": next((n for n in listed if n), snap.name), "version": snap.version}


def load_findings(doc: dict) -> list[Finding]:
    if doc.get("schema") != SCHEMA:
        raise SchemaError(f"schema must be {SCHEMA}")
    return [finding_from_dict(d) for d in doc["findings"]]


def merge_llm(doc: dict, llm_doc: dict) -> dict:
    """Add reviewer-agent findings. Re-merging the same IDs replaces them, so retries never double-count."""
    if not isinstance(llm_doc, dict) or not isinstance(llm_doc.get("findings", []), list):
        raise SchemaError("llm file must be {'findings': [...]}")
    incoming = [finding_from_dict(d) for d in llm_doc.get("findings", [])]
    for f in incoming:
        if f.source != "llm":
            raise SchemaError(f"{f.id}: merged findings must have source 'llm'")
    replaced = {f.id for f in incoming}
    findings = [f for f in load_findings(doc) if not (f.source == "llm" and f.id in replaced)] + incoming
    return build_document(doc["app"], findings, doc.get("benchmark"))


def _count(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def headline(store: str, doc: dict) -> str:
    s = doc["scores"][store]
    passed = "" if s["status"] != "ready" else " · ready to package"
    line = (f"Readiness {s['readiness']} ({s['low']}–{s['high']}) · {_count(s['warnings'], 'warning')} · "
            f"{_count(s['blockers'], 'blocker')}{passed}")
    b = doc.get("benchmark")
    if b:
        line += f" · recall {b['recall']:.2f} on {b['cases']} seeded cases"
    return line


def render_markdown(doc: dict) -> str:
    lines = [f"# Store review: {doc['app']['name']} {doc['app']['version']}", ""]
    for store, label in STORES.items():
        lines += [f"## {label}: {doc['scores'][store]['status']}", "", headline(store, doc), ""]
        rows = [f for f in doc["findings"] if f["store"] in (store, "shared")]
        if rows:
            lines += ["| Severity | Rule | Finding | Evidence | Guideline |", "|---|---|---|---|---|"]
            for f in sorted(rows, key=lambda f: ("blocker", "warning", "info").index(f["severity"])):
                ev = f["evidence"][0]
                where = f"`{ev['path']}`" + (f":{ev['line']}" if ev.get("line") else "")
                lines.append(f"| {f['severity']} | {f['id']} | {f['title']} | {where} | {f['guideline']} |")
            lines.append("")
    return "\n".join(lines)


def render_handoff(doc: dict, mention: str = DEFAULT_MENTION) -> str:
    items = doc["inputs_required"]
    manual = [f for f in doc["findings"] if f["severity"] == "blocker" and f["fix"]["kind"] == "manual"]
    if not items and not manual:
        return "Nothing needed from you. The review can finish on its own.\n"
    lines = []
    if manual:
        lines += ["### Fixes only you can make", ""]
        for f in manual:
            ev = f["evidence"][0]
            where = f"`{ev['path']}`" + (f":{ev['line']}" if ev.get("line") else "")
            lines.append(f"- [ ] **{f['id']}** ({where}): {f['fix']['recipe']}.")
        lines.append("")
    if not items:
        lines.append(f"When these are merged, comment `{mention} resume`.")
        return "\n".join(lines) + "\n"
    lines += ["### I need these from you to continue", ""]
    for item in items:
        if item["kind"] == "ci_variable":
            # Flow sessions cannot see CI/CD variables, so ask for confirmation; the release pipeline checks it.
            where = ("Tick this if it is already set; otherwise add it in Settings > CI/CD > Variables (masked). "
                     "The release pipeline checks it")
        else:
            where = "Put it in " + {"url": "`store/listing.yaml`", "answer": "a reply on this issue"}[item["kind"]]
        lines.append(f"- [ ] **{item['key']}**: {item['ask']}. {where}. "
                     f"Needed for: {', '.join(STORES[s] for s in item['stores'])}.")
    lines += ["", f"When everything is in place, comment `{mention} resume`.",
              "Never paste passwords into this issue. I only check that the variable exists."]
    return "\n".join(lines) + "\n"
