"""Google Play automated checks over the manifest, gradle config and store metadata."""

from __future__ import annotations

import re
from collections.abc import Iterator

from store_review.checks.shared import has_accounts
from store_review.model import Evidence
from store_review.rules import Hit, check
from store_review.snapshot import ANDROID_NS, AppSnapshot, line_of


def _android_present(snap: AppSnapshot) -> bool:
    return snap.manifest is not None or snap.target_sdk is not None


@check("AND-TARGETSDK")
def target_sdk(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    t = snap.target_sdk
    required = pack["required_target_sdk"]
    if t is not None and t.value is not None and t.value < required:
        yield Hit(f"targetSdk {t.value} is below the required {required} (since {pack['required_target_sdk_since']})",
                  [Evidence(t.path, t.line, t.text)], {"required": required, "path": t.path})


@check("AND-DEBUG-SIGNING")
def debug_signing(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.gradle is None:
        return
    path, text = snap.gradle
    in_release, depth = False, 0
    for n, line in enumerate(text.splitlines(), start=1):
        code = line.split("//", 1)[0]
        if re.search(r"\brelease\s*\{", code) or re.search(r'getByName\(\s*"release"\s*\)\s*\{', code):
            in_release, depth = True, 0
        if in_release:
            depth += code.count("{") - code.count("}")
            if re.search(r"signingConfig\s*=?\s*signingConfigs\.(debug|getByName\(\s*\"debug\"\s*\))", code):
                yield Hit("The release build is signed with the debug key", [Evidence(path, n, code.strip())], {"path": path})
                return
            if depth <= 0:
                in_release = False


@check("AND-DELETION-URL")
def deletion_url(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if _android_present(snap) and has_accounts(snap) and not snap.store["listing"].get("account_deletion_url"):
        yield Hit("Users can create accounts but there is no web link for account deletion",
                  [Evidence("store/listing.yaml", None, "account_deletion_url is not set")])


@check("AND-DATASAFETY-PERM")
def data_safety_permissions(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    declared = set(snap.store["data_safety"].get("declared_permissions") or [])
    for perm, line in snap.manifest_permissions().items():
        if perm in pack["dangerous_permissions"] and perm not in declared:
            yield Hit(f"{perm.rsplit('.', 1)[-1]} is requested but not declared in the Data safety answers",
                      [Evidence(snap.manifest_path, line, perm)], {"permission": perm})


def _application_flag(snap: AppSnapshot, attr: str) -> bool:
    app = snap.manifest.find("application") if snap.manifest is not None else None
    return app is not None and app.get(f"{ANDROID_NS}{attr}") == "true"


@check("AND-CLEARTEXT")
def cleartext(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if _application_flag(snap, "usesCleartextTraffic"):
        yield Hit("Cleartext HTTP is allowed for every host",
                  [Evidence(snap.manifest_path, line_of(snap.manifest_text, "usesCleartextTraffic"), 'usesCleartextTraffic="true"')])


@check("AND-DEBUGGABLE")
def debuggable(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if _application_flag(snap, "debuggable"):
        yield Hit("The manifest marks the app debuggable",
                  [Evidence(snap.manifest_path, line_of(snap.manifest_text, "debuggable"), 'android:debuggable="true"')])


@check("AND-EXPORTED")
def exported(snap: AppSnapshot, pack: dict) -> Iterator[Hit]:
    if snap.manifest is None:
        return
    for tag in ("activity", "service", "receiver", "activity-alias"):
        for el in snap.manifest.iter(tag):
            if el.find("intent-filter") is not None and el.get(f"{ANDROID_NS}exported") is None:
                name = el.get(f"{ANDROID_NS}name", tag)
                yield Hit(f"{tag} {name} has an intent filter but no android:exported",
                          [Evidence(snap.manifest_path, line_of(snap.manifest_text, name), f"<{tag} android:name=\"{name}\">")],
                          {"component": name})

