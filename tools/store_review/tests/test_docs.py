"""SPEC criteria 12 and 13: docs cover every rule and say what is simulated; the MIT license is kept."""

from pathlib import Path

from store_review.rules import all_rule_ids

REPO = Path(__file__).resolve().parents[3]


def test_docs_list_every_rule_from_the_packs():
    text = (REPO / "docs/STORE_REVIEW.md").read_text()
    missing = [rid for rid in all_rule_ids() if f"`{rid}`" not in text]
    assert not missing, f"docs/STORE_REVIEW.md does not mention {missing}"


def test_docs_state_what_is_simulated_and_what_is_real():
    text = (REPO / "docs/STORE_REVIEW.md").read_text()
    assert "## What is real and what is simulated" in text
    assert "never uploads" in text.lower()


def test_license_is_mit_with_both_copyrights():
    text = (REPO / "LICENSE.md").read_text()
    assert "Andrea Bizzotto" in text and "Ramy Magdy" in text
    assert "Permission is hereby granted, free of charge" in text


def test_readme_links_store_review_docs():
    assert "docs/STORE_REVIEW.md" in (REPO / "README.md").read_text()
