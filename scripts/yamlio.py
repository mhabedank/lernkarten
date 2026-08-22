#!/usr/bin/env python3
"""Reads the YAML this project owns — card files, the source register, frontmatter.

A thin layer over PyYAML. What it adds is worth having and nothing more:

  * one exception type, `YamlError`, subclassing ValueError so call sites can
    catch it next to OSError;
  * a one-line message with the line number in it. PyYAML's own report runs to
    six lines and calls the input "<unicode string>", which tells someone
    looking at their own card file nothing at all;
  * `safe_load`, always — a card file must never be able to construct objects;
  * the dependency bootstrap, so the first read installs PyYAML if this machine
    has none (see scripts/deps.py).

This replaced scripts/minyaml.py, a hand-written parser that existed only
because the project once allowed no dependencies. 222 lines of our own YAML
handling against a library everyone else already trusts was the wrong trade once
that rule went.
"""

import sys

_yaml = None


class YamlError(ValueError):
    """Malformed YAML — with the line number the reader stopped at."""


def _load_pyyaml():
    """PyYAML, installing it on first use if this machine has none."""
    global _yaml
    if _yaml is not None:
        return _yaml
    try:
        import yaml
    except ImportError:
        import deps

        deps.activate()
        try:
            import yaml
        except ImportError as e:  # pragma: no cover - the bootstrap already raised
            raise YamlError(f"PyYAML is not available and could not be installed: {e}") from e
    _yaml = yaml
    return _yaml


def _tidy(text):
    return " ".join(str(text).split())


def _one_line(error):
    """A PyYAML error as a single line, keeping the part that helps: where.

    Both ends when they differ. An unclosed quote is *detected* at the end of the
    file but has to be *fixed* where it opened, so naming only one of the two
    sends the reader to the wrong place or hides how far the damage ran.
    """
    problem_mark = getattr(error, "problem_mark", None)
    context_mark = getattr(error, "context_mark", None)
    problem = _tidy(getattr(error, "problem", None) or str(error).splitlines()[0])
    context = getattr(error, "context", None)

    mark = problem_mark or context_mark
    if mark is None:
        return problem

    message = f"line {mark.line + 1}: {problem}"
    started = context_mark.line + 1 if context_mark is not None else None
    if started is not None and started != mark.line + 1:
        where = f"from line {started}"
        message += f" ({_tidy(context)} {where})" if context else f" (started {where})"
    return message


def load(text):
    """The document in `text`, or None if it is empty. Raises YamlError."""
    yaml = _load_pyyaml()
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise YamlError(_one_line(e)) from e


def compose(text):
    """The document in `text` as a *node tree*, keeping every node's position.

    `load` gives values; this gives nodes, and a node carries `start_mark` and
    `end_mark` — the line and column the parser found it at. That is what lets
    a caller edit a card file as text without re-serialising it, which is the
    only way to add a key and keep the comments and quoting the user wrote.

    Goes through the same bootstrap as `load`, so a machine that has never
    installed PyYAML still works. A caller doing `import yaml` itself would
    skip that and fail on a fresh checkout.
    """
    yaml = _load_pyyaml()
    try:
        return yaml.compose(text)
    except yaml.YAMLError as e:
        raise YamlError(_one_line(e)) from e


def main():
    """Reads a file named on the command line — a way to eyeball a card file."""
    if len(sys.argv) != 2:
        sys.exit("usage: python3 scripts/yamlio.py <file.yaml>")
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            print(load(f.read()))
    except (YamlError, OSError) as e:
        sys.exit(f"ERROR: {sys.argv[1]}: {e}")


if __name__ == "__main__":
    main()
