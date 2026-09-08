# Data model: Sphinx documentation foundation (012)

**No file format changes.** The spec's *Format Contracts* table is "none" on all
four rows: `sources.yaml`, `knowledge/<id>/<doc>.md`, `catalog/topics.md` and
`cards/*.yaml` are untouched, and nothing a user has on disk is read or written.
The `SKILL.md` `metadata.docs` block belongs to **013**.

What this feature does introduce is a set of build-time entities. They are listed
here because tests assert against them and because 013 and 014 extend them.

## Entities

### Documentation source

An existing repository file published unchanged.

| Field | Value |
|---|---|
| Instances | `docs/workflow.md`, `docs/design.md`, `docs/testing.md`, `CONTRIBUTING.md` |
| Location | **where it already is.** Never moved — `check_docs.REQUIRED_FILES` pins the first three and GitHub reads the fourth from the root (FR-009, FR-028) |
| Reaches the site by | one MyST `{include}` with `:relative-images:` and no other option |
| Title | its own H1. Nothing is retyped (FR-008) |
| Copies | exactly one |

### Embedded page

| Field | Value |
|---|---|
| Instance | `docs/leitner.html` |
| Change | **none — byte-identical** (FR-010) |
| URL | exactly one: `/leitner.html`, the site root. Never a second copy under `/docs/` (SC-012), and never a `_downloads/` copy (plan.md C4) |
| Navigation | through the wrapper page, never by conversion |
| Gates | `LEITNER_PAGE`, `check_leitner_intervals` (bidirectional against `scripts/leitner.py`) and `tests/test_check_docs.py`'s existence assertion all keep working, because the file does not move (FR-011) |

### Documentation area

| Field | Value |
|---|---|
| Instances in 012 | **user guide**, **contributing** |
| Represented by | a `toctree` in `docsite/index.md` and an index page per area |
| Asserted by | SC-002 — a test walks the built `toctree` from the root document; the two areas are separate top-level branches. The `toctree`, not the rendered sidebar, so the assertion is not tied to a theme version |
| Extension point | 013 adds a reference area, 014 a tutorial area — two more entries, no restructuring (FR-012) |

### Wrapper page

| Field | Value |
|---|---|
| Instance | `docsite/user/leitner.md` |
| Contains | a short introduction and one link out. **Not** a restatement of the method — that would be a second copy (FR-008, FR-032) |
| Exists because | a `toctree` accepts documents and absolute URLs, never a relative `.html` file, and an absolute URL breaks `file://` viewing (FR-018) |

### Repository-link transform

| Field | Value |
|---|---|
| Instance | `docsite/_ext/repolinks.py` |
| Input | a link written in a repository file, kept relative in the source |
| Output | an internal cross-reference, a site-root relative link, or an absolute GitHub URL |
| Resolution base | the **source file's own directory** — `node.source`, which carries the real path even inside an `{include}` |
| Tables | `PAGES` and `SERVED` — see [contracts/docsite-layout.md](contracts/docsite-layout.md) |
| Constraint | it must never require a source file to change, or `check_docs.check_links` loses coverage that SC-005 forbids losing |

### Docs requirements

| Field | Value |
|---|---|
| Instance | `requirements-docs.txt` |
| Contents | `sphinx==9.0.4`, `myst-parser==5.1.0`, `pydata-sphinx-theme==0.21.0`, one comment each |
| Distinct from | `requirements-dev.txt` (what every contributor installs) and `scripts/deps.py` (the runtime channel a user reaches) |
| Invariant | no name in it may appear in `scripts/deps.py`'s `REQUIREMENTS`, and nothing under `bin/` or `scripts/` may import one (FR-003, FR-005, SC-009) |

### Site assembly

| Field | Value |
|---|---|
| Instances | the local `_site` (`scripts/build_docs.py`) and the deployed `_site` (`pages.yml`) |
| Invariant | **the same shape**, which is what makes the local build a preview (FR-038) |
| Layout | see [contracts/docsite-layout.md § 7](contracts/docsite-layout.md) |
| Written by | the three root files are written **by both** on CI — `pages.yml`'s `cp` lines (which two existing tests read as text) and `build_docs.py`'s copies (which make the local build real). Idempotent, identical bytes; see [plan.md § The `_site` assembly](plan.md#the-_site-assembly-stated-once) |
| Assertion | every relative link in `docs/index.html` is present in `_site`, by a `cp` or by the documentation build (FR-016) |

## State transitions

None. Nothing here has a lifecycle; a build either succeeds with zero warnings
or fails (FR-020).

## Validation rules

| Rule | Enforced by |
|---|---|
| A cross-reference to a non-existent target fails the build | `-W --keep-going` (FR-020, SC-003) |
| Every relative link in a migrated document still resolves on the file system | `check_docs.check_links`, unchanged (SC-011) |
| Every Markdown file under `docsite/` is covered by the docs gate | `markdown_files()`, extended (FR-037) |
| The build is byte-identical between runs | SC-004, excluding `.doctrees/` and `.buildinfo` |
| The site loads no third-party sub-resource | SC-014 |
| `docs/leitner.html` appears exactly once in `_site` | SC-012 |
