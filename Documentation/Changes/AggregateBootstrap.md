# Retire the aggregate bootstrap

## Problem

PR #49 added the aggregate workflow.
Later PRs still scheduled its one-time `pull_request` preview.
GitHub reported the skipped job with an unevaluated name expression.
The trusted aggregate rejected the unexpected skipped check and workflow.

## Change

The repair removes the obsolete preview trigger and uses the stable `CI Agg` name.
Normal PR aggregation continues through `pull_request_target`.
The reporter uses trusted base code with read-only permissions and no PR code checkout.
Merge-group aggregation and component validation remain active.
The repair does not weaken expected checks or failure criteria.

## Recorded verification

The failure occurred in [PR #50 CI](https://github.com/TryUniCAD/Kit/actions/runs/42560078342).
The original change assigned event-inventory and workflow-policy verification to remote CI.
No local tests ran.
This historical record does not establish the current PR or queue result.
See [merge queue operations](../../MergeQueue.md).
