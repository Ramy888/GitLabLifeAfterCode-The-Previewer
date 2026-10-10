"""Command-line entry point: store-review <command>."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from store_review import inputs
from store_review.benchmark import run_benchmark
from store_review.model import SchemaError
from store_review.package import PackageBlocked, write_package
from store_review.report import DEFAULT_MENTION, app_info, build_document, merge_llm, render_handoff, render_markdown
from store_review.rules import run_checks
from store_review.snapshot import load_snapshot

EXIT_SCHEMA = 2
EXIT_INPUTS = 3
EXIT_BLOCKED = 4
EXIT_BENCHMARK = 5
DEFAULT_CORPUS = Path(__file__).resolve().parent.parent / "corpus"


def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _write_json(path: str, doc: dict) -> None:
    Path(path).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def cmd_scan(args: argparse.Namespace) -> int:
    snap = load_snapshot(args.app)
    benchmark = _read_json(args.benchmark) if args.benchmark else None
    doc = build_document(app_info(snap), run_checks(snap), benchmark)
    _write_json(args.out, doc)
    if args.report:
        Path(args.report).write_text(render_markdown(doc))
    for store in ("ios", "android"):
        s = doc["scores"][store]
        print(f"{store}: {s['status']} readiness {s['readiness']} ({s['low']}-{s['high']}), {s['blockers']} blockers")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    try:
        doc = merge_llm(_read_json(args.findings), _read_json(args.llm))
    except (SchemaError, json.JSONDecodeError) as err:
        print(f"merge rejected: {err}", file=sys.stderr)
        return EXIT_SCHEMA
    _write_json(args.findings, doc)
    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    mention = args.mention or os.environ.get("STORE_REVIEW_MENTION") or DEFAULT_MENTION
    print(render_handoff(_read_json(args.findings), mention), end="")
    return 0


def cmd_validate_inputs(args: argparse.Namespace) -> int:
    snap = load_snapshot(args.app)
    items = _read_json(args.findings).get("inputs_required", []) if args.findings else inputs.required_inputs(snap)
    if args.skip_ci_variables:
        # Duo flow sessions do not see project CI/CD variables; the release pipeline (review:inputs) checks them.
        items = [i for i in items if i["kind"] != "ci_variable"]
    problems = inputs.validate_inputs(items, snap, inputs.http_status)
    if not problems:
        print("All inputs are in place. Resuming the review.")
        if args.skip_ci_variables:
            print("CI/CD variables are checked by the release pipeline.")
        return 0
    print("### Still missing")
    print()
    for p in problems:
        print(f"- [ ] **{p['key']}**: {p['problem']}. {p['ask']}.")
    print()
    print("Fix these, then comment `@store-review resume` again.")
    return EXIT_INPUTS


def cmd_package(args: argparse.Namespace) -> int:
    try:
        d = write_package(load_snapshot(args.app), _read_json(args.findings), args.store, Path(args.out))
    except PackageBlocked as err:
        print(f"package refused: {err}", file=sys.stderr)
        return EXIT_BLOCKED
    print(f"wrote {d}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    result = run_benchmark(args.corpus)
    if args.out:
        _write_json(args.out, result)
    print(f"{result['cases']} cases: precision {result['precision']:.3f}, recall {result['recall']:.3f} "
          f"(tp {result['tp']}, fp {result['fp']}, fn {result['fn']})")
    for m in result["misses"]:
        print(f"  {m['case']}: missed {m['missed']} extra {m['extra']}")
    if result["precision"] < args.min_precision or result["recall"] < args.min_recall:
        print(f"benchmark below threshold (precision >= {args.min_precision}, recall >= {args.min_recall})", file=sys.stderr)
        return EXIT_BENCHMARK
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="store-review", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    p = sub.add_parser("scan", help="Review the app and write findings.json")
    p.add_argument("--app", default=".", help="Flutter app root")
    p.add_argument("--out", default="findings.json")
    p.add_argument("--report", help="Also write a Markdown report here")
    p.add_argument("--benchmark", help="benchmark.json to show next to the score")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("merge", help="Merge reviewer-agent findings into findings.json")
    p.add_argument("--findings", default="findings.json")
    p.add_argument("--llm", required=True, help="JSON file with {'findings': [...]} from the reviewer agents")
    p.set_defaults(func=cmd_merge)

    p = sub.add_parser("handoff", help="Print the checklist of inputs only a human can provide")
    p.add_argument("--findings", default="findings.json")
    p.add_argument("--mention", help="The flow's service account, e.g. @ai-store-review-mygroup (default: $STORE_REVIEW_MENTION)")
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("validate-inputs", help="Check the human's inputs before resuming")
    p.add_argument("--findings", help="findings.json from the run that posted the handoff (default: derive from the app)")
    p.add_argument("--app", default=".")
    p.add_argument("--skip-ci-variables", action="store_true",
                   help="Do not check CI/CD variables (use inside a Duo flow session, which cannot see them)")
    p.set_defaults(func=cmd_validate_inputs)

    p = sub.add_parser("package", help="Write the ready-to-submit package for one store")
    p.add_argument("--store", required=True, choices=["ios", "android"])
    p.add_argument("--findings", default="findings.json")
    p.add_argument("--app", default=".")
    p.add_argument("--out", default="dist/store-package")
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("benchmark", help="Score the deterministic rules against the Rejection Corpus")
    p.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    p.add_argument("--out", help="Write benchmark.json here")
    p.add_argument("--min-precision", type=float, default=0.90)
    p.add_argument("--min-recall", type=float, default=0.85)
    p.set_defaults(func=cmd_benchmark)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
