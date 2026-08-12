# Contributing

Thanks for your interest. Bug reports, improvements to the skills, the card
layout or the docs are all welcome. If your change touches anything visible —
the card, the mark, the readme graphics, the landing page — start with
[docs/design.md](docs/design.md).

## Ground rule: no content in the repo

This repo is subject-agnostic — it holds tools, not knowledge. `sources.yaml`,
`knowledge/`, `catalog/`, `cards/` (except `example.yaml`) and `output/` are in
`.gitignore` on purpose. Please do not override that with `git add -f`: your
own sources are useless to everyone else, and ingested third-party texts do not
belong here for copyright reasons.

Example cards should demonstrate a format, not a field of study.
`cards/example.yaml` is the only card file that is versioned.

## Development setup

```bash
git clone https://github.com/mhabedank/lernkarten.git
cd lernkarten
python3 -m pip install --user -r requirements-dev.txt
```

That is only pytest and ruff — the tools themselves need nothing but Python.
To try your changes as a plugin, add the clone as a marketplace from inside
Claude Code: `/plugin marketplace add .` and then
`/plugin install lernkarten@mhabedank`.

## Before the pull request

Exactly what CI checks:

```bash
ruff check .                                                # lint
ruff format --check .                                       # formatting
pytest                                                      # tests
lernkarten check cards/example.yaml                         # card schema + PDF build
python3 scripts/check_docs.py                               # skill frontmatter + doc links
```

All of them have to be green — CI blocks the merge otherwise.

## Branch model

`main` is protected: **direct pushes are blocked server-side.** Every change
goes through a pull request with green CI.

```bash
git switch -c fix/card-margin
# … change, commit …
git push -u origin fix/card-margin
gh pr create
```

Install the local hook once, and an accidental push to `main` fails before it
even reaches the network:

```bash
scripts/install-hooks.sh
```

## Commits

A short, descriptive subject line in the imperative, ideally with a prefix
(`skill:`, `build:`, `docs:`, `ci:`).

```
build: make the page margin configurable
```

## What to aim for

- **Language**: English, everywhere — code, comments, docstrings, docs and
  commit messages. The cards a user generates are of course in whatever
  language their sources are.
- **Skills** (`skills/*/SKILL.md`): terse and action-oriented. A skill
  describes a procedure, not a theory. New skills need frontmatter with `name`
  and a `description` that spells out its triggers.
- **Python**: the standard library only. A runtime dependency the user has to
  install is a bug, not a trade-off — that is why `scripts/minyaml.py` exists
  instead of PyYAML.
- **Layout**: the card is `templates/card.typ`, the press sheet
  `templates/cards.typ` — never the generated file. Read
  [docs/design.md](docs/design.md) first: it says what the bands mean, why
  colour never carries meaning alone, and how to re-render the brand graphics
  afterwards.
- **The engine** is pinned by version and SHA-256 in `scripts/engine.py`. When
  you bump it, bump every platform's checksum with it.
- **Card conventions** (schema, escaping, style) live in [CLAUDE.md](CLAUDE.md)
  and apply to contributions too.

## Reporting bugs

Please include: operating system, Python version, the command you ran,
the full error message — and, if it is about a card, the YAML snippet in
question (without your private material, if you can avoid it).
