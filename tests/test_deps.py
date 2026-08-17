"""The dependency bootstrap: scripts/deps.py.

REQUIREMENTS is empty today, so almost everything here works against synthetic
requirement sets. That is the point — the machinery has to be known-good before
the first real dependency leans on it, not after.

The one test that really talks to PyPI is opt-in via LERNKARTEN_DEPS_NET=1, the
same bargain tests/test_e2e.py strikes with the engine: a plain `pytest` never
reaches the network.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deps  # noqa: E402

# A module every Python has, and one nobody has.
PRESENT = [("json-is-built-in", "json")]
ABSENT = [("lernkarten-nonexistent-package", "lernkarten_nonexistent_package")]


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Never touch the real cache, and never inherit an outside override."""
    monkeypatch.setenv("LERNKARTEN_DEPS_DIR", str(tmp_path))
    monkeypatch.delenv("LERNKARTEN_NO_BOOTSTRAP", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)


def test_there_are_no_runtime_dependencies_yet():
    """A guard, not a wish. When this fails, the rest of the file matters."""
    assert deps.REQUIREMENTS == [], (
        "a runtime dependency has appeared — check it clears the gates in "
        "CONTRIBUTING.md, and that bin/lernkarten still bootstraps it"
    )


def test_activate_does_nothing_while_nothing_is_required():
    before = list(sys.path)
    assert deps.activate() == "none"
    assert sys.path == before, "an empty requirement set must not touch sys.path"


def test_missing_spots_what_cannot_be_imported():
    assert deps.missing(PRESENT) == []
    assert deps.missing(ABSENT) == ["lernkarten-nonexistent-package"]


def test_the_target_directory_separates_interpreters_and_requirement_sets():
    mine = deps.target_dir(PRESENT)
    assert mine != deps.target_dir(ABSENT), "different requirements must not share a directory"
    assert f"py{sys.version_info.major}{sys.version_info.minor}" in mine.name, (
        "a compiled wheel belongs to one Python version — that has to be in the path"
    )
    assert deps.target_dir(PRESENT) == mine, "the same requirements must resolve to the same place"


def test_the_target_directory_lands_under_the_override(tmp_path):
    assert str(deps.target_dir(PRESENT)).startswith(str(tmp_path)), (
        "LERNKARTEN_DEPS_DIR has to be honoured, or a test would write to the real cache"
    )


def test_no_bootstrap_refuses_to_install_and_says_what_to_do(monkeypatch):
    monkeypatch.setenv("LERNKARTEN_NO_BOOTSTRAP", "1")
    with pytest.raises(deps.DependencyError) as e:
        deps.install(ABSENT)
    assert "lernkarten-nonexistent-package" in str(e.value), "the message has to name the package"


def test_a_python_without_pip_explains_itself(monkeypatch):
    monkeypatch.setattr(deps, "_importable", lambda module, extra_path=None: module != "pip")
    with pytest.raises(deps.DependencyError) as e:
        deps.install(ABSENT)
    message = str(e.value)
    assert "no pip" in message
    assert "lernkarten-nonexistent-package" in message, "tell the user what to install by hand"


def test_install_asks_pip_for_wheels_only(monkeypatch):
    """A source build would need a compiler, which is the friction we refuse."""
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(deps.subprocess, "run", fake_run)
    deps.install(PRESENT, quiet=True)
    command = seen["command"]
    assert command[:3] == [sys.executable, "-m", "pip"]
    assert "--only-binary" in command and ":all:" in command
    assert "--target" in command
    assert "json-is-built-in" in command


def test_a_failing_pip_is_reported_with_its_own_complaint(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "ERROR: no matching distribution")

    monkeypatch.setattr(deps.subprocess, "run", fake_run)
    with pytest.raises(deps.DependencyError) as e:
        deps.install(ABSENT, quiet=True)
    assert "no matching distribution" in str(e.value), "pip's own words are the useful part"


def test_activate_without_installing_refuses_rather_than_reaching_out(monkeypatch):
    monkeypatch.setattr(deps, "REQUIREMENTS", ABSENT)
    with pytest.raises(deps.DependencyError) as e:
        deps.activate(install_if_missing=False)
    assert "not installed yet" in str(e.value)


def test_the_command_can_report_its_dependencies():
    """`lernkarten deps --check` alongside `lernkarten engine --check`.

    Whatever the bootstrap does has to be inspectable without running a build,
    or the first person it fails for has nothing to look at.
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "lernkarten"), "deps", "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "no runtime dependencies" in result.stdout


def test_the_check_flag_reports_and_installs_nothing():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "deps.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "no runtime dependencies" in result.stdout


@pytest.mark.skipif(
    os.environ.get("LERNKARTEN_DEPS_NET") != "1",
    reason="set LERNKARTEN_DEPS_NET=1 to let this one install from PyPI",
)
def test_a_real_requirement_installs_and_becomes_importable(tmp_path):
    """End to end against PyPI, with a small well-known pure-Python package.

    Everything above proves the plumbing with fakes. This proves a package
    genuinely lands somewhere importable, which is the only claim that matters
    when the first real dependency arrives.

    The import is checked in a subprocess started with -S, so site-packages is
    out of the picture: on a machine that already has the package ambiently — and
    plenty do have six — importing it would otherwise prove nothing about the
    target directory.
    """
    requirements = [("six==1.17.0", "six")]
    target = tmp_path / "real"
    assert not target.exists() or not list(target.iterdir()), "the target must start empty"

    deps.install(requirements, target=target, quiet=True)

    # -S keeps site-packages off sys.path, so the stdlib is still importable but
    # an ambient copy of the package is not. PYTHONPATH is cleared for the same
    # reason.
    probe = "import sys; sys.path.insert(0, sys.argv[1]); import six; print(six.__file__)"
    result = subprocess.run(
        [sys.executable, "-S", "-c", probe, str(target)],
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
    )
    assert result.returncode == 0, f"not importable from the target alone: {result.stderr}"
    assert str(target) in result.stdout, f"imported from somewhere else entirely: {result.stdout}"
