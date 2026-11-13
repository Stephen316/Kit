# Example corpus relocation into `re/`

## Change

The change removes the root `examples/` directory.
Each sample file moves into the `re/` directory for its CAD vendor.
Git records every file as a 100% rename, so the bytes do not change.

| Previous path                                              | New path                                                                 |
| ---------------------------------------------------------- | ------------------------------------------------------------------------ |
| `examples/.SLDPRT/`                                        | `re/solidworks/examples/.SLDPRT/`                                        |
| `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/` | `re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/` |
| `examples/Fixtures/SolidWorks/donors/`                     | `re/solidworks/Fixtures/donors/`                                         |
| `examples/Random/` (gitignored, local only)                | `re/solidworks/examples/Random/` (gitignored, local only)                |
| `examples/.f3d/`, `examples/.f3z/`                         | `re/Fusion/examples/.f3d/`, `re/Fusion/examples/.f3z/`                   |
| `examples/.CATPart/`, `examples/.CATProduct/`              | `re/catia/examples/.CATPart/`, `re/catia/examples/.CATProduct/`          |

## Usage

Tests, research tools and research notes use the new paths.
Put a local `Random/` corpus in `re/solidworks/examples/Random/`.

## Limits

`.CATPart` and `.CATProduct` stay sibling directories.
The CATIA reader looks for linked parts in the sibling `.CATPart` directory.

`re/` is export-ignored.
The donor fixtures stay out of source archives and release builds.
The separate donor export-ignore rule is therefore removed.

Recorded Windows trace paths in `re/data/` keep their original `examples\` values.
`SolidworksArchiveTests` maps those paths to `re/solidworks/examples/`.

Security-scan exclusions for `examples/` are not changed.
History scans still read commits that contain the old directory.

## Recorded verification

Git reports 321 renames with 100% similarity and no other changes to the moved files.
Black 26.10.1 and Ruff 0.17.3 pass on the changed Python files.
No local tests ran.
Remote CI and merge-group acceptance must supply their own results.

See [the research workspace layout](../../re/README.md#layout).
