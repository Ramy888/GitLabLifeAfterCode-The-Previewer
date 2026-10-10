"""SPEC criteria 2 and 9 against the real Path B app in this repository."""

import plistlib
import shutil
from pathlib import Path

import yaml

from store_review.report import build_document
from store_review.rules import run_checks
from store_review.snapshot import load_snapshot

REPO = Path(__file__).resolve().parents[3]
COPY = ("pubspec.yaml", "pubspec.lock", "ios/Runner", "android/app", "store", "lib")


def scan(root, env):
    findings = run_checks(load_snapshot(root, env=env))
    return findings, build_document({"name": "x", "version": "1"}, findings)


def test_live_repo_findings_match_spec():
    findings, doc = scan(REPO, env={})
    by_id = {f.id: f.severity for f in findings}
    for rid in ("AND-TARGETSDK", "AND-DELETION-URL", "SHR-DEMO-LOGIN", "SHR-PRIVACY-URL"):
        assert by_id.get(rid) == "blocker", rid
    assert by_id.get("IOS-PRIVACY-MANIFEST") == "warning"
    assert "SHR-ACCOUNT-DELETION" not in by_id  # FirebaseUI ProfileScreen is deletion evidence
    for store in ("ios", "android"):
        assert doc["scores"][store]["status"] == "blocked" and doc["scores"][store]["readiness"] <= 40


def test_fixes_clear_every_blocker(tmp_path):
    for rel in COPY:
        src, dst = REPO / rel, tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if src.is_dir() else shutil.copy)(src, dst)
    gradle = tmp_path / "android/app/build.gradle"
    gradle.write_text(gradle.read_text().replace("targetSdk = 34", "targetSdk = 36"))
    plist_path = tmp_path / "ios/Runner/Info.plist"
    info = plistlib.loads(plist_path.read_bytes())
    info["ITSAppUsesNonExemptEncryption"] = False
    plist_path.write_bytes(plistlib.dumps(info))
    (tmp_path / "ios/Runner/PrivacyInfo.xcprivacy").write_bytes(plistlib.dumps({"NSPrivacyAccessedAPITypes": [{
        "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryUserDefaults",
        "NSPrivacyAccessedAPITypeReasons": ["CA92.1"]}]}))
    listing_path = tmp_path / "store/listing.yaml"
    listing = yaml.safe_load(listing_path.read_text())
    listing.update(privacy_policy_url="https://example.com/privacy", account_deletion_url="https://example.com/delete")
    listing_path.write_text(yaml.safe_dump(listing))

    findings, doc = scan(tmp_path, env={"STORE_REVIEW_DEMO_LOGIN": "reviewer:demo"})
    assert [f.id for f in findings if f.severity == "blocker"] == []
    for store in ("ios", "android"):
        assert doc["scores"][store]["status"] in ("ready", "needs-work")
