# Version release tags

## Problem

[Release.yml](../../../.github/workflows/Release.yml) tagged each GitHub release as `commit-<sha>`.
GitHub sorts the releases of one day by tag name.
The [releases page](https://github.com/TryUniCAD/Kit/releases) therefore listed the releases of one day in SHA order.
On 2026-11-13, the first page showed `Kit v0.1.0.465`, `.458`, `.460`, `.456`, `.462`, `.463`, `.457`, `.459`, `.455`, and `.461`.
See [GitHub release order](../../Gotchas/Packaging/GithubReleaseOrder.md).

## Change

The release job tags each release as `v<package-version>`, for example `v0.1.0.465`.
The tag uses the same version as the release title and the PyPI upload.
The [package version](../PackageReleaseVersions.md) has a different commit count for each first-parent commit on `main`.
Thus, each release commit gets a different tag.

The job keeps the existing tag check.
If the tag exists, it must point to the release commit.
Otherwise, the job stops before it creates the release.
The release title, notes, assets, and PyPI publishing do not change.

## Existing releases

Releases published before this change keep their `commit-<sha>` tags until a maintainer moves them.
To move a release, create the `v<package-version>` tag at its commit.
Then set the release `tag_name` to that tag.
Releases from before package versions use `0.1.0.<first-parent-commit-count>` for the same commit.
The old `commit-<sha>` tags stay in the repository.

## Limitations

The recorded order does not show whether GitHub compares tag numbers by value.
If GitHub compares text, `v0.1.0.999` and `v0.1.0.1000` from one day can sort in the wrong order.
A rerun for a commit with a release still fails because the release owns its tag.

## Verification

The [release order gotcha](../../Gotchas/Packaging/GithubReleaseOrder.md) records the page order and the SHA order on 2026-11-13.
The tag change takes effect on the next push to `main`.
No local tests ran.
