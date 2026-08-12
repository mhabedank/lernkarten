"""Tests for scripts/engine.py — the one-time fetch of the typesetting engine.

Nothing here touches the network: the download itself is exercised by CI, which
builds the example cards on a machine that has never seen the engine.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import engine  # noqa: E402


def test_every_platform_we_claim_to_support_is_pinned():
    for (system, machine), (asset, digest) in engine.BUILDS.items():
        assert system in {"Darwin", "Linux", "Windows"}
        assert machine and asset.startswith("typst-")
        assert len(digest) == 64 and set(digest) <= set("0123456789abcdef"), (
            f"{system}/{machine}: a checksum is what keeps us from running a tampered binary"
        )


def test_the_release_url_names_the_pinned_version():
    url = engine.RELEASE.format(version=engine.VERSION, asset="typst-x86_64-apple-darwin.tar.xz")
    assert url.startswith("https://github.com/typst/typst/releases/download/")
    assert engine.VERSION in url


def test_platform_names_that_mean_the_same_thing_resolve(monkeypatch):
    monkeypatch.setattr(engine.platform, "system", lambda: "Linux")
    monkeypatch.setattr(engine.platform, "machine", lambda: "aarch64")
    assert engine.platform_key() == ("Linux", "aarch64")

    monkeypatch.setattr(engine.platform, "machine", lambda: "arm64")
    assert engine.platform_key() == ("Linux", "aarch64"), "arm64 and aarch64 are one platform"

    monkeypatch.setattr(engine.platform, "system", lambda: "Windows")
    monkeypatch.setattr(engine.platform, "machine", lambda: "AMD64")
    assert engine.platform_key() == ("Windows", "AMD64")


def test_an_unsupported_platform_says_what_to_do(monkeypatch):
    monkeypatch.setattr(engine.platform, "system", lambda: "Plan9")
    monkeypatch.setattr(engine.platform, "machine", lambda: "mips")
    with pytest.raises(engine.EngineError, match="LERNKARTEN_ENGINE"):
        engine.platform_key()


def test_the_cache_follows_the_plugin_data_directory(monkeypatch, tmp_path):
    monkeypatch.delenv("LERNKARTEN_ENGINE_DIR", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
    assert engine.cache_dir() == tmp_path / "engine"

    monkeypatch.setenv("LERNKARTEN_ENGINE_DIR", str(tmp_path / "elsewhere"))
    assert engine.cache_dir() == tmp_path / "elsewhere" / "engine"


def test_the_cache_falls_back_to_a_normal_cache_folder(monkeypatch, tmp_path):
    for name in ("LERNKARTEN_ENGINE_DIR", "CLAUDE_PLUGIN_DATA"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert engine.cache_dir() == tmp_path / "lernkarten" / "engine"


def test_your_own_engine_wins(monkeypatch, tmp_path):
    mine = tmp_path / "typst"
    mine.write_text("#!/bin/sh\n")
    monkeypatch.setenv("LERNKARTEN_ENGINE", str(mine))
    assert engine.find(fetch_if_missing=False) == (mine, "LERNKARTEN_ENGINE")


def test_a_missing_override_is_an_error_not_a_silent_download(monkeypatch, tmp_path):
    monkeypatch.setenv("LERNKARTEN_ENGINE", str(tmp_path / "nope"))
    with pytest.raises(engine.EngineError, match="does not exist"):
        engine.find()


def test_a_tampered_download_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(
        engine.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(b"not the real binary")
    )
    target = tmp_path / "x"
    with pytest.raises(engine.EngineError, match="checksum"):
        engine._download("https://example.invalid/x", target, "0" * 64)
    assert not target.exists(), "a binary that fails its checksum must not be left behind"


def test_a_matching_download_is_kept(monkeypatch, tmp_path):
    import hashlib

    payload = b"pretend this is the engine"
    monkeypatch.setattr(engine.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(payload))
    target = tmp_path / "x"
    engine._download("https://example.invalid/x", target, hashlib.sha256(payload).hexdigest())
    assert target.read_bytes() == payload


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
