"""`lernkarten setup` — the one place the Leitner questions are asked.

    lernkarten setup --project .
    lernkarten setup --project . --compartments 4 --dividers-printed no --box-printed no

A build never asks. It reads what this wrote, and when nothing has been written
it says once that this command exists. Keeping the asking in one place is what
lets the answers be tested: the flag form above is reachable from pytest, and
the prompting form needs a terminal, which pytest has not got.

Why `--project` rather than the working directory alone: the build resolves the
settings file from the *card files*, so writing it somewhere else would produce
a file nothing reads. The flag makes the two agree; its default is the cwd,
which is right when you are standing in your project.
"""

import argparse
import sys
from pathlib import Path

import leitner
import settings

QUESTIONS = "how many compartments, and whether the dividers and the box are printed"


def _ask(prompt, answers):
    while True:
        given = input(f"{prompt} ").strip().lower()
        if given in answers:
            return answers[given]
        print(f"  please answer one of: {', '.join(sorted(set(answers)))}", file=sys.stderr)


def main(argv=None):
    counts = [str(n) for n in leitner.COMPARTMENT_COUNTS]
    p = argparse.ArgumentParser(
        prog="lernkarten setup",
        description="Answer once what lernkarten should not ask you twice.",
    )
    p.add_argument(
        "--project",
        default=".",
        metavar="DIR",
        help="the project root, the folder your cards/ directory sits in (default: .)",
    )
    p.add_argument("--compartments", choices=[*counts, settings.DECLINED])
    p.add_argument("--dividers-printed", choices=["yes", "no"])
    p.add_argument("--box-printed", choices=["yes", "no"])
    p.add_argument(
        "--sides",
        choices=settings.SIDES,
        help="how your printer wants the pages sequenced. This one is about the *machine*, "
        f"so it is written to {settings.machine_path()} and applies to every project",
    )
    args = p.parse_args(sys.argv[1:] if argv is None else argv)

    root = Path(args.project).resolve()
    if not root.is_dir():
        p.error(f"--project {args.project}: not a directory")

    # The machine answer is routed by its key, not by a flag the user has to
    # pick. Nobody should have to know which of two files a setting lives in.
    if args.sides is not None:
        warning = settings.save_machine(sides=args.sides)
        if warning:
            print(f"NOTE: {warning}", file=sys.stderr)
        else:
            print(f"wrote {settings.machine_path()}")
        if all(g is None for g in (args.compartments, args.dividers_printed, args.box_printed)):
            return 0

    given = (args.compartments, args.dividers_printed, args.box_printed)
    if any(g is None for g in given):
        # Refuse rather than guess. A pipe is not a terminal: there is nobody
        # on the other end to answer, and a guessed answer is worse than none
        # because nothing will ever ask again.
        if not sys.stdin.isatty():
            p.error(
                "nothing to ask on — this is not a terminal. Pass the answers instead:\n"
                f"  lernkarten setup --project {args.project} "
                f"--compartments {'|'.join([*counts, settings.DECLINED])} "
                "--dividers-printed yes|no --box-printed yes|no"
            )
        compartments = args.compartments or _ask(
            f"How many Leitner compartments? [{'/'.join([*counts, settings.DECLINED])}]",
            {v: v for v in [*counts, settings.DECLINED]},
        )
        yes_no = {"y": True, "yes": True, "n": False, "no": False, "": False}
        dividers = (
            yes_no[args.dividers_printed]
            if args.dividers_printed
            else _ask("Are the dividers already printed? [y/N]", yes_no)
        )
        box = (
            yes_no[args.box_printed]
            if args.box_printed
            else _ask("Is the card box already printed? [y/N]", yes_no)
        )
    else:
        compartments = args.compartments
        dividers = args.dividers_printed == "yes"
        box = args.box_printed == "yes"

    settings.save(
        root,
        compartments=None if compartments == settings.DECLINED else int(compartments),
        dividers_printed=dividers,
        box_printed=box,
    )
    print(f"wrote {root / settings.FILENAME}")
    return 0
