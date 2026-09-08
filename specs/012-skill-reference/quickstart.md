# Quickstart: verifying the documentation foundation (012)

Everything below is runnable. It is the sequence a reviewer walks to decide
whether 012 is done, and it maps one-to-one onto the success criteria.

## Prerequisites

Python 3.12 or newer. Nothing else — no typesetting engine, no network after the
install, no separately installed binary.

```bash
python3 -m pip install --user -r requirements-docs.txt
```

## 1 — The build (SC-001, FR-019)

```bash
python3 scripts/build_docs.py
```

**Expect**: exit 0, and a printed path to `_site/index.html`. No arguments, no
network.

## 2 — Read it (SC-002, SC-007, FR-007, FR-038)

`_site` is a site, so serve it rather than opening it — FR-014's landing-page
link points at the **directory** `docs/`, and over `file://` a browser shows a
directory listing instead of following it:

```bash
python3 -m http.server -d _site 8000
```

Open `http://localhost:8000/`.

**Expect**:

- the landing page, unchanged, with one new link into the documentation;
- following it reaches `/docs/` in one click;
- a persistent sidebar with **two** top-level areas, *user guide* and
  *contributing*;
- `docs/workflow.md` and the Leitner method page under the first;
  `docs/design.md`, `docs/testing.md` and `CONTRIBUTING.md` under the second;
- the Leitner entry links out to `/leitner.html` at the site root — one page,
  one URL, opened rather than downloaded (SC-012);
- the pictures in the workflow and design pages **render**, not link (FR-030).

## 3 — Warnings are errors (SC-003, FR-020)

```bash
printf '# Probe\n\n[nothing](nowhere.md)\n' > docsite/probe.md
python3 scripts/build_docs.py ; echo "exit=$?"
rm docsite/probe.md
```

**Expect**: non-zero exit, and a message naming `docsite/probe.md` and the
missing target.

## 4 — Determinism (SC-004)

```bash
python3 scripts/build_docs.py && cp -R _site/docs /tmp/docs-a
python3 scripts/build_docs.py && cp -R _site/docs /tmp/docs-b
diff -r -x '.doctrees' -x '.buildinfo' /tmp/docs-a /tmp/docs-b && echo identical
```

**Expect**: `identical`. The two exclusions are Sphinx's own incremental-build
state, which is why SC-004 names them.

## 5 — The gates are unchanged (SC-005, SC-010, FR-024)

The same four commands as before this feature — **no fifth**:

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

**Expect**: all four green. `ruff` now also reads `docsite/conf.py` and
`docsite/_ext/`, which is the scope widening FR-024 records.

Then the bidirectional Leitner gate, by hand:

```bash
# remove an interval from docs/leitner.html, then:
python3 scripts/check_docs.py    # names that interval, exits non-zero
# add an interval scripts/leitner.py does not define, then:
python3 scripts/check_docs.py    # reports that too
```

## 6 — Without the docs requirements (SC-006, SC-009, FR-023)

In an environment where none of the three packages is installed:

```bash
pytest -q
python3 bin/lernkarten check cards/example.yaml
python3 bin/lernkarten build cards/example.yaml -o output/cards.pdf
```

**Expect**: the suite passes with the docs-build tests reported as **skipped**,
each naming `requirements-docs.txt`; both `lernkarten` commands run unchanged.

## 7 — Every link (SC-011)

```bash
python3 scripts/check_docs.py       # the file-system half — all 31 still resolve
grep -ro 'href="[^"]*"' _site/docs | grep -c 'github.com'
```

**Expect**: `check_docs` green, and the GitHub URLs present in the *output* while
the *sources* still carry relative paths. The two checks overlap on purpose
(US4 scenario 3).

Spot-check the four shapes in `_site/docs/contributing/design.html`:

| Source link | Expect |
|---|---|
| `../templates/card.typ` | `https://github.com/…/blob/main/templates/card.typ` |
| `../assets/fonts/` | `https://github.com/…/tree/main/assets/fonts` |
| `index.html` | `../../index.html` |
| `../assets/card-box.pdf` | `../../card-box.pdf` |

## 8 — No third party (SC-014)

```bash
grep -rEo '<(link|script|img)[^>]+https?://[^>]*>' _site/docs | sort -u
```

**Expect**: nothing. The three faces come out of `assets/fonts/`; the theme
bundles its own icon font.

## 9 — On the other two platforms (SC-001, FR-034)

Nothing to run by hand: the `docs-build` CI job does steps 1 and 5 on
`ubuntu-latest`, `macos-latest` and `windows-latest`. Check that the job exists,
that its id is **not** `docs`, and that all three legs are green.

## 10 — The manual rows (SC-005, SC-008, SC-013)

Three, and only three, in `docs/testing.md`:

| # | Do |
|---|---|
| 44 | Open a documentation page at a 375 px viewport. No horizontal scrolling, and no Archivo prose below 15 px — a code sample and a letterspaced label are exempt |
| 45 | Read the diff of `tests/test_landing_page.py` and `scripts/check_docs.py`. No assertion deleted, no target dropped from a derived set, no condition relaxed |
| 46 | Confirm the documentation build ran on the pull request that introduced the change |

## 11 — Deployed (SC-007, SC-013)

After the merge, on `https://mhabedank.github.io/lernkarten/`:

- the landing page is byte-identical to the repository copy;
- every relative link it makes resolves;
- `/docs/` serves the documentation;
- `/leitner.html` serves the method page, and there is no copy under `/docs/`;
- a documentation build that fails publishes **nothing** (FR-033).
