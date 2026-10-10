"""Command-line entry point: store-review <command>."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from store_review.model import SchemaError
from store_review.report import app_info, build_document, merge_llm, render_handoff, render_markdown
from store_review.rules import run_checks
from store_review.snapshot import load_snapshot

EXIT_SCHEMA = 2


def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _write_json(path: str, doc: dict) -> None:
    Path(path).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def cmd_scan(args: argparse.Namespace) -> int:
    snap = load_snapshot(args.app)
    doc = build_document(app_info(snap), run_checks(snap))
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
    except SchemaError as err:
        print(f"merge rejected: {err}", file=sys.stderr)
        return EXIT_SCHEMA
    _write_json(args.findings, doc)
    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    print(render_handoff(_read_json(args.findings)), end="")
    return 0


def _not_yet(args: argparse.Namespace) -> int:
    print(f"{args.command}: not implemented yet", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="store-review", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    p = sub.add_parser("scan", help="Review the app and write findings.json")
    p.add_argument("--app", default=".", help="Flutter app root")
    p.add_argument("--out", default="findings.json")
    p.add_argument("--report", help="Also write a Markdown report here")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("merge", help="Merge reviewer-agent findings into findings.json")
    p.add_argument("--findings", default="findings.json")
    p.add_argument("--llm", required=True, help="JSON file with {'findings': [...]} from the reviewer agents")
    p.set_defaults(func=cmd_merge)

    p = sub.add_parser("handoff", help="Print the checklist of inputs only a human can provide")
    p.add_argument("--findings", default="findings.json")
    p.set_defaults(func=cmd_handoff)

    for name, help_text in (("validate-inputs", "Check the human's inputs before resuming"),
                            ("package", "Write the ready-to-submit package for one store"),
                            ("benchmark", "Score the deterministic rules against the Rejection Corpus")):
        sub.add_parser(name, help=help_text).set_defaults(func=_not_yet)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
