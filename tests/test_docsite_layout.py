"""Guards the documentation site's boundaries — what it may cost and where it may live.

The documentation toolchain is the largest dependency this repository has ever
taken, and it is taken on the condition that nobody who is not building
documentation ever pays for it. That condition is not self-enforcing: a single
`import sphinx` in a module a user's run reaches would put its whole transitive
tree in front of somebody who only wanted to print flashcards, and nothing about
the build would look different. (The size of that tree is measured in
`specs/012-skill-reference/research.md` and deliberately not repeated here — a
count restated in a second place is a count that drifts.)

So the assertions here are about the *seams* rather than about the site:
the manifest is pinned, the manifest stays off the runtime path, the build
output stays out of the repository, and the sources stay where the four gates
can still see them.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

DOCS_REQUIREMENTS = ROOT / "requirements-docs.txt"

# The three the site is built from. Named here rather than derived from the
# file, so that dropping one from the manifest is a failure rather than a
# smaller assertion.
DOCS_PACKAGES = ("sphinx", "myst-parser", "pydata-sphinx-theme")


def requirement_lines():
    """The manifest's requirement lines, comments and blanks removed."""
    text = DOCS_REQUIREMENTS.read_text(encoding="utf-8")
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_the_docs_requirements_are_pinned_exactly():
    """Sphinx is a tool here, not a library, so it is pinned like one.

    Its output is compared byte-for-byte between two runs and its warning set
    is a gate, so a patch release drifting under a contributor is exactly the
    failure the exact-pin rule exists to prevent — the same reasoning that
    pins ruff. A range would make the build's own definition of "correct"
    move on its own.
    """
    assert DOCS_REQUIREMENTS.exists(), (
        "requirements-docs.txt does not exist — the docs toolchain has no manifest, "
        "and without one it would land in requirements-dev.txt on every contributor "
        "who only wants to run the four gates"
    )

    lines = requirement_lines()
    named = {re.split(r"[=<>!~\[]", line, maxsplit=1)[0].strip().lower() for line in lines}
    for package in DOCS_PACKAGES:
        assert package in named, (
            f"requirements-docs.txt does not name {package!r} — the site cannot be built "
            f"from this manifest. It names {sorted(named)}"
        )

    for line in lines:
        assert "==" in line, (
            f"requirements-docs.txt pins {line!r} loosely. Sphinx is a tool here: its "
            "warning set is a gate and its output is compared byte-for-byte, so a patch "
            "release arriving on its own changes what 'the build passes' means"
        )

    text = DOCS_REQUIREMENTS.read_text(encoding="utf-8")
    comments = [line for line in text.splitlines() if line.lstrip().startswith("#")]
    assert len(comments) >= len(DOCS_PACKAGES), (
        f"requirements-docs.txt carries {len(comments)} comment lines for "
        f"{len(DOCS_PACKAGES)} packages. Each one says what it is for, because a "
        "manifest of three names is a manifest nobody can review"
    )


def docs_import_names():
    """The manifest's packages as they are spelled in an `import` statement."""
    names = set()
    for line in requirement_lines():
        distribution = re.split(r"[=<>!~\[]", line, maxsplit=1)[0].strip().lower()
        names.add(distribution.replace("-", "_"))
    return names


def runtime_closure():
    """Every local module a user's run can reach, starting at `bin/lernkarten`.

    Derived, never listed. `check_docs.real_graph()` already reads each
    `scripts/*.py` module's local imports out of the source, so the closure is
    a walk over that graph from the command's own imports — which means a new
    module is inside it exactly when something reachable imports it, and
    outside it otherwise, with nobody maintaining a list.
    """
    import check_docs

    graph = check_docs.real_graph()
    entry = ROOT / "bin" / "lernkarten"
    reachable = set()
    frontier = {
        match.group(1)
        for line in entry.read_text(encoding="utf-8").splitlines()
        if (match := re.match(r"\s*(?:import|from) ([a-z_]+)", line)) and match.group(1) in graph
    }
    while frontier:
        module = frontier.pop()
        if module in reachable:
            continue
        reachable.add(module)
        frontier |= graph.get(module, set())
    return reachable


def test_the_docs_requirements_are_not_a_runtime_dependency():
    """A guard, green from the start — see the note on scope below.

    Nothing here was ever red and nothing could be without adding the defect
    on purpose, the shape `test_the_page_stays_one_self_contained_file` in
    `tests/test_landing_page.py` already documents. It defends a property that
    is easy to lose later: a documentation package must never end up in front
    of somebody who is printing flashcards.

    **Scoped to the import closure of `bin/lernkarten`, never to `scripts/` as
    a directory.** `scripts/build_docs.py` imports Sphinx on purpose, so a
    directory-wide rule would go red the moment that file lands, and the cheap
    repair — excluding it by name — is a guard that no longer guards. The
    closure is the thing the requirement actually names: "any script a user's
    run reaches". A leaf nothing imports falls outside it by construction, and
    so does the next documentation script, without this test being touched.
    """
    import deps

    docs_names = docs_import_names()

    pinned = {req.split("==")[0].strip().lower().replace("-", "_") for req, _ in deps.REQUIREMENTS}
    collision = docs_names & pinned
    assert not collision, (
        f"{sorted(collision)} is both a documentation requirement and a runtime one in "
        "scripts/deps.py REQUIREMENTS. Every `lernkarten` command installs that list, so "
        "a user printing cards would install a documentation toolchain"
    )

    closure = runtime_closure()
    offenders = {}
    for module in sorted(closure):
        source = (ROOT / "scripts" / f"{module}.py").read_text(encoding="utf-8")
        found = {
            name
            for name in docs_names
            if re.search(rf"^\s*(?:import|from) {re.escape(name)}\b", source, re.MULTILINE)
        }
        if found:
            offenders[module] = sorted(found)
    assert not offenders, (
        f"these modules are reachable from `bin/lernkarten` and import a documentation "
        f"package: {offenders}. The closure is {sorted(closure)} — anything in it runs "
        "for a user who is only building cards"
    )
