# PR diff breakdown

## Purpose

The `Publish diff breakdown` check adds a collapsed analysis comment to each PR.
It runs when a PR opens, reopens, or receives a new head commit.
The comment shows how the changed lines divide across repository areas.
It also shows how many lines need review.

## Report contents

Each report contains the following information:

- Total changed lines, reviewable lines, and the share excluded from review
- A colour bar and a table of additions, deletions, lines, share, files, and policy for each category
- Risk signals from the configured categories
- The largest changed files
- Unclassified, renamed, deleted, binary, and metadata-only files
- Composition changes since the previous report, with the actual head-to-head push diff
- Links to the base, merge base, head, and trusted implementation commits

The comment summary shows the report title, the total changed lines, and the reviewable lines.
Expand the comment to read the full report.
The workflow summary contains the same Markdown.
The run artifact contains the complete per-file JSON snapshot.

## Categories

[DiffRules.txt](../../../.github/config/DiffRules.txt) maps paths to category names.
[DiffBreakdown.json](../../../.github/config/DiffBreakdown.json) sets the policy, colour, and risk text for each category.

| Category            | Paths                                                                              | Policy   |
| ------------------- | ---------------------------------------------------------------------------------- | -------- |
| Documentation       | `Documentation/` and Markdown files outside other categories                       | excluded |
| Reverse Engineering | `re/`                                                                              | excluded |
| Source              | `src/` and `typings/`                                                              | review   |
| Tests               | `tests/`                                                                           | review   |
| Tools               | `tools/`                                                                           | review   |
| GitHub              | `.github/`                                                                         | review   |
| Agents              | `.agents/`, `.claude/`, `.codex/`, `.hoplite/`, `.kiro/`, `AGENTS.md`, `CLAUDE.md` | review   |
| Unclassified        | All other paths                                                                    | review   |
| Binary Assets       | Files that Git reports as binary                                                   | separate |
| Whitespace Only     | Modified text files with only whitespace changes                                   | review   |

The last matching rule sets the category.
Markdown under `.github/`, `.agents/`, and `re/` therefore keeps the category of its directory.
A changed file with a binary or whitespace-only diff uses the binary or whitespace category.

## Policies

Lines in a category with the `excluded` policy are not reviewable lines.
All other policies add their lines to the reviewable count.
The excluded policy is a review-size setting only.
It is not a safety claim for documentation or research changes.
Unclassified files must keep the `review` policy.
The configuration check rejects other values.
Whitespace-only changes remain reviewable because indentation can change Python behavior.

## Rule syntax

Each nonblank line in `DiffRules.txt` contains a pattern, whitespace, and a category name.
Lines that start with `#` are comments.
Category names can contain spaces.

- A leading `/` anchors the pattern at the repository root.
- A pattern that contains `/` is also anchored.
- A pattern without `/` matches a path component at any depth.
- `*`, `?`, and character classes match inside one path component.
- A `**` component matches zero or more directories.
- A trailing `/` matches the contents of a directory.
- A match on a directory includes all its descendants.
- A leading `!` resets matching paths to unclassified and takes no category name.
- Write `\ ` for a space in a path.

A new category name in `DiffRules.txt` uses the `review` policy and a colour from its name.
Add the category to `DiffBreakdown.json` to set another policy, colour, or risk text.
Add a narrow rule in the same PR as a new diff-heavy path.

## Accounting

The PR diff compares the head commit with the merge base of the base and head commits.
Git collects every file directly, so the GitHub file API limit does not apply.
Shares use additions plus deletions, rounded to 0.1% with largest-remainder rounding.
Binary files count as files, with no line count.

A later report compares the previous reported head with the current head.
A rebase or force push still gets an exact tree comparison when Git can fetch the old head.
If Git cannot fetch the old head, the report states that the push diff is unavailable.
The report also states a changed merge base and changed classification rules.

## Security and publication

The workflow uses `pull_request_target` and checks out only the trusted base revision.
It does not check out or run PR code.
Git fetches PR commits as objects and runs with hooks, external diff tools, and text conversion turned off.
A PR cannot change the rules for its own report.
Rule changes take effect after they reach `main`.

The workflow never edits a published comment.
A hidden marker in each comment records the compact snapshot.
The publisher reads only markers from the GitHub Actions bot.
A head that already has a report does not get a second report.
An older run does not publish after a newer run.
Runs for one PR use one concurrency group without cancellation.
GitHub keeps one pending run in the group, so a newer pending run replaces an older pending run.

The publisher uses the `gh` CLI with the workflow token.
If GitHub rate-limits the token, the run records the status and ends without failure.
The next head then reports against the last published head.
Other publication errors fail the check.

The job has a two-minute timeout and a 90-second runner budget.
The budget includes checkout, analysis, publication, and artifact upload.
The run artifact is kept for 90 days.

## Implementation

The engine is in [.github/scripts/DiffBreakdown](../../../.github/scripts/DiffBreakdown/).
It uses only the Python standard library, Git, and the `gh` CLI.
The colour bar uses solid-colour images from [Placehold](https://placehold.co/).
The image URLs contain only configured colours.
If the image service is unavailable, the category table still contains every count.

[DiffBreakdownTests.py](../../../tests/Policy/DiffBreakdownTests.py) runs the engine against a temporary Git repository.
It checks the categories, the excluded totals, and the trusted publication guard.
It also checks the `GITHUB_REPOSITORY` identity guard with rejected and accepted values.

## Related information

- [Change entry](../../Changes/DiffBreakdownReports.md)
- [CodeQL repair](../../Changes/DiffBreakdownCodeql.md)
- [Repository guard coverage](../../Changes/RepoGuardCoverage.md)
- [CI allowlist](../../../.github/scripts/CiAllowlist.cjs)
- [Repository policy](Policy.md)
