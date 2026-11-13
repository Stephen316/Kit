# Merge queue operations

Kit uses GitHub's native merge queue for `main`. The desired settings live in
[`.github/MergeQueue.json`](.github/MergeQueue.json). Repository settings are
outside Git history: merging this configuration PR does not activate them.

The live `Protect` ruleset requires both `CI Agg` and `Merge queue acceptance`
from GitHub Actions (`15368`). GitHub applies required checks to synthetic
queue commits, where PR reviewers do not report. Native review requirements
apply to PR readiness through the reviewer workflow below. Inspect the
checked-in desired ruleset and live rules separately.

## Validation phases

PRs run Python lint, formatting, types, steering, import, path, skill, and
workflow policies, including actionlint and Zizmor. Existing metadata labeling
continues. Load every entry in `Reviewers` from
[ReviewBot.json](.agents/skills/standard-pr-practice/ReviewBot.json), the sole source
of reviewer identities, report names, and exact request comments. Submit each
`Comment` verbatim once per head unless that reviewer already has a request or
review for that revision. Every configured reviewer must pass all its native
reports and submit an actual `APPROVED` review on the current head. Address every
finding from its verified account or app. Missing, pending, failed, stale, or
dismissed evidence blocks readiness. No human or code-owner approval is required
by the agent workflow; independently enforced GitHub requirements must still be
inspected and reported separately. The repository's CODEOWNERS file is removed.

Use each reviewer's native review and status indicator. Approval and findings
remain separate from CI health. Changing the JSON does not install integrations
or modify live rulesets.

[`Pull Request / CI Agg`](.github/workflows/PullRequest.yml) reports overall CI
health for the exact revision using the [CI allowlist](.github/scripts/CiAllowlist.cjs).
A check must come from GitHub Actions and match its workflow path, event, and
job name. The aggregate also checks the outcome of each listed workflow run.
It reads check runs and workflow runs. Commit statuses and unlisted reports
cannot satisfy a required CI job.

The [breaking change label check](Documentation/Changes/BreakingChangeLabelChecks.md)
separates PR event types into different concurrency groups and reads current metadata.

The [PR diff breakdown](Documentation/Reference/Operations/DiffBreakdown.md)
publishes an immutable composition report for each new PR head from trusted base code.

PR aggregation includes lint, formatting, types, repository policies, metadata
labels, release artifact validation, and GitHub-managed Code Quality for Python,
Java/Kotlin, and JavaScript/TypeScript. The first-time contributor label applies
on PR creation. Merge-group aggregation includes the static checks and their
reuse preflights, the full test suite, both candidate CodeQL jobs, all security
and SBOM scans, and the acceptance gate. PR runs of the queue workflow report
the acceptance gate with the heavy jobs deferred. Missing jobs keep the
aggregate pending. Unexpected skips, cancellations, timeouts, and failures
fail the aggregate. The summary links individual reports.

When adding or renaming CI, update the allowlist alongside the workflow and
register each job under the event that runs it. Keep automated review outside
those workflows and verify its reports during PR review follow-up.

Removing metadata from the JSON does not change integration-owned settings.
Do not change live rulesets as part of this workflow.

## Reuse healthy PR CI

A successful PR aggregate publishes a small immutable evidence artifact bound
to its repository, PR number, head repository, head SHA and tree, event base SHA,
base ancestry, workflow event, workflow run, and attempt. A queued PR is
included when its head is an ancestor of the candidate or when the candidate's
`gh-readonly-queue/<branch>/pr-<number>-<sha>` ref names it. Squash candidates
never contain the PR head as an ancestor, so the ref is the only membership
signal for them. The merge queue
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
evidence never produces a cached success. Change-range checks, acceptance, and heavy security always
execute on the actual merge group. No acceptance result is inferred from PR CI.

On merge groups, `Merge queue acceptance` requires every heavy job to succeed.
`CI Agg` then combines static validation, verified reuse, every heavy check and
the completed queue workflow. It explicitly expects `Merge queue acceptance`
and fails immediately when any heavy check or the queue workflow fails. Missing
or pending acceptance keeps the aggregate pending. Acceptance does not wait on
the aggregate, so there is no dependency cycle. Both contexts are required by
the live ruleset. The previous combination of excluding the queue workflow from
`CI Agg` and not requiring acceptance allowed PR #42 to merge with failed
CodeQL, dlint, Scorecard, and tests; both gaps are repaired here.

[MergeQueue.yml](.github/workflows/MergeQueue.yml) reports the required
`Merge queue acceptance` context on PRs with an explicit deferral summary. Its
acceptance jobs are deliberately skipped at this stage, so green PR checks
establish eligibility for queue enrollment, not acceptance success.

The `Scorecard` job uses the checksum-pinned OpenSSF Scorecard CLI instead of
`ossf/scorecard-action`, which rejects `merge_group` events. It runs the complete
default repository scan and then the commit-compatible checks against the exact
`merge_group.head_sha`. The second scan supplements the repository scan because
commit-specific mode omits checks that cannot evaluate arbitrary commits. Both
JSON reports are summarized in the job log, command failures fail the job, and
`Merge queue acceptance` still requires it. Results are not published to the
Scorecard API. See [the repair and verification entry](Documentation/Changes/QueueScorecard.md).

On `merge_group.checks_requested`, the same workflow runs the complete pytest
suite, both CodeQL language analyses, and every existing heavy security/SBOM scanner
as direct jobs in the queue workflow. No tests, assertions, scanner jobs, or security
thresholds are removed. The stable acceptance gate depends explicitly on every heavy job, runs with `always()` and
requires every acceptance and heavy security job to succeed; failures, cancellations,
timeouts, and unexpected skips fail the gate. Fast CI additionally runs the existing CodeQL policy and pytest compatibility
process checks, catching stale workflow references before enrollment. Static checks retain their required
contexts on the merge group and either execute or use verified equivalent PR evidence.

The pytest suite runs as [runtime-planned shards](Documentation/Changes/ShardedTestSuite.md).
`Test suite / Plan` collects the candidate's tests and sizes the shard matrix.
Each shard holds at most 300 tests.
Each `Test suite / Shard (n)` job runs only its planned node IDs.
`Test suite / Report` fails unless every planned test ran exactly once.
The acceptance gate requires the plan, every shard, and the report to succeed.
`Run the complete test suite` remains as a compatibility job that requires the same three jobs.
The trusted-base `CI Agg` of the first sharded candidate still requires that name.
The CI allowlist matches shard check names by pattern because the shard count changes with the suite.

The checked-in desired queue has no bypass actors, uses squash merges, requires `ALLGREEN`, builds
at most two candidates concurrently, and merges one entry at a time. Its
90-minute response timeout allows the existing 60-minute analyses plus runner
scheduling. Each candidate has its own concurrency group; a later PR update
cannot cancel a different queue candidate. Heavy workflows do not repeat on
the subsequent `main` push. The observed live `Protect` settings differ: five
concurrent builds, up to five merged entries, a five-minute minimum wait, a
60-minute response timeout, and an existing organization-admin bypass. These
were preserved; only the required status contexts were changed for this repair.

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
   and every listed static check from the GitHub Actions integration (`15368`).
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
and configured reviewer follow-up and leave it open with acceptance clearly deferred.

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
