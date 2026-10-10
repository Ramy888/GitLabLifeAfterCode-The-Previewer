# SPEC: Store Review Rehearsal

Status: approved by Ramy, who delegated all decisions on 2026-10-10. Source of truth for `/build`.
Background and rationale: `../DEBATE.md` (Debates 2 and 3, plus the decisions dated 2026-10-10), `../CLAUDE.md`, `../BRIEF.md`.

## Context
Mobile releases stall in store review. Teams submit, wait hours to days, and then get a rejection that cites a guideline number.
**"The store said no, and the email doesn't say why."**
Store Review Rehearsal is a GitLab Duo Agent Platform product. It reviews a Flutter app the way **Apple App Store review** and
**Google Play review** would, before submission. It fixes what it can safely fix through MRs, asks the human **once** for what only a
human has, then produces a **ready-to-submit package per store** with a **readiness score** whose method is published and benchmarked.

Hackathon entry: **GitLab "Life After Code", Path B, Supervised autonomy**. Target prizes: Best Supervised (Path B) + Most Creative.
Deadline Oct 27, 2026 at 13:00 UTC (submit Oct 26).

## Current state (verified 2026-10-10)
The Path B base is `bizz84/starter_architecture_flutter_firebase`: MIT, 1.8k stars, last push 2025-09-09, 167 commits. It's a time-tracking
app with Firebase Auth and Firestore, Riverpod and go_router, targeting iOS, Android, web and macOS. It's cloned here on branch `store-review`.
The `upstream` remote has push disabled.

Real review-relevant facts in this app (these become the demo's live findings):
| Area | Evidence | Store consequence |
|---|---|---|
| Android target SDK | `android/app/build.gradle:31`, `targetSdk = 34` | Google Play: since 2026-08-31, new apps and updates must target API 36. **Blocker** |
| iOS privacy manifest | `ios/Runner/PrivacyInfo.xcprivacy` is absent. The app depends on `shared_preferences` (UserDefaults, a required-reason API) | Apple upload check ITMS-91053 risk. **Warning** (plugins may ship their own manifest) |
| iOS usage strings | `ios/Runner/Info.plist` has 0 `*UsageDescription` keys | Pass today. Must stay true when permission plugins are added |
| Account creation | `firebase_auth` plus `firebase_ui_auth` sign-up | Apple 5.1.1(v) and Google Play both require account deletion |
| In-app deletion | `lib/src/features/authentication/presentation/custom_profile_screen.dart:12` uses FirebaseUI `ProfileScreen` (I believe its default includes a delete-account action; confirm in task T4) | **Satisfies** in-app deletion. Used for the "rejection is wrong → appeal" demo beat |
| Web deletion link (Play) | No deletion URL anywhere in the repo | Google Play requires a web link for account deletion. **Blocker → handoff input** |
| Firebase config | `lib/firebase_options.dart` is gitignored (`.gitignore:98`) | CI must generate it from a masked variable before any build |
| Tests | 2 Dart test files under `test/` | The Flutter suite runs in CI as the baseline |

## Proposed change
```
Release issue ──assign──▶ Duo flow "store-review"
   │ Reviewer agents run the CI job `store-review scan` ─▶ findings.json (deterministic, guideline-cited)
   │ Reviewer agents add judgement findings ─▶ findings.llm.json (each with a confidence)
   │ Fixer opens MRs for safe findings ─▶ pipeline re-scans ─▶ readiness recomputed
   │ Advocate: any pasted/seeded rejection ─▶ fix MR (rejection valid) or appeal draft (rejection wrong, with evidence)
   │ Governor posts readiness per store + ONE handoff checklist ─▶ session ends
Human sets CI variables / answers ─▶ comments "@store-review resume"
   │ Governor validates inputs ─▶ narrowed checklist (incomplete) or packages (complete)
   ▼
GitLab Release: per-store ready-to-submit package + findings + benchmark. The human submits in each console.
```

### Components and files
| Path | Purpose |
|---|---|
| `tools/store_review/` | Python 3.12 package and CLI `store-review` (uv project, deps: `pyyaml` only. Tests use `pytest`) |
| `tools/store_review/store_review/rules/{ios,android,shared}.yaml` | Rule packs: `id, store, layer, guideline, title, severity, weight, check, source_url, verified` |
| `tools/store_review/store_review/checks/{ios,android,shared}.py` | Deterministic checks. Each is a pure function `(AppSnapshot) -> list[Finding]` |
| `tools/store_review/store_review/snapshot.py` | Reads an app tree into `AppSnapshot` (pubspec/lock, Info.plist, xcprivacy, AndroidManifest, gradle, `store/*.yaml`, Dart sources) |
| `tools/store_review/store_review/score.py` | Gated readiness score and band |
| `tools/store_review/store_review/report.py` | `findings.json`, Markdown report, handoff checklist |
| `tools/store_review/store_review/package.py` | Per-store ready-to-submit package |
| `tools/store_review/store_review/inputs.py` | Validates human inputs (CI vars present, URLs reachable through an injectable fetcher) |
| `tools/store_review/corpus/<case>/` | **Rejection Corpus**: ≥36 fixture cases, each with `expected.yaml` |
| `tools/store_review/store_review/benchmark.py` | Precision and recall of deterministic rules over the corpus |
| `store/listing.yaml`, `store/data_safety.yaml`, `store/review_notes.yaml` | App store metadata the reviewer reads. Created for this app |
| `ios/Runner/PrivacyInfo.xcprivacy` | Added by a Fixer MR (live demo fix) |
| `.gitlab-ci.yml` | Stages: test → build → review → package → deploy |
| `.gitlab/duo/flows/store-review.yaml` + `.gitlab/duo/agents/*.md` | Duo custom flow and the agent prompts |
| `deploy/cloudrun/` | Dockerfile (nginx serving `build/web`) and deploy script (Path B live URL, Google Cloud bonus) |
| `docs/STORE_REVIEW.md` | How the score works, what is simulated, how to run it on any app |

### Data shapes
`findings.json` (schema `store-review/findings@1`):
```json
{
  "schema": "store-review/findings@1",
  "generated_at": "2026-10-20T10:00:00Z",
  "app": {"name": "...", "version": "2.1.0", "ios_bundle_id": "...", "android_package": "..."},
  "findings": [{
    "id": "AND-TARGETSDK", "store": "android", "layer": "automated",
    "guideline": "Play: Target API level requirement", "title": "targetSdk 34 is below the required 36",
    "severity": "blocker", "weight": 0, "source": "deterministic", "confidence": 1.0,
    "evidence": [{"path": "android/app/build.gradle", "line": 31, "detail": "targetSdk = 34"}],
    "fix": {"kind": "auto", "recipe": "set targetSdk = 36 in android/app/build.gradle"}
  }],
  "inputs_required": [{"key": "STORE_REVIEW_DEMO_LOGIN", "kind": "ci_variable", "why": "Apple 2.1 / Play App access", "stores": ["ios","android"]}],
  "scores": {"ios": {"status": "blocked", "readiness": 40, "low": 31, "high": 40, "blockers": 2, "warnings": 1}, "android": {"...": "..."}},
  "benchmark": {"cases": 36, "precision": 0.94, "recall": 0.88}
}
```
- `severity` is one of `blocker | warning | info`. `layer` is `automated | reviewer`. `source` is `deterministic | llm`. `fix.kind` is `auto | manual | handoff`.
- LLM findings arrive through `store-review merge --llm findings.llm.json`, which runs the same schema validation. A finding without evidence is rejected.

### Readiness score (per store)
1. `det = Σ weight` over open deterministic warnings, with weight 1–8 from the rule pack.
2. `llm = Σ weight × confidence` over open LLM findings, with weight 2–10 and confidence in [0,1].
3. `readiness = clamp(100 − det − llm, 0, 100)`. Band: `low = clamp(100 − det − Σ llm weights)`, `high = clamp(100 − det)`.
4. If any **blocker** is open, including a missing required input, then `status = "blocked"` and readiness, low and high are each capped at **40**.
   Otherwise `status = "ready"` when readiness ≥ 80, else `"needs-work"`.
5. Benchmark precision and recall are printed **beside** the score and never folded into it.
6. On-screen string: `Readiness 78 (68–86) · 43 checks passed · 5 warnings · 1 blocker · recall 0.88 on 36 seeded cases`.

### Deterministic rules (MVP set)
| ID | Store | Check | Severity |
|---|---|---|---|
| IOS-USAGE-MISSING | ios | A plugin in pubspec implies a permission (map in rule pack: image_picker→Camera+PhotoLibrary, geolocator→LocationWhenInUse, permission_handler/camera→Camera, record→Microphone, contacts…) and the `NS*UsageDescription` key is absent | blocker (5.1.1) |
| IOS-USAGE-PLACEHOLDER | ios | Usage string <12 chars, or contains TODO/placeholder/lorem | warning 5 (5.1.1) |
| IOS-PRIVACY-MANIFEST | ios | No app-level `PrivacyInfo.xcprivacy` while a dependency maps to a required-reason API category | warning 4 (ITMS-91053) |
| IOS-PRIVACY-REASON | ios | xcprivacy declares a category without an approved reason code from the rule-pack list | blocker (ITMS-91053) |
| IOS-ENCRYPTION-FLAG | ios | `ITSAppUsesNonExemptEncryption` absent | warning 2 (export compliance) → handoff question |
| IOS-ATS-ARBITRARY | ios | `NSAllowsArbitraryLoads` is true | warning 4 |
| IOS-SIWA | ios | A third-party social login dependency (google_sign_in, flutter_facebook_auth, firebase_ui_oauth_*) with no `sign_in_with_apple` | warning 6 (4.8). LLM confirms |
| SHR-ACCOUNT-DELETION | both | Account creation detected and no deletion evidence (FirebaseUI `ProfileScreen`, or `.delete()` on a user object, or `store/review_notes.yaml: account_deletion_path`) | blocker (Apple 5.1.1(v), Play User Data) |
| AND-TARGETSDK | android | `targetSdk` below `required_target_sdk` in the rule pack (36, verified 2026-10-10) | blocker |
| AND-DELETION-URL | android | Account creation detected and `store/listing.yaml: account_deletion_url` absent | blocker → handoff |
| AND-DATASAFETY-PERM | android | A dangerous permission in the merged-source manifest is not declared in `store/data_safety.yaml` | blocker |
| AND-CLEARTEXT | android | `usesCleartextTraffic="true"` | warning 4 |
| AND-DEBUGGABLE | android | `android:debuggable="true"` | blocker |
| AND-DEBUG-SIGNING | android | The release buildType uses `signingConfigs.debug` (found live: `android/app/build.gradle:40`) | blocker |
| AND-EXPORTED | android | An activity with an intent-filter lacks `android:exported` | blocker |
| SHR-DEMO-LOGIN | both | Account creation detected and CI variable `STORE_REVIEW_DEMO_LOGIN` absent | blocker → handoff (Apple 2.1, Play App access) |
| SHR-PRIVACY-URL | both | `store/listing.yaml: privacy_policy_url` absent, or unreachable at resume | blocker → handoff |
| SHR-PLACEHOLDER-UI | both | A Dart string literal shown in the UI contains "coming soon", "lorem" or "TODO" | warning 5 (Apple 2.1 / Play Minimum functionality) |
| SHR-METADATA-PLATFORM | both | iOS listing text mentions "Android" or "Google Play", or Android text mentions "iPhone" or "App Store" | warning 3 (Apple 2.3.10) |

### Agents (Duo custom flow `store-review`)
1. **iOS Reviewer**: runs and reads the iOS scan. Adds judgement findings (4.2 minimum functionality, 2.3 metadata accuracy, 4.8) with confidence.
2. **Android Reviewer**: same for Play (Minimum functionality, deceptive behaviour, Data safety accuracy).
3. **Fixer**: for findings with `fix.kind = auto`, opens one MR per finding (targetSdk, xcprivacy, usage strings). Never touches secrets.
4. **Advocate**: given a rejection text (pasted, or a seeded corpus case labelled on screen), decides **valid** (route to Fixer) or **invalid** (write an appeal citing the guideline, plus evidence paths and screenshots).
5. **Governor**: posts the per-store readiness and the single handoff checklist, ends the session, resumes on `@mention`, validates inputs, and triggers the package job.
Triggers: **Assign** (start) and **Mention** (resume). Work-item event triggers are optional.

### Human handoff (exactly one round)
The checklist lists only `fix.kind = handoff` items. Secrets are **never** in comments: the demo login goes in the masked CI variable
`STORE_REVIEW_DEMO_LOGIN`. On resume, `store-review validate-inputs` checks each item:
- CI variable present (presence only, never the value)
- URLs return HTTP 200
- yes/no answers present

Anything that fails is re-posted as a narrowed checklist, and no package is produced for a store that still has a blocker. Runs are idempotent.

## Acceptance criteria
1. `uv run pytest` in `tools/store_review` passes. Every rule ID in the MVP table has ≥1 positive and ≥1 negative unit test.
2. `store-review scan --app . --out findings.json` on this repo (before fixes) reports **AND-TARGETSDK (blocker)**, **AND-DEBUG-SIGNING (blocker)**, **AND-DELETION-URL (blocker)**,
   **SHR-DEMO-LOGIN (blocker)**, **SHR-PRIVACY-URL (blocker)** and **IOS-PRIVACY-MANIFEST (warning)**. It does **not** report SHR-ACCOUNT-DELETION,
   because FirebaseUI `ProfileScreen` is detected as deletion evidence. Both stores show `status: blocked`, readiness ≤ 40.
3. `findings.json` validates against the schema. A finding without `evidence` is rejected by `merge`, with exit code 2.
4. The Rejection Corpus has **≥36 cases**: ≥24 positive (each rule ≥1) and ≥8 clean negatives. `store-review benchmark` prints precision and recall and exits non-zero if
   recall < 0.85 or precision < 0.90.
5. Score unit tests cover: no findings → 100 (100–100) ready; one blocker → cap 40; warnings only → exact arithmetic; LLM confidence produces the band.
6. `store-review handoff` lists only handoff-kind items and never prints a CI variable's value. A test asserts that a seeded secret string is absent from the output.
7. `store-review validate-inputs` with all inputs valid exits 0. With one URL returning 404 it exits 3 and prints the narrowed checklist. Tested with an injected fetcher, no network.
8. `store-review package --store ios|android` writes `dist/store-package/<store>/{metadata.json,reviewer-notes.md,privacy-answers.json,release-notes.en.md,release-notes.ar.md,checklist.md}`.
   It refuses (exit 4) while that store has an open blocker.
9. Applying the Fixer recipes (targetSdk 36, release signing config, xcprivacy with UserDefaults CA92.1), adding `store/listing.yaml` URLs and setting the demo-login variable
   leaves **0 blockers**. The scan then shows both stores `ready` or `needs-work`, never `blocked`.
10. `.gitlab-ci.yml` passes `gitlab-ci-lint` (local schema check) and defines jobs `engine:test`, `flutter:test`, `build:web`, `build:android`, `review:scan`,
    `review:benchmark`, `package:stores` (tags or manual) and `deploy:cloudrun` (manual, protected). `findings.json` and the benchmark are job artifacts.
11. The flow YAML and agent prompts exist and validate against GitLab's published custom-flow schema (version noted in the file). *Running them needs GitLab access and is verified after onboarding.*
12. `docs/STORE_REVIEW.md` states what is simulated (store decisions, seeded rejections) and what is real (scans, fixes, score, packages).
13. `LICENSE.md` stays MIT. The original copyright is preserved and a line is added for the new work.

## Testing plan
| Layer | What | Count |
|---|---|---|
| Unit | each deterministic rule (positive + negative), snapshot parsing (plist, xcprivacy, manifest, gradle, pubspec.lock), score, schema validation, handoff redaction, input validation | ~60 |
| Corpus | benchmark over ≥36 cases | 1 suite |
| Integration | `scan` on this repo matches criterion 2. Applying the fixes matches criterion 9 | 2 |
| E2E (post-access) | Release issue → flow → MRs → handoff → resume → Release package on gitlab.com | 1 recorded run |

## Out of scope
Uploading to any store · Fire OS / HMS / Amazon / Huawei · building or signing an iOS binary (no macOS runners assumed) · real-time monitoring of user reviews
(roadmap slide) · LLM calls inside the Python engine (judgement lives in Duo agents) · changing the app's features beyond review fixes.

## Rollback
Each task is one commit on branch `store-review`, so any task reverts with `git revert`. Cloud Run deploy is manual and protected. Delete the service to roll it back.
No data migrations.

## Effort
Engine and rules about 1.5 days · corpus and benchmark about 1.5 days · package, handoff and inputs about 0.5 day · CI about 0.5 day · flow and prompts about 1 day ·
Cloud Run about 0.5 day · docs and demo seed about 0.5 day. Total about 6 days, leaving about 4 days for GitLab bring-up, E2E and the video.

## Blocked on Ramy or GitLab (not doable locally)
- GitLab contributor onboarding approval → creating the project, importing this repo, running flows (Q1–Q5 in `../BRIEF.md`).
- A Firebase or GCP project for the web build config and the Cloud Run deploy (billing, possibly the $300 credit).
- Confirming the trademark question (Q9) before recording.
