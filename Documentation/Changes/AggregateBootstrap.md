<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Retire the aggregate bootstrap

After the aggregate workflow landed in PR #49, later PRs still scheduled its
one-time `pull_request` preview. GitHub skipped that job with the unevaluated
name expression instead of `Inactive aggregate bootstrap`, so the trusted
aggregate rejected it as an unexpected skipped check and workflow.

Remove the obsolete preview trigger and give the aggregate its stable `CI Agg`
name. Normal PR aggregation continues through `pull_request_target`, executing
the trusted base reporter with read-only permissions and no PR code checkout.
Merge-group aggregation and every component validation workflow remain active.
No expected checks or failure criteria are weakened.

The failure was observed in [PR #50 CI](https://github.com/TryUniCAD/Kit/actions/runs/42560078342).
Remote CI verifies the repaired event inventory and workflow policies; no local
tests run. See [merge queue operations](../../MergeQueue.md).
