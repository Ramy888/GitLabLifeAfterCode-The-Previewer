from conftest import plist

from store_review.rules import run_checks
from store_review.snapshot import load_snapshot

PUBSPEC = "name: demo\nversion: 1.0.0\ndependencies:\n{deps}\n"


def ids(root, **env):
    return {f.id for f in run_checks(load_snapshot(root, env=env))}


def info(keys: str = "") -> str:
    return plist(f"<dict>{keys}<key>ITSAppUsesNonExemptEncryption</key><false/></dict>")


def findings(root, rule_id):
    return [f for f in run_checks(load_snapshot(root, env={})) if f.id == rule_id]


# IOS-USAGE-MISSING
def test_usage_missing_when_plugin_needs_key(make_app):
    root = make_app({"pubspec.yaml": PUBSPEC.format(deps="  image_picker: ^1.0.0"), "ios/Runner/Info.plist": info()})
    (f,) = [f for f in findings(root, "IOS-USAGE-MISSING") if "NSCameraUsageDescription" in f.title]
    assert f.severity == "blocker" and f.store == "ios" and f.guideline.startswith("Apple 5.1.1")
    assert f.evidence[0].path == "pubspec.yaml"


def test_usage_present_passes(make_app):
    keys = "<key>NSCameraUsageDescription</key><string>Take a photo of your receipt</string>" \
           "<key>NSPhotoLibraryUsageDescription</key><string>Pick a receipt photo from your library</string>"
    root = make_app({"pubspec.yaml": PUBSPEC.format(deps="  image_picker: ^1.0.0"), "ios/Runner/Info.plist": info(keys)})
    assert "IOS-USAGE-MISSING" not in ids(root)


# IOS-USAGE-PLACEHOLDER
def test_usage_placeholder_flagged(make_app):
    root = make_app({"ios/Runner/Info.plist": info("<key>NSCameraUsageDescription</key><string>TODO</string>")})
    assert "IOS-USAGE-PLACEHOLDER" in ids(root)


def test_usage_real_text_not_placeholder(make_app):
    root = make_app({"ios/Runner/Info.plist": info("<key>NSCameraUsageDescription</key><string>Scan the QR code on your ticket</string>")})
    assert "IOS-USAGE-PLACEHOLDER" not in ids(root)


# IOS-PRIVACY-MANIFEST
def test_privacy_manifest_missing_with_required_reason_dep(make_app):
    root = make_app({"pubspec.yaml": PUBSPEC.format(deps="  shared_preferences: ^2.5.3"), "ios/Runner/Info.plist": info()})
    (f,) = findings(root, "IOS-PRIVACY-MANIFEST")
    assert f.severity == "warning" and f.fix.kind == "auto"


def test_privacy_manifest_not_needed_without_dep(make_app):
    root = make_app({"ios/Runner/Info.plist": info()})
    assert "IOS-PRIVACY-MANIFEST" not in ids(root)


def test_privacy_manifest_present_passes(make_app):
    xcp = plist("<dict><key>NSPrivacyAccessedAPITypes</key><array><dict>"
                "<key>NSPrivacyAccessedAPIType</key><string>NSPrivacyAccessedAPICategoryUserDefaults</string>"
                "<key>NSPrivacyAccessedAPITypeReasons</key><array><string>CA92.1</string></array></dict></array></dict>")
    root = make_app({"pubspec.yaml": PUBSPEC.format(deps="  shared_preferences: ^2.5.3"),
                     "ios/Runner/Info.plist": info(), "ios/Runner/PrivacyInfo.xcprivacy": xcp})
    assert not {"IOS-PRIVACY-MANIFEST", "IOS-PRIVACY-REASON"} & ids(root)


# IOS-PRIVACY-REASON
def test_privacy_reason_invalid_code(make_app):
    xcp = plist("<dict><key>NSPrivacyAccessedAPITypes</key><array><dict>"
                "<key>NSPrivacyAccessedAPIType</key><string>NSPrivacyAccessedAPICategoryUserDefaults</string>"
                "<key>NSPrivacyAccessedAPITypeReasons</key><array><string>ZZ99.9</string></array></dict></array></dict>")
    root = make_app({"ios/Runner/Info.plist": info(), "ios/Runner/PrivacyInfo.xcprivacy": xcp})
    (f,) = findings(root, "IOS-PRIVACY-REASON")
    assert "ZZ99.9" in f.title and f.severity == "blocker"


# IOS-ENCRYPTION-FLAG
def test_encryption_flag_missing(make_app):
    root = make_app({"ios/Runner/Info.plist": plist("<dict></dict>")})
    (f,) = findings(root, "IOS-ENCRYPTION-FLAG")
    assert f.fix.kind == "handoff"


def test_encryption_flag_present(make_app):
    assert "IOS-ENCRYPTION-FLAG" not in ids(make_app({"ios/Runner/Info.plist": info()}))


# IOS-ATS-ARBITRARY
def test_ats_arbitrary_loads(make_app):
    keys = "<key>NSAppTransportSecurity</key><dict><key>NSAllowsArbitraryLoads</key><true/></dict>"
    assert "IOS-ATS-ARBITRARY" in ids(make_app({"ios/Runner/Info.plist": info(keys)}))


def test_ats_default_passes(make_app):
    assert "IOS-ATS-ARBITRARY" not in ids(make_app({"ios/Runner/Info.plist": info()}))


# IOS-SIWA
def test_social_login_without_apple(make_app):
    root = make_app({"pubspec.yaml": PUBSPEC.format(deps="  google_sign_in: ^6.0.0"), "ios/Runner/Info.plist": info()})
    assert "IOS-SIWA" in ids(root)


def test_social_login_with_apple_passes(make_app):
    root = make_app({"pubspec.yaml": PUBSPEC.format(deps="  google_sign_in: ^6.0.0\n  sign_in_with_apple: ^6.0.0"),
                     "ios/Runner/Info.plist": info()})
    assert "IOS-SIWA" not in ids(root)


def test_no_ios_folder_means_no_ios_findings(make_app):
    root = make_app({"pubspec.yaml": PUBSPEC.format(deps="  image_picker: ^1.0.0\n  shared_preferences: ^2.0.0")})
    assert not {i for i in ids(root) if i.startswith("IOS-")}
