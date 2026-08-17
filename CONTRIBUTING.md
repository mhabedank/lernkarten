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
`cards/example.yaml` is the only card file of your own that is versioned.

The one exception is the test data under `tests/fixtures/demo-project`: a
complete miniature project about an invented archipelago, written for this
repository and covered by its licence. Extend it when you need test material —
and keep inventing rather than quoting, so it stays free of anyone else's
copyright.

## Development setup

```bash
git clone https://github.com/mhabedank/lernkarten.git
cd lernkarten
python3 -m pip install --user -r requirements-dev.txt
```

That is pytest and ruff; the tools themselves currently need no packages of
their own. Python 3.12 or newer. To try your changes as a plugin, add the clone
as a marketplace from inside Claude Code: `/plugin marketplace add .` and then
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

The end-to-end tests need test data that is not in the repo — the PDFs, the
scan, the infographic and the Word document are generated — and a typesetting
engine. Both are one command each, and CI does the same:

```bash
python3 scripts/make_testdata.py            # builds the binary test material
LERNKARTEN_E2E=1 pytest tests/test_e2e.py   # fetches the engine if missing
```

They run against the demo project in `tests/fixtures/demo-project`, which is
also what you copy when you want to try the skills by hand. How to do that, and
what to test that no script can check, is in [docs/testing.md](docs/testing.md).

## Branch model

`main` is protected: **direct pushes are blocked server-side.** Every change
goes through a pull request with green CI.

Branch names are `<prefix>/<short-kebab-case>` — always a prefix, always a
slash. The prefixes are `fix/`, `feat/`, `skill/`, `build/`, `docs/`, `ci/`,
`test/` and `design/`.

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

A short, descriptive subject line in the imperative, with the same prefixes the
branches use: `fix:`, `feat:`, `skill:`, `build:`, `docs:`, `ci:`, `test:`,
`design:`.

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
- **Python**: 3.12 or newer. Dependencies are allowed — see
  [Dependencies](#dependencies) below for what one has to clear. Don't reinvent
  a wheel a maintained library already turns.
- **Layout**: the card is `templates/card.typ`, the press sheet
  `templates/cards.typ` — never the generated file. Read
  [docs/design.md](docs/design.md) first: it says what the bands mean, why
  colour never carries meaning alone, and how to re-render the brand graphics
  afterwards.
- **The engine** is pinned by version and SHA-256 in `scripts/engine.py`. When
  you bump it, bump every platform's checksum with it.
- **Card conventions** (schema, escaping, style) live in [CLAUDE.md](CLAUDE.md)
  and apply to contributions too.

## Dependencies

This project used to allow none at all, on the grounds that a non-technical
person should not have to install anything. That reason no longer holds: this is
a Claude Code extension, so the person running it already has a terminal and a
working install. Optimising for someone who has neither cost real quality and
bought nothing.

So dependencies are allowed. What is not allowed is **friction**:

> A dependency is acceptable when someone on Windows, macOS or Linux gets it
> with one ordinary command and no further work.

Concretely, a Python package has to install from PyPI with a plain
`pip install`, on every supported Python version, on all three platforms. It
ships prebuilt wheels or is pure Python — an sdist-only package that needs a
C, C++ or Rust toolchain is friction and is out, however good it is. No `apt`,
no `brew`, no `choco`, no manual `PATH` edit, no post-install step. It works
offline once installed.

An **external binary** has exactly two acceptable shapes: self-fetching and
checksum-pinned, the way `scripts/engine.py` handles Typst, or genuinely
optional, the way `pdftotext` is — absent, it degrades or skips, never fails.
A binary the user must install by hand for a core path is neither.

And prefer the library. Hand-rolling something a maintained package already does
needs a reason in the pull request; "it is only 200 lines" is not one. Both
things this project had hand-rolled under the old rule are gone: PyYAML replaced
`scripts/minyaml.py`, and Pillow replaced the `sips`/`magick` shell-out in
`scripts/make_testdata.py`.

### What a new dependency has to clear

Answer these in the pull request. A question you cannot answer is a reason to
stop rather than a formality to skip.

- **Wheels** for Windows, macOS and Linux, or pure Python. No compiler needed.
- **Maintained**: a release within roughly the last 12 months, issues being
  triaged, not archived or looking for a maintainer.
- **Production-ready**: a stable line. No alpha, beta or release candidate;
  either ≥ 1.0 or a long, obviously stable track record.
- **Really used** by other people — meaningful download volume and real
  dependents. A package with forty downloads a week is a liability.
- **Provenance**: an identifiable maintainer or organisation, a public
  repository, a PyPI history that matches it. Signed or attested releases are
  a plus.
- **Not a typo-squat.** Check the spelling against the package you actually
  mean.
- **No install-time scripts** that build, download or phone home.
- **Licence** compatible with MIT.
- **Proportionate**: a shallow transitive tree. Thirty packages to get one
  function is a reason to copy the three lines instead.
- **No known unfixed advisory**, and `.github/dependabot.yml` covers whatever
  manifest declares it.
- **Declared honestly**: actually imported somewhere, with a version bound and
  a one-line comment saying what it is for. Tools pinned exactly (the way
  `ruff==0.16.2` is), libraries given a range. Unused dependencies get deleted.

### Getting one to the user

There is no install step between `/plugin install` and the skills calling
`bin/lernkarten` — no virtualenv, no `pip` hook, just whatever Python the user
has. So a runtime dependency has to fetch itself, exactly as the typesetting
engine does.

`scripts/deps.py` is that mechanism. It declares the runtime requirements,
installs them once into a cache folder, and puts that folder on `sys.path`:

```bash
lernkarten deps --check      # what is required, and where it came from
```

To add a runtime dependency, put it in `REQUIREMENTS` there with the module name
to import, pinned exactly — the user is not installing this on purpose, so it
must not drift under them. Any module that imports it at the top level has to
call `deps.activate()` first; `lernkarten build` and `lernkarten check` already
do.

Two details worth knowing before you rely on it:

- It installs with `pip install --target`, not into a virtualenv, because
  `python3 -m venv` needs `ensurepip` and Debian and Ubuntu ship that as a
  separate `python3-venv` package. A bootstrap whose failure mode is "now
  apt-get something" would defeat its own purpose.
- It passes `--only-binary :all:`, so a package with no wheel for the user's
  platform fails loudly here rather than trying to compile on their machine.
  That is the friction rule of this section, enforced.

`LERNKARTEN_NO_BOOTSTRAP=1` forbids installing anything, and
`LERNKARTEN_DEPS_DIR` moves the cache. There are no runtime dependencies at the
moment, so `activate()` currently returns without doing anything.

## Reporting bugs

Please include: operating system, Python version, the command you ran,
the full error message — and, if it is about a card, the YAML snippet in
question (without your private material, if you can avoid it).
