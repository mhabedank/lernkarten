# Phase 0 — Research: Figure cards

**Feature**: [spec.md](./spec.md) · **Date**: 2026-08-22

Six questions had to be answered before the design could be written. Four were
settled by spiking against the pinned engine (typst 0.15.1, already cached) and
against PyPI; two by reading the code this feature has to fit into. The spikes
were thrown away (constitution XI).

---

## R1 — Does the overflow mechanism still work when a card holds a picture?

**Decision**: yes, unchanged. `measure()` sees an image, so the existing
`<overflow>` metadata path needs no new machinery — only the picture has to be
inside the block that gets measured.

**Evidence**: spiked against `typst 0.15.1`. The same block measured with and
without a 30 mm picture box:

```json
[{"text":"7.24pt","both":"111.15pt"}]
```

7.24 pt of text alone; 111.15 pt once the picture is in it. The number the
template already compares against `field-h - 2 * pad-y` therefore accounts for
the picture for free.

**Consequence for the design**: the picture must be part of the *measured*
body, not placed beside it. A picture given `1fr` measures as its minimum, so
the template computes overflow against a **minimum useful picture height**
rather than against the room the picture happens to be given — otherwise a
picture squeezed to 2 mm would report "fits" while being useless.

**Alternatives considered**: a second `typst query` pass for pictures
specifically — rejected, it would double the compile cost for a fact the first
pass already knows.

---

## R2 — How does the engine reach a picture, given the build compiles in a temp workdir?

**Decision**: **stage the pictures into the workdir**, content-addressed, next
to the templates that already get copied there.

**Evidence**: Typst sandboxes the compile to a project root, and the root
defaults to the input file's parent — which is the temp workdir. A relative
path out of it is refused outright:

```text
error: path "../../figspike-outside.png" would escape the project root
  = hint: you can adjust the project root with the --root argument
```

**Rationale**: the alternative is `--root <project>`, and it fails on something
structural: `build_pdf.py` has no notion of a project. It takes a list of card
*files*, which may come from anywhere, and `offending_card()` re-typesets one
card at a time to attribute an engine error. Staging keeps the workdir
self-contained, which is exactly the property that lets `offending_card()` work
without new plumbing. It also mirrors what the module already does with
`templates/*.typ`.

Staged names are `fig-<sha256[:12]>.<ext>` — content-addressed, so a picture
used by three cards is copied once per run and a rename in the project cannot
collide inside the workdir.

**Alternatives considered**:

- `--root` plus project-relative paths — rejected above.
- Embedding the bytes in `cards.json` — Typst can take `image(bytes)`, but
  `cards.json` is decoded as JSON and there is no base64 decoder in Typst to
  turn a string back into bytes. Also inflates the JSON by a third.

---

## R3 — Which picture formats may a card name?

**Decision**: `png`, `jpg`, `jpeg`, `gif`, `svg`, `webp`. Anything else is
refused by name, before the engine is called.

**Evidence**: spiked each against `typst 0.15.1`. GIF, WebP, PNG, JPEG and SVG
compile; TIFF and BMP fail with `error: unknown image format`.

**Rationale**: the accepted set is a property of the pinned engine, so the
constant lives next to `engine.VERSION`'s consumers with a comment saying that
bumping the engine may widen it (constitution XV already requires the engine
bump to be deliberate).

> **Correction, 2026-08-25 ([BUG-008](./bugs/BUG-008.md))**: right for a *card*,
> and wrongly reused for a *fetch*. AVIF is genuinely not in the set — verified,
> `error: unknown image format` — but the web serves it constantly, and a URL
> frequently carries no extension to check at all. What may be *downloaded* is a
> different question; see R8.

---

## R8 — What may be accepted from the network? *(added by BUG-008)*

**Decision**: a **second, wider set**, decided from the response rather than from
the URL. `build_pdf.IMAGE_FORMATS` stays what it is — what typst 0.15.1 can
print — and `figures.py` gets its own list of what a web server may hand back.

**Why R3 was not enough**: R3 asked "which picture formats may a *card* name?"
and answered correctly. `figures.py:47` copied that answer for "what may we
*download*?", with a comment asserting the two are "kept in step". They are not
the same question:

| | what the engine prints | what the web hands back |
|---|---|---|
| decided by | typst 0.15.1, pinned | the server |
| knowable from | the file's extension | the response |
| AVIF | **no** — `error: unknown image format` | yes, and often: 53 of 851 URLs |

**Evidence**: a genuine AVIF (`ftypavif` magic, round-tripped through Pillow)
compiled against the pinned engine fails. So AVIF cannot simply be added to
`IMAGE_FORMATS`: that would move a clear message to an engine error at build
time, and would wrongly let a card name one.

**Consequence**: three answers where there was one —

1. *Is this an image?* — the response says: `Content-Type`, then magic bytes.
2. *May it go on a card?* — the engine's set says.
3. *Does this URL name a file at all?* — often not, and that is its own message.

**Alternatives considered**: *widening `IMAGE_FORMATS`* — refuted above.
*Converting AVIF to PNG on fetch* — needs a runtime image library (Pillow is
dev-only) to clear Principle IV for something the user solves with one command;
refusing with an honest message is proportionate, and FR-028 says so.

---

## R4 — What can be checked in Python, and what has to be left to the engine?

**Decision**: split the four causes FR-004 requires by who can answer them
soonest.

| Cause | Answered by | When |
|---|---|---|
| picture missing | Python — `exists()` | before the engine runs |
| picture outside the project | Python — resolved path vs project root | before the engine runs |
| unsupported format | Python — extension vs the R3 set | before the engine runs |
| picture corrupt / undecodable | the engine, attributed by `offending_card()` | at test-compile |

**Evidence**: `lernkarten check` already test-typesets (`--check`: "only
validate and test-typeset, write no PDF"), and `offending_card()` already
exists to name the card an engine error belongs to. The engine's own messages
are specific — `file not found (searched at …)`, `unknown image format` — so
nothing is lost by letting it own the last one.

**Rationale**: this avoids a runtime image-decoding dependency entirely.
Pillow would have answered "corrupt" in Python, but it is a *dev* dependency
and promoting it to runtime for one boolean fails the proportionality gate
(constitution IV) when the engine already answers it. `imghdr` is not an option
— it was removed from the standard library in Python 3.13, which this project
supports.

**Open consequence**: `overflowing()` calls `typst query`, which 0.15.1 now
prints a deprecation warning for (`use typst eval … instead`). It still works
and the warning goes to stderr while the JSON goes to stdout, so nothing breaks
here. Out of scope for this feature; worth its own `fix/` branch.

---

## R5 — What resolves a picture path, given a card file can live anywhere?

**Decision**: a picture path is **relative to the project root, and the project
root is the parent of the directory holding the card file**. `cards/x.yaml` →
the project is `cards/`'s parent; `figures/…` resolves under it.

**Rationale**: the same project then builds identically from any working
directory, which is what makes a project portable between machines — the
property FR-004's "inside the project" rule exists to protect. Resolving
against the current directory would make a deck build for whoever ran it from
the right folder, which is a defect wearing a preference's clothes.

**Alternatives considered**: an explicit `--project` flag (more to remember,
and every skill invocation would have to pass it); absolute paths in the card
file (breaks the moment the project is copied, and breaks Windows immediately).

---

## R6 — Is there a library for pulling figures out of a PDF, and does it clear the gates?

**Decision**: **`pypdfium2`**, pinned exactly, installed on demand as an
*optional* set through the existing `scripts/deps.py`.

**Evidence** (PyPI, checked 2026-08-22):

| Fact | Value |
|---|---|
| Latest version | `5.13.0`, released **2026-08-13** — nine days old |
| Wheels | `py3-none-*` for macOS arm64/x86_64, manylinux x86_64/aarch64, musllinux, **`win32`, `win_amd64`, `win_arm64`** |
| Transitive dependencies | **none** — `requires_dist` is null |
| Wheel size | 3.5 MB (macOS arm64), 3.7 MB (manylinux x86_64), 3.9 MB (win_amd64) |
| Licence | BSD-3-Clause / Apache-2.0 — compatible with MIT |
| Release history | 129 releases, stable 5.x line |
| Python floor | `>=3.6`, so 3.12 is covered |

`py3-none` wheels with a bundled PDFium binary mean no compiler, no C
extension, no per-Python build — the same shape that makes the constitution's
friction rule satisfiable. The `win_arm64` wheel matters specifically: its
absence for PyYAML on cp311 is what moved this project's Python floor to 3.12,
so it is a gate this project has already failed once and knows to check.

**Alternatives considered**:

- **PyMuPDF** — the obvious first thought and the best API of the three.
  **Rejected on licence**: AGPL-3.0, which is not compatible with shipping
  under MIT. This is a hard stop, not a preference.
- **pdfplumber / pdfminer.six** — pure Python, permissive, and it can list
  embedded images. Rejected on capability: it hands back the image *objects*
  and their boxes but not a rendered region, so a vector figure (the common
  case for a chart in a real paper) yields nothing to print. It also pulls
  `pdfminer.six`, `cryptography` and `Pillow` — a deep tree for one function.
- **pikepdf** — qpdf bindings, MPL-2.0, wheels everywhere. Same capability gap
  as pdfminer: it is a PDF *object* library, not a renderer.
- **Shelling out to `pdftoppm`** (poppler, already an optional binary here) —
  renders whole pages only, and a whole page is not a figure. Kept in mind as
  the fallback if pypdfium2 ever fails a gate.

**Runtime or dev?** Runtime, but **optional**. `deps.py` already parameterises
`missing()`, `install()` and `target_dir()` by a requirement list, so a second
module-level set costs a few lines and gets its own cache directory for free.
It installs the first time a PDF figure is actually asked for — a user who
never ingests a PDF never downloads 3.5 MB, and a user offline gets the
degraded path FR-018 requires rather than a failure.

---

## R7 — Does the demo project already carry the material?

**Decision**: mostly. Four generators exist and gain a figure; two new pieces
are needed.

| Path this feature claims | Demo material | Status |
|---|---|---|
| A standalone picture worth showing | `generators/tide-chart.typ` → `raw/images/tide-chart.png` | exists |
| A standalone picture *not* worth showing | `generators/noticeboard.typ` → `raw/images/harbour-noticeboard.jpg` | exists |
| A figure inside a PDF, plus a repeated logo to reject | `generators/handbook.typ` | needs a figure and a page header added |
| A picture linked from a markdown file | — | **new**: a markdown file under `raw/field-notes/` with a relative `![…](…)` link |
| A picture on a web page | `raw/web/` | needs an `<img>` and a generated picture |
| Four broken card fixtures for SC-002 | `broken/` holds ten today | **new**: four files |

No second corpus (constitution XI). The generated pictures join the other
generated binaries in `.gitignore` and in `scripts/make_testdata.py`.

---

## Summary of decisions

1. Pictures are staged into the compile workdir, content-addressed (R2).
2. Paths resolve against the project root, inferred from the card file (R5).
3. Three of the four failure causes are Python's, one is the engine's (R4).
4. Accepted formats are the engine's five plus WebP, checked by extension (R3).
5. Overflow needs no new mechanism, only a minimum picture height (R1).
6. `pypdfium2==5.13.0` as an optional runtime set through `deps.py` (R6).
7. The demo project is extended, never duplicated (R7).
