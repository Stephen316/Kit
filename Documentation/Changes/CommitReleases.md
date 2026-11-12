<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Commit releases and PyPI publishing

[Release.yml](../../.github/workflows/Release.yml) builds artifacts from the exact commit selected when the workflow starts. A manual run from `main` publishes a GitHub release with the full SHA as its title, a `commit-<sha>` tag pointing at that commit, and the commit's author, committer, dates, and message as the description. It attaches `Kit-<sha>.zip` and `Kit-<sha>.tar.gz`, plus one `.SHA256` and one `.SHA512` file per archive. The source archives omit the research workspace, including its proprietary SOLIDWORKS DLLs, and the SOLIDWORKS donor fixtures. Use a Git checkout for research or tests that need those inputs.

GitHub generates its own source links. Verify the attached files instead: from the directory containing the downloaded files, run `sha256sum -c Kit-<sha>.zip.SHA256` or `sha512sum -c Kit-<sha>.tar.gz.SHA512`, substituting the release SHA. Enable [GitHub's immutable releases setting](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes) before dispatching to lock the published tag and uploaded assets.

## Configure and publish

1. In the repository's [GitHub environments](https://github.com/TryUniCAD/Kit/settings/environments), create `pypi` and allow deployments only from the `main` branch.
2. In [PyPI publishing settings](https://pypi.org/manage/account/publishing/), create a [pending Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) for `unicad-kit`, owner `TryUniCAD`, repository `Kit`, workflow `Release.yml`, and environment `pypi`. After the project exists, manage its publisher from the project settings. The workflow uses short-lived credentials and requires no PyPI API token.
3. Before each new release, set an unused Python package version in [pyproject.toml](../../pyproject.toml) and update `uv.lock` in a reviewed PR. The SHA identifies the source in GitHub; PyPI uses the package version.
4. After merging, run [Release](https://github.com/TryUniCAD/Kit/actions/workflows/Release.yml) from `main`, or use `gh workflow run Release.yml --repo TryUniCAD/Kit --ref main`. After GitHub attaches the source archives, the workflow publishes the wheel and Python source distribution to PyPI.
5. Check the [GitHub release](https://github.com/TryUniCAD/Kit/releases) for the tag, title, notes and six assets. Check the matching [PyPI version](https://pypi.org/project/unicad-kit/) for the wheel and source distribution, then follow the [installation guide](../GettingStarted.md).

If GitHub succeeds and PyPI fails, rerun the failed job after correcting the cause. Do not dispatch a new run for the same SHA: the existing GitHub release will already own its tag. PyPI does not allow replacing published files or reusing their filenames.

## Verification

[Pull request CI](https://github.com/TryUniCAD/Kit/actions/runs/43161060340) built both archives and both Python distributions, verified the archive contents and checksums, and installed the wheel in an isolated environment to load its public entry point. [ReleaseBuild.yml](../../.github/workflows/ReleaseBuild.yml) and the publishing workflow run the same [build script](../../.github/scripts/BuildRelease.sh). Verify GitHub release creation and PyPI authentication in the first run on `main`.
