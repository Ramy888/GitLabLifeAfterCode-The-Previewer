"""Regenerate the Rejection Corpus fixtures: `uv run python corpus/_generate.py`.

Each case is a tiny Flutter app tree plus case.yaml with the store-style rejection it models and the rule IDs a
correct reviewer must report. Two cases are known gaps of the deterministic rules and are kept on purpose, so the
published precision and recall stay honest.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

HERE = Path(__file__).parent
PLIST = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
         '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<dict>\n{body}</dict>\n</plist>\n')
ENC = "  <key>ITSAppUsesNonExemptEncryption</key><false/>\n"
LISTING = {"privacy_policy_url": "https://example.com/privacy", "account_deletion_url": "https://example.com/delete",
           "ios": {"name": "Demo", "description": "Track your time."},
           "android": {"name": "Demo", "description": "Track your time."}}
LOGIN_ENV = {"STORE_REVIEW_DEMO_LOGIN": "reviewer:demo"}
PROFILE = "Widget profile() => ProfileScreen(providers: providers);\n"


def manifest(perms=(), app_attrs="", app_body=""):
    p = "".join(f'  <uses-permission android:name="{x}"/>\n' for x in perms)
    return ('<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
            f'{p}  <application android:label="demo"{app_attrs}>\n{app_body}  </application>\n</manifest>\n')


def xcprivacy(category, code):
    return PLIST.format(body=(
        "  <key>NSPrivacyAccessedAPITypes</key><array><dict>"
        f"<key>NSPrivacyAccessedAPIType</key><string>{category}</string>"
        f"<key>NSPrivacyAccessedAPITypeReasons</key><array><string>{code}</string></array></dict></array>\n"))


def app(deps=(), plist_body=ENC, sdk=36, signing="release", perms=(), app_attrs="", app_body="", listing=None, dart=None,
        xcp=None, data_safety=None, review_notes=None):
    dep_lines = "".join(f"  {d}: any\n" for d in deps)
    files = {
        "pubspec.yaml": f"name: demo\nversion: 1.0.0\ndependencies:\n  flutter:\n    sdk: flutter\n{dep_lines}",
        "ios/Runner/Info.plist": PLIST.format(body=plist_body),
        "android/app/build.gradle": (f"android {{\n  defaultConfig {{\n    targetSdk = {sdk}\n  }}\n"
                                     f"  buildTypes {{\n    release {{\n      signingConfig = signingConfigs.{signing}\n"
                                     "    }\n  }\n}\n"),
        "android/app/src/main/AndroidManifest.xml": manifest(perms, app_attrs, app_body),
        "store/listing.yaml": yaml.safe_dump(LISTING if listing is None else listing, allow_unicode=True),
        "lib/main.dart": "void main() => runApp(const App());\n",
    }
    for rel, text in (dart or {}).items():
        files[rel] = text
    if xcp:
        files["ios/Runner/PrivacyInfo.xcprivacy"] = xcp
    if data_safety:
        files["store/data_safety.yaml"] = yaml.safe_dump(data_safety)
    if review_notes:
        files["store/review_notes.yaml"] = yaml.safe_dump(review_notes)
    return files


def key(k, v):
    return f"  <key>{k}</key><string>{v}</string>\n"


ACCOUNT = dict(deps=("firebase_auth", "firebase_ui_auth"), dart={"lib/profile.dart": PROFILE})
UD = "NSPrivacyAccessedAPICategoryUserDefaults"
CASES = [
    # --- positives: every rule at least once -------------------------------------------------------------
    ("ios-camera-no-purpose", "Apple 5.1.1: the app accesses the camera without a purpose string.",
     app(deps=("image_picker",)), ["IOS-USAGE-MISSING"], {}),
    ("ios-location-no-purpose", "Apple 5.1.1: location is requested without explaining why.",
     app(deps=("geolocator",)), ["IOS-USAGE-MISSING"], {}),
    ("ios-microphone-no-purpose", "Apple 5.1.1: microphone access has no usage description.",
     app(deps=("record",)), ["IOS-USAGE-MISSING"], {}),
    ("ios-placeholder-purpose", "Apple 5.1.1: the camera purpose string does not explain the use.",
     app(plist_body=ENC + key("NSCameraUsageDescription", "TODO")), ["IOS-USAGE-PLACEHOLDER"], {}),
    ("ios-short-purpose", "Apple 5.1.1: the purpose string 'Camera' is not sufficient.",
     app(plist_body=ENC + key("NSCameraUsageDescription", "Camera")), ["IOS-USAGE-PLACEHOLDER"], {}),
    ("ios-missing-privacy-manifest", "ITMS-91053: missing API declaration for UserDefaults.",
     app(deps=("shared_preferences",)), ["IOS-PRIVACY-MANIFEST"], {}),
    ("ios-invalid-reason-code", "ITMS-91053: invalid reason code in the privacy manifest.",
     app(xcp=xcprivacy(UD, "ZZ99.9")), ["IOS-PRIVACY-REASON"], {}),
    ("ios-reason-from-wrong-category", "ITMS-91053: reason C617.1 is not valid for UserDefaults.",
     app(xcp=xcprivacy(UD, "C617.1")), ["IOS-PRIVACY-REASON"], {}),
    ("ios-no-export-compliance", "Missing export compliance information for the build.",
     app(plist_body=""), ["IOS-ENCRYPTION-FLAG"], {}),
    ("ios-ats-disabled", "Apple 2.5: App Transport Security is disabled globally without justification.",
     app(plist_body=ENC + "  <key>NSAppTransportSecurity</key><dict><key>NSAllowsArbitraryLoads</key><true/></dict>\n"),
     ["IOS-ATS-ARBITRARY"], {}),
    ("ios-google-login-only", "Apple 4.8: the app uses a third-party login without an equivalent option.",
     app(deps=("google_sign_in",)), ["IOS-SIWA"], {}),
    ("shared-no-account-deletion", "Apple 5.1.1(v): the app supports account creation but not deletion.",
     app(deps=("firebase_auth",)), ["SHR-ACCOUNT-DELETION"], LOGIN_ENV),
    ("android-target-34", "Play: your app must target API level 36 or higher.",
     app(sdk=34), ["AND-TARGETSDK"], {}),
    ("android-target-35", "Play: target API level 35 is below the current requirement.",
     app(sdk=35), ["AND-TARGETSDK"], {}),
    ("android-no-deletion-url", "Play User Data: provide a web link where users can request account deletion.",
     app(**ACCOUNT, listing={**LISTING, "account_deletion_url": None}), ["AND-DELETION-URL"], LOGIN_ENV),
    ("android-camera-undeclared", "Play Data safety: the app collects photos but the form says no data is collected.",
     app(perms=("android.permission.CAMERA",)), ["AND-DATASAFETY-PERM"], {}),
    ("android-location-undeclared", "Play Data safety: location access is not disclosed.",
     app(perms=("android.permission.ACCESS_FINE_LOCATION",)), ["AND-DATASAFETY-PERM"], {}),
    ("android-cleartext", "Play security: cleartext traffic is allowed for all hosts.",
     app(app_attrs=' android:usesCleartextTraffic="true"'), ["AND-CLEARTEXT"], {}),
    ("android-debuggable", "Play: the release build is debuggable.",
     app(app_attrs=' android:debuggable="true"'), ["AND-DEBUGGABLE"], {}),
    ("android-debug-signed-release", "Play: you uploaded an app bundle that was signed in debug mode.",
     app(signing="debug"), ["AND-DEBUG-SIGNING"], {}),
    ("android-exported-missing", "Upload error: android:exported must be set for components with intent filters.",
     app(app_body='    <activity android:name=".Main"><intent-filter><action android:name="android.intent.action.MAIN"/>'
                  "</intent-filter></activity>\n"), ["AND-EXPORTED"], {}),
    ("shared-no-demo-login", "Apple 2.1: we could not sign in; please provide a demo account.",
     app(**ACCOUNT), ["SHR-DEMO-LOGIN"], {}),
    ("shared-no-privacy-url", "Apple 5.1.1(i): the app is missing a privacy policy link.",
     app(listing={k: v for k, v in LISTING.items() if k != "privacy_policy_url"}), ["SHR-PRIVACY-URL"], {}),
    ("shared-coming-soon", "Apple 2.1: the app shows features marked 'coming soon'.",
     app(dart={"lib/reports.dart": "Text('Reports: coming soon')\n"}), ["SHR-PLACEHOLDER-UI"], {}),
    ("shared-lorem-ipsum", "Play Minimum functionality: placeholder content is shown to users.",
     app(dart={"lib/about.dart": "const about = 'Lorem ipsum dolor sit amet';\n"}), ["SHR-PLACEHOLDER-UI"], {}),
    ("shared-ios-listing-mentions-android", "Apple 2.3.10: the description references another platform.",
     app(listing={**LISTING, "ios": {"name": "Demo", "description": "Also on Android."}}), ["SHR-METADATA-PLATFORM"], {}),
    ("shared-android-listing-mentions-iphone", "Play: the listing references another platform's devices.",
     app(listing={**LISTING, "android": {"name": "Demo", "description": "Best on iPhone."}}), ["SHR-METADATA-PLATFORM"], {}),
    ("multi-android-release", "Play: several policy issues found in this release.",
     app(sdk=34, perms=("android.permission.CAMERA",), dart={"lib/x.dart": "Text('Export: coming soon')\n"}),
     ["AND-TARGETSDK", "AND-DATASAFETY-PERM", "SHR-PLACEHOLDER-UI"], {}),
    ("multi-ios-release", "Apple: several issues found in this build.",
     app(deps=("image_picker",), plist_body="  <key>NSAppTransportSecurity</key><dict><key>NSAllowsArbitraryLoads</key>"
         "<true/></dict>\n"), ["IOS-USAGE-MISSING", "IOS-ENCRYPTION-FLAG", "IOS-ATS-ARBITRARY"], {}),
    # --- known gaps, kept on purpose -----------------------------------------------------------------------
    ("gap-permission-handler-camera", "Apple 5.1.1: camera requested through permission_handler without a purpose "
     "string. Known gap: permission_handler declares nothing by itself, so the rule cannot see it.",
     app(deps=("permission_handler",), dart={"lib/cam.dart": "await Permission.camera.request();\n"}),
     ["IOS-USAGE-MISSING"], {}),
    ("gap-custom-delete-method", "Not a rejection: the app deletes accounts through a custom API call. Known gap: "
     "the rule does not recognise removeMyProfile() as deletion and reports a false positive.",
     app(deps=("firebase_auth",), dart={"lib/settings.dart": "onTap: () => api.removeMyProfile(),\n"}), [], LOGIN_ENV),
    # --- clean apps ----------------------------------------------------------------------------------------
    ("clean-minimal", "Clean app.", app(), [], {}),
    ("clean-camera-with-purposes", "Clean app with camera and photo purpose strings.",
     app(deps=("image_picker",), plist_body=ENC + key("NSCameraUsageDescription", "Take a photo of your receipt")
         + key("NSPhotoLibraryUsageDescription", "Attach a receipt photo from your library")), [], {}),
    ("clean-prefs-with-manifest", "Clean app that declares UserDefaults with CA92.1.",
     app(deps=("shared_preferences",), xcp=xcprivacy(UD, "CA92.1")), [], {}),
    ("clean-firebaseui-deletion", "Wrong rejection: 'Apple 5.1.1(v), account deletion missing.' FirebaseUI's "
     "ProfileScreen renders a Delete account button, so the right response is an appeal.",
     app(**ACCOUNT), [], LOGIN_ENV),
    ("clean-delete-call", "Clean account app that deletes the user in code.",
     app(deps=("firebase_auth",), dart={"lib/settings.dart": "await FirebaseAuth.instance.currentUser!.delete();\n"}),
     [], LOGIN_ENV),
    ("clean-android-declared-camera", "Clean app that declares camera data in Data safety.",
     app(perms=("android.permission.CAMERA",), data_safety={"declared_permissions": ["android.permission.CAMERA"]}),
     [], {}),
    ("clean-google-and-apple-login", "Clean app offering Sign in with Apple next to Google.",
     app(deps=("google_sign_in", "sign_in_with_apple")), [], {}),
    ("clean-todo-in-comment", "Clean app with a TODO only in a code comment.",
     app(dart={"lib/a.dart": "// TODO: refactor\nText('Reports')\n"}), [], {}),
    ("clean-normal-permission", "Clean app that only needs INTERNET.",
     app(perms=("android.permission.INTERNET",)), [], {}),
    ("clean-exported-activity", "Clean app whose launcher activity declares android:exported.",
     app(app_body='    <activity android:name=".Main" android:exported="true"><intent-filter>'
                  '<action android:name="android.intent.action.MAIN"/></intent-filter></activity>\n'), [], {}),
]


def main() -> None:
    for d in HERE.iterdir():
        if d.is_dir():
            shutil.rmtree(d)
    for name, rejection, files, expected, env in CASES:
        case = HERE / name
        for rel, text in files.items():
            p = case / "app" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        meta = {"rejection": rejection, "expected": expected, "env": env}
        (case / "case.yaml").write_text(yaml.safe_dump(meta, sort_keys=False, allow_unicode=True))
    print(f"wrote {len(CASES)} cases")


if __name__ == "__main__":
    main()
