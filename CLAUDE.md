# Lernkarten — project instructions

Pipeline: `/sources` → `/ingest` → `/catalog` → `/cards` → `/print`.
The skills live under `.claude/skills/`. The project language is English:
code, comments, docs and commit messages are written in English.

## Conventions

- **Source register**: `sources.yaml` is the single source of truth about
  registered sources. Every source has a unique `id` (kebab-case).
- **Knowledge store**: `knowledge/<source-id>/<document>.md` — plain
  text/markdown with one frontmatter block (`source`, `path`/`url`,
  `ingested`).
- **Topic catalog**: `catalog/topics.md` — a hierarchy of topics (`##`) and
  subtopics (`###`), each with a short description and references (links to
  files under `knowledge/`).
- **Cards**: `cards/<topic-slug>.yaml` with this schema:

  ```yaml
  topic: "Display name of the topic"
  language: german          # language of the cards in this file
  cards:
    - subtopic: "Subtopic"
      front: "Question or term"
      back: "Answer or definition"
      source: "Short reference (optional)"
    - ...
  ```

  `language` is a plain language name or ISO code (`german`, `de`, `french`,
  …); `python3 scripts/build_pdf.py --help` lists the ones that work. It
  defaults to English and decides hyphenation and quotation marks. Files in
  different languages can go into one PDF.

  `front`/`back` are **LaTeX source**: special characters (`%`, `&`, `_`, `#`)
  have to be escaped; maths in `$...$` is allowed; `\\` produces a line break.
  The build script does NOT escape anything itself.
  No ASCII `"` inside the YAML strings (it terminates the string!) — write
  quotation marks as `` `...' `` or, in German, ``\glqq ...\grqq{}``.
- **PDF build**: `python3 scripts/build_pdf.py` (see `--help`). Output goes to
  `output/`. Never edit LaTeX by hand in `output/` — always go through the
  YAML files.

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
  force them in with `git add -f` — not even "just briefly".
- **Stay subject-agnostic**: examples and docs demonstrate the format, not a
  field of study. No subject-specific content in the README, the skills or the
  code.
- **`main` is locked**: changes go through a branch and a pull request. The
  server rejects direct pushes, and so does the `pre-push` hook.
- **Before every PR** these four gates have to be green (CI checks the same):

  ```bash
  ruff check . && ruff format --check .
  pytest
  python3 scripts/build_pdf.py --check cards/example.yaml
  python3 scripts/check_docs.py
  ```
