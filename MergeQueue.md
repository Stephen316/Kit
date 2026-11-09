<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Merge queue operations

Kit uses GitHub's native merge queue for `main`. The desired settings live in
[`.github/MergeQueue.json`](.github/MergeQueue.json). Repository settings are
outside Git history: merging this configuration PR does not activate them.

## Validation phases

PRs run Python lint, formatting, types, steering, import, SPDX, path, skill, and
workflow policies, including actionlint and Zizmor. Existing metadata labeling continues. Cubic is the only
automated reviewer; request `@cubic-dev-ai review this PR` once per head and
address every finding from its verified account or app on that revision. Cubic
must submit an actual `APPROVED` review on that exact head. No human or
code-owner approval is required. `@cubic-dev-ai` is the wildcard owner in
`CODEOWNERS`; `@odinglyn0` is not listed.

Use Cubic's existing native review and status indicator. There is no duplicate
Cubic approval workflow. Review evidence and approval remain separate from CI.

[`Pull Request / CI Agg`](.github/workflows/PullRequest.yml) reports overall CI
health for the exact PR revision, excluding Cubic by verified app identity. It
waits for every expected static, policy, label, and GitHub-managed Code Quality
check, and inventories additional check runs and commit statuses. Failed,
cancelled, timed-out, missing, and unexpectedly skipped reports cannot pass.
The managed Code Quality workflow's required check names are `Analyze (python)`
and `Analyze (java-kotlin)`; `Code Quality` is a workflow label, not an additional
check context. Both actual check names are explicitly expected by the aggregate.
The summary links the individual reports. CI execution stays in the existing
workflows; the aggregate does not replace their assertions or thresholds.

[`cubic.yaml`](cubic.yaml) enables live approval for every clean PR and allows no
open Cubic issues. Cubic reads this file only from the default branch; feature
branch configuration does not take effect until merged. Before then, a repository
administrator manages the equivalent approval setting in Cubic. Do not change
live rulesets as part of this workflow. The code-owner replacement takes effect
when this PR merges. GitHub requires the named user to have repository write
access before it recognizes ownership; the installed review app's access does
not grant that separate user write permission.

## Reuse healthy PR CI

A successful PR aggregate publishes a small immutable evidence artifact bound
to its repository, PR number, head repository, head SHA and tree, event base SHA,
base ancestry, workflow event, workflow run, and attempt. The merge queue
checks current CI health for every included PR and validates the artifact's
origin and SHA-256 digest. Reuse requires identical candidate and PR-head trees,
identical base commits, and ancestry from that base to the PR head. With that
ancestry, merging the base into the PR head adds no files or content. Only
whole-tree checks are reusable. Header, path-diff, and rationale-diff checks
always execute freshly on the queue candidate. Supplementary merge-ref reports
are included only after their parents match the recorded head and base.

Normal PR aggregation runs on `pull_request_target` using the trusted default
branch's workflow and reporter, without checking out or executing PR code. Its
artifact records the PR head input tree rather than treating the event's base
SHA as a tested PR merge. The one-time `pull_request` preview used to install
the pipeline in PR #49 has been retired. The aggregate runs only on
`pull_request_target` and `merge_group`; component validation retains its own
PR workflows. Bootstrap artifacts are never eligible for queue reuse; only
successful trusted `pull_request_target` runs qualify.

Queue preflights and the queue aggregate load the verifier from the exact trusted
merge-group base commit. PR changes to the helper are not executed by those
artifact-reading queue jobs. PR aggregation uses read-only permissions and does
not receive repository secrets. The aggregate's 80-minute wait covers the
45-minute audit jobs within its 90-minute job limit.

When that proof succeeds, eligible static jobs retain their check names but explicitly
skip duplicate execution. The aggregate independently verifies reuse before
accepting those skips. If a head, base, tree, report, or evidence artifact does
not match, static checks execute on the candidate instead. Missing or expired
evidence never produces a cached success. Header and change-range checks, acceptance, and heavy security always
execute on the actual merge group. No acceptance result is inferred from PR CI.

On merge groups, `CI Agg` covers static validation and verified reuse. The
existing required `Merge queue acceptance` gate combines that result with every
heavy job, so missing or failing aggregate evidence blocks acceptance too. This
avoids a dependency cycle: the static aggregate does not wait for heavy jobs on
the queue. No additional live ruleset changes are needed for this dependency.
The gate verifies the latest merge-group run from `PullRequest.yml`, its check
suite, exact candidate SHA, and successful workflow completion. A passing check
with the same display name from another workflow cannot substitute.

[MergeQueue.yml](.github/workflows/MergeQueue.yml) reports the required
`Merge queue acceptance` context on PRs with an explicit deferral summary. Its
acceptance jobs are deliberately skipped at this stage, so green PR checks
establish eligibility for queue enrollment, not acceptance success.

On `merge_group.checks_requested`, the same workflow runs the complete pytest
suite, both CodeQL language analyses, and every existing heavy security/SBOM scanner
as direct jobs in the queue workflow. No tests, assertions, scanner jobs, or security
thresholds are removed. The stable acceptance gate depends explicitly on every heavy job, runs with `always()` and
requires every acceptance and heavy security job to succeed; failures, cancellations,
timeouts, and unexpected skips fail the gate. Fast CI additionally runs the existing CodeQL policy and pytest compatibility
process checks, catching stale workflow references before enrollment. Static checks retain their required
contexts on the merge group and either execute or use verified equivalent PR evidence.

The queue has no bypass actors, uses squash merges, requires `ALLGREEN`, builds
at most two candidates concurrently, and merges one entry at a time. Its
90-minute response timeout allows the existing 60-minute analyses plus runner
scheduling. Each candidate has its own concurrency group; a later PR update
cannot cancel a different queue candidate. Heavy workflows do not repeat on
the subsequent `main` push.

## Activate after this PR merges

A repository administrator must perform these steps using an authenticated
account with repository Administration write permission. Do not activate before
the workflows exist on `main`, since the required acceptance context would be
missing. Do not enqueue this setup PR to validate itself or treat its green PR
checks as completed acceptance.

1. Read the merged `main` versions of this document, the workflows, and the
   ruleset manifest. Verify the authenticated user's identity and `admin`
   repository permission and preserve the existing `Protect` ruleset.
2. Inspect current rulesets to avoid creating duplicate queue rules. Add the
   manifest as the separate `Merge queue` ruleset, or update that exact
   existing ruleset using its observed ID. Preserve unrelated linear-history,
   update, and conversation protections.
   Keep generic human and code-owner approval requirements disabled.

   ```sh
   gh api user --jq .login
   gh repo view TryUniCAD/Kit --json viewerPermission
   gh api repos/TryUniCAD/Kit/rulesets --paginate
   ```

   These commands are read-only. An administrator manages settings separately
   in GitHub Settings, updating an observed existing queue configuration instead
   of creating a duplicate. If queue rules already live inside `Protect` or
   another mixed ruleset, preserve all its unrelated rules; never replace it
   wholesale with the standalone manifest. No ruleset mutations are part of CI,
   ordinary PR follow-up, or an agent's merge authorization.

3. Read back the returned ruleset ID and
   `gh api repos/TryUniCAD/Kit/rules/branches/main --paginate`. Verify the native
   queue is active, has no bypass actors, and requires `Merge queue acceptance`
   and every listed static check, including the final SPDX
   failure gate from the GitHub Actions integration (`15368`).
   The manifest is additive; do not replace unrelated protections.
4. With explicit merge authorization from a verified administrator, enqueue a
   ready normal PR. Verify that GitHub creates a `merge_group` run on its
   synthetic SHA and that every acceptance and scanner job executes. Follow
   the candidate until all static and acceptance checks pass and GitHub reports
   the PR merged. A failed gate must prevent merging. A verified administrator merge request also authorizes a supported override
   of existing update restrictions after all applicable phase checks
   pass, but only if that supported path preserves the native queue and every
   acceptance gate. If no such path exists, report the exact policy boundary.
   Never use an override to merge directly while queue acceptance is deferred,
   pending, or failing.

Only repository administrators can authorize agents to enroll PRs, enable
auto-merge, or merge. Verify the requesting user's identity and current `admin`
permission with the collaborator-permission endpoint; the tool account's
permission alone does not identify the person requesting the merge. A coding
request, PR creation, skill invocation, or green CI grants no merge authority.
Absent an explicit administrator merge request, finish the PR's available CI
and Cubic review and leave it open with acceptance clearly deferred.

GitHub-managed `CodeQL - Code Quality` is a separate service configuration and
currently still runs on PRs. This PR moves repository-owned heavy jobs; moving
that external analyzer also requires its service settings to change. Include
its current PR results when reporting all-CI readiness.

GitHub runs repository settings and queue management outside the PR, so report
activation and the first successful live merge-group run as separate evidence.
Do not describe this configuration as active until the settings are read back.

## References

- [GitHub merge queue and coupled PR/merge-group checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [Repository rulesets API](https://docs.github.com/en/rest/repos/rules)
- [Trusted pull-request metadata workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target)
- [Cubic live approval](https://docs.cubic.dev/ai-review/auto-approval)
- [Cubic default-branch configuration](https://docs.cubic.dev/configure/cubic-yaml)
