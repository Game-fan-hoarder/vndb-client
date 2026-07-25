# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```
<!-- END BEADS INTEGRATION -->

<!-- Project-specific beads rules. Deliberately OUTSIDE the BEADS INTEGRATION
     markers above: `bd setup claude` owns everything between those markers and
     may rewrite it wholesale, which would silently drop these rules. -->

## Beads Rules (project)

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Create beads tasks AFTER `/opsx:propose` produces the delta spec — never before; tasks must mirror the spec's `tasks.md`
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember "insight"` for ALL persistent knowledge — search with `bd memories <keyword>`
- Do NOT use the auto-memory file system (the `~/.claude-personal/.../memory/` directory) — ignore it entirely
- **Issue ID prefix** must match the project `name` in `pyproject.toml` (`vndb-client`).

## Session Completion

1. **File issues for remaining work** — create issues for anything needing follow-up
2. **Update issue status** — close finished work, update in-progress items
3. **Push beads** — `bd dolt push` before finishing the branch

> Git push is handled by `/superpowers:finishing-a-development-branch` (Workflow 2, step 10).

## Output calibration

Keep responses focused and concise. Spend most of the response on the main answer; keep caveats and disclaimers short. When asked to explain something, give a high-level summary unless depth is specifically requested.

Match the length of written documents — design docs, delta specs, reports, ledgers — to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate.

Before the first tool call, say in one sentence what you're about to do. While working, give a brief update only on finding something important or changing direction. When finishing, lead with the outcome.

## Superpowers overrides (Opus 5)

Superpowers 6.2.0 predates Opus 5 and its verification scaffolding now causes over-verification. These overrides take precedence over the skills' own text. Cross-project migration notes: `~/.claude/opus-5-workflow-migration.md`.

- **Do not invoke `superpowers:verification-before-completion`.** Verify your own work directly and once — run `make check` / `make test`, read the output, report what it said. The skill's "Iron Law" and rationalization tables are scaffolding for models that skipped verification.
- **`superpowers:subagent-driven-development`: skip the per-task reviewer subagent and the per-task fix loop.** Keep the ledger (it survives compaction) and keep the single whole-branch review at Workflow 2 step 9. Never dispatch a subagent to check work you just did yourself.
- **Do not invoke `superpowers:writing-plans`** — the delta spec's `tasks.md` is the plan.
- **`superpowers:brainstorming`: its HARD-GATE does not apply to every change.** Use the workflow tier that fits the work. A config change or docs fix does not need a design document.
- **`superpowers:using-superpowers`: the "1% chance a skill might apply" rule is advisory.** Invoke a skill when it earns its keep; a skill check is not required before answering a question.
- Ignore the skills' red-flag and rationalization tables. Positive descriptions of the wanted behavior work better than lists of what not to do.

## Development Workflows

### Workflow 1: Product Vision (Initial Design)

Use when starting a new product or defining major scope.

1. **Brainstorm vision** — `/superpowers:brainstorming`; Claude asks "what does done look like?", surfaces constraints and goals
2. **Define feature map** — second brainstorm refines into feature areas (MVP / Beta / V1) with dependency map
3. **Save brainstorm docs** to `docs/`:
   - Vision doc: `YYYY-MM-DD_<major_scope>.md`
   - Feature map: `YYYY-MM-DD_<major_scope>_feature_map.md`
4. **Create Beads epics** — one epic per feature area, with description and sub-epic for each major feature.

> **STOP.** Workflow 1 ends here. Do NOT start Workflow 2 unless explicitly asked to work on a feature.

### Workflow 2: Feature Implementation

Use for each individual feature once the epic exists.

1. **Brainstorm** — `/superpowers:brainstorming` to surface unknowns; produces a design document saved to `docs/YYYY-MM-DD_<feature_name>_design.md`

   > **Transition after brainstorm:** The next step is ALWAYS `/opsx:propose` — prompt the user to run it. Never suggest `writing-plans` here. The brainstorming skill's terminal state says otherwise but it is WRONG for this project.

2. **Propose change spec** — `/opsx:propose` using the design doc + memory → delta spec created in `openspec/changes/`

   > **Transition after propose:** The `opsx:propose` skill ends with "Run `/opsx:apply` to start implementing" — this is WRONG for this project. The next step is ALWAYS step 3 (Verify delta). Do NOT run `/opsx:apply` directly.

3. **Verify delta** — make sure that the delta spec has no delta with the initial design
4. **Isolate workspace** — `/superpowers:using-git-worktrees`
5. **Create Beads issues** — one task per `tasks.md` entry, following beads conventions, linked to the parent epic

   > **Pre-implementation gate** — beads issues MUST be created before starting implementation. Do NOT proceed to step 6 until issues exist.

6. **Implement** — the delta spec's `tasks.md` is the plan; there is no separate plan file. Default to implementing directly. Dispatch `subagent_type: implementer` (sonnet) per task only where tasks are genuinely independent and each is a well-specified 1–2 file change. No per-task reviewer subagent.
   > **Post-subtask gate** validate the corresponding checkbox in the delta spec

7. **Verify** — `/opsx:verify`
8. **Archive spec** — `/opsx:archive`
9. **Code review** — `/code-review` before merging. This is the single review gate; run it on opus.
10. **Finish branch** — `/superpowers:finishing-a-development-branch` (handles git push for feature branches; satisfies the beads Session Completion protocol)

### Workflow 3: Explicit bugfix implementation

Use for targeted bugfixes where a spec is overkill but the change is non-trivial.

1. **Debug** — `/superpowers:systematic-debugging` to investigate root cause and scope
2. **Create Beads issue** — `bd create --type=bug` with reproduction steps and expected behavior
3. **Isolate workspace** — `/superpowers:using-git-worktrees`
4. **Implement** — direct edit, with a regression test that fails before the fix
5. **Verify** — run tests; confirm bug is gone and no regressions
6. **Code review** — `/code-review` before merging
7. **Finish branch** — `/superpowers:finishing-a-development-branch`

> **STOP.** Do NOT use `/opsx:propose` for bugfixes — a delta spec is not required here.

### Workflow 4: Other workflow

Use for small tasks that don't warrant a feature workflow or bugfix investigation (docs, config, dependency bumps, refactors).

1. **Create Beads issue** — `bd create --type=task` describing the change
2. **Implement** — directly, no worktree needed unless risky
3. **Code review** — `/code-review` before merging, for anything touching `src/`. Skip it for docs, config, and dependency bumps that `make check` already gates.
4. **Finish branch** — `/superpowers:finishing-a-development-branch` if on a branch, or commit directly to main for trivial changes


## Build & Test

This project uses **uv** for environment/dependency management. All tooling runs through `uv run`. A `Makefile` wraps the common workflows:

```bash
make install      # uv sync + install pre-commit hooks
make check        # lock-file check, pre-commit (ruff), mypy, deptry — run before committing
make test         # pytest with coverage (writes coverage.xml)
make build        # build wheel via hatchling
make docs         # build + serve mkdocs site locally
make docs-test    # build docs in strict mode (fails on warnings)
```

Direct commands when you need finer control:

```bash
uv run python -m pytest                          # full test suite
uv run python -m pytest tests/test_foo.py        # single test file
uv run python -m pytest tests/test_foo.py::test_foo   # single test
uv run python -m pytest --doctest-modules tests  # also run doctests (as CI/tox does)
uv run mypy                                       # type-check src/ (config in pyproject.toml)
uv run deptry src                                 # detect unused/missing dependencies
uv run ruff check / uv run ruff format            # lint / format manually
uv run pre-commit run -a                          # run all hooks against all files
tox                                               # run the suite across Python 3.10–3.14
```

## Architecture & Conventions

- **Layout:** `src/` layout. The package is `src/vndb_client/` (the wheel target). Tests live in `tests/`. Docs are MkDocs Material sources under `docs/` with API pages auto-generated via `mkdocstrings`.
- **Target Python:** 3.10–3.14. Code must remain compatible across all of these (enforced by `tox`).
- **Typing is strict:** mypy runs with `disallow_untyped_defs`, `disallow_any_unimported`, `no_implicit_optional`, and `warn_return_any`. All functions need full type annotations.
- **Lint/format via Ruff:** line length 120, `target-version = py310`, `fix = true`. An extensive lint rule set is enabled (bandit `S`, bugbear `B`, comprehensions, simplify, isort, pyupgrade, tryceratops, etc.). `tests/*` is exempt from `S101` (asserts allowed). Format uses `preview = true`.
- **Docstrings:** Google-style (see `foo.py`); they feed the generated documentation, so keep them accurate for public APIs.
- **Pre-commit** enforces ruff check/format plus file hygiene (trailing whitespace, EOF, TOML/YAML/JSON validity). `ruff-check` runs with `--exit-non-zero-on-fix`, so commits fail if files needed auto-fixing — re-stage and retry.
- **OpenSpec** is configured (`openspec/`, `.claude/commands/opsx/`) for spec-driven change workflows. Use the `opsx:*` skills/commands when proposing and implementing structured changes.

## CI/CD

GitHub Actions (`.github/workflows/main.yml`) runs the quality gates (`make check`) and the test matrix across Python versions on PRs and pushes to `main`. Coverage is uploaded to Codecov. Releases are tag-driven (`*.*.*`) and publish to PyPI via `on-release-main.yml`.
