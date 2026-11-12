# CI follow-up

Read this when inventorying an opened PR's CI or repairing a failure. [GithubCommands.md](GithubCommands.md) contains the exact queries. Acceptance and heavy security workflows are deferred on PRs and required on merge-group candidates. Deferred jobs are not missing PR checks and are not passing acceptance evidence. The scope is this task's PR head and its applicable test-merge or merge-group revisions, never direct repair of main.

## Inventory before editing

Collect the fresh remote head/base pair and all applicable workflow runs, check runs, and commit statuses, including external CI and non-required checks. Record names, providers, workflow identities, events, attempts, conclusions, links, and failed job IDs. Enumerate every page. A branch-wide latest run, one workflow, `--required`, or a capped run list cannot certify all CI.

Correlate synthetic test-merge checks with this PR's current head/base pair. A GitHub test-merge SHA is not the head SHA or evidence that the PR merged. Existing queue entries can have a different merge-group SHA; tie its checks to the actual group containing this PR. Inspect applicable head-repository push CI as well as PR checks in the base repository.

Keep the latest attempt for each workflow/event identity and latest status for each context. Preserve provider, suite, workflow, event, and attempt identities when display names collide. Superseded failures are history; new failures on a different applicable event are not. Read unchanged workflow conditions to determine expected checks. A missing expected check is unresolved even when every visible check is green.

Read the first causal error in failed-job logs and annotations. Downstream cancellations and the final nonzero exit rarely identify the cause. If failed-only logs omit setup or context, inspect the full failed job and relevant artifacts. Obtain annotation IDs from the job's `check_run_url`; job IDs and check-run IDs are different.

## Repair the cause within the authorized scope

The scoped CI repair authorization and local-test restrictions in SKILL.md apply throughout this reference.

Classify the cause as an implementation defect, an independently justified test/fixture defect, a reproducible flake, or an external/workflow blocker. Use the repository's pinned runtime and the command CI actually ran to understand the failure, but do not execute tests locally under this user's rule. Diagnose from remote logs, source, and permitted non-test checks; test verification belongs in PR CI.

Fix production behavior and add meaningful regression coverage. Correct test fixtures or expectations only when the intended contract independently proves they are wrong, preserving equivalent or stronger coverage. Dependency, lockfile, and application configuration repairs are allowed if they fix the diagnosed defect while preserving all applicable validation and acceptance gates. A flaky test needs synchronization or another root-cause repair that preserves its assertions, not repeated reruns until it passes.

Repair evidenced CI execution defects in workflows, reusable workflows, actions/scripts, runner sizing, caches, matrices, sharding, scheduling, concurrency, dependency setup, and preview harnesses without asking for separate permission. Preserve the complete applicable check inventory, test coverage, required status names, timing targets, and trust boundaries. Diagnose queue/setup/execution/finalization time separately and compare the complete suite before and after each repair.

Do not change acceptance thresholds, repository protections, required-check configuration, credentials, or reviewer configuration. Do not omit tasks, add skip/continue-on-error behavior, hide exit codes, delete assertions, loosen coverage/lint/type/security gates, edit baselines merely to accept defects, or use skip-CI commits. Changes to triggers, filters, conditions, permissions, package scripts, and the task graph must preserve every applicable validation and trust boundary. A broken workflow or slow schedule is work to repair; missing access or a required target change remains a blocker.

A faithful base integration may bring upstream CI changes; any conflict resolution must preserve both revisions' intended execution and gates. Inspect the resulting integration and distinguish it from changing CI to make a failure disappear.

Settle the PR title, description, and changelog declarations before starting the final timed full-suite run. Metadata edits can trigger additional policy workflows on the same head and extend the measured suite. If such an edit is necessary during validation, wait for its policy checks to settle, then rerun the complete timed suite with that cause recorded; do not rerun only the elapsed-budget gate.

An evidenced transient runner/service error allows one justified rerun. Record the reason, resulting attempt, and outcome. Recurrence without new evidence is an external blocker; do not retry real failures by chance. Missing secrets, fork approvals, runner capacity, or service outages are not permission to modify repository settings.

## Publication and final evidence

Before publishing a fix, review the staged paths and outgoing commits, preserve unrelated work, perform permitted non-test validation, and refetch head/base. Integrate concurrent work without rewriting published history. Use a conventional commit and a normal push with the user's required `--no-verify`, read back the accepted SHA, and request review with each entry’s `Comment` loaded from `Reviewers` from [ReviewBot.json](../ReviewBot.json) for the accepted head as described in [ReviewFindings.md](ReviewFindings.md).

Wait for checks to schedule for that revision, rediscovering them as they appear. Use yielding sessions or discrete reads separated by responsive 30–60 second waits. `gh pr checks` may initially report no checks after a push; that means wait and investigate scheduling. A watcher is an intermediate signal, not the complete inventory.

Before calling CI green, refresh the exact head/base and every applicable latest attempt, check, and status again. All expected applicable CI must be successful, with no failed, pending, queued, cancelled, timed-out, action-required, or missing expected result. Explain genuine non-applicable conditional skips/neutrals from unchanged configuration. If head/base moves during verification, re-evaluate the affected evidence.

CI health alone proves neither a clean review from each configured reviewer nor merge readiness. Continue the combined workflow after green CI until its other gates are also verified.
