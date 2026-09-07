# Contributing to SciTeX App

Thank you for your interest in contributing to SciTeX. This guide covers the
process for reporting issues, suggesting features, and submitting code.

## Contributor License Agreement

Before your first contribution can be merged, you must agree to the
[SciTeX CLA](CLA.md). This is a one-time process. The CLA ensures that:

- You retain copyright of your work.
- The project can continue to offer dual licensing (free for researchers,
  commercial for enterprises).

See [CLA.md](CLA.md) for full details.

## Reporting Issues

- Search [existing issues](https://github.com/ywatanabe1989/scitex-app/issues)
  before opening a new one.
- Include a minimal reproducible example when reporting bugs.
- Specify your Python version, OS, and `scitex-app` version.

## Development Setup

```bash
git clone git@github.com:ywatanabe1989/scitex-app.git
cd scitex-app
python -m pip install --upgrade pip   # --group needs pip >= 25.1
pip install -e ".[all]" --group dev
```

`dev` and `docs` are [PEP 735](https://peps.python.org/pep-0735/) dependency
groups, not extras, so they are requested with `--group` and are *not*
installable as `.[dev]`. That is deliberate: they build the package rather than
use it, so they must stay out of `pip install scitex-app[all]`, which is the
user-facing install. Use `--group docs` to build the documentation.

## Branch Workflow

- `main` — stable releases only. Do not push directly.
- `develop` — integration branch. PRs target here.
- Feature branches — create from `develop`, name as `feature/<description>`.

```bash
git checkout develop
git checkout -b feature/my-change
# ... make changes ...
git push origin feature/my-change
# Open PR targeting develop
```

## Cutting a Release

Pushing the version tag is what triggers publish + GitHub Release. **Push that
tag from a linked worktree, not from the main checkout**, using literal paths:

```
git -C /path/to/repo/.worktrees/SOMETREE tag -a vX.Y.Z SHA -m "..."
git -C /path/to/repo/.worktrees/SOMETREE push origin vX.Y.Z
```

Why this is written down rather than left to be rediscovered: the main checkout
sits on `develop`, and the pre-push guard correctly refuses tag pushes from it.
The tempting way around that is `gh release create` — but that **also creates
the tag**, so the workflow then tries to create a Release that already exists
and the `release` job goes red. Measured both directions, same workflow, one
variable changed:

    tag made by the GitHub API         release job FAILED
    tag pushed from a linked worktree  release job SUCCESS

So the workflow step is not at fault and does not need to be made idempotent —
the API route is simply the wrong path. Let the tag push trigger the workflow,
and let the workflow create its own Release.

Two traps worth knowing, both hit more than once:

- **Never put a shell variable in the `-C` argument.** The guard inspects the
  real argv and does not run your shell, so an unexpanded variable arrives
  literally, resolves to nothing, and is refused. Spell the path out.
- **The guard fails closed on any `-C` path it cannot resolve**, including
  placeholder text. That is deliberate and correct; it just means example
  commands need real-looking paths.

## Code Style

- Follow existing conventions in the codebase.
- Use `_` prefix for internal/private modules and functions.
- Keep files under 512 lines.
- Run tests before submitting:

```bash
pytest tests/ -x -q
```

## Pull Request Process

1. Ensure your branch is up to date with `develop`.
2. Write tests for new functionality.
3. Run the test suite and confirm all tests pass.
4. Open a PR targeting `develop` with a clear description.
5. The CLA bot will check your CLA status on your first PR.

## License

By contributing, you agree to the terms of the [CLA](CLA.md), which includes
licensing under AGPL-3.0 (see [LICENSE](LICENSE)) and the dual-licensing
provisions described therein.
