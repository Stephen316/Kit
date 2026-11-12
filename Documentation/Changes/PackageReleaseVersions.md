<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Package versions from commit history

Each push to `main` builds `unicad-kit` at `major.minor.patch.commit-count`. The fourth component counts commits along the first-parent history of the commit at the tip of the push.
A push with multiple commits on that history can skip numbers.
Rerunning the build for the same commit produces the same version.

The release workflow uses the installed wheel's version in the GitHub release title and PyPI version lookup. For example, `Kit v0.1.0.1276` corresponds to `unicad-kit==0.1.0.1276`.

The GitHub release notes contain the commit subject and body as Markdown. Git omits its author, committer, and date headers from the notes. The `commit-<sha>` tag identifies the source commit.

The build sets the package version in its temporary checkout. The GitHub source archives contain the original files from the release commit. The PyPI wheel and source distribution contain the four-part version.

## Change the base version

1. Run `uv version --no-sync --bump patch`. Use `minor` or `major` for the other bumps.
2. Include `pyproject.toml` and `uv.lock` in the PR.
3. A repository administrator signs the PR head with a signing key registered with GitHub. Use `git commit -S` to sign the version bump commit.
4. Check that GitHub marks the PR head as Verified. Any later commit on the PR must also have an administrator's verified signature.

The required `CI Agg` check uses the policy from the trusted base branch. It checks the signer's current repository permission. The release workflow checks the original PR head's signature and version after the merge. Use a personal signing key for base version changes. GitHub's web signing key does not identify a repository administrator as the signer.

The commit count continues across base version bumps. For example, a patch bump can take the package from `0.1.0.1276` to `0.1.1.1277`.

## Verification

`bash -n` and ShellCheck passed for the [release script](../../.github/scripts/BuildRelease.sh).
The [PR build](../../.github/workflows/ReleaseBuild.yml) checks the version policy, the source distribution filename, and the installed wheel version. It also loads the wheel's public entry point.
PyPI returned HTTP 200 for [an existing four-part release](https://pypi.org/pypi/opencv-python/4.12.0.88/json) and HTTP 404 for the unpublished Kit candidate.
The first release on `main` exercises the GitHub title and PyPI upload with the new version.
