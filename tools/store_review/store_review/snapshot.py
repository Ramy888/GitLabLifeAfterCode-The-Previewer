"""Read a Flutter app tree into an AppSnapshot that the checks inspect."""

from __future__ import annotations

import os
import plistlib
import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
INFO_PLIST = "ios/Runner/Info.plist"
XCPRIVACY = "ios/Runner/PrivacyInfo.xcprivacy"
MANIFEST = "android/app/src/main/AndroidManifest.xml"
GRADLE_FILES = ("android/app/build.gradle", "android/app/build.gradle.kts")
STORE_FILES = ("listing", "data_safety", "review_notes")
GENERATED_DART = re.compile(r"\.(g|freezed|gr|mocks)\.dart$")
TARGET_SDK = re.compile(r"targetSdk(?:Version)?\s*(?:=\s*|\(\s*|\s+)([^\s)]+)")


@dataclass(frozen=True)
class GradleValue:
    path: str
    line: int
    text: str
    value: int | None


@dataclass
class AppSnapshot:
    root: Path
    name: str
    version: str
    pubspec: dict
    dependencies: set[str]
    info_plist: dict | None
    xcprivacy: dict | None
    manifest: ET.Element | None
    manifest_text: str
    target_sdk: GradleValue | None
    store: dict[str, dict]
    dart_sources: list[tuple[str, str]]
    env: Mapping[str, str] = field(default_factory=dict)
    info_plist_path: str = INFO_PLIST
    xcprivacy_path: str = XCPRIVACY
    manifest_path: str = MANIFEST

    def manifest_permissions(self) -> dict[str, int]:
        """Permission name -> 1-based line in AndroidManifest.xml."""
        if self.manifest is None:
            return {}
        perms = {}
        for el in self.manifest.iter("uses-permission"):
            name = el.get(f"{ANDROID_NS}name")
            if name:
                perms[name] = line_of(self.manifest_text, name)
        return perms

    def read(self, rel: str) -> str | None:
        p = self.root / rel
        return p.read_text(errors="replace") if p.is_file() else None


def line_of(text: str, needle: str) -> int:
    """1-based line of the first occurrence of needle, or 1 when absent."""
    idx = text.find(needle)
    return text.count("\n", 0, idx) + 1 if idx >= 0 else 1


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data if isinstance(data, dict) else {}


def _load_plist(path: Path) -> dict | None:
    if not path.is_file():
        return None
    with path.open("rb") as fh:
        return plistlib.load(fh)


def _target_sdk(root: Path) -> GradleValue | None:
    for rel in GRADLE_FILES:
        p = root / rel
        if not p.is_file():
            continue
        for n, line in enumerate(p.read_text().splitlines(), start=1):
            m = TARGET_SDK.search(line)
            if m:
                raw = m.group(1).strip("\"'")
                return GradleValue(rel, n, line.strip(), int(raw) if raw.isdigit() else None)
    return None


def _dart_sources(root: Path) -> list[tuple[str, str]]:
    lib = root / "lib"
    if not lib.is_dir():
        return []
    out = []
    for p in sorted(lib.rglob("*.dart")):
        rel = p.relative_to(root).as_posix()
        if not GENERATED_DART.search(rel):
            out.append((rel, p.read_text(errors="replace")))
    return out


def load_snapshot(root: Path | str, env: Mapping[str, str] | None = None) -> AppSnapshot:
    root = Path(root)
    pubspec = _load_yaml(root / "pubspec.yaml")
    lock = _load_yaml(root / "pubspec.lock")
    deps = set((pubspec.get("dependencies") or {}).keys()) | set((lock.get("packages") or {}).keys())
    manifest_path = root / MANIFEST
    manifest_text = manifest_path.read_text() if manifest_path.is_file() else ""
    return AppSnapshot(
        root=root,
        name=str(pubspec.get("name", root.name)),
        version=str(pubspec.get("version", "0.0.0")),
        pubspec=pubspec,
        dependencies=deps,
        info_plist=_load_plist(root / INFO_PLIST),
        xcprivacy=_load_plist(root / XCPRIVACY),
        manifest=ET.fromstring(manifest_text) if manifest_text else None,
        manifest_text=manifest_text,
        target_sdk=_target_sdk(root),
        store={name: _load_yaml(root / "store" / f"{name}.yaml") for name in STORE_FILES},
        dart_sources=_dart_sources(root),
        env=dict(os.environ if env is None else env),
    )
