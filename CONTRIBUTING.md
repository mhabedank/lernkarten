# Contributing

Thanks for your interest. Bug reports, improvements to the skills, the LaTeX
layout or the docs are all welcome.

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

On the system side you need the same things as for normal use: `pdflatex`,
`pdftotext`, Python ≥ 3.10 (see the [README](README.md#requirements)).

## Before the pull request

Exactly what CI checks:

```bash
ruff check .                                                # lint
ruff format --check .                                       # formatting
pytest                                                      # tests
python3 scripts/build_pdf.py --check cards/example.yaml     # card schema + LaTeX build
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
- **Skills** (`.claude/skills/*/SKILL.md`): terse and action-oriented. A skill
  describes a procedure, not a theory. New skills need frontmatter with `name`
  and a `description` that spells out its triggers.
- **Python**: standard library plus PyYAML, no further runtime dependencies.
- **LaTeX**: layout changes go into `templates/cards.tex.in` only, never into
  the generated `.tex`.
- **Card conventions** (schema, escaping, style) live in [CLAUDE.md](CLAUDE.md)
  and apply to contributions too.

## Reporting bugs

Please include: operating system, Python and TeX version, the command you ran,
the full error message — and, if it is about a card, the YAML snippet in
question (without your private material, if you can avoid it).
