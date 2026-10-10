# The Previewer

Reviews your app the way Apple and Google will, before you submit. The Previewer rehearses Apple App Store review
and Google Play review for this Flutter app.
A GitLab Duo flow reviews the app the way each store would, fixes what it can through merge requests, asks you once
for what only you have, and hands you a package ready to submit for each store. It never uploads anything to a store.

## How a review runs

1. Open an issue such as "Release 2.1.0" and assign it to the flow's service account.
2. The **governor** agent runs the engine (`store-review scan`) and asks the **iOS reviewer** and **Android reviewer**
   agents for judgement findings. It asks the **fixer** to open one merge request per auto-fixable finding.
3. The governor posts one note: readiness per store, the fix merge requests, and a checklist of what it needs from you.
4. You add what it asks for (URLs in `store/listing.yaml`, the demo account as the masked CI/CD variable
   `STORE_REVIEW_DEMO_LOGIN`, yes/no answers as a reply), make any "fixes only you can make" (such as release
   signing, below), and comment `@<service account> resume`. The note gives the exact account to mention.
5. The governor validates your inputs. If something is missing it posts a shorter checklist. If everything is in
   place it opens the release merge request on `store-review/<version>`, whose pipeline rebuilds the findings and the
   per-store packages. **Merging it is your approval.** Tag the merge to publish a GitLab Release.
6. If a store rejects the app later, comment `@<service account> rejection: <the store's message>`. The **advocate**
   decides whether the rejection is valid (the fixer opens a fix) or wrong (it writes the appeal with evidence).

## Run it locally

```sh
cd tools/store_review
uv run store-review scan --app ../.. --out ../../findings.json --report ../../review-report.md
uv run store-review handoff --findings ../../findings.json
uv run store-review validate-inputs --app ../..
uv run store-review package --store ios --findings ../../findings.json --app ../..
uv run store-review benchmark
uv run pytest
```

## The readiness score

Each store gets a score from 0 to 100 with a range:

- Any open **blocker**, including a missing input, caps the score at 40 and marks the store **blocked**.
- Otherwise the score is 100 minus the weight of each open warning. Warnings found by the reviewer agents count
  their weight times the agent's confidence.
- The range shows how much the agents' judgement could move the score: the low end assumes every agent finding is
  right, the high end assumes none is.
- The benchmark line next to the score is the precision and recall of the deterministic rules on the Rejection
  Corpus. It describes the tool, not your app, so it never changes the score.

The score is a rehearsal signal. It is not a prediction from Apple or Google.

## The Rejection Corpus

`tools/store_review/corpus/` holds small app trees, each modelling one store rejection (or a clean app), with the rule
IDs a correct reviewer must report. `store-review benchmark` runs every rule over every case and CI fails below 0.90
precision or 0.85 recall. Two cases are known gaps, kept on purpose so the numbers stay honest:
`gap-permission-handler-camera` (a missed camera purpose string) and `gap-custom-delete-method` (a false account
deletion alarm). Regenerate the cases with `uv run python corpus/_generate.py`.

## Rules

Rule packs live in `tools/store_review/store_review/rules/*.yaml`. Each rule cites its guideline and source page.

| Rule | Store | Checks |
|---|---|---|
| `IOS-USAGE-MISSING` | Apple | A plugin needs an `NS*UsageDescription` key that Info.plist lacks (5.1.1) |
| `IOS-USAGE-PLACEHOLDER` | Apple | A purpose string is too short or reads like a placeholder (5.1.1) |
| `IOS-PRIVACY-MANIFEST` | Apple | A required-reason API is used but there is no app privacy manifest (ITMS-91053) |
| `IOS-PRIVACY-REASON` | Apple | The privacy manifest uses an unapproved reason code (ITMS-91053) |
| `IOS-ENCRYPTION-FLAG` | Apple | The export compliance answer is missing |
| `IOS-ATS-ARBITRARY` | Apple | App Transport Security is off for every domain (2.5) |
| `IOS-SIWA` | Apple | A third-party login without Sign in with Apple (4.8) |
| `AND-TARGETSDK` | Google Play | `targetSdk` below the current requirement (36 since 2026-08-31) |
| `AND-DEBUG-SIGNING` | Google Play | The release build is signed with the debug key |
| `AND-EXAMPLE-PACKAGE` | Google Play | The applicationId starts with the restricted `com.example` prefix |
| `AND-DELETION-URL` | Google Play | Accounts exist but there is no web link for account deletion |
| `AND-DATASAFETY-PERM` | Google Play | A dangerous permission is missing from the Data safety answers |
| `AND-CLEARTEXT` | Google Play | Cleartext HTTP allowed for every host |
| `AND-DEBUGGABLE` | Google Play | The manifest marks the app debuggable |
| `AND-EXPORTED` | Google Play | A component with an intent filter lacks `android:exported` |
| `SHR-ACCOUNT-DELETION` | Both | Accounts can be created but not deleted in the app (Apple 5.1.1(v), Play User Data) |
| `SHR-DEMO-LOGIN` | Both | Reviewers need a demo account (Apple 2.1, Play App access) |
| `SHR-PRIVACY-URL` | Both | No privacy policy URL |
| `SHR-PLACEHOLDER-UI` | Both | Text such as "coming soon" or "lorem ipsum" in the UI (Apple 2.1, Play Minimum functionality) |
| `SHR-METADATA-PLATFORM` | Both | A listing mentions the other platform (Apple 2.3.10) |

## What is real and what is simulated

| Real | Simulated |
|---|---|
| The scans of this repository, every finding and its evidence | Store decisions: the tool never uploads, and only Apple and Google decide |
| Fix merge requests and the pipelines that prove them | Rejection messages in the demo come from the Rejection Corpus and are labelled as such |
| The readiness score, computed from the findings by a published formula | The reviewer agents' judgement findings are model output, shown with their confidence |
| The per-store packages in the GitLab Release | A signed Android build is proven only once the upload key variables exist; the tests check the gradle text, not a signed AAB |
| The live web build on Cloud Run | |

## Release signing (a fix only you can make)

`AND-DEBUG-SIGNING` is a manual fix because it involves your upload key. Create an upload keystore, save it as the
masked CI/CD variables `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` and
`ANDROID_KEY_PASSWORD` (the `build:android` job writes `android/key.properties` from them), then point the release
build at it in `android/app/build.gradle`:

```groovy
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    signingConfigs {
        release {
            keyAlias = keystoreProperties["keyAlias"]
            keyPassword = keystoreProperties["keyPassword"]
            storeFile = keystoreProperties["storeFile"] ? file(keystoreProperties["storeFile"]) : null
            storePassword = keystoreProperties["storePassword"]
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.release
        }
    }
}
```

## Secrets

The demo account is stored only in the masked CI/CD variable `STORE_REVIEW_DEMO_LOGIN`. The engine checks that it
exists and never prints it. Never paste passwords into an issue or a merge request.
