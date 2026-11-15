# Vendor binary guard

## Behavior

Repository ignore rules exclude `.dll` and `.dmg` filenames in every directory, including mixed-case extensions.
The existing `Verify path policies` CI job also scans the complete tracked Git index.
It rejects these paths even when an ignored-file override added them.
It also rejects prohibited paths introduced and later removed within incoming commit history.
The check runs on pull requests, merge-group candidates, and pushes to `main`.
Its job remains covered by the existing CI allowlist and always executes on the candidate.

## Usage

Use Bash and Git from a checkout:

```sh
bash .github/scripts/CheckBinaries.sh
```

Pass an optional directory to inspect another checkout.
Pass base and head revisions after that directory to scan incoming commits as CI does.
Exit codes are zero for no prohibited paths, one for prohibited paths, and two for invalid arguments or Git failures.
Remove reported paths from the Git index and keep authorized vendor software outside repository checkouts.
See [the research artifact policy](../../Reference/Research/ResearchArtifacts.md).

## Limits

The guard checks names rather than contents.
It does not inspect archives, recognize renamed vendor software, rewrite previous commits, or prevent a local commit before CI runs.
No repository protection settings change.

## Verification

Source inspection found no DLL or DMG paths in the freshly fetched `main` tree at `4b730a8ff92f2a63dfdf3c16566d835b79c04835`.
No local tests ran.
Bash syntax checks and Prettier 3.6.2 formatting checks passed locally.
Remote CI process checks exercise a separate Git index with synthetic empty blobs.
They cover allowed CAD paths, root and nested prohibited paths, mixed-case extensions, spaces, newlines, staged removal, and Git failures.
Synthetic commits verify that adding and later removing prohibited paths still fails the incoming-history check.
The guard and its process checks passed in [remote CI](https://github.com/TryUniCAD/Kit/actions/runs/43699428039/job/132767077962).
All current-revision PR checks and merge-group acceptance remain separate requirements.

See [why ignore rules do not block tracked files](../../Gotchas/Git/IgnoreRulesDoNotBlockTrackedFiles.md).
