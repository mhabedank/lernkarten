"""Shared fixtures. Today: one, and it exists to keep the suite honest.

`scripts/settings.py` reads a machine-scoped settings file from the user's
config home. Left alone, every test would inherit whatever the person running
it happens to have answered — and the failure mode is the worst kind: green on
CI, which has no such file, and red on exactly one laptop, for reasons nothing
in the test names.

So the whole run gets an empty config home. A test that wants a machine file
writes one into it.
"""

import os
import tempfile

import pytest


@pytest.fixture(autouse=True, scope="session")
def _isolated_config_home():
    """Point XDG_CONFIG_HOME at an empty directory for the whole session."""
    with tempfile.TemporaryDirectory(prefix="lernkarten-test-config-") as tmp:
        previous = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = tmp
        try:
            yield tmp
        finally:
            if previous is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = previous
