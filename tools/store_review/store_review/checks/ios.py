"""Apple App Store automated checks over Info.plist, the privacy manifest and pubspec."""

from __future__ import annotations

import re
from collections.abc import Iterator

from store_review.model import Evidence
from store_review.rules import Hit, check
from store_review.snapshot import AppSnapshot, line_of


def _pubspec_evidence(snap: AppSnapshot, dep: str) -> Evidence:
    text = snap.read("pubspec.yaml") or ""
    return Evidence("pubspec.yaml", line_of(text, f"{dep}:"), f"depends on {dep}")


def _plist_evidence(snap: AppSnapshot, needle: str, detail: str) -> Evidence:
    return Evidence(snap.info_plist_path, line_of(snap.read(snap.info_plist_path) or "", needle), detail)


@check("IOS-USAGE-MISSING")
def usage_missing(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.info_plist is None:
        return
    for plugin, keys in pack["permission_plugins"].items():
        if plugin not in snap.dependencies:
            continue
        for key in keys:
            if key not in snap.info_plist:
                yield Hit(f"{plugin} needs {key} in Info.plist", [_pubspec_evidence(snap, plugin)], {"key": key})


@check("IOS-USAGE-PLACEHOLDER")
def usage_placeholder(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.info_plist is None:
        return
    pattern = re.compile(pack["placeholder_pattern"])
    for key, value in snap.info_plist.items():
        if key.endswith("UsageDescription") and isinstance(value, str):
            if len(value.strip()) < pack["min_usage_length"] or pattern.search(value):
                yield Hit(f"{key} reads like a placeholder: {value!r}",
                          [_plist_evidence(snap, key, f"{key} = {value!r}")], {"key": key})


@check("IOS-PRIVACY-MANIFEST")
def privacy_manifest(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.info_plist is None or snap.xcprivacy is not None:
        return
    for plugin, category in pack["required_reason_plugins"].items():
        if plugin in snap.dependencies:
            reason = pack["default_reason"].get(category, "an approved reason")
            yield Hit(f"No app privacy manifest, but {plugin} uses {category}",
                      [_pubspec_evidence(snap, plugin), Evidence(snap.xcprivacy_path, None, "file is missing")],
                      {"category": category, "reason": reason})
            return


@check("IOS-PRIVACY-REASON")
def privacy_reason(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.xcprivacy is None:
        return
    text = snap.read(snap.xcprivacy_path) or ""
    for entry in snap.xcprivacy.get("NSPrivacyAccessedAPITypes", []):
        category = entry.get("NSPrivacyAccessedAPIType", "")
        approved = pack["approved_reasons"].get(category, [])
        for code in entry.get("NSPrivacyAccessedAPITypeReasons", []):
            if code not in approved:
                yield Hit(f"Reason {code} is not approved for {category}",
                          [Evidence(snap.xcprivacy_path, line_of(text, code), f"{category}: {code}")],
                          {"code": code, "category": category})


@check("IOS-ENCRYPTION-FLAG")
def encryption_flag(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.info_plist is not None and "ITSAppUsesNonExemptEncryption" not in snap.info_plist:
        yield Hit("Export compliance answer is not set (ITSAppUsesNonExemptEncryption)",
                  [Evidence(snap.info_plist_path, None, "key absent")])


@check("IOS-ATS-ARBITRARY")
def ats_arbitrary(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    ats = (snap.info_plist or {}).get("NSAppTransportSecurity") or {}
    if ats.get("NSAllowsArbitraryLoads") is True:
        yield Hit("App Transport Security is disabled for all domains",
                  [_plist_evidence(snap, "NSAllowsArbitraryLoads", "NSAllowsArbitraryLoads = true")])


@check("IOS-SIWA")
def sign_in_with_apple(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.info_plist is None or snap.dependencies & set(pack["apple_login_plugins"]):
        return
    for plugin in pack["social_login_plugins"]:
        if plugin in snap.dependencies:
            yield Hit(f"Third-party login ({plugin}) without Sign in with Apple",
                      [_pubspec_evidence(snap, plugin)], {"plugin": plugin})
            return
