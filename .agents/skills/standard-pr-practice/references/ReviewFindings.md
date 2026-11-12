<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Follow up on automated reviews

Address every finding from the verified account or app that responds to the `Comment` loaded from [ReviewBot.json](../ReviewBot.json), including advisory findings, top-level comments, and findings in neutral checks. Only a review from that integration clears the bot review gate. Use [GithubCommands.md](GithubCommands.md) for paginated inventory, replies, and thread resolution.

## Inventory the report and its revision

Read the complete PR reviews, inline comments, conversation comments, PR-body reports, check outputs, and commit statuses. Verify the author's login or app identity; a bot name quoted by another author is not provenance. Capture report URLs, finding text, affected paths, any reviewed SHA or run ID, and thread resolution state. Paginate both threads and their comments. An API failure is unavailable evidence, not an empty findings list.

Reviews expose `commit_id`; checks expose `head_sha`; a report may link a review run or identify its revision in its body. Verify that metadata before calling a result current. A recent comment timestamp alone is insufficient. If revision attribution is unavailable, label it unknown while still evaluating every finding against the current code.

Keep a compact disposition for each finding: fixed with an accepted commit and validation evidence, answered with concrete evidence, or open with the unresolved question. Include summary-only findings and outdated threads. A stale location can describe a defect that still exists.

## Investigate and repair

Read the implicated code, callers, tests, and relevant official API documentation. Evaluate conditional concerns such as “may be unsupported” or “could be wrong if” rather than discarding them as uncertainty. Establish whether the production path actually works. If correctness depends on an external service restriction, verify that restriction from authoritative documentation or authorized integration evidence; a mocked response or green unrelated CI does not settle it.

Fix actionable code, fixture, and documentation defects coherently. Preserve test, type, security, and CI gates. Follow the main workflow's isolated-worktree, commit/push authorization, and no-local-tests rules. Written regression coverage becomes passing evidence only after remote CI executes it.

For an already-fixed finding, point to the accepted fix and relevant verification. For a false positive or conflicting instruction, answer with specific code, contract, or documentation evidence. An unverifiable concern remains open; do not label it a false positive merely because no failure has been reproduced.

Reply inside an existing review thread, then resolve it only after the finding is addressed. For findings in a top-level report, post a concise consolidated response linked to that report with each disposition and its evidence. Do not delete or minimize the report, and do not claim that an issue comment was resolved through a review-thread API. If a human decision is necessary, report that boundary without messaging people unless authorized.

## Request review for the current head

After opening the PR and after each accepted push that changes its head, submit
each entry's Comment from [ReviewBot.json](../ReviewBot.json) verbatim as a
separate top-level PR comment unless that reviewer already has a request or
review for the current head. A verified native run queued or in progress on that
SHA counts as an existing request on later heads. Record the accepted SHA and
request URL for each reviewer. Verify the responding account or app and revision.

Poll in responsive intervals around 30–60 seconds and inspect new findings promptly. Do not manufacture commits to provoke a review. Report missing integration, inaccessible evidence, or a persistently unavailable result; do not install or reconfigure the service as part of repair.

## Verify completion

Require every configured reviewer's actual approval attributable to the current head, all reported findings fixed or answered with evidence, no unresolved review threads from the configured reviewer including outdated ones, and no outstanding blocking verdict. Track human-authored concerns and independently enforced conversation-resolution requirements separately; do not resolve someone else's threads through this bot-review workflow. Read the substance of the configured reviewer's own report and status indicator: a successful or neutral check with actionable findings is not a clean review. Keep approval and review evidence separate from `Pull Request / CI Agg`, whose existing provider exclusions are documented in [MergeQueue.md](../../../../MergeQueue.md). Do not add a duplicate reviewer approval workflow or invent a numeric score requirement.

Verify the responding GitHub account or app against the integration named by
`Comment` in [ReviewBot.json](../ReviewBot.json). Record its observed login, immutable
user or app ID, and account type from GitHub metadata; do not assume the mention
and responding bot login are identical or accept a quoted bot name as provenance.
Correlate the native review's `commit_id` and status `head_sha` with the current PR
head. A stale or dismissed approval is insufficient. No human or code-owner
approval is required by this workflow. Report unavailable approval evidence
separately from passing CI and independently enforced repository requirements.
Changing the comment does not install a reviewer, change ownership, alter CI
provider exclusions, or reconfigure branch protections.

Keep “findings addressed”, “current-head review completed”, “CI passed”, “mergeable”, “required approvals satisfied”, and “queued/merged/deployed” as separate facts. Unknown revision attribution or a missing current-head review remains unavailable evidence, not a clean pass. If the head changes, refresh the report and CI inventory. If the PR merges or closes externally, report that change and any unresolved review evidence before further publication.

Do not weaken or silence the reviewer, alter its configuration, dismiss blocking reviews, or resolve unaddressed findings to reach completion. Continue while substantive repairs are progressing; if the same evidenced concern repeats without progress or the service is unavailable, report the exact finding or service boundary and the smallest next action.
