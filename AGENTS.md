<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Agent guidance

## Documentation and gotchas

Every new feature, API, adapter, command, configuration option, workflow, tool,
or other repository addition MUST include a new PascalCase Markdown entry in
`Documentation/Changes/` in the same PR. Describe behavior, usage or configuration,
limitations, and actual verification evidence. Update the relevant guide and
[change index](Documentation/Changes/Index.md), and link the entry in the PR. An update
to an existing reference page does not replace the required new entry. Pure
documentation corrections may update their existing entry.

Read [Documentation/Gotchas/README.md](Documentation/Gotchas/README.md) before working in an
affected area. If you discover a new gotcha, unexpected API behavior, wrong
assumption, or undocumented quirk while working on this codebase, you MUST add
it to that bullet list before finishing your task. This is mandatory, not
optional. Format: a short description of the gotcha, what you expected vs what
actually happened, and the fix or workaround. Link evidence when available.

Maintained documentation lives in `Documentation/`. Follow
[the publishing guide](Documentation/Publishing.md) for generated imports and GitHub wiki
updates; generated docs must be reviewed and must not overwrite manual entries.

## Repository workflow

Agents MUST activate [standard-pr-practice](.agents/skills/standard-pr-practice/SKILL.md)
every time they work on this repository, before any task, including investigation,
documentation, skill edits, implementation, and PR follow-up. It is the only repository skill and the
canonical source for Codex and Claude Code. Edit it directly. Do not restore
the removed Kiro skill registrations, steering directories, or skill generator.
All prior rules and resources are preserved in full inside standard-pr-practice;
read its complete standards index and every applicable rule before coding.

- Use an isolated worktree and a separate normal PR for each task. Preserve
  user-owned changes and never write directly to `main`.
- Push with `--no-verify`. Never run tests locally, including collection,
  reproductions, hooks, or build commands that execute tests.
- Unit tests are prohibited, including policy, security, and tooling unit
  tests. Validate through integration, end-to-end, smoke, compatibility, and
  repository policy checks at real component or process boundaries.
- Run heavy acceptance and security checks on the merge-group candidate through
  [the native merge queue](MergeQueue.md). Keep every applicable CI gate enabled.
  Distinguish green PR checks from successful queue acceptance.
- Use `Pull Request / CI Agg` for overall CI health, with its existing provider
  exclusions documented in [MergeQueue.md](MergeQueue.md). Reuse healthy PR reports
  in the queue only with verified identical inputs; otherwise rerun. Header and
  change-range verification and heavy acceptance always execute on the candidate.
- Read every entry in `Reviewers` from
  [ReviewBot.json](.agents/skills/standard-pr-practice/ReviewBot.json), the sole
  source of reviewer identities, report names, and exact request comments.
  Submit each entry's `Comment` verbatim once per accepted head unless that
  reviewer already has a request or review for that head. Verify every responding
  account/app and reviewed SHA, and address all findings. Every configured
  reviewer must pass all its native reports and submit an actual `APPROVED`
  review on the current head before the PR is ready. Missing, pending, failed,
  stale, or dismissed evidence blocks readiness. Comments and green checks do
  not substitute for approval. Keep reviewer names and identifiers only in that
  JSON. No human or code-owner approval is required by this workflow. Report
  unavailable review evidence and independently enforced requirements separately.
- Only an explicit merge request from a verified repository administrator
  authorizes an agent to enroll a PR in the queue, enable auto-merge, or merge.
  Verify the requester's identity and current repository `admin` permission.
  Implementation requests and PR creation alone do not authorize merging.
- Use Python for backend work, React for frontend work, and `uv` for Python
  dependencies outside `Parashell/` and `modules/`.
- Do not add code comments or comment-oriented docstrings. Preserve required
  license notices. Use `license: MIT` in skill frontmatter, the exact
  `HEADER_NOTICE` for other comment-capable new files, and pinned Actions and
  runner versions.
- Keep chat lowercase, extremely concise, without emojis or terminal full
  stops. These response rules do not constrain artifacts.

The repository-root `re/` tree remains an unrestricted research workspace,
exempt from code standards and unit-test requirements, including naming,
formatting, typing, imports, rationale comments, SPDX headers, declaration
splitting, architecture, and directory density. This applies only to `re/` and
its descendants; code promoted into other directories follows their normal
rules. Git isolation and preservation of user-owned work still apply.

The research exemption does not waive product acceptance. Code or artifacts
shipped in production, and outputs claimed to be production-ready, must satisfy
no-CAD-runtime, no-donor-block, lossless-conversion, parametric feature/history,
vendor-loadability, and target-application acceptance requirements. Research
experiments may remain unrestricted in `re/`; their location does not qualify
them for shipping or establish acceptance evidence.

An administrator's explicit merge request remains valid through repairs and
authorizes a supported admin override when independently enforced protections
otherwise block a fully green, conflict-free PR. It never authorizes bypassing
pending or failed queue acceptance, changing protection settings, or bypassing
enforced tool approvals. Follow the skill's administrator-requested merge rules.
