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
Please note this documentation assumes you already have `uv` and `Git` installed and ready to go.

1. Fork the `vndb-client` repo on GitHub.

2. Clone your fork locally:

```bash
cd <directory_in_which_repo_should_be_created>
git clone git@github.com:YOUR_NAME/vndb-client.git
```

3. Now we need to install the environment. Navigate into the directory

```bash
cd vndb-client
```

Then, install and activate the environment with:

```bash
uv sync
```

4. Install the commit-time linters/formatters. `make install` does this for you; the two
   commands below are what it runs, and which one applies depends on whether you use the
   [beads](https://github.com/steveyegge/beads) issue tracker.

   **Without beads** — the normal case for outside contributors. Install the git hook:

```bash
uv run pre-commit install
```

**With beads** — `bd` points `core.hooksPath` at `.beads/hooks`, and `pre-commit install`
refuses to run while that is set (it exits 1 with *"Cowardly refusing to install hooks with
`core.hooksPath` set"*). Nothing is broken: the commit gate is already committed to
`.beads/hooks/pre-commit`, so there is no hook to install and it works in every clone. You only
need the hook environments pre-built:

```bash
uv run pre-commit install-hooks
```

Verify either way — the first command shows which mode you are in, the second proves the hooks
work:

```bash
git config core.hooksPath          # empty = no beads; .beads/hooks = beads mode
uv run pre-commit run --all-files
```

Note that `pre-commit run --all-files` is a one-off lint pass over the whole tree, not a setup
step. It builds the environments as a side effect, which is why it is a useful check here.

5. Create a branch for local development:

```bash
git checkout -b name-of-your-bugfix-or-feature
```

Now you can make your changes locally.

6. Don't forget to add test cases for your added functionality to the `tests` directory.

7. When you're done making changes, check that your changes pass the formatting tests.

```bash
make check
```

Now, validate that all unit tests are passing:

```bash
make test
```

9. Before raising a pull request you should also run tox.
   This will run the tests across different versions of Python:

```bash
tox
```

This requires you to have multiple versions of python installed.
This step is also triggered in the CI/CD pipeline, so you could also choose to skip this step locally.

10. Commit your changes and push your branch to GitHub:

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

11. Submit a pull request through the GitHub website.

# Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated.
   Put your new functionality into a function with a docstring, and add the feature to the list in `README.md`.
