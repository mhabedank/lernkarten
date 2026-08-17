#!/usr/bin/env python3
"""Makes the runtime dependencies importable, installing them once if needed.

The plugin has no install step: `/plugin install` drops the files in place and
the skills then call `bin/lernkarten` with whatever Python the user happens to
have. So a runtime dependency has to fetch itself, the same way the typesetting
engine does in scripts/engine.py — otherwise "one ordinary command" stops being
true the moment this project needs a package.

    python3 scripts/deps.py            # make them importable, installing if needed
    python3 scripts/deps.py --check    # report, install nothing

Set LERNKARTEN_DEPS_DIR to keep the packages somewhere of your own, or
LERNKARTEN_NO_BOOTSTRAP=1 to forbid installing anything — then a missing
dependency is an error and you install it however you like.

There are no runtime dependencies at the moment: REQUIREMENTS is empty, so
`activate()` does nothing at all. The machinery is here, and tested against
synthetic requirements, so that the first one to arrive has somewhere to land.

Why `pip install --target` and not a virtualenv: `python3 -m venv` needs
ensurepip, which Debian and Ubuntu ship as a separate python3-venv package. A
bootstrap whose failure mode is "now go and apt-get something" would defeat its
own purpose. Installing into a plain directory needs pip and nothing else.
"""

import argparse
import hashlib
import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

# (pip requirement, module name to import). Pinned exactly: the user is not
# installing this on purpose, so it must not drift under them.
REQUIREMENTS = []

# Bumped by hand when the layout of the cache directory changes.
LAYOUT = "1"


class DependencyError(RuntimeError):
    """Raised when a dependency is missing and cannot be installed."""


def cache_dir():
    """Where installed packages live. Mirrors engine.cache_dir()."""
    for env in ("LERNKARTEN_DEPS_DIR", "CLAUDE_PLUGIN_DATA"):
        if os.environ.get(env):
            return Path(os.environ[env]).expanduser() / "deps"
    base = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(base).expanduser() / "lernkarten" / "deps"


def target_dir(requirements=None):
    """The directory for *this* interpreter and *this* requirement set.

    Keyed by Python version, machine and the requirements themselves, because a
    wheel with a C extension is built for one of each. Two projects, two
    Pythons or two dependency sets never tread on each other.
    """
    requirements = REQUIREMENTS if requirements is None else requirements
    spec = "\n".join(sorted(r for r, _ in requirements))
    tag = hashlib.sha256(f"{LAYOUT}\n{spec}".encode()).hexdigest()[:12]
    python = f"py{sys.version_info.major}{sys.version_info.minor}"
    return cache_dir() / f"{python}-{platform.machine()}-{tag}"


def _importable(module, extra_path=None):
    """Whether `module` can be imported, optionally with one more path entry."""
    saved = list(sys.path)
    if extra_path is not None:
        sys.path.insert(0, str(extra_path))
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False
    finally:
        sys.path[:] = saved


def missing(requirements=None, extra_path=None):
    """The requirements whose module cannot be imported."""
    requirements = REQUIREMENTS if requirements is None else requirements
    return [r for r, module in requirements if not _importable(module, extra_path)]


def install(requirements=None, target=None, quiet=False):
    """Installs `requirements` into `target` with pip. Returns the directory."""
    requirements = REQUIREMENTS if requirements is None else requirements
    target = target_dir(requirements) if target is None else Path(target)
    if os.environ.get("LERNKARTEN_NO_BOOTSTRAP") == "1":
        raise DependencyError(
            "LERNKARTEN_NO_BOOTSTRAP is set, so nothing was installed. "
            f"Install these yourself and re-run: {', '.join(r for r, _ in requirements)}"
        )
    if not _importable("pip"):
        raise DependencyError(
            "this Python has no pip, so the dependencies cannot install themselves.\n"
            f"  Install them by hand and re-run: {', '.join(r for r, _ in requirements)}"
        )

    target.mkdir(parents=True, exist_ok=True)
    if not quiet:
        names = ", ".join(r for r, _ in requirements)
        print(f"Installing what lernkarten needs ({names}, one time)…", file=sys.stderr)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--quiet",
            "--only-binary",
            ":all:",
            "--target",
            str(target),
            *[r for r, _ in requirements],
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise DependencyError(
            "could not install the dependencies "
            f"({detail[-1] if detail else 'pip failed'}).\n"
            "  Check your connection, or install them yourself and re-run: "
            f"{', '.join(r for r, _ in requirements)}"
        )
    return target


def activate(install_if_missing=True, quiet=False):
    """Makes the runtime dependencies importable. Returns where they came from.

    One of "none" (nothing is required), "system" (already importable),
    "cache" (a previous run installed them) or "installed".
    """
    if not REQUIREMENTS:
        return "none"
    if not missing():
        return "system"

    target = target_dir()
    if not missing(extra_path=target):
        sys.path.insert(0, str(target))
        return "cache"

    if not install_if_missing:
        raise DependencyError(
            f"not installed yet: {', '.join(missing())} — they are fetched on first use"
        )

    install(quiet=quiet)
    sys.path.insert(0, str(target))
    still = missing()
    if still:
        raise DependencyError(f"still missing after installing: {', '.join(still)}")
    return "installed"


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--check", action="store_true", help="report the state, install nothing")
    args = p.parse_args()

    if not REQUIREMENTS:
        print("no runtime dependencies")
        return
    try:
        origin = activate(install_if_missing=not args.check)
    except DependencyError as e:
        sys.exit(f"ERROR: {e}")
    print(f"{target_dir()}\n  {len(REQUIREMENTS)} requirement(s) (from {origin})")


if __name__ == "__main__":
    main()
