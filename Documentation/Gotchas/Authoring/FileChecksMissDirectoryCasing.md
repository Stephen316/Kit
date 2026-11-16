# File checks can miss directory casing

## Expectation

A passing complete-tree path check might appear to prove that every internal directory uses PascalCase.

## Actual behavior

The original checker applied `PTH001` to file stems and `PTH002` to direct directory counts.
It did not inspect directory names.
Lowercase internal directories could pass both checks.
Its successful path count included paths without directory-casing evidence.

## Workaround

Use the checker with the [directory-name rule](../../../tools/Policy/CheckDirNames.py).
Stage intended path changes and run the complete tracked-tree scan.
PR CI now runs that scan before the changed-destination check.

Keep lowercase names only for the exact [public compatibility directories](../../../tools/Policy/CompatDirs.py).
Their descendants receive no naming exemption.
Update imports, workflow selections, package metadata, and source links when moving internal packages.
For a case-only rename on a case-insensitive filesystem, move through a temporary name before choosing the final path.

See [the change record](../../Changes/Policy/CodeDirectoryCasing.md) and [the contributor policy](../../Reference/Operations/Policy.md).
