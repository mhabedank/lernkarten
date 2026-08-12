#!/usr/bin/env python3
"""Finds the typesetting engine, fetching it once if this machine has none.

The cards are typeset with Typst, a single self-contained binary. Nobody has to
install a document toolchain: the first build downloads the pinned release for
this platform, checks it against the hash below and keeps it in a cache folder.

    python3 scripts/engine.py            # print the path, fetching if needed
    python3 scripts/engine.py --check    # say where it came from, fetch nothing

Set LERNKARTEN_ENGINE to a typst binary of your own to bypass all of this.
"""

import argparse
import hashlib
import lzma
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

VERSION = "0.15.1"
RELEASE = "https://github.com/typst/typst/releases/download/v{version}/{asset}"

# sha256 of the official release archives, so a tampered download cannot run.
BUILDS = {
    ("Darwin", "arm64"): (
        "typst-aarch64-apple-darwin.tar.xz",
        "48f62ed034aa3a7978309579ac6ca00045e2ef0da73114e8af27cfd8e74dc05a",
    ),
    ("Darwin", "x86_64"): (
        "typst-x86_64-apple-darwin.tar.xz",
        "7f9fdd9584866245de9a79e0add8f9236fae6f40a8a45e2c4771ccc14db4e0fa",
    ),
    ("Linux", "x86_64"): (
        "typst-x86_64-unknown-linux-musl.tar.xz",
        "a6d077d0a95eed5a2eba715b2dae06be954f624ccbf85758a03f389ded33118c",
    ),
    ("Linux", "aarch64"): (
        "typst-aarch64-unknown-linux-musl.tar.xz",
        "5aa8d74a3d906e60ea12a66ac2f37f8eef1b14cbad7182a745e393a10c23dcee",
    ),
    ("Windows", "AMD64"): (
        "typst-x86_64-pc-windows-msvc.zip",
        "19ce3551153c2fe7ee9fa2f95208310c8f4d3209fedb699e0333faf8913f6736",
    ),
    ("Windows", "ARM64"): (
        "typst-aarch64-pc-windows-msvc.zip",
        "4ab28e1b71ec3184d38d580ab797f499b6770d952b6b19167be5cea5c2662e14",
    ),
}
ALIASES = {"AMD64": "x86_64", "aarch64": "arm64", "arm64": "aarch64"}


class EngineError(RuntimeError):
    """Raised when no engine can be found or fetched."""


def platform_key():
    """This machine as a key into BUILDS, tolerating the usual naming drift."""
    system, machine = platform.system(), platform.machine()
    for candidate in (machine, ALIASES.get(machine, machine)):
        if (system, candidate) in BUILDS:
            return system, candidate
    raise EngineError(
        f"no prebuilt engine for {system}/{machine} — install typst yourself and "
        "point LERNKARTEN_ENGINE at it"
    )


def cache_dir():
    """Where the fetched engine lives. Survives plugin updates when installed."""
    for env in ("LERNKARTEN_ENGINE_DIR", "CLAUDE_PLUGIN_DATA"):
        if os.environ.get(env):
            return Path(os.environ[env]).expanduser() / "engine"
    base = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(base).expanduser() / "lernkarten" / "engine"


def binary_path():
    name = "typst.exe" if platform.system() == "Windows" else "typst"
    return cache_dir() / VERSION / name


def _download(url, target, expected_sha):
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            payload = response.read()
    except (urllib.error.URLError, TimeoutError) as e:
        raise EngineError(
            f"could not download the typesetting engine ({e}).\n"
            "  Check your connection, or install typst yourself and set LERNKARTEN_ENGINE."
        ) from e

    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected_sha:
        raise EngineError(
            f"the downloaded engine does not match its expected checksum "
            f"(got {actual}, want {expected_sha}) — refusing to run it"
        )
    target.write_bytes(payload)


def _extract(archive, into):
    """Pulls just the typst executable out of the release archive."""
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            member = next(n for n in zf.namelist() if n.endswith(("typst.exe", "typst")))
            with zf.open(member) as src, (into / Path(member).name).open("wb") as dst:
                shutil.copyfileobj(src, dst)
            return into / Path(member).name
    with lzma.open(archive) as raw, tarfile.open(fileobj=raw) as tf:
        member = next(m for m in tf.getmembers() if m.isfile() and m.name.endswith("/typst"))
        source = tf.extractfile(member)
        target = into / "typst"
        with target.open("wb") as dst:
            shutil.copyfileobj(source, dst)
        return target


def fetch(quiet=False):
    """Downloads and installs the pinned engine. Returns its path."""
    asset, expected_sha = BUILDS[platform_key()]
    target = binary_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not quiet:
        print(f"Fetching the typesetting engine (typst {VERSION}, one time)…", file=sys.stderr)

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        archive = work / asset
        _download(RELEASE.format(version=VERSION, asset=asset), archive, expected_sha)
        extracted = _extract(archive, work)
        extracted.chmod(0o755)
        shutil.move(str(extracted), str(target))
    return target


def _version_of(binary):
    try:
        out = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def find(fetch_if_missing=True):
    """The engine to use, as (path, where it came from)."""
    override = os.environ.get("LERNKARTEN_ENGINE")
    if override:
        if not Path(override).exists():
            raise EngineError(f"LERNKARTEN_ENGINE points at {override}, which does not exist")
        return Path(override), "LERNKARTEN_ENGINE"

    cached = binary_path()
    if cached.exists():
        return cached, "cache"

    on_path = shutil.which("typst")
    if on_path and _version_of(on_path):
        return Path(on_path), "PATH"

    if not fetch_if_missing:
        raise EngineError("no engine installed yet — it is fetched on the first build")
    return fetch(), "downloaded"


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--check", action="store_true", help="report the engine, download nothing")
    args = p.parse_args()

    try:
        binary, origin = find(fetch_if_missing=not args.check)
    except EngineError as e:
        sys.exit(f"ERROR: {e}")

    version = _version_of(binary) or "unknown version"
    print(f"{binary}\n  {version} (from {origin})" if args.check else binary)


if __name__ == "__main__":
    main()
