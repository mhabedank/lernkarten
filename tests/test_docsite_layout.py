"""Guards the documentation site's boundaries — what it may cost and where it may live.

The documentation toolchain is the largest dependency this repository has ever
taken, and it is taken on the condition that nobody who is not building
documentation ever pays for it. That condition is not self-enforcing: a single
`import sphinx` in a module a user's run reaches would put its whole transitive
tree in front of somebody who only wanted to print flashcards, and nothing about
the build would look different. (The size of that tree is measured in
`specs/013-skill-reference/research.md` and deliberately not repeated here — a
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


def test_the_build_directory_is_ignored():
    """Generated output is never committed, and neither tree is generated yet.

    `docsite/_build/` is Sphinx's own output and `_site/` is the assembled
    site — the same bytes the deploy uploads. Both are derived from sources
    that *are* versioned, so committing either would put a second copy of the
    documentation in the repository that nothing keeps in step.
    """
    from test_repo_hygiene import ignored

    candidates = ["docsite/_build/index.html", "_site/index.html"]
    missing = sorted(set(candidates) - ignored(candidates))
    assert not missing, (
        f".gitignore does not keep {missing} out. Both are build output: the first is "
        "Sphinx's, the second is the assembled site, and either one committed is a "
        "second copy of the documentation that drifts from the sources it came from"
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


def test_the_docsite_holds_no_symlink_and_no_copy():
    """A guard: the site reaches its sources, it never holds them.

    Two arrangements were excluded by name, and both are the kind that get
    proposed as simplifications later. A symlink into `docsite/` needs
    developer mode on Windows, so it would work for whoever wrote it and fail
    for a contributor on another machine. A copy is worse and quieter: two
    editable files with the same content, one of which the four gates read and
    the other of which the site publishes, drifting apart the first time
    somebody edits the nearer one.

    The requirement says it is written "so that a later change does not
    simplify it into a move". That sentence had no gate until this one. Green
    from the first run — making it red would mean committing the arrangement
    the requirement forbids.
    """
    docsite = ROOT / "docsite"

    links = sorted(p.relative_to(ROOT).as_posix() for p in docsite.rglob("*") if p.is_symlink())
    assert not links, (
        f"these paths under docsite/ are symlinks: {links}. They need developer mode on "
        f"Windows, so the build works for whoever made them and fails for the next "
        f"contributor"
    )

    migrated = {
        path.read_bytes(): path.relative_to(ROOT).as_posix()
        for path in [*(ROOT / "docs").glob("*.md"), ROOT / "CONTRIBUTING.md"]
    }
    copies = {
        p.relative_to(ROOT).as_posix(): migrated[p.read_bytes()]
        for p in docsite.rglob("*.md")
        if p.read_bytes() in migrated
    }
    assert not copies, (
        f"these pages under docsite/ are byte-identical copies of a repository document: "
        f"{copies}. A page includes its source; it never holds it, or the gates and the "
        f"site read two files that start identical and stop being so"
    )


def test_the_ci_docs_job_runs_the_docs_tests():
    """CI must actually run the tests that only run with Sphinx installed.

    `tests/test_build_docs.py` skips when the documentation requirements are
    absent, which is deliberate — a contributor running the four gates should
    not need a docs toolchain. The consequence is that those assertions
    execute in exactly one place, and if that job only *builds* the site they
    execute nowhere at all while every job stays green.

    Scoped to the one job rather than matched against the file as text, and
    that matters: read as text, four of these five clauses are already true of
    `ci.yml` today. Two other jobs list all three runners, the `test` job runs
    pytest, and `requirements-dev.txt` is installed in four places — so an
    unscoped assertion is red on one clause and vacuous on the rest.
    """
    import yamlio

    workflow = yamlio.load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    def runs_the_build(job):
        return any("build_docs.py" in str(step.get("run", "")) for step in job.get("steps", []))

    matches = {name: job for name, job in jobs.items() if runs_the_build(job)}
    assert matches, (
        f"no job in ci.yml runs scripts/build_docs.py, so the documentation is never built "
        f"or tested in CI. The jobs are {sorted(jobs)}"
    )
    assert len(matches) == 1, f"more than one job builds the documentation: {sorted(matches)}"

    job_id, job = next(iter(matches.items()))

    assert job_id != "docs", (
        "the documentation job reuses the id `docs`, which already belongs to the "
        "'Skills & docs' job. Two jobs with one id is a YAML error found as a red run "
        "rather than at review"
    )

    runners = set(job.get("strategy", {}).get("matrix", {}).get("os", []))
    assert runners == {"ubuntu-latest", "macos-latest", "windows-latest"}, (
        f"the documentation job runs on {sorted(runners) or 'one implicit runner'}. The "
        f"build resolves paths and reads text files, and this is the only job that "
        f"exercises either on macOS or Windows"
    )

    steps = " ".join(str(step.get("run", "")) for step in job.get("steps", []))
    assert "requirements-docs.txt" in steps, (
        "the documentation job never installs requirements-docs.txt, so its build cannot "
        "run and its tests would skip"
    )
    assert "pytest" in steps, (
        "the documentation job builds the site but never runs pytest. tests/test_build_docs.py "
        "skips without Sphinx, and this is the only job that has it — so every assertion in "
        "that module would execute nowhere while CI stayed green"
    )


def test_the_extension_imports_nothing_from_lernkarten():
    """A guard: the build-time extensions know nothing about this project's code.

    Green from the first run. It is the enforcement rather than the intention
    behind a decision the specification made deliberately: the Sphinx
    extension that documents Agent Skills is being written here because its
    schema has one consumer and needs to survive contact with it, and it is
    meant to be extracted into a package of its own once it has.

    "Extract it later" is a promise that keeps itself only if nothing grows
    across the seam in the meantime. One `import yamlio` and the extraction
    becomes a refactor nobody schedules. So the seam is a test, and 013's
    skill extension inherits both the directory and the rule.
    """
    import ast

    ext = ROOT / "docsite" / "_ext"
    modules = sorted(ext.glob("*.py"))
    assert modules, "docsite/_ext/ holds no modules — this assertion has nothing to check"

    local = {p.stem for p in (ROOT / "scripts").glob("*.py")}
    offenders = {}
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
        if found := imported & local:
            offenders[path.name] = sorted(found)

    assert not offenders, (
        f"these extensions import lernkarten's own modules: {offenders}. The directory is "
        f"meant to leave this repository as a package once its schema has settled, and a "
        f"single import across that seam turns the extraction into a refactor"
    )
