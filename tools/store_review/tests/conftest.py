from pathlib import Path

import pytest

PLIST_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n'


@pytest.fixture(autouse=True)
def _isolate_ci_env(monkeypatch):
    # CI sets these as project variables; tests opt in with setenv when they need one.
    for name in ("STORE_REVIEW_MENTION", "STORE_REVIEW_DEMO_LOGIN"):
        monkeypatch.delenv(name, raising=False)


def plist(body: str) -> str:
    return PLIST_HEAD + body + "\n</plist>\n"


def manifest(application: str = "", permissions: str = "") -> str:
    return (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
        f"{permissions}\n"
        f'<application android:label="app">\n{application}\n</application>\n'
        "</manifest>\n"
    )


@pytest.fixture
def make_app(tmp_path: Path):
    """Write a minimal Flutter app tree. Keys are relative paths, values are file contents."""

    def _make(files: dict[str, str]) -> Path:
        defaults = {"pubspec.yaml": "name: demo\nversion: 1.0.0\ndependencies:\n  flutter:\n    sdk: flutter\n"}
        for rel, text in {**defaults, **files}.items():
            p = tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        return tmp_path

    return _make
