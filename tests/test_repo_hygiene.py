"""Guards that the repo stays subject-agnostic.

Only the tools are versioned — sources, ingested texts, the catalog and the
generated cards belong to the user and stay local.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import minyaml  # noqa: E402

# Everything below these paths is user content — except for the exceptions.
BLOCKED = ("knowledge/", "catalog/", "cards/", "output/")
ALLOWED = {
    "knowledge/.gitkeep",
    "catalog/.gitkeep",
    "cards/.gitkeep",
    "cards/example.yaml",
}


def versioned_files():
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        pytest.skip("not a git repository")
    return result.stdout.split()


def test_no_user_content_in_the_repo():
    intruders = [f for f in versioned_files() if f.startswith(BLOCKED) and f not in ALLOWED]
    assert not intruders, (
        f"user content must not be versioned (see .gitignore and CONTRIBUTING.md): {intruders}"
    )


def test_no_personal_source_register_in_the_repo():
    assert "sources.yaml" not in versioned_files(), (
        "sources.yaml holds the user's sources — only sources.example.yaml is versioned"
    )


def test_example_source_register_is_valid():
    data = minyaml.load((ROOT / "sources.example.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict) and data.get("sources"), "key 'sources' missing"

    ids = set()
    required_field = {"folder": "path", "pdf": "path", "web": "url", "zotero": None}
    for entry in data["sources"]:
        assert entry.get("id"), f"entry without id: {entry}"
        assert entry["id"] not in ids, f"duplicate id: {entry['id']}"
        ids.add(entry["id"])
        assert entry.get("type") in required_field, f"unknown type: {entry.get('type')}"
        field = required_field[entry["type"]]
        assert field is None or entry.get(field), f"{entry['id']}: '{field}' missing"


def test_gitignore_covers_the_user_paths():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    for pattern in ("sources.yaml", "knowledge/*", "catalog/*", "cards/*", "output/"):
        assert pattern in lines, f".gitignore does not cover {pattern}"
