# Ignore rules do not block tracked files

## Expectation

An ignore rule might appear to prevent a DLL or DMG from entering Git.

## Actual behavior

Git ignore rules apply to untracked files.
Previously tracked files remain tracked, and an ignored-file override can add a matching path.
Ignore rules alone do not enforce the vendor software restriction.
See [the Git ignore documentation](https://git-scm.com/docs/gitignore).

## Workaround

Use the repository-wide binary guard in the `Verify path policies` CI job.
It checks every tracked filename rather than relying on ignore rules.
Remove prohibited paths from the index and store authorized software outside repository checkouts.
See [the artifact policy](../../Reference/Research/ResearchArtifacts.md) and [the guard change](../../Changes/Git/VendorBinaryGuard.md).
