# Repository guard coverage

## Change

[The CodeQL repair](DiffBreakdownCodeql.md) replaced the `GITHUB_REPOSITORY` regular expression with a character-set check.
That change did not add test coverage for the new check.

`TestRepoGuard` in [DiffBreakdownTests.py](../../tests/Policy/DiffBreakdownTests.py) runs the engine as a subprocess with each identity.
The engine must reject these values with `Invalid repository identity`:

| Value                 | Reason                    |
| --------------------- | ------------------------- |
| `TryUniCAD/Kit/Extra` | More than one separator   |
| `TryUniCAD/`          | Empty name                |
| `/Kit`                | Empty owner               |
| `Try UniCAD/Kit`      | Space in the owner        |
| `TryUniCAD/Kït`       | Non-ASCII letter          |

The engine must accept `Try-UniCAD/Kit.io_2`, which uses each permitted punctuation character.
`RunEngine` takes an optional repository value. The default stays `TryUniCAD/Kit`.

## Limits

The test covers the identity guard only.
It does not run CodeQL, which runs only on merge-group candidates.
The [diff breakdown guide](../Reference/Operations/DiffBreakdown.md) lists the test scope.

## Verification

Black, Ruff, and repository-wide steering passed locally.
The test was not run locally under the repository test policy.
PR CI runs the module.
