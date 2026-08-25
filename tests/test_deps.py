"""The dependency bootstrap: scripts/deps.py.

Most of this works against synthetic requirement sets rather than the real
REQUIREMENTS, because the interesting paths are the ones a development checkout
never takes: a missing package, a Python without pip, a pip that fails. Those
have to be known-good precisely because nobody here will hit them.

The one test that really talks to PyPI is opt-in via LERNKARTEN_DEPS_NET=1, the
same bargain tests/test_e2e.py strikes with the engine: a plain `pytest` never
reaches the network.
"""

import importlib.util
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


def test_every_requirement_is_pinned_exactly():
    """The user did not choose to install these, so they must not drift.

    A range would mean two people on the same lernkarten version get different
    parsers, and the second one's bug report is unreproducible.
    """
    assert deps.REQUIREMENTS, "if this is empty again, activate() has nothing to do"
    for requirement, _ in deps.REQUIREMENTS:
        assert "==" in requirement, f"{requirement} is not pinned to one version"


def test_the_pins_here_and_in_requirements_dev_agree():
    """Dependabot can see requirements-dev.txt. It cannot see this file.

    The runtime pin lives in REQUIREMENTS as a Python literal, which no
    dependency bot will ever read. requirements-dev.txt repeats it so a checkout
    can run the tests without waiting for the bootstrap — and that repetition is
    exactly what drifts. When Dependabot bumps the one it can see, this fails
    until the other follows.
    """
    declared = dict(
        line.split("==", 1)
        for line in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()
        if "==" in line and not line.startswith("#")
    )
    for requirement, _ in [*deps.REQUIREMENTS, *getattr(deps, "FIGURES", [])]:
        name, version = requirement.split("==", 1)
        assert name in declared, f"{name} is pinned in deps.py but absent from requirements-dev.txt"
        assert declared[name] == version, (
            f"{name} is {version} in deps.py but {declared[name]} in requirements-dev.txt"
        )


def test_every_requirement_names_a_module_that_can_be_checked():
    """The module name is how absence is detected, so it must be the real one."""
    for requirement, module in deps.REQUIREMENTS:
        assert module and " " not in module, f"{requirement}: {module!r} is not an import name"


def test_the_optional_set_is_separate_from_the_default_one():
    """The PDF renderer is 3.5 MB that most projects never need.

    It reaches a user only when a PDF figure is actually asked for, so it must
    not sit in REQUIREMENTS: everything there is installed on the first
    `lernkarten` command, whatever that command happens to be.
    """
    assert not any("pypdfium2" in r for r, _ in deps.REQUIREMENTS), (
        "the PDF renderer belongs in FIGURES, not in the set every user installs"
    )
    figures = getattr(deps, "FIGURES", [])
    assert figures, "deps.FIGURES has to exist, and hold something, before it can be optional"
    for requirement, module in figures:
        assert "==" in requirement, f"{requirement} is not pinned to one version"
        assert module and " " not in module, f"{requirement}: {module!r} is not an import name"


def test_the_optional_set_gets_its_own_cache_directory():
    """Two requirement sets, two directories — or installing one clobbers the other."""
    figures = getattr(deps, "FIGURES", [])
    assert figures, "deps.FIGURES has to exist before it can have a directory of its own"
    assert deps.target_dir(figures) != deps.target_dir()


@pytest.mark.skipif(
    importlib.util.find_spec("pypdfium2") is not None,
    reason="pypdfium2 is installed here, so its absence cannot be observed",
)
def test_missing_reports_the_optional_set_separately():
    """Absent optional package, present default set. The two must not be confused."""
    assert deps.missing() == [], "a development checkout already has the default set"
    figures = getattr(deps, "FIGURES", [])
    assert figures, "deps.FIGURES has to exist before its absence can be reported"
    assert deps.missing(figures) == [figures[0][0]]


def test_activate_is_satisfied_by_an_installed_package():
    """A development checkout has these already, so nothing should be fetched."""
    before = list(sys.path)
    assert deps.activate() == "system"
    assert sys.path == before, "already importable — sys.path must not be touched"


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


def test_a_freshly_created_directory_is_importable_at_once(monkeypatch, tmp_path):
    """The one that bit: importlib caches the fact that a directory was absent.

    The target directory does not exist when activate() starts, so the import
    machinery records a negative result for it. Install into it, put it on
    sys.path, and `find_spec` still says no — the install looked like it had
    failed when in fact it had worked. Only invalidate_caches() clears that.
    """
    requirements = [("lernkarten-fake==1.0", "lernkarten_fake")]
    monkeypatch.setattr(deps, "REQUIREMENTS", requirements)
    target = deps.target_dir()
    assert not target.exists(), "the point of this test is a directory born mid-run"

    def fake_install(reqs=None, target=None, quiet=False):
        directory = deps.target_dir() if target is None else Path(target)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "lernkarten_fake.py").write_text("ok = True\n", encoding="utf-8")
        return directory

    monkeypatch.setattr(deps, "install", fake_install)
    try:
        assert deps.activate(quiet=True) == "installed"
    finally:
        sys.path[:] = [p for p in sys.path if p != str(target)]


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
    assert "requirement(s)" in result.stdout, result.stdout


def test_the_check_flag_reports_and_installs_nothing():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "deps.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "requirement(s)" in result.stdout, result.stdout


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
