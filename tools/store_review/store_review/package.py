"""Write the ready-to-submit package for one store. Refuses while the store has an open blocker."""

from __future__ import annotations

import json
from pathlib import Path

from store_review.report import STORES
from store_review.snapshot import AppSnapshot

DEMO_LOGIN_VARIABLE = "STORE_REVIEW_DEMO_LOGIN"
DEFAULT_NOTES = {"en": "Bug fixes and improvements.\n", "ar": "إصلاحات وتحسينات.\n"}
CONSOLE_STEPS = {
    "ios": [
        "Open App Store Connect > your app > the new version.",
        "Paste release-notes.en.md into What's New (add Arabic from release-notes.ar.md if the app is localized).",
        "Copy name, subtitle and description from metadata.json.",
        "App Review Information: turn on Sign-in required and enter the demo account from the masked CI/CD variable "
        f"{DEMO_LOGIN_VARIABLE}. Paste reviewer-notes.md into Notes.",
        "App Privacy: answer from privacy-answers.json.",
        "Select the build, then Add for Review and Submit.",
    ],
    "android": [
        "Open Play Console > your app > Test and release > create a new release.",
        "Upload the AAB from this GitLab Release and paste release-notes.en.md (and Arabic) into release notes.",
        "Store listing: copy name, short description and description from metadata.json.",
        f"App content > App access: add the demo account from the masked CI/CD variable {DEMO_LOGIN_VARIABLE}.",
        "App content > Data safety: answer from privacy-answers.json and add the account deletion URL from metadata.json.",
        "Review the release and send it for review.",
    ],
}


class PackageBlocked(Exception):
    """The store still has open blockers."""


def _metadata(snap: AppSnapshot, store: str, version: str) -> dict:
    listing = snap.store["listing"]
    meta = {"store": store, "app": snap.name, "version": version, **(listing.get(store) or {}),
            "privacy_policy_url": listing.get("privacy_policy_url")}
    if store == "android":
        meta["account_deletion_url"] = listing.get("account_deletion_url")
    return meta


def _privacy_answers(snap: AppSnapshot, store: str) -> dict:
    answers = snap.store["review_notes"].get("answers") or {}
    if store == "android":
        return {"data_safety": snap.store["data_safety"], "answers": answers}
    categories = [e.get("NSPrivacyAccessedAPIType") for e in (snap.xcprivacy or {}).get("NSPrivacyAccessedAPITypes", [])]
    return {"required_reason_api_categories": categories, "answers": answers}


def _reviewer_notes(snap: AppSnapshot, store: str) -> str:
    notes = snap.store["review_notes"]
    lines = [f"# Notes for the {STORES[store]} reviewer", ""]
    lines.append(f"- Demo account: provided in the review form (kept in CI/CD variable {DEMO_LOGIN_VARIABLE}, never in this file).")
    if notes.get("account_deletion_path"):
        lines.append(f"- Delete an account: {notes['account_deletion_path']}.")
    for extra in notes.get("notes") or []:
        lines.append(f"- {extra}")
    return "\n".join(lines) + "\n"


def _release_notes(snap: AppSnapshot, version: str, lang: str) -> str:
    return snap.read(f"store/release_notes/{version}.{lang}.md") or DEFAULT_NOTES[lang]


def write_package(snap: AppSnapshot, doc: dict, store: str, out_dir: Path) -> Path:
    score = doc["scores"][store]
    if score["status"] == "blocked":
        raise PackageBlocked(f"{STORES[store]} still has {score['blockers']} blocker(s); fix them before packaging")
    version = doc["app"]["version"]  # the version that was reviewed, not whatever pubspec says now
    d = Path(out_dir) / store
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(json.dumps(_metadata(snap, store, version), indent=2, ensure_ascii=False) + "\n")
    (d / "privacy-answers.json").write_text(json.dumps(_privacy_answers(snap, store), indent=2, ensure_ascii=False) + "\n")
    (d / "reviewer-notes.md").write_text(_reviewer_notes(snap, store))
    for lang in ("en", "ar"):
        (d / f"release-notes.{lang}.md").write_text(_release_notes(snap, version, lang))
    steps = "\n".join(f"{n}. {s}" for n, s in enumerate(CONSOLE_STEPS[store], start=1))
    readiness = (f"Readiness {score['readiness']} ({score['low']}–{score['high']}), "
                 f"{score['warnings']} warnings open.")
    (d / "checklist.md").write_text(f"# Submit to {STORES[store]}\n\n{readiness}\n\n{steps}\n")
    return d
