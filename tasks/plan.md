# Plan: The Previewer (from SPEC.md)

Each task is RED → GREEN → full suite → commit. Status: [ ] pending · [x] done · [~] blocked.
Dependency order is top to bottom unless noted.

- [x] **T1 Scaffold** (`tools/store_review`): uv project, `store-review` CLI entry, the `Finding` model plus schema validation. AC: `uv run pytest` green, `store-review --help` works.
- [x] **T2 Snapshot parsers**: pubspec.yaml/lock, Info.plist, PrivacyInfo.xcprivacy, AndroidManifest.xml, gradle targetSdk, `store/*.yaml`, Dart string literals. AC: parser unit tests on fixtures. *Deps: T1*
- [x] **T3 iOS rules**: rule pack `ios.yaml` and checks IOS-USAGE-MISSING, IOS-USAGE-PLACEHOLDER, IOS-PRIVACY-MANIFEST, IOS-PRIVACY-REASON, IOS-ENCRYPTION-FLAG, IOS-ATS-ARBITRARY, IOS-SIWA. AC: one positive and one negative test per rule. *Deps: T2*
- [x] **T4 Android + shared rules**: AND-TARGETSDK, AND-DELETION-URL, AND-DATASAFETY-PERM, AND-CLEARTEXT, AND-DEBUGGABLE, AND-EXPORTED, SHR-ACCOUNT-DELETION (FirebaseUI ProfileScreen evidence), SHR-DEMO-LOGIN, SHR-PRIVACY-URL, SHR-PLACEHOLDER-UI, SHR-METADATA-PLATFORM. AC: one positive and one negative test per rule. *Deps: T2*
- [x] **T5 Score**: gated readiness and band per store. AC: SPEC criterion 5. *Deps: T1*
- [x] **T6 Report and CLI**: `scan`, `merge --llm` (exit 2 when evidence is missing), Markdown report, `handoff` (redacts values). AC: SPEC criteria 3 and 6. *Deps: T3, T4, T5*
- [x] **T7 Inputs**: `validate-inputs` with an injectable fetcher (exit 3 plus a narrowed list). AC: SPEC criterion 7. *Deps: T6*
- [x] **T8 Package**: `package --store` (exit 4 while blocked). AC: SPEC criterion 8. *Deps: T6*
- [x] **T9 Rejection Corpus and benchmark**: at least 36 cases and the `benchmark` command with thresholds. AC: SPEC criterion 4. *Deps: T3, T4*
- [x] **T10 Repo integration**: add `store/` metadata files (no URLs yet). Integration tests for SPEC criterion 2 (live repo) and criterion 9 (fixes applied in a temp copy). *Deps: T6*
- [x] **T11 CI**: `.gitlab-ci.yml` with the SPEC criterion 10 jobs, plus a local lint test. *Deps: T6, T9*
- [x] **T12 Duo flow and agent prompts**: `.gitlab/duo/flows/store-review.yaml` and `.gitlab/duo/agents/*.md`, checked against GitLab's custom-flow docs. AC: SPEC criterion 11 (static check only). *Deps: T6*
- [x] **T13 Cloud Run**: `deploy/cloudrun/{Dockerfile,nginx.conf,deploy.sh}`. AC: `docker build` of the image succeeds with a stub `build/web`. *Deps: none*
- [x] **T14 Docs and license**: `docs/STORE_REVIEW.md`, a README section, and a LICENSE line for the new work. AC: SPEC criteria 12 and 13. *Deps: all*

## Bring-up checklist (the hour GitLab access lands)
- [x] Create the project in the provisioned group (public, so the MIT license shows in About; BRIEF Q2). Push this repo and make **`store-review` the default branch** (or merge it into `master` first): `.gitlab/duo/agent-config.yml` is read only from the default branch.
- [x] AI > Flows > New flow: paste `.gitlab/duo/flows/store-review.yaml`. Enable the **Assign** and **Mention** triggers on the project.
- [x] Note the flow's service account (`ai-<flow>-<group>`) and set CI/CD variable `STORE_REVIEW_MENTION` to it.
- [x] Set `STORE_REVIEW_DEMO_LOGIN` **masked, not protected** (or protect the `store-review/*` wildcard), so release-MR pipelines can see it.
- [x] Check that `python3` and `pip` exist in the default flow image. (They don't: agent-config fetches the uv binary with python3 alone.)
- [x] `FIREBASE_OPTIONS_DART` (base64 of a real `lib/firebase_options.dart`) for the deployed web build; GCP variables plus Workload Identity Federation for `deploy:cloudrun`.
- [x] First end-to-end run on #2 (v2.1.0): handoff → 7 fix MRs → resume → release MR !8 → merge (2026-10-12). Release-on-merge added after, so v2.1.0 has no Release.
- [ ] Throwaway run on v2.1.1 to exercise release:gitlab, then the recorded run on v2.1.2.

## T15 Account deletion removes the user's data (FULL lane: deletion)
Reviewer finding LLM-AND-DELETION-DATA-ORPHANED: FirebaseUI's ProfileScreen deletes only the Auth account, and Firestore
rules then block any cleanup of `users/{uid}/**`. ProfileScreen's delete button can't be hidden or hooked before deletion,
so the Account tab gets its own screen.

- [x] AC1: Deleting the account deletes every document in `users/{uid}/jobs` and `users/{uid}/entries` **before** the Auth
      account is deleted (Firestore rules need the user signed in).
- [x] AC2: If Firebase answers `requires-recent-login`, the user re-authenticates and the deletion retries. Data deletion is
      idempotent, so a cancelled re-auth leaves an account with no data, which the confirm text already promised.
- [x] AC3: The confirm dialog says jobs and time entries are deleted permanently, then the account.
- [x] AC4: The Account tab keeps avatar, display name, sign-in identity and sign out (linking an email to an
      anonymous account, which ProfileScreen offered, is dropped); "Account > Delete account" still works.
- [x] AC5: `/delete-account` no longer tells users to delete jobs first.
- [x] AC6: Unit tests prove the order (data, then account) and the retry path; a live check with a throwaway Auth user (never
      the reviewer account) proves the Firestore documents are gone.
      Live check done with an anonymous user (2 jobs, 3 entries, then 0 and no Auth user). The email-user
      `requires-recent-login` re-auth path has widget-test coverage only.

## T16 Time Tracker redesign v2.2.0 (FULL lane; spec: tasks/redesign-spec.md)
Branch `redesign/2.2.0`. Each task lands green (analyze + tests) before the next.
- [x] T16.1 Theme + logo + R1 source guard (RED first: app/entry/entries screens use indigo/white literals).
- [x] T16.2 Nav shell (bar/rail with logo) + Account (pure `AccountBody`, danger zone, anonymous sign-out warning).
- [x] T16.3 Jobs cards + confirm-delete + job form decimal rate with validation (R4, R4b).
- [x] T16.4 Entry editor: start/duration math unit-tested first, then sliders with nudges and live summary (R5).
- [x] T16.5 Entries tab: explainer, day cards, orphan-entry fix (R6).
- [x] T16.6 Sign-in header/side panel (R3) + onboarding with the new logo; web favicon and manifest icons.
- [x] T16.7 Five-size layout tests over every plain widget (R8).
- [x] T16.8 Headless screenshots of the web build at five sizes, contact sheet checked.
- [ ] T16.9 MR to main; then version 2.2.0, "Release v2.2.0" run, merge release MR, trigger deploy:cloudrun.
