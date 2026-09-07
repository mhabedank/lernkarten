"""Stub."""

from dataclasses import dataclass, field


class SettingsError(Exception):
    pass


@dataclass
class Settings:
    compartments: int | None = None
    dividers_printed: bool = False
    box_printed: bool = False
    unanswered: bool = True
    warnings: list[str] = field(default_factory=list)


def load(card_file):
    return Settings()


def save(root, compartments=None, dividers_printed=False, box_printed=False):
    return None


def mark_printed(root, dividers=False, box=False):
    return None
