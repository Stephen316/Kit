<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# CI allowlist for PRs and merge groups

`CI Agg` reads the [CI allowlist](../../.github/scripts/CiAllowlist.cjs). A
report must come from GitHub Actions and match an allowlisted workflow path,
event, and job name. The aggregate also checks the listed workflow runs for
failure. It uses the same PR rules when validating evidence for queue reuse.

PRs include static validation, metadata labeling, release artifact validation,
and all three managed Code Quality analyses. Merge groups include static
validation, reuse preflights, the complete test suite, CodeQL, all security and
SBOM scans, and the acceptance gate. The first-time label applies at PR
creation. PRs report heavy acceptance as deferred. See
[merge queue operations](../../MergeQueue.md).

Add every new CI job to its applicable phase in the allowlist alongside its
workflow. Keep automated review out of the allowlist and its workflows.
The standard PR practice checks configured reviewers' native reports,
current-head approvals, and findings during review follow-up.

The allowlist was matched against GitHub's
[PR runs](https://github.com/TryUniCAD/Kit/pull/76/checks?sha=5648a56d4b2b36fcb6da05dcac9551836dab6ea2)
and [merge-group acceptance jobs](https://github.com/TryUniCAD/Kit/actions/runs/43166611149).
The remote CI policy suite builds its job inventory from the workflow files and
checks that the reporter includes every job for each phase. Its API-shaped
responses exercise pending and failed review reports, unknown workflows and
jobs, a same-name report from the wrong workflow, and required CI failures.
The live aggregate loads the trusted base revision, so the allowlist takes
effect for new runs after the change reaches that branch.
