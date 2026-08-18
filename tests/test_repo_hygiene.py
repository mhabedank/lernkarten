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

import make_testdata  # noqa: E402
import yamlio  # noqa: E402

# Everything below these paths is user content — except for the exceptions.
BLOCKED = ("knowledge/", "catalog/", "cards/", "output/")
ALLOWED = {
    "knowledge/.gitkeep",
    "catalog/.gitkeep",
    "cards/.gitkeep",
    "cards/example.yaml",
}


def versioned_files():
    """Every path git tracks, verbatim — see `ignored()` for why that is fiddly."""
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("not a git repository")
    lines = result.stdout.decode("utf-8").splitlines()
    return [line for line in lines if line]


def test_versioned_files_are_reported_unquoted():
    """A quoted name would slip straight past the guard below.

    git wraps anything non-ASCII in quotes and octal escapes, and
    `"knowledge/\\303\\274ber.md"` starts with a quote rather than with
    `knowledge/` — so the check for user content would wave through exactly the
    file it exists to catch. The demo project ships a path with an umlaut, so
    this is not hypothetical.
    """
    files = versioned_files()
    assert any(not f.isascii() for f in files), (
        "no non-ASCII path is versioned any more — this test has stopped proving anything"
    )
    assert not [f for f in files if f.startswith('"')], "git quoted a path instead of reporting it"


def test_no_user_content_in_the_repo():
    intruders = [f for f in versioned_files() if f.startswith(BLOCKED) and f not in ALLOWED]
    assert not intruders, (
        f"user content must not be versioned (see .gitignore and CONTRIBUTING.md): {intruders}"
    )


def test_no_personal_source_register_in_the_repo():
    assert "sources.yaml" not in versioned_files(), (
        "sources.yaml holds the user's sources — only sources.example.yaml is versioned"
    )


def test_no_personal_learning_goal_in_the_repo():
    """`goal.md` states what its author is studying — the fifth user-content format."""
    intruders = [
        f
        for f in versioned_files()
        if Path(f).name == "goal.md" and not f.startswith("tests/fixtures/")
    ]
    assert not intruders, f"goal.md holds the user's learning goal and stays local: {intruders}"


def test_example_source_register_is_valid():
    data = yamlio.load((ROOT / "sources.example.yaml").read_text(encoding="utf-8"))
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


def ignored(paths):
    """The subset of `paths` that .gitignore keeps out of the repo.

    Three things have to be got right, or the answer cannot be compared with
    the question:

    * `core.quotePath=false`, or git wraps anything non-ASCII in quotes and
      octal escapes — and on Windows, where the separator is a backslash, that
      is every single path.
    * bytes rather than `text=True`, because a text-mode stdin translates the
      newline between paths into CRLF on Windows and git then reads the
      carriage return as part of the file name.
    * split on line breaks, not on whitespace, so a name with a space in it
      survives.
    """
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "check-ignore", "--stdin"],
        cwd=ROOT,
        input="\n".join(paths).encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if result.returncode > 1:
        pytest.skip("not a git repository")
    lines = result.stdout.decode("utf-8").splitlines()
    return {line.strip() for line in lines if line.strip()}


@pytest.mark.parametrize(
    "path",
    [
        "output/two words.pdf",
        "output/über.pdf",
    ],
)
def test_ignored_hands_back_exactly_what_it_was_given(path):
    """The answer has to stay comparable with the question.

    git quotes any path it thinks unusual — non-ASCII, backslashes — and
    splitting its output on whitespace tears a name with a space in half.
    Either one makes the result uncomparable with the input, which is how the
    generated test data came back "not ignored" on Windows: there every path
    arrives with backslash separators, so git quoted all of them.
    """
    assert ignored([path]) == {path}


def fixture_files():
    files = [p for p in (ROOT / "tests" / "fixtures").rglob("*") if p.is_file()]
    assert files, "the demo project is missing — the end-to-end tests run against it"
    generated = {t.resolve() for t, _, _ in make_testdata.JOBS}
    # as_posix(), not str(): git speaks forward slashes on every platform, and a
    # backslash-separated path matches none of the .gitignore patterns.
    return (
        [p.relative_to(ROOT).as_posix() for p in files if p.resolve() not in generated],
        [p.relative_to(ROOT).as_posix() for p in files if p.resolve() in generated],
    )


def test_the_demo_project_is_not_swallowed_by_gitignore():
    """`sources.yaml`, `goal.md` and `*.pdf` match at every level — the fixture must survive."""
    versioned, _ = fixture_files()
    assert not ignored(versioned), (
        f"these test files would never be committed: {sorted(ignored(versioned))}"
    )


def test_the_demo_learning_goal_survives_gitignore():
    """The negation pattern, checked on its own.

    `goal.md` has no slash, so it matches at every directory level — the same
    hazard `sources.yaml` has. Without `!tests/fixtures/**/goal.md` the fixture's
    copy is silently uncommittable, and the demo project loses the artifact the
    whole goal-driven catalog is built on.
    """
    goal = ROOT / "tests/fixtures/demo-project/goal.md"
    assert goal.exists(), "the demo project has no goal.md"
    relative = goal.relative_to(ROOT).as_posix()
    assert not ignored([relative]), (
        f"{relative} is ignored — .gitignore needs !tests/fixtures/**/goal.md"
    )


def test_the_generated_test_data_stays_out_of_the_repo():
    """Binaries belong in nobody's git history — they are built, not committed."""
    _, generated = fixture_files()
    if not generated:
        pytest.skip("run scripts/make_testdata.py first")
    assert ignored(generated) == set(generated), (
        f"generated test data is not ignored: {sorted(set(generated) - ignored(generated))}"
    )


def test_gitignore_covers_the_user_paths():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    for pattern in (
        "sources.yaml",
        "goal.md",
        "knowledge/*",
        "catalog/*",
        "cards/*",
        "output/",
    ):
        assert pattern in lines, f".gitignore does not cover {pattern}"
