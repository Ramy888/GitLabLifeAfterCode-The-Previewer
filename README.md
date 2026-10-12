# The Previewer

**Reviews your app the way Apple and Google will, before you submit.**

The Previewer is a GitLab Duo custom flow that rehearses **App Store** and **Google Play** review for a Flutter app.
You assign a release issue; agents review the app against the stores' guidelines, open fix merge requests, ask you
one checklist, and hand back a release merge request with a readiness score and a ready-to-submit package per store.
**Merging that MR is your approval** (Supervised autonomy). Nothing is ever uploaded to a store.

Built for the GitLab "Life After Code" hackathon, **Path B**: a fork of the MIT project
[bizz84/starter_architecture_flutter_firebase](https://github.com/bizz84/starter_architecture_flutter_firebase)
(a Flutter + Firebase time tracker), with all automation and the deployment added on or after Oct 5, 2026.

| | |
|---|---|
| Live app (Google Cloud Run) | https://time-tracker-web-57342278583.us-central1.run.app |
| Privacy policy / account deletion | [/privacy](https://time-tracker-web-57342278583.us-central1.run.app/privacy) · [/delete-account](https://time-tracker-web-57342278583.us-central1.run.app/delete-account) |
| A full review, end to end | [Issue #2 "Release v2.1.0"](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/1947121/showcase/-/work_items/2): handoff → fix MRs !1–!7 → resume → release MR [!8](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/1947121/showcase/-/merge_requests/8) |
| Flow definition | [`.gitlab/duo/flows/store-review.yaml`](.gitlab/duo/flows/store-review.yaml) · guide: [docs/STORE_REVIEW.md](docs/STORE_REVIEW.md) |
| Pipelines | [https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/1947121/showcase/-/pipelines](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/1947121/showcase/-/pipelines) |

## Before and after

| Before (manual, fragmented) | After (The Previewer) |
|---|---|
| Submit, wait a day or more, read a rejection, guess the fix, resubmit | Rehearse both reviews in minutes, before the first submission |
| Store rules spread across Apple's guidelines, Play policy and Data safety forms | Rule packs that cite the guideline for every finding |
| Fixes done by hand, one rejection at a time | One fix MR per auto-fixable finding, opened by an agent |
| No signal of readiness | Per-store readiness 0–100 with a confidence range; any blocker caps it at 40 |
| Rejection replies written from scratch | `@flow rejection: <message>`: an advocate decides fix or appeal and drafts the appeal with evidence |

What the first run found on this app, all real: targetSdk 34 below Play's required 36, release builds signed with the
debug key, **no INTERNET permission in release builds** (sign-in and Firestore would fail in production), no iOS
privacy manifest, template app names, and an account deletion that left the user's data behind. All are fixed in
this repository; both stores now score 100 with no blockers.

## How it uses the GitLab Duo Agent Platform

- **One custom flow, five agents**: a governor delegates to an Apple reviewer, a Google Play reviewer, a fixer (opens
  MRs) and a rejection advocate. Triggers: **Assign** (start a review) and **Mention** (`resume`, `rejection:`).
- **A deterministic engine the agents call** ([`tools/store_review`](tools/store_review)): it scans the app, scores it,
  validates the human's inputs and builds the store packages, so scores never come from a model's guess. The agents
  add judgement findings with a confidence, which the engine merges into the score.
- **Benchmarked**: a Rejection Corpus of 42 seeded cases; precision 0.971, recall 0.971, with two known gaps kept on
  purpose. CI fails below 0.90 / 0.85.
- **CI/CD as the gate**: the release MR pipeline re-checks every input (URLs return 200, the demo login exists as a
  masked variable), rebuilds the findings with the reviewers' judgement, and builds the packages and a signed AAB.
  Merging it publishes a GitLab Release with the report and artifacts.

## Lifecycle stages covered

**Plan** (release issue and one checklist) · **Create** (fix MRs) · **Verify** (scan, tests, benchmark) ·
**Secure** (privacy manifest, release signing, secrets only in masked variables, keyless deploy) · **Package**
(per-store packages, signed AAB) · **Release** (release MR, GitLab Release on merge) · **Configure** (store listing,
review notes, CI/CD variables) · **Govern** (Supervised approval by merge, cited guidelines, rejection advocate).

## Google Cloud

The web app runs on **Cloud Run** (nginx serving the Flutter web build plus the legal pages). GitLab CI deploys it
with **Workload Identity Federation**: no service-account keys exist; the trust is limited to this project's protected
branches. Firebase Auth and Firestore (owner-only rules) back the app. Deploy code: [`deploy/cloudrun`](deploy/cloudrun),
setup: [docs/KEYLESS_DEPLOY.md](docs/KEYLESS_DEPLOY.md).

## License

MIT ([LICENSE.md](LICENSE.md)): the original app by Andrea Bizzotto, and The Previewer's additions by Ramy Magdy.
Third-party components keep their own OSI-approved licenses (mostly BSD-3-Clause for the Flutter and Firebase
packages; MIT for Riverpod, PyYAML and pytest).

---

## The original app

A time tracking application built with Flutter & Firebase: 

![](/.github/images/time-tracker-screenshots.png)

This is intended as a **reference app** based on my [Riverpod Architecture](https://codewithandrea.com/articles/flutter-app-architecture-riverpod-introduction/).

> **Note**: this project used to be called "Started Architecture for Flutter & Firebase" (based on this [old article](https://codewithandrea.com/videos/starter-architecture-flutter-firebase/)). As of January 2023, it follows my updated [Riverpod Architecture](https://codewithandrea.com/articles/flutter-app-architecture-riverpod-introduction/), using the latest packages.

## Flutter web preview

A Flutter web preview of the app is available here:

- [Time Tracker | Flutter web demo](https://starter-architecture-flutter.web.app)

## Features

- **Simple onboarding page**
- **Full authentication flow** (using email & password)
- **Jobs**: users can view, create, edit, and delete their own private jobs (each job has a name and hourly rate)
- **Entries**: for each job, user can view, create, edit, and delete the corresponding entries (an entry is a task with a start and end time, with an optional comment)
- **A report page** that shows a daily breakdown of all jobs, hours worked and pay, along with the totals.

All the data is persisted with Firestore and is kept in sync across multiple devices.

## Roadmap

- [ ] Add missing tests
- [x] Stateful Nested Navigation (available since GoRouter 7.1)
- [ ] Use controllers / notifiers consistently across the app (some code still needs to be updated)
- [ ] Add localization
- [ ] Use the new Firebase UI packages where useful
- [ ] Responsive UI

> This is a tentative roadmap. There is no ETA for any of the points above. This is a low priority project and I don't have much time to maintain it.

## Relevant Articles

The app is based on my Flutter Riverpod architecture, which is explained in detail here:

- [Flutter App Architecture with Riverpod: An Introduction](https://codewithandrea.com/articles/flutter-app-architecture-riverpod-introduction/)
- [Flutter Project Structure: Feature-first or Layer-first?](https://codewithandrea.com/articles/flutter-project-structure/)
- [Flutter App Architecture: The Repository Pattern](https://codewithandrea.com/articles/flutter-repository-pattern/)
- [How to Build a Robust Flutter App Initialization Flow with Riverpod](https://codewithandrea.com/articles/robust-app-initialization-riverpod/)

More more info on Riverpod, read this:

- [Flutter Riverpod 2.0: The Ultimate Guide](https://codewithandrea.com/articles/flutter-state-management-riverpod/)

## Packages in use

These are the main packages used in the app:

- [Flutter Riverpod](https://pub.dev/packages/flutter_riverpod) for data caching, dependency injection, and more
- [Riverpod Generator](https://pub.dev/packages/riverpod_generator) and [Riverpod Lint](https://pub.dev/packages/riverpod_lint) for the latest Riverpod APIs
- [GoRouter](https://pub.dev/packages/go_router) for navigation
- [Firebase Auth](https://pub.dev/packages/firebase_auth) and [Firebase UI Auth](https://pub.dev/packages/firebase_ui_auth) for authentication
- [Cloud Firestore](https://pub.dev/packages/cloud_firestore) as a realtime database
- [Firebase UI for Firestore](https://pub.dev/packages/firebase_ui_firestore) for the `FirestoreListView` widget with pagination support
- [RxDart](https://pub.dev/packages/rxdart) for combining multiple Firestore collections as needed
- [Intl](https://pub.dev/packages/intl) for currency, date, time formatting
- [Mocktail](https://pub.dev/packages/mocktail) for testing
- [Equatable](https://pub.dev/packages/equatable) to reduce boilerplate code in model classes

See the [pubspec.yaml](pubspec.yaml) file for the complete list.

## Running the project with Firebase

To use this project with Firebase, follow these steps:

- Create a new project with the Firebase console
- Enable Firebase Authentication, along with the Email/Password Authentication Sign-in provider in the Firebase Console (Authentication > Sign-in method > Email/Password > Edit > Enable > Save)
- Enable Cloud Firestore

Then, follow one of the two approaches below. 👇

### 1. Using the CLI

Make sure you have the Firebase CLI and [FlutterFire CLI](https://pub.dev/packages/flutterfire_cli) installed.

Then run this on the terminal from the root of this project:

- Run `firebase login` so you have access to the Firebase project you have created
- Run `flutterfire configure` and follow all the steps

For more info, follow this guide:

- [How to add Firebase to a Flutter app with FlutterFire CLI](https://codewithandrea.com/articles/flutter-firebase-flutterfire-cli/)

### 2. Manual way (not recommended)

If you don't want to use FlutterFire CLI, follow these steps instead:

- Register separate iOS, Android, and web apps in the Firebase project settings.
- On Android, use `com.RDPT.thepreviewer` as the package name.
- then, [download and copy](https://firebase.google.com/docs/flutter/setup#configure_an_android_app) `google-services.json` into `android/app`.
- On iOS, use `com.RDPT.thepreviewer` as the bundle ID.
- then, [download and copy](https://firebase.google.com/docs/flutter/setup#configure_an_ios_app) `GoogleService-Info.plist` into `iOS/Runner`, and add it to the Runner target in Xcode.

That's it. Have fun!

## [License: MIT](LICENSE.md)
