# Phase 1 — Data model: Figure cards

**Feature**: [spec.md](./spec.md) · **Research**: [research.md](./research.md) · **Date**: 2026-08-22

In this project the data model *is* the file formats — they are the entire
contract between the two halves (constitution I). Three artifacts change; the
formal contracts are under [contracts/](./contracts/).

---

## 1. Figure — a picture worth showing

**Lives at** `figures/<source-id>/<slug>.<ext>` in the user's project, beside
`knowledge/<source-id>/`. Written by `/ingest`, read by `lernkarten build`,
gitignored like every other piece of user content.

| Field | Where it lives | Rule |
|---|---|---|
| source | the directory name | equals a `sources.yaml` `id`, exactly as `knowledge/` does |
| slug | the file name | kebab-case, unique within the source |
| format | the extension | one of `png`, `jpg`, `jpeg`, `gif`, `svg`, `webp` ([R3](./research.md#r3--which-picture-formats-may-a-card-name)) |
| bytes | the file | a copy, never a move — the original is untouched (FR-010) |

A figure has **no metadata file of its own**. Everything said about it is said
in the knowledge document it came from, because that is the thing that also
holds the transcription explaining it. A directory of orphan pictures with a
sidecar JSON each would be a second catalog to keep in step.

**Relationships**: one source → many figures. One knowledge document → many
figures (a PDF has several). One figure → many cards (a description card and a
recognition card, and nothing stops two decks referencing it).

---

## 2. Visual judgement — the verdict, recorded per picture

**Lives in** the `figures:` list in `knowledge/<source-id>/<slug>.md`
frontmatter. One entry per picture *considered*, kept or not.

```yaml
figures:
  - at: 'page 3'
    visual: chart
    path: figures/handbook/tide-curve.png
    caption: 'Semidiurnal tide curve for the Kestrel Deep'
  - at: 'page 1'
    visual: none
    why: 'harbour office logo, repeated in every page header'
```

| Field | Required | Rule |
|---|---|---|
| `at` | always | where the picture sat: `page 3`, the linking line, or the file name for a folder source. Free text — a human locator, not a parsed one |
| `visual` | always | one of `diagram`, `chart`, `map`, `none`. Anything but `none` means kept |
| `path` | when kept | project-relative, resolves to an existing file, inside the project |
| `caption` | when kept | one line saying what the picture shows — what `/cards` turns into the answer text |
| `why` | when `none` | one line saying why not — so a re-run does not re-litigate it |

**Why a vocabulary and not a boolean.** `show: yes` parses as `True` under
YAML 1.1 and `show: "no"` does not, which is a trap this project would step in
exactly once. A closed vocabulary follows the precedent `content: sparse`
already set, and the kind is not dead weight: `/cards` phrases a prompt about a
`chart` differently from one about a `map`.

**State**: a picture is *unconsidered* (no entry), *kept* or *rejected*. There
is no fourth state and no transition back — a verdict is rewritten only when the
user edits the line or asks for a re-ingest (FR-014).

---

## 3. The inline marker — where the figure sat

**Lives in** the body of the knowledge document, at the position the picture
occupied in the original (FR-011):

```markdown
The tide runs semidiurnal through the Deep, with the second high the weaker.

![Figure: Semidiurnal tide curve for the Kestrel Deep](figures/handbook/tide-curve.png)

Slack water follows roughly two hours after the turn.
```

Ordinary markdown, so nothing new parses it. `/cards` reads the picture in the
paragraphs that explain it rather than as a loose file, and
`check_project.py` can assert the obvious invariant: **every kept figure's
`path` appears in the body**. A figure named in the frontmatter and absent from
the text is half an edit, which is the failure this format invites.

---

## 4. Figure card — a card with a picture on a face

**Lives in** `cards/<topic-slug>.yaml`, as two optional keys on a card:

```yaml
- id: F3M2Q
  subtopic: 'Tide charts'
  front: 'Describe the shape of the Kestrel Deep tide curve'
  back: 'Two highs and two lows a day, the second high the weaker one.'
  back_image: 'figures/island-images/tide-chart.png'
  source: 'Tide chart, harbour office'
```

| Field | Required | Rule |
|---|---|---|
| `front_image` | no | project-relative path; the picture printed under the prompt |
| `back_image` | no | project-relative path; the picture printed above the source line |

Both optional, both independent — a card may carry neither, either or both.
Every other rule is unchanged: same id alphabet, same uniqueness, same topic
file, same text budget on the face that also holds the picture.

**Invariants** (`check_project.py`, and `build_pdf.load_cards` where the build
must not proceed):

1. A path resolves against the project root — the parent of the directory
   holding the card file ([R5](./research.md#r5--what-resolves-a-picture-path-given-a-card-file-can-live-anywhere)).
2. It exists, is inside the project, and its extension is in the accepted set.
3. The face carrying a picture carries non-empty text too (FR-023).
4. At most one card per figure uses it as `back_image`, and at most one as
   `front_image` (FR-022).

**Not on a card**: the caption. It is the `back` text, written once by `/cards`
from the figure's `caption`, because a card that printed both would say the same
thing twice on 74 mm of paper.

---

## What the build sees

`payload()` gains two keys per card, holding the **staged** file name inside
the compile workdir rather than the project path — `fig-<sha256[:12]>.<ext>`,
or `""` for a face without a picture ([R2](./research.md#r2--how-does-the-engine-reach-a-picture-given-the-build-compiles-in-a-temp-workdir)).
Empty string rather than a missing key, for the same reason `id` is: the
template reads the field unconditionally.

`templates/card.typ` therefore never sees a project path, never resolves
anything, and cannot escape its sandbox. Everything about *where a picture came
from* is settled in Python before the engine starts.
