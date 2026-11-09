<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# GitHub and Git mechanics

Use observed owners, repositories, PR numbers, refs, SHAs, paths, IDs, and the actual Git host in place of examples. Use first-party tools when preferred and available; otherwise run each `gh` command in its own shell call containing only that command. No pipes, redirects, shell variables, command substitution, or chained commands. Parse outputs separately. `gh api` uses explicit repository paths and accepts `--hostname` for GitHub Enterprise; ordinary `gh pr` commands use the correct `--repo` target. Consult installed help and current official docs for unfamiliar flags or schemas.

## Resolve identity and create the task's PR

```sh
git rev-parse --show-toplevel
git status --short
git worktree list --porcelain
git remote -v
gh repo view --json nameWithOwner,url,defaultBranchRef,isFork,parent
gh api --method GET repos/base-owner/base-repo/pulls -f state=open -f head='head-owner:head-branch' -f per_page=100 --paginate --slurp
gh pr create --repo base-owner/base-repo --base base-branch --head head-owner:head-branch --title 'fix(api): correct requested behavior' --body-file /absolute/path/pr-body.md
gh pr view 123 --repo base-owner/base-repo --json number,url,state,headRefName,headRefOid,baseRefName,baseRefOid,headRepository,headRepositoryOwner,isCrossRepository,mergeable,mergeStateStatus,reviewDecision,latestReviews,autoMergeRequest,potentialMergeCommit
gh api repos/base-owner/base-repo/pulls/123
```

For a PR created in the same repository, its unqualified head branch is also valid. `gh pr list --head` does not support the `owner:branch` filter; use the pulls API above when resolving a fork. Resolve `head.repo.full_name` and `head.ref` as the publish destination, and `base.repo.full_name` as the PR query repository. Read-only discovery must precede coding in the isolated worktree. Inspect managed task artifacts if the host offers them; attach every created or explicitly targeted PR when supported.

## Isolate, scope, and publish

```sh
git fetch base-remote base-branch
git worktree add -b codex/task-name /absolute/path/to/task-worktree fetched-base-sha
git merge-base fetched-base-sha HEAD
git log --oneline fetched-base-sha..HEAD
git diff --stat fetched-base-sha...HEAD
git diff --name-only fetched-base-sha...HEAD
git diff fetched-base-sha...HEAD
git diff --cached --check
git diff --cached
git push --no-verify head-remote HEAD:refs/heads/head-branch
git ls-remote --heads head-remote refs/heads/head-branch
```

Run worktree commands from the original repository as needed; run coding, generation, staging, and validation inside the resulting worktree. For an existing task PR, create/reuse the worktree at its verified remote head instead of the base. Never reuse another task's dirty worktree or base a new PR on unrelated unpublished history. The `--no-verify` flag is the user's explicit push instruction, not a force option; never add `--force`, `--force-with-lease`, or a leading `+` refspec.

## Inventory all applicable CI

```sh
gh pr checks 123 --repo base-owner/base-repo --json name,state,bucket,workflow,event,link,startedAt,completedAt
gh api --method GET repos/owner/repo/actions/runs -f head_sha=exact-sha -f per_page=100 --paginate --slurp
gh api --method GET repos/owner/repo/commits/exact-sha/check-runs -f filter=latest -f per_page=100 --paginate --slurp
gh api --method GET repos/owner/repo/commits/exact-sha/statuses -f per_page=100 --paginate --slurp
gh api repos/base-owner/base-repo/git/commits/test-merge-sha
```

Query applicable head-repository push CI and base-repository PR CI. Tie a synthetic merge to the current head/base through its parents and linked run metadata. Keep merge-group checks distinct and verify that the observed group contains this PR; a group can contain additional queued PRs, so its parents need not equal a simple two-parent test merge.

`gh run list` defaults to 20 results and its chosen limit remains a cap. Paginate APIs; the filtered workflow-runs endpoint can have a 1,000-result ceiling, requiring partitioned queries. Commit-status histories are newest-first; retain the latest status per context. Preserve check provider/suite/workflow/event/attempt identities when names collide. `--required` omits non-required CI.

```sh
gh run view 456 --repo owner/repo --json databaseId,headSha,event,status,conclusion,attempt,jobs,url
gh run view 456 --repo owner/repo --attempt 2 --log-failed
gh run view 456 --repo owner/repo --attempt 2 --job 789 --log
gh api --method GET repos/owner/repo/actions/runs/456/attempts/2/jobs -f per_page=100 --paginate --slurp
gh api --method GET repos/owner/repo/check-runs/987/annotations -f per_page=100 --paginate --slurp
gh run rerun 456 --repo owner/repo --failed
gh pr checks 123 --repo base-owner/base-repo --watch --fail-fast --interval 30
gh run watch 456 --repo owner/repo --compact --exit-status --interval 30
```

Rerun only for one evidenced transient failure under the CI reference. Run watchers through yielding sessions and still perform a final full inventory. `gh pr checks` exit 8 means pending; `gh run view --exit-status` can return zero before completion, so inspect `status` and `conclusion`. Failed-job IDs and annotation check-run IDs are different. Empty, cancelled, skipped, neutral, queued, and successful are not interchangeable.

## Inventory @cubic-dev-ai results and threads

```sh
gh api --method GET repos/owner/repo/pulls/123/reviews -f per_page=100 --paginate --slurp
gh api --method GET repos/owner/repo/pulls/123/comments -f per_page=100 --paginate --slurp
gh api --method GET repos/owner/repo/issues/123/comments -f per_page=100 --paginate --slurp
gh api graphql -f query='query($owner:String!,$repo:String!,$number:Int!,$cursor:String){repository(owner:$owner,name:$repo){pullRequest(number:$number){headRefOid baseRefOid reviewThreads(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{id isResolved isOutdated path line comments(first:100){pageInfo{hasNextPage endCursor} nodes{id fullDatabaseId author{login} body url createdAt updatedAt originalCommit{oid} commit{oid}}}}}}}}' -F owner=owner -F repo=repo -F number=123
gh api graphql -f query='query($threadId:ID!,$cursor:String){node(id:$threadId){... on PullRequestReviewThread{comments(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{id fullDatabaseId author{login} body url createdAt updatedAt originalCommit{oid} commit{oid}}}}}}' -F threadId=PRRT_exampleNodeId -F cursor=observed-end-cursor
```

Paginate `reviewThreads` with its returned cursor until `hasNextPage` is false, and separately paginate each thread's comments when needed. Select the output from `@cubic-dev-ai` using the verified responding GitHub account or app and identify its threads from their originating comment's author. REST review comments do not establish resolution state; GraphQL threads do. Query failures and truncated pages are blockers to completeness, not proof that no findings from `@cubic-dev-ai` exist.

GitHub review submissions carry `commit_id`, comments can link their original/current commit, and checks carry `head_sha`. Correlate them with the current revision before trusting a verdict. A PR-body or issue-comment summary needs verified revision provenance; its timestamp alone does not establish the reviewed head. Read every reported concern even when no numeric score or formal review exists. Outdated threads from `@cubic-dev-ai` still need to be addressed and resolved.

## Trigger, answer, and resolve

```sh
gh pr comment 123 --repo owner/repo --body '@cubic-dev-ai review this PR'
gh api --method POST repos/owner/repo/pulls/123/comments/456789/replies -f body='Addressed in the accepted commit; the referenced path now enforces the documented contract'
gh api graphql -f query='mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{id isResolved}}}' -F threadId=PRRT_exampleNodeId
```

Use the exact top-level comment above to request review after opening the PR and after each new head. Check for an existing request or result first. Use [ReviewFindings.md](ReviewFindings.md) for revision attribution and completion rules. Finding replies must contain observed evidence rather than blindly copying the example. For a top-level report without review threads, post one concise finding-by-finding response linking the report, accepted fix SHA, and verification evidence; do not pretend an issue comment has a thread-resolution API. Resolve only threads from `@cubic-dev-ai` with genuinely addressed findings; do not dismiss a blocking review or use resolution to hide a defect.

## Conflict mechanics and read-only merge state

```sh
git status
git rev-parse --git-path MERGE_HEAD
git rev-parse --git-path rebase-merge
git rev-parse --git-path rebase-apply
git rev-parse --git-path sequencer
git merge --no-commit --no-ff --no-rerere-autoupdate fetched-base-sha
git ls-files --unmerged
git show :1:path/to/file
git show :2:path/to/file
git show :3:path/to/file
git diff --cached HEAD
git diff --cached fetched-base-sha
git merge-base --is-ancestor remote-head-sha HEAD
gh api repos/base-owner/base-repo/pulls/123
```

Read `git status` before any mutation to detect an interrupted operation. The `rev-parse --git-path` commands only locate metadata paths; they succeed even when the paths do not exist. Inspect filesystem metadata at each returned path before inferring operation state: `MERGE_HEAD` is a file, while `rebase-merge`, `rebase-apply`, and `sequencer` are directories. Preserve an unrelated active operation in its original worktree.

Check fresh remote mergeability before starting a merge. In an ordinary merge the index stages are ancestor, checked-out head, and merged base; a stage can be absent for additions/deletions. In a rebase stage 2 is the rebased series and stage 3 the replayed commit. Empty unmerged output and clean `diff --check` are mechanical evidence only. `merge-base --is-ancestor` exits 0 for ancestry, 1 for non-ancestry, and other nonzero for errors; ancestry alone does not prove outgoing commits are in scope.

GitHub computes mergeability asynchronously. `mergeable: null` requires waiting and another read. Refresh head/base refs alongside `mergeable: true` and repeat if either changed. `mergeStateStatus: BLOCKED` may mean missing approvals or checks rather than conflicts. Use available read-only PR/queue tooling or the GitHub UI to inspect actual merge-queue entries and merge-group checks; never call `gh pr merge` as an inspection shortcut, because it can merge, enroll in the queue, or enable auto-merge.

## Merge the ready PR

Only after the readiness gates in `SKILL.md` pass, use the first-party merge tool with the verified head SHA or the supported CLI path. The example uses squash; honor the user's requested method or the repository's supported default instead.

```sh
gh pr merge 123 --repo base-owner/base-repo --squash --match-head-commit verified-head-sha
gh api repos/base-owner/base-repo/pulls/123
```

The REST merge endpoint accepts `sha` as the expected PR head; never omit this guard when using that endpoint. Refresh head/base and gate evidence before the action and reverify on any mismatch. On a branch requiring a merge queue, `gh pr merge` enrolls a ready PR without requiring a merge strategy; verify the queue's supported path and follow merge-group checks until GitHub reports the PR merged. Queue enrollment and merging require an explicit request from a verified repository administrator. An admin override must never bypass pending or failing merge-group acceptance; follow the administrator-requested merge exception only for independently established remaining protections. Read back `merged`, `merge_commit_sha`, and `base.ref`; an accepted request or queue entry is not completion.

## Official references

- [PR creation](https://cli.github.com/manual/gh_pr_create), [PR view](https://cli.github.com/manual/gh_pr_view), [PR checks](https://cli.github.com/manual/gh_pr_checks)
- [Workflow runs](https://docs.github.com/en/rest/actions/workflow-runs), [workflow jobs](https://docs.github.com/en/rest/actions/workflow-jobs), [check runs](https://docs.github.com/en/rest/checks/runs), [commit statuses](https://docs.github.com/en/rest/commits/statuses)
- [Reviews](https://docs.github.com/en/rest/pulls/reviews), [review comments](https://docs.github.com/en/rest/pulls/comments), [issue comments](https://docs.github.com/en/rest/issues/comments)
- [GraphQL reference](https://docs.github.com/en/graphql/reference), [merge queues](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request-with-a-merge-queue)
- [Git worktree](https://git-scm.com/docs/git-worktree), [Git merge](https://git-scm.com/docs/git-merge), [Git rebase](https://git-scm.com/docs/git-rebase), [Git merge-base](https://git-scm.com/docs/git-merge-base), [Git ls-files](https://git-scm.com/docs/git-ls-files)
- [PR merge](https://cli.github.com/manual/gh_pr_merge), [REST merge endpoint](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request)
- [Codex repository skills and invocation](https://learn.chatgpt.com/docs/build-skills), [Claude Code skills and invocation](https://code.claude.com/docs/en/skills)
