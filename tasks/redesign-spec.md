# Spec: Time Tracker redesign (v2.2.0)

Decided with Ramy on 2026-10-13: a clean, modern Material 3 look with one teal brand colour (distinct from The Previewer's
indigo); the entry screen uses a start slider and a duration slider; the release goes through a "Release v2.2.0" run of
The Previewer. FULL lane: new screens, plus the Account tab, which holds account deletion.

## Goals
1. The app looks like a finished product: its own logo, one theme (light and dark), consistent cards and type.
2. Logging time is fast and can't go wrong: pick a day, drag a start time and a duration; the end time and pay follow.
3. Every screen works on a phone, a tablet and a laptop, with no overflow.
4. A first-time user understands what each tab is for.

## Non-goals
- No data model or Firestore rules changes. Entries stay `{jobId, start, end, comment}`; jobs stay `{name, ratePerHour}`.
- No change to how account deletion works (T15). The Account tab is restyled around the same `DeleteAccountAndDataButton`.
- No new sign-in providers.

## Acceptance criteria
- **R1 Theme.** One `AppTheme` (light and dark, `ThemeMode.system`) seeded from teal `#0F766E`. Screens take colours from the
  theme: no `Colors.indigo` and no hard-coded white or black text outside the theme file (a test checks the source,
  comments stripped).
- **R2 Logo.** A new Time Tracker logo (SVG, stopwatch with a check mark; no third-party marks), used on onboarding, the
  sign-in header and the navigation rail, plus the web favicon and manifest icons.
- **R3 Sign-in.** A branded header (logo, name, one-line purpose). On wide screens, a side panel with the same content.
  Email and anonymous sign-in and the privacy link stay.
- **R4 Jobs.** Each job is a card with its name and hourly rate. Swipe-to-delete asks for confirmation and says that the
  job's time entries are deleted too (reviewer finding LLM-IOS-DESTRUCTIVE-SWIPE-NO-CONFIRM). The empty state explains
  what a job is and offers "New job".
- **R4b Job form.** The hourly rate accepts decimals (for example 12.50) and shows a validation message for bad input
  instead of silently saving 0 (reviewer findings LLM-IOS-RATE-INPUT-WHOLE-NUMBERS and LLM-AND-RATE-SILENT-ZERO).
- **R5 Entry screen.** A day picker, a **start slider** (00:00–23:45, 15-minute steps) and a **duration slider**
  (15 minutes to 12 hours, 15-minute steps). The end time is computed as start plus duration, so it can never come before
  the start (reviewer finding LLM-AND-ENTRY-NEGATIVE-DURATION); an end past midnight shows "+1 day". Live summary: start,
  end, duration and pay (rate × hours). Each slider has ±15-minute nudge buttons and a large readout, because a
  96-step slider is too fine to hit exactly on a phone. Editing an existing entry keeps its exact times until a slider moves; an existing
  duration over 12 hours widens the slider instead of truncating.
- **R6 Entries tab.** A one-line explainer at the top ("Your timesheet: hours and pay per day, across all jobs"). Each day
  is a card with its total hours and pay and one row per job. The empty state says how to add the first entry. An entry
  whose job was deleted shows as "(deleted job)" instead of breaking the tab (reviewer finding
  LLM-IOS-ENTRIES-TAB-CRASH-RACE).
- **R7 Account.** A profile card (avatar, name, email or an "Anonymous" badge), Sign out, a separate "Danger zone" card
  holding `DeleteAccountAndDataButton`, the privacy link and the app version. An anonymous user who taps Sign out is
  warned first that their data can't be recovered afterwards. (The anonymous re-authentication finding during deletion
  is T15 territory and out of scope here.)
- **R8 Responsive.** A bottom bar below 600 px and a navigation rail with the logo from 600 px up. Content stays at most
  720 px wide on forms. Each screen is a thin Firebase-wired shell around a plain widget that takes data
  (`JobCard`, `DayCard`, `EntryEditor`, `AccountBody`, `SignInHeader`). Widget tests render those plain widgets and the nav shell at 360×740, 390×844, 820×1180,
  1180×820 and 1440×900 with no RenderFlex overflow.
- **R9 No regressions.** All existing tests pass, including the account deletion tests. `flutter analyze` is clean.
- **R10 Store review.** The Previewer's scan of the redesign has no new blockers, and it ships as v2.2.0 through the flow.

## Process
Build on branch `redesign/2.2.0` (CI runs on every push), merge by MR, then bump to 2.2.0 on `main`, open "Release
v2.2.0" for The Previewer, merge its release MR, and trigger the manual `deploy:cloudrun` job so the live URL shows the
redesign. The PAT `previewer-setup` expires 2026-10-17: renew it before the v2.2.0 run.

## Verification
`flutter analyze` · `flutter test` · engine gates (`uv run pytest`, `benchmark`, CI schema) · screenshots of the live web
build at the five sizes (headless, per the responsive recipe) on a contact sheet · the v2.2.0 Previewer run.
