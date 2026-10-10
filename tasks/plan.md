# Plan: Store Review Rehearsal (from SPEC.md)

Each task is RED → GREEN → full suite → commit. Status: [ ] pending · [x] done · [~] blocked.
Dependency order is top to bottom unless noted.

- [x] **T1 Scaffold** (`tools/store_review`): uv project, `store-review` CLI entry, the `Finding` model plus schema validation. AC: `uv run pytest` green, `store-review --help` works.
- [x] **T2 Snapshot parsers**: pubspec.yaml/lock, Info.plist, PrivacyInfo.xcprivacy, AndroidManifest.xml, gradle targetSdk, `store/*.yaml`, Dart string literals. AC: parser unit tests on fixtures. *Deps: T1*
- [x] **T3 iOS rules**: rule pack `ios.yaml` and checks IOS-USAGE-MISSING, IOS-USAGE-PLACEHOLDER, IOS-PRIVACY-MANIFEST, IOS-PRIVACY-REASON, IOS-ENCRYPTION-FLAG, IOS-ATS-ARBITRARY, IOS-SIWA. AC: one positive and one negative test per rule. *Deps: T2*
- [x] **T4 Android + shared rules**: AND-TARGETSDK, AND-DELETION-URL, AND-DATASAFETY-PERM, AND-CLEARTEXT, AND-DEBUGGABLE, AND-EXPORTED, SHR-ACCOUNT-DELETION (FirebaseUI ProfileScreen evidence), SHR-DEMO-LOGIN, SHR-PRIVACY-URL, SHR-PLACEHOLDER-UI, SHR-METADATA-PLATFORM. AC: one positive and one negative test per rule. *Deps: T2*
- [x] **T5 Score**: gated readiness and band per store. AC: SPEC criterion 5. *Deps: T1*
- [ ] **T6 Report and CLI**: `scan`, `merge --llm` (exit 2 when evidence is missing), Markdown report, `handoff` (redacts values). AC: SPEC criteria 3 and 6. *Deps: T3, T4, T5*
- [ ] **T7 Inputs**: `validate-inputs` with an injectable fetcher (exit 3 plus a narrowed list). AC: SPEC criterion 7. *Deps: T6*
- [ ] **T8 Package**: `package --store` (exit 4 while blocked). AC: SPEC criterion 8. *Deps: T6*
- [ ] **T9 Rejection Corpus and benchmark**: at least 36 cases and the `benchmark` command with thresholds. AC: SPEC criterion 4. *Deps: T3, T4*
- [ ] **T10 Repo integration**: add `store/` metadata files (no URLs yet). Integration tests for SPEC criterion 2 (live repo) and criterion 9 (fixes applied in a temp copy). *Deps: T6*
- [ ] **T11 CI**: `.gitlab-ci.yml` with the SPEC criterion 10 jobs, plus a local lint test. *Deps: T6, T9*
- [ ] **T12 Duo flow and agent prompts**: `.gitlab/duo/flows/store-review.yaml` and `.gitlab/duo/agents/*.md`, checked against GitLab's custom-flow docs. AC: SPEC criterion 11 (static check only). *Deps: T6*
- [ ] **T13 Cloud Run**: `deploy/cloudrun/{Dockerfile,nginx.conf,deploy.sh}`. AC: `docker build` of the image succeeds with a stub `build/web`. *Deps: none*
- [ ] **T14 Docs and license**: `docs/STORE_REVIEW.md`, a README section, and a LICENSE line for the new work. AC: SPEC criteria 12 and 13. *Deps: all*

Blocked until GitLab access and GCP are available: importing the project into GitLab, running the flow end to end, the real Cloud Run deploy, and recording the video.
