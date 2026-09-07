"""The project settings: `lernkarten.yaml`, in the root beside `cards/`.

Read by `lernkarten build`, written by `lernkarten setup`. It holds the answers
to questions nobody should be asked twice — how many Leitner compartments, and
whether the dividers and the box are already on paper.

    lernkarten build → settings.load()   → what to render
    lernkarten setup → settings.save()   → the only place the questions are asked
    a finished build → settings.mark_printed()

Deliberately **not** one of the six formats Principle I couples the two halves
with. It holds choices, never content (Principle VII), and it is gitignored
like everything else a user owns.

Why it is its own module rather than part of `scripts/yamlio.py`: yamlio is the
*format reader*, and Principle VI wants it near the bottom of the import graph.
Teaching it the key names of one particular file would make it a policy module.
This sits one level above it and knows about `lernkarten.yaml` and nothing else.
"""

from dataclasses import dataclass, field
from pathlib import Path

import leitner
import yamlio

FILENAME = "lernkarten.yaml"

# `compartments` takes an integer or the word `none`. `none` is a real answer —
# asked and declined — which is why it cannot be spelled by leaving the key out.
DECLINED = "none"
BOOLEAN_KEYS = ("dividers_printed", "box_printed")
KNOWN_KEYS = ("compartments", *BOOLEAN_KEYS)


class SettingsError(Exception):
    """A settings file that cannot be used as written."""


@dataclass
class Settings:
    """What the file says, plus whether it was ever answered at all.

    `unanswered` is the distinction the whole advisory hangs on. Three states,
    not two: no file (or an empty one) means never asked, so the run says so
    once; `compartments: none` means asked and declined, so it says nothing.
    Collapsing them would either nag someone who has said no, or swallow the
    single chance to mention the feature.
    """

    compartments: int | None = None
    dividers_printed: bool = False
    box_printed: bool = False
    unanswered: bool = True
    warnings: list[str] = field(default_factory=list)


def path_for(card_file):
    """Where the settings file lives for a build over `card_file`.

    The same root a picture path resolves against, and for the same reason: a
    file picked up from whatever directory the command happened to run in would
    make a project build differently depending on where you stood.
    """
    return Path(card_file).resolve().parent.parent / FILENAME


def load(card_file):
    """The settings for a build over `card_file`. Raises SettingsError.

    An absent or empty file is not an error — it is the behaviour this project
    had before the file existed, which is what every optional artifact here
    promises.
    """
    path = path_for(card_file)
    if not path.exists():
        return Settings()
    try:
        data = yamlio.load(path.read_text(encoding="utf-8"))
    except yamlio.YamlError as e:
        raise SettingsError(f"{FILENAME}: {e}") from e
    if data is None:
        return Settings()
    if not isinstance(data, dict):
        raise SettingsError(
            f"{FILENAME}: expected a mapping of settings, got {type(data).__name__}"
        )

    warnings = [
        f"{FILENAME}: unknown key '{key}' — this version knows "
        f"{', '.join(KNOWN_KEYS)}. Ignoring it."
        for key in data
        if key not in KNOWN_KEYS
    ]
    return Settings(
        compartments=_compartments(data),
        dividers_printed=_boolean(data, "dividers_printed"),
        box_printed=_boolean(data, "box_printed"),
        unanswered="compartments" not in data,
        warnings=warnings,
    )


def _compartments(data):
    if "compartments" not in data:
        return None
    value = data["compartments"]
    if value in (DECLINED, None):
        return None
    if value in leitner.COMPARTMENT_COUNTS:
        return value
    allowed = ", ".join([*(str(n) for n in leitner.COMPARTMENT_COUNTS), DECLINED])
    raise SettingsError(f"{FILENAME}: compartments is {value!r}; expected one of {allowed}")


def _boolean(data, key):
    value = data.get(key, False)
    if not isinstance(value, bool):
        raise SettingsError(f"{FILENAME}: {key} is {value!r}; expected true or false")
    return value


def save(root, compartments=None, dividers_printed=False, box_printed=False):
    """Write the three keys. The only caller is `lernkarten setup`."""
    written = compartments if compartments is not None else DECLINED
    Path(root, FILENAME).write_text(
        "# What lernkarten should not ask you twice. Yours, never committed.\n"
        f"compartments: {written}\n"
        f"dividers_printed: {str(dividers_printed).lower()}\n"
        f"box_printed: {str(box_printed).lower()}\n",
        encoding="utf-8",
    )


def mark_printed(root, dividers=False, box=False):
    """Record that a successful build put these on paper.

    Without it a project answering `4 / no / no` prints fresh dividers on every
    rebuild forever. Two limits keep it safe: it **never creates** the file, and
    it only touches one that has actually been answered. Writing into an absent
    or declined file would invent a fourth state the three-state model does not
    have — `dividers_printed: true` with nothing saying how many compartments.
    """
    path = Path(root, FILENAME)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    data = yamlio.load(text) or {}
    if not isinstance(data, dict) or data.get("compartments") not in leitner.COMPARTMENT_COUNTS:
        return
    save(
        root,
        compartments=data["compartments"],
        dividers_printed=data.get("dividers_printed", False) or dividers,
        box_printed=data.get("box_printed", False) or box,
    )
