# Contract: the command-line surface

This project's external interface is the `lernkarten` command. Two flags are
added to `build` and one subcommand is added.

## `lernkarten build … [--dividers N] [--box]`

| Flag | Values | Default | Refuses when |
|---|---|---|---|
| `--dividers` | `3`, `4` | from `lernkarten.yaml`, else none | any other integer; `--grid` is not `a8` |
| `--box` | (no argument) | from `lernkarten.yaml`, else off | `--grid` is not `a8` |

**The grid refusal applies to flags only.** The same values coming from
`lernkarten.yaml` at a non-A8 grid skip with an advisory instead of failing
(FR-015a).

**Precedence**: an explicit flag always wins over `lernkarten.yaml`
(FR-015). `--dividers 4` renders dividers even when `dividers_printed: true`,
which is how a user replaces a lost one.

**Refusals** exit non-zero, write no PDF, and name the accepted value or the
required grid — never a bare traceback and never a silent fallback:

```
$ lernkarten build cards/*.yaml --dividers 5
error: --dividers takes 3 or 4, not 5

$ lernkarten build cards/*.yaml --grid a7 --dividers 4
error: --dividers needs --grid a8 (FR-009); see docs/design.md "The box"
```

## Output

| Path | When | Content |
|---|---|---|
| `output/cards.pdf` | always | cards, plus dividers when asked |
| `output/box.pdf` | `--box` | a byte-identical copy of `assets/card-box.pdf` |

The box is a **separate file, never merged**. Merging would require a PDF
library; copying requires `shutil.copyfile`. The separation also matches the
physical fact that drives it: the box wants 160–250 gsm and the cards do not.

## Advisory lines (stderr)

Advisories go to **stderr** (FR-012c), where every existing `NOTE`/`WARNING` in
`scripts/build_pdf.py:412-416, 599-603` already goes; only the closing summary
stays on stdout. Each is a normal pytest assertion, not a manual checklist item.

**Every advisory is prefixed `NOTE:`** — the prefix `advise_about_ids` already
uses at `build_pdf.py:413`. This is load-bearing rather than cosmetic: once the
unanswered-setup line exists, *every* e2e run over the demo project emits it, and
`tests/test_e2e.py:73` and `:723` assert `"WARNING" not in result.stderr`. A
`WARNING:` prefix would break two passing tests that have nothing to do with this
feature.

| Trigger | Line says |
|---|---|
| dividers fit an existing sheet | that they cost no extra paper |
| dividers add a sheet | that a sheet was added, and under `--sides simplex` that it is fed twice |
| `--box` | 160–250 gsm, and that it applies to the box alone |
| file-driven dividers at a non-A8 grid | that they were skipped, naming FR-009's constraint |
| settings absent or empty | once, that the Leitner setup is unanswered and `lernkarten setup` answers it |
| `compartments: none` | nothing — the user was asked and declined |
| unknown key in the file | a warning naming the file, the key and the known keys; the run continues (FR-016a) |

Advisories are **cumulative**: a run that adds a page, writes the box and skips
file-driven dividers at a non-A8 grid emits all three, each once, in a stable
order (FR-012b).

Counts are reported **separately**: `31 cards, 4 dividers`. A divider must never
inflate the existing `"<n> cards valid"` line, which `test_e2e.py` asserts and
which states what the user wrote (FR-012a).

## `lernkarten setup`

The single place the three questions are asked (FR-014b). Writes
`lernkarten.yaml`; asks nothing that the file already answers.

```
$ lernkarten setup --project .
How many Leitner compartments? [3/4/none]        4
Are the dividers already printed? [y/N]          n
Is the card box already printed? [y/N]           n
wrote lernkarten.yaml
```

**Without a terminal it refuses** rather than guessing — including a piped
stdin, which is not a terminal — and the error names the three flags that set
the same values non-interactively:

```
lernkarten setup --compartments 3|4|none --dividers-printed yes|no --box-printed yes|no
```

Those flags are the only pytest-reachable path, so they are the ones the tests
use. The prompting path is a manual checklist item.

**Write-back** (FR-020): a successful **build** that renders dividers sets
`dividers_printed: true`, and one that writes the box sets `box_printed: true`.
Three limits: it writes only into a file that **already exists** and whose
`compartments` is 3 or 4; it **never creates** one; and it **never fires on
`lernkarten check`**, which test-typesets the dividers without anything being
printed — and which `/print` runs before every build.

**Lookup root**: `lernkarten.yaml` is read from the project root derived from the
card files, not from the current working directory (FR-021). A build never asks; it only
reports that setup is unanswered.
