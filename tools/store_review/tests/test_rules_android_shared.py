from conftest import manifest

from store_review.rules import run_checks
from store_review.snapshot import load_snapshot

AUTH = "name: demo\nversion: 1.0.0\ndependencies:\n  firebase_auth: ^5.0.0\n"
LISTING_OK = "privacy_policy_url: https://example.com/privacy\naccount_deletion_url: https://example.com/delete\n"
GRADLE = "android {{\n  defaultConfig {{\n    targetSdk = {sdk}\n  }}\n}}\n"
MANIFEST = "android/app/src/main/AndroidManifest.xml"


def run(root, env=None):
    return run_checks(load_snapshot(root, env=env or {}))


def ids(root, env=None):
    return {f.id for f in run(root, env)}


def android_app(make_app, sdk=36, application="", permissions="", extra=None):
    files = {"android/app/build.gradle": GRADLE.format(sdk=sdk), MANIFEST: manifest(application, permissions)}
    return make_app({**files, **(extra or {})})


# AND-TARGETSDK
def test_target_sdk_below_required(make_app):
    (f,) = [f for f in run(android_app(make_app, sdk=34)) if f.id == "AND-TARGETSDK"]
    assert f.severity == "blocker" and f.evidence[0].line == 3 and "36" in f.fix.recipe


def test_target_sdk_current_passes(make_app):
    assert "AND-TARGETSDK" not in ids(android_app(make_app, sdk=36))


def test_target_sdk_unknown_is_not_flagged(make_app):
    root = make_app({"android/app/build.gradle": "targetSdk = flutter.targetSdkVersion\n", MANIFEST: manifest()})
    assert "AND-TARGETSDK" not in ids(root)


# AND-DELETION-URL
def test_deletion_url_missing_for_account_app(make_app):
    root = android_app(make_app, extra={"pubspec.yaml": AUTH})
    (f,) = [f for f in run(root) if f.id == "AND-DELETION-URL"]
    assert f.fix.kind == "handoff"


def test_deletion_url_present(make_app):
    root = android_app(make_app, extra={"pubspec.yaml": AUTH, "store/listing.yaml": LISTING_OK})
    assert "AND-DELETION-URL" not in ids(root)


def test_deletion_url_not_needed_without_accounts(make_app):
    assert "AND-DELETION-URL" not in ids(android_app(make_app))


# AND-DATASAFETY-PERM
def test_dangerous_permission_undeclared(make_app):
    root = android_app(make_app, permissions='<uses-permission android:name="android.permission.CAMERA"/>')
    (f,) = [f for f in run(root) if f.id == "AND-DATASAFETY-PERM"]
    assert f.evidence[0].path == MANIFEST and "CAMERA" in f.title


def test_dangerous_permission_declared(make_app):
    root = android_app(make_app, permissions='<uses-permission android:name="android.permission.CAMERA"/>',
                       extra={"store/data_safety.yaml": "declared_permissions:\n  - android.permission.CAMERA\n"})
    assert "AND-DATASAFETY-PERM" not in ids(root)


def test_normal_permission_ignored(make_app):
    root = android_app(make_app, permissions='<uses-permission android:name="android.permission.INTERNET"/>')
    assert "AND-DATASAFETY-PERM" not in ids(root)


# AND-CLEARTEXT / AND-DEBUGGABLE / AND-EXPORTED
def test_cleartext_and_debuggable(make_app):
    m = ('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application '
         'android:usesCleartextTraffic="true" android:debuggable="true"></application></manifest>')
    root = make_app({"android/app/build.gradle": GRADLE.format(sdk=36), MANIFEST: m})
    assert {"AND-CLEARTEXT", "AND-DEBUGGABLE"} <= ids(root)


def test_clean_manifest_has_no_flags(make_app):
    assert not {"AND-CLEARTEXT", "AND-DEBUGGABLE", "AND-EXPORTED"} & ids(android_app(make_app))


def test_exported_missing_on_intent_filter(make_app):
    app = '<activity android:name=".Main"><intent-filter><action android:name="android.intent.action.MAIN"/></intent-filter></activity>'
    assert "AND-EXPORTED" in ids(android_app(make_app, application=app))


def test_exported_declared(make_app):
    app = ('<activity android:name=".Main" android:exported="true"><intent-filter>'
           '<action android:name="android.intent.action.MAIN"/></intent-filter></activity>')
    assert "AND-EXPORTED" not in ids(android_app(make_app, application=app))


# SHR-ACCOUNT-DELETION
def test_account_without_deletion_path(make_app):
    root = make_app({"pubspec.yaml": AUTH, "lib/main.dart": "void main() {}\n"})
    (f,) = [f for f in run(root) if f.id == "SHR-ACCOUNT-DELETION"]
    assert f.store == "shared" and f.severity == "blocker"


def test_firebase_ui_profile_screen_counts_as_deletion(make_app):
    root = make_app({"pubspec.yaml": AUTH, "lib/profile.dart": "Widget build() => ProfileScreen(providers: p);\n"})
    assert "SHR-ACCOUNT-DELETION" not in ids(root)


def test_user_delete_call_counts_as_deletion(make_app):
    root = make_app({"pubspec.yaml": AUTH, "lib/a.dart": "await FirebaseAuth.instance.currentUser!.delete();\n"})
    assert "SHR-ACCOUNT-DELETION" not in ids(root)


def test_review_notes_path_counts_as_deletion(make_app):
    root = make_app({"pubspec.yaml": AUTH, "store/review_notes.yaml": "account_deletion_path: Settings > Account > Delete\n"})
    assert "SHR-ACCOUNT-DELETION" not in ids(root)


# SHR-DEMO-LOGIN
def test_demo_login_missing(make_app):
    root = make_app({"pubspec.yaml": AUTH})
    (f,) = [f for f in run(root) if f.id == "SHR-DEMO-LOGIN"]
    assert f.fix.kind == "handoff"


def test_demo_login_present(make_app):
    assert "SHR-DEMO-LOGIN" not in ids(make_app({"pubspec.yaml": AUTH}), env={"STORE_REVIEW_DEMO_LOGIN": "u:p"})


def test_demo_login_not_needed_without_accounts(make_app):
    assert "SHR-DEMO-LOGIN" not in ids(make_app({}))


# SHR-PRIVACY-URL
def test_privacy_url_missing(make_app):
    assert "SHR-PRIVACY-URL" in ids(make_app({}))


def test_privacy_url_present(make_app):
    assert "SHR-PRIVACY-URL" not in ids(make_app({"store/listing.yaml": LISTING_OK}))


# SHR-PLACEHOLDER-UI
def test_placeholder_ui_string(make_app):
    root = make_app({"lib/a.dart": "Text('Reports: coming soon')\n"})
    (f,) = [f for f in run(root) if f.id == "SHR-PLACEHOLDER-UI"]
    assert f.evidence[0].line == 1


def test_placeholder_in_comment_ignored(make_app):
    assert "SHR-PLACEHOLDER-UI" not in ids(make_app({"lib/a.dart": "// TODO: refactor\nText('Reports')\n"}))


# SHR-METADATA-PLATFORM
def test_metadata_mentions_other_platform(make_app):
    listing = LISTING_OK + "ios:\n  description: Also available on Google Play\n"
    assert "SHR-METADATA-PLATFORM" in ids(make_app({"store/listing.yaml": listing}))


def test_metadata_clean(make_app):
    listing = LISTING_OK + "ios:\n  description: Track your time\nandroid:\n  description: Track your time\n"
    assert "SHR-METADATA-PLATFORM" not in ids(make_app({"store/listing.yaml": listing}))


# AND-DEBUG-SIGNING
RELEASE_DEBUG = "android {\n  buildTypes {\n    release {\n      signingConfig = signingConfigs.debug\n    }\n  }\n}\n"
RELEASE_OK = "android {\n  buildTypes {\n    release {\n      signingConfig = signingConfigs.release\n    }\n  }\n}\n"


def test_release_signed_with_debug_key(make_app):
    root = make_app({"android/app/build.gradle": RELEASE_DEBUG, MANIFEST: manifest()})
    (f,) = [f for f in run(root) if f.id == "AND-DEBUG-SIGNING"]
    assert f.severity == "blocker" and f.evidence[0].line == 4


def test_release_signed_with_release_key(make_app):
    root = make_app({"android/app/build.gradle": RELEASE_OK, MANIFEST: manifest()})
    assert "AND-DEBUG-SIGNING" not in ids(root)


def test_debug_build_type_may_use_debug_key(make_app):
    gradle = "android {\n  buildTypes {\n    debug {\n      signingConfig = signingConfigs.debug\n    }\n  }\n}\n"
    assert "AND-DEBUG-SIGNING" not in ids(make_app({"android/app/build.gradle": gradle, MANIFEST: manifest()}))


# AND-EXAMPLE-PACKAGE
def test_example_package_rejected(make_app):
    gradle = 'android {\n  defaultConfig {\n    applicationId = "com.example.myapp"\n    targetSdk = 36\n  }\n}\n'
    (f,) = [f for f in run(make_app({"android/app/build.gradle": gradle, MANIFEST: manifest()})) if f.id == "AND-EXAMPLE-PACKAGE"]
    assert f.severity == "blocker" and f.evidence[0].line == 3


def test_real_package_passes(make_app):
    gradle = 'android {\n  defaultConfig {\n    applicationId = "com.RDPT.thepreviewer"\n    targetSdk = 36\n  }\n}\n'
    assert "AND-EXAMPLE-PACKAGE" not in ids(make_app({"android/app/build.gradle": gradle, MANIFEST: manifest()}))
