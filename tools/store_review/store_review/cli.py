"""Command-line entry point: store-review <command>."""

from __future__ import annotations

import argparse
import sys

COMMANDS = {
    "scan": "Review the app and write findings.json",
    "merge": "Merge reviewer-agent findings into findings.json",
    "handoff": "Print the checklist of inputs only a human can provide",
    "validate-inputs": "Check the human's inputs before resuming",
    "package": "Write the ready-to-submit package for one store",
    "benchmark": "Score the deterministic rules against the Rejection Corpus",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="store-review", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")
    for name, help_text in COMMANDS.items():
        sub.add_parser(name, help=help_text)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"{args.command}: not implemented yet", file=sys.stderr)
    return 1
