"""Checks that apply to both stores: accounts, demo login, privacy policy, unfinished UI, metadata."""

from __future__ import annotations

import re
from collections.abc import Iterator

from store_review.model import Evidence
from store_review.rules import Hit, check, load_pack
from store_review.snapshot import AppSnapshot, line_of


def has_accounts(snap: AppSnapshot) -> bool:
    return bool(snap.dependencies & set(load_pack("shared")["account_plugins"]))


def _account_dep_evidence(snap: AppSnapshot) -> Evidence:
    dep = sorted(snap.dependencies & set(load_pack("shared")["account_plugins"]))[0]
    return Evidence("pubspec.yaml", line_of(snap.read("pubspec.yaml") or "", f"{dep}:"), f"account sign-up via {dep}")


@check("SHR-ACCOUNT-DELETION")
def account_deletion(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if not has_accounts(snap) or snap.store["review_notes"].get("account_deletion_path"):
        return
    patterns = [re.compile(p) for p in pack["deletion_evidence"]]
    for _, text in snap.dart_sources:
        if any(p.search(text) for p in patterns):
            return
    yield Hit("Users can create an account but the app has no way to delete it",
              [_account_dep_evidence(snap), Evidence("lib/", None, "no account deletion call or screen found")])


@check("SHR-DEMO-LOGIN")
def demo_login(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    var = pack["demo_login_variable"]
    if has_accounts(snap) and not snap.env.get(var):
        yield Hit("Reviewers need a demo account, and none is provided",
                  [_account_dep_evidence(snap), Evidence("CI/CD variables", None, f"{var} is not set")])


@check("SHR-PRIVACY-URL")
def privacy_url(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if not snap.store["listing"].get("privacy_policy_url"):
        yield Hit("No privacy policy URL", [Evidence("store/listing.yaml", None, "privacy_policy_url is not set")])


def _code_lines(text: str) -> Iterator[tuple[int, str]]:
    for n, line in enumerate(text.splitlines(), start=1):
        code = line.split("//", 1)[0] if not line.lstrip().startswith("///") else ""
        if code.strip():
            yield n, code


@check("SHR-PLACEHOLDER-UI")
def placeholder_ui(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    pattern = re.compile(pack["placeholder_ui_pattern"])
    for path, text in snap.dart_sources:
        for n, code in _code_lines(text):
            m = pattern.search(code)
            if m:
                literal = m.group(0)
                yield Hit(f"Unfinished feature text shown to users: {literal}",
                          [Evidence(path, n, code.strip())], {"text": literal.strip("'\"")})


@check("SHR-METADATA-PLATFORM")
def metadata_platform(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    listing = snap.store["listing"]
    for store, words in pack["other_platform_words"].items():
        text = " ".join(str(v) for v in (listing.get(store) or {}).values())
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", text):
                yield Hit(f"The {store} listing mentions {word}",
                          [Evidence("store/listing.yaml", None, f"{store}: ...{word}...")], {"word": word, "store": store})
