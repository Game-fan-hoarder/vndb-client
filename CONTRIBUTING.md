# Contributing to `vndb-client`

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

You can contribute in many ways:

# Types of Contributions

## Report Bugs

Report bugs at https://github.com/Game-fan-hoarder/vndb-client/issues

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

## Fix Bugs

Look through the GitHub issues for bugs.
Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

## Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

## Write Documentation

vndb-client could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

## Submit Feedback

The best way to send feedback is to file an issue at https://github.com/Game-fan-hoarder/vndb-client/issues.

If you are proposing a new feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

# Get Started!

Ready to contribute? Here's how to set up `vndb-client` for local development.
This assumes you already have `git` and [`uv`](https://docs.astral.sh/uv/) installed. The project
targets Python 3.10–3.14; `uv` will fetch a suitable interpreter for you.

1. Fork the `vndb-client` repo on GitHub, then clone your fork:

```bash
git clone git@github.com:YOUR_NAME/vndb-client.git
cd vndb-client
```

2. Set up the environment and the commit-time linters:

```bash
make install
```

That runs `uv sync` and prepares the `pre-commit` hooks. There is no virtualenv to activate —
every command below goes through `uv run`, which resolves the project environment for you.

3. Create a branch for your work:

```bash
git checkout -b name-of-your-bugfix-or-feature
```

4. Make your changes, and add test cases for new functionality under `tests/`.

5. Run the quality gates:

```bash
make check   # lock file, ruff lint + format, mypy, deptry
make test    # pytest with coverage
```

6. Optionally run the suite across every supported Python version. This needs those versions
   installed locally, and CI runs it anyway, so it is fine to skip:

```bash
tox
```

7. Commit and push. Stage files explicitly rather than with `git add .`, so build artefacts and
   local scratch files don't end up in the PR:

```bash
git add <the files you changed>
git commit -m "A detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

Commits are lint-gated. If a hook reformats a file, the commit is rejected on purpose — re-stage
the now-fixed file and commit again.

8. Open a pull request through the GitHub website.

## Troubleshooting setup

**`pre-commit install` fails with "Cowardly refusing to install hooks with `core.hooksPath` set".**
Something else owns your git hooks — in this repo that is the maintainers' issue tracker, which
points `core.hooksPath` at `.beads/hooks`. You do not need to fix it: the lint gate is committed
to that directory and already active. Run `uv run pre-commit install-hooks` to pre-build the hook
environments instead. `git config core.hooksPath` tells you which mode you are in.

**The hooks never seem to run.** Confirm with a deliberate violation rather than by inspecting
config: make a badly formatted change, try to commit it, and check the commit is refused.

# Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated.
   Put your new functionality into a function with a docstring, and add the feature to the list in `README.md`.

3. `make check` and `make test` should pass. CI runs the same gates across all supported Python
   versions.
