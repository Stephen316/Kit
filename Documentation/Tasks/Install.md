<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Install the repository environment

## Purpose

Prepare an isolated Kit checkout for Python integration work.
This procedure uses the repository lockfile.
It does not install a CAD application or run tests.

## Before you start

- Install Git and `uv`.
- Obtain read access to the [Kit repository](https://github.com/TryUniCAD/Kit).
- Select an unused checkout directory.
- Provide network access for the locked dependencies.
- Read [the contribution workflow](../Reference/Overview/Contributing.md) before making changes.

Kit requires Python 3.11 or later in its package metadata.
The example selects Python 3.11 for a reproducible starting environment.
The lockfile can contain development dependencies with additional platform requirements.

## Procedure

1. Clone the repository into an unused directory.

   ```sh
   git clone https://github.com/TryUniCAD/Kit.git Kit
   ```

2. Open the repository directory.

   ```sh
   cd Kit
   ```

3. Create an isolated worktree for the task.

   ```sh
   git worktree add ../KitIntegration -b docs/integration origin/main
   ```

4. Open the worktree.

   ```sh
   cd ../KitIntegration
   ```

5. Install the locked environment.

   ```sh
   uv sync --frozen --all-groups --all-extras --python 3.11
   ```

6. Record the source revision.

   ```sh
   git rev-parse HEAD
   ```

7. Start Python in the installed environment.

   ```sh
   uv run --frozen python
   ```

Expected result: Python starts with the installed checkout packages available.
The recorded revision identifies the installed source.
This result does not establish that tests passed.

Use this interpreter for the Python examples in these guides.
For a saved script, run `uv run --frozen python path/to/script.py` from this worktree.

## Package identity

The distribution name is `unicad-kit`.
The installed Python packages are `convert` and `interchange`.
Use `from convert import convert` for the public conversion function.
Do not infer an import name from the distribution name.

The `kit` entry-point group in package metadata is not a console command declaration.
This guide uses the Python API.
It does not claim that `kit convert` is an installed executable.

## If the task fails

| Symptom                          | Action                                     | Stop condition                                  |
| -------------------------------- | ------------------------------------------ | ----------------------------------------------- |
| Repository access fails          | Check the account and repository URL       | Do not use another repository as a substitute   |
| Worktree path already exists     | Select an unused directory                 | Do not delete another task's files              |
| Branch name already exists       | Select a distinct task branch              | Do not reset the existing branch                |
| Locked dependency cannot install | Record the dependency and platform error   | Do not silently regenerate the lockfile         |
| Python import cannot be found    | Start Python with `uv run --frozen python` | Do not install an unrelated package named `kit` |

## Remove the task environment

Keep the source files and outputs until the task owner no longer needs them.
Remove only the environment or worktree that belongs to this task.
Do not remove shared checkouts or CAD source files during cleanup.

## Related information

- [Package metadata](../../pyproject.toml)
- [Getting started](../GettingStarted.md)
- [Select a format](SelectFormat.md)
