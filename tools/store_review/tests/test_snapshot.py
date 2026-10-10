from conftest import manifest, plist

from store_review.snapshot import load_snapshot


def test_dependencies_from_pubspec_and_lock(make_app):
    root = make_app({
        "pubspec.yaml": "name: demo\nversion: 2.1.0\ndependencies:\n  firebase_auth: ^5.5.2\n  flutter:\n    sdk: flutter\n",
        "pubspec.lock": "packages:\n  firebase_auth:\n    version: 5.5.2\n  shared_preferences_foundation:\n    version: 2.5.3\n",
    })
    snap = load_snapshot(root)
    assert {"firebase_auth", "shared_preferences_foundation"} <= snap.dependencies
    assert snap.version == "2.1.0"
    assert snap.name == "demo"


def test_info_plist_and_xcprivacy(make_app):
    root = make_app({
        "ios/Runner/Info.plist": plist("<dict><key>NSCameraUsageDescription</key><string>Scan receipts</string></dict>"),
        "ios/Runner/PrivacyInfo.xcprivacy": plist("<dict><key>NSPrivacyAccessedAPITypes</key><array/></dict>"),
    })
    snap = load_snapshot(root)
    assert snap.info_plist["NSCameraUsageDescription"] == "Scan receipts"
    assert snap.xcprivacy == {"NSPrivacyAccessedAPITypes": []}
    assert snap.info_plist_path == "ios/Runner/Info.plist"


def test_missing_platform_files_are_none(make_app):
    snap = load_snapshot(make_app({}))
    assert snap.info_plist is None
    assert snap.xcprivacy is None
    assert snap.manifest is None
    assert snap.target_sdk is None


def test_manifest_permissions_and_line(make_app):
    root = make_app({
        "android/app/src/main/AndroidManifest.xml": manifest(
            permissions='<uses-permission android:name="android.permission.CAMERA"/>',
        ),
    })
    snap = load_snapshot(root)
    assert snap.manifest_permissions() == {"android.permission.CAMERA": 2}


def test_target_sdk_groovy_and_kts(make_app):
    snap = load_snapshot(make_app({"android/app/build.gradle": "android {\n  defaultConfig {\n    targetSdk = 34\n  }\n}\n"}))
    assert (snap.target_sdk.value, snap.target_sdk.line, snap.target_sdk.path) == (34, 3, "android/app/build.gradle")
    (root := make_app({})).joinpath("android/app/build.gradle").unlink()
    snap = load_snapshot(make_app({"android/app/build.gradle.kts": "defaultConfig {\n  targetSdkVersion(35)\n}\n"}))
    assert snap.target_sdk.value == 35


def test_target_sdk_from_flutter_default_is_unknown(make_app):
    snap = load_snapshot(make_app({"android/app/build.gradle": "targetSdk = flutter.targetSdkVersion\n"}))
    assert snap.target_sdk.value is None
    assert "flutter.targetSdkVersion" in snap.target_sdk.text


def test_store_yaml_and_dart_sources(make_app):
    root = make_app({
        "store/listing.yaml": "privacy_policy_url: https://example.com/privacy\n",
        "lib/src/a.dart": "final s = 'Coming soon';\n",
        "lib/generated.g.dart": "final x = 'ignored';\n",
    })
    snap = load_snapshot(root)
    assert snap.store["listing"]["privacy_policy_url"] == "https://example.com/privacy"
    assert [path for path, _ in snap.dart_sources] == ["lib/src/a.dart"]


def test_env_is_injected(make_app):
    snap = load_snapshot(make_app({}), env={"STORE_REVIEW_DEMO_LOGIN": "x"})
    assert snap.env["STORE_REVIEW_DEMO_LOGIN"] == "x"
