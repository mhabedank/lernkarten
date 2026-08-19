# Lernkarten — project instructions

Pipeline: `/learning-goal` → `/sources` → `/ingest` → `/catalog` →
`/research-gaps` → `/cards` → `/print`. `/learning-goal` and
`/research-gaps` are optional: without them the pipeline behaves as it did
before they existed.
The skills live under `skills/`. The project language is English:
code, comments, docs and commit messages are written in English.

## Conventions

- **Learning goal**: `goal.md` at the project root — frontmatter (`goal`,
  `kind`, `depth`, `updated`), `## Required topics` grouped into `### <Area>`,
  and `## Out of scope`. Optional; when present, `/catalog` builds the topic
  tree from it and a required topic nothing covers becomes `Status: gap`.
- **Source register**: `sources.yaml` is the single source of truth about
  registered sources. Every source has a unique `id` (kebab-case). The
  `research` type is written by `/research-gaps`, not by hand, and carries the
  `gap` it closes instead of a `path`/`url`.
- **Knowledge store**: `knowledge/<source-id>/<document>.md` — plain
  text/markdown with one frontmatter block (`source`, `path`/`url`,
  `ingested`).
- **Topic catalog**: `catalog/topics.md` — a hierarchy of topics (`##`) and
  subtopics (`###`), each with a short description and references (links to
  files under `knowledge/`). Optional per subtopic: `Status: gap` |
  `out of scope`, `Parents:` (every topic it belongs under, primary first) and
  `Related:`; optional per topic: `Also covers:`. Every one of them absent
  means the behaviour this repo had before the goal-driven catalog.
- **Cards**: `cards/<topic-slug>.yaml` with this schema:

  ```yaml
  topic: 'Display name of the topic'
  language: german          # language of the cards in this file
  cards:
    - subtopic: 'Subtopic'
      front: 'Question or term'
      back: 'Answer or definition'
      source: 'Short reference (optional)'
    - ...
  ```

  `language` is a plain language name or ISO code (`german`, `de`, `french`,
  …); `lernkarten build --help` lists the ones that work. It
  defaults to English and decides hyphenation and quotation marks. Files in
  different languages can go into one PDF.

  `front`/`back` are **Typst markup**. Write them in single quotes, so a
  backslash is a line break and `"` needs no escaping; double the apostrophe
  (`''`) for a literal one. Maths goes in `$...$` — Typst syntax, not LaTeX:
  `(a) / (b)` for fractions, `Omega`, `sigma`, `>=`, `"Var"(X)` for upright
  text, `#list([a], [b])` for a bulleted back. `#`, `*`, `_`, `@`, `<`, `>`
  and backtick need a backslash in running text; `%` and `&` do not.

  **Emphasis is a single star**: `*bold*` and `_italic_`. `**bold**` is
  markdown — Typst reads it as two *empty* strong elements around plain text,
  so the card prints unemphasised. It typesets, so nothing fails; only
  `check_project.py` reports it.

  **A backslash is a line break only before whitespace.** Before a markup
  character it escapes that character, which is what it is for. A card is one
  line of YAML, so `'first\*bold* rest'` gives a literal `*`, no line break,
  and every following `*` shifted by one. Write `'first\ *bold* rest'`, or
  reorder so no markup character follows the break.
- **PDF build**: `lernkarten build` / `lernkarten check` (see `--help`). Output
  goes to `output/`. The typesetting engine downloads itself on first use.
  Never hand-edit anything in `output/` — always go through the YAML files.
- **Design**: the card layout is `templates/card.typ`, the press sheet
  `templates/cards.typ`, the brand graphics `assets/brand/*.typ` (re-render
  with `python3 scripts/render_brand.py`). What the parts mean and which rules
  hold is in `docs/design.md` — read it before changing anything visible.

## Card style

- One card = one fact/concept. No double questions.
- Front short (max. ~2 lines), back max. ~6 lines — the card is only about
  100 × 72 mm. Two cards beat one overloaded card.
- Phrase an active recall prompt ("What …?", "Why …?", "Name …"), no yes/no
  questions.
- Card language = language of the source, unless the user says otherwise.
  Always write it into the file's `language:` key — the build reads it from
  there, so nobody has to remember a flag at print time.

## Repo rules

This is a public open-source repo — it holds the tools, not the knowledge.

- **Never commit your own content**: `sources.yaml`, `knowledge/`, `catalog/`,
  `cards/` (except `example.yaml`) and `output/` are in `.gitignore`. Never
  force them in with `git add -f` — not even "just briefly". The test data
  under `tests/fixtures/demo-project` is the one exception: invented for this
  repo, versioned on purpose, never anyone else's text.
- **Stay subject-agnostic**: examples and docs demonstrate the format, not a
  field of study. No subject-specific content in the README, the skills or the
  code.
- **`main` is locked**: changes go through a branch and a pull request. The
  server rejects direct pushes, and so does the `pre-push` hook. Branches are
  `<prefix>/<short-kebab-case>` (`fix/card-margin`, `feat/zotero-tags`); the
  prefixes are `fix/`, `feat/`, `skill/`, `build/`, `docs/`, `ci/`, `test/`,
  `design/`, and commit subjects use the same set.
- **Dependencies** are allowed when they install with a plain `pip install` on
  Windows, macOS and Linux, with wheels and no compiler — and prefer a
  maintained library over hand-rolling. There are none at runtime yet, and there
  is no mechanism to deliver one to a plugin user, so a *runtime* dependency
  cannot ship today. The gates are in `CONTRIBUTING.md`. Python 3.12 or newer.
- **Before every PR** these four gates have to be green (CI checks the same):

  ```bash
  ruff check . && ruff format --check .
  pytest
  lernkarten check cards/example.yaml
  python3 scripts/check_docs.py
  ```

- **Test first**: write the test, watch it fail on its assertion, then make it
  pass. For a skill (prompt) change the red artifact is a check in
  `scripts/check_project.py` plus a failing case in
  `tests/test_check_project.py` — if no failing check can be written, the
  requirement is too vague to implement yet. Details in `docs/testing.md`.
- **Testing**: the demo project under `tests/fixtures/` carries raw material
  for every source type. Its binary half (PDFs, a scan, an image, a DOCX, the
  Zotero attachments) is generated from typst sources by
  `scripts/make_testdata.py` — never commit binaries. `tests/test_e2e.py`
  drives the real command and skips without a typesetting engine, so run it
  once with `LERNKARTEN_E2E=1` before the PR. `scripts/check_project.py` checks
  what the model-driven steps write, `scripts/zotero_stub.py` fakes Zotero, and
  `scripts/demo.py` sets up a scratch project for testing by hand. The
  checklist is in `docs/testing.md`; a new feature or failure mode belongs in
  the demo project, not in a fixture of its own.
