<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Gotchas

- **Fusion research availability differs from public discovery:** Expected the packaged Fusion reader to be advertised as a supported production adapter; discovery deliberately excludes it because coverage is partial. Instantiate the research reader explicitly and do not infer lossless translation from a successful partial read. See [the import entry](../Changes/FusionResearchImport.md).

Read this log before working in an affected area. Keep entries short, searchable, and specific. Add a source or verification link when available. Move a growing topic into a focused PascalCase page in this folder and link it here; keep the bullet format.

- **Header remediation can leave dependency CI awaiting approval:** Expected the automated SPDX commit to complete PR validation; its current-head workflows can await maintainer approval while the aggregate remains on an older head. Approve the exact current-head runs and restart validation from a maintainer-authored commit when the aggregate did not start. See [PR 61's blocked run](https://github.com/TryUniCAD/Kit/actions/runs/42783888706).
- **Pyright infers literal integer struct formats:** Expected `isinstance` to narrow an unpacked value; Pyright 1.1.414 already knows `H` and `I` return integers and rejects those checks as unnecessary. Return an explicit integer after the existing buffer bounds check. See [the compatibility entry](../Changes/PyrightCompatibility.md).

- **Distribution name differs from the import:** Expected `from kit import convert` after installing the `kit` distribution; the wheel packages `convert` and `interchange`. Use `from convert import convert` and consult [the package metadata](../../pyproject.toml) and [public exports](../../src/convert/__init__.py).
- **Strict reading does not reject carriers:** Expected `strict=True` to ensure vendor-usable output; it only controls reader validation. Pass `allow_carrier=False` separately and inspect output attestations plus target-application evidence. See [ApiConvert](../../src/convert/api/ApiConvert.py).
- **Cubic sync paths fail repository naming policy:** Expected generated pages to pass CI; numbered kebab-case page names and lowercase manifest/index stems fail `PTH001`. Import into the PascalCase `Documentation/Reference/` layout, preserve provenance, and repair links before merging. Keep manual docs outside Cubic's `docs/` destination.
- **Enabling a wiki does not initialize its Git repository:** Expected `gh repo edit --enable-wiki` to make `Kit.wiki.git` clonable; GitHub returned repository not found until a first page was saved through the website. Create the first page once, then use the separate wiki Git remote. See [GitHub's wiki instructions](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).
- **Case-only directory changes on macOS:** Expected `Docs/` and `docs/` to be distinct; a case-insensitive filesystem treats them as the same directory. Use `Documentation/` for maintained pages, separate from Cubic's `docs/` path; use an intermediate path for case-only renames and inspect staged paths before deleting old files.
- **Queue configuration is not live enforcement:** Expected the checked-in queue manifest to establish acceptance gating; the live ruleset required only static `CI Agg`, allowing PR #42 to merge despite failed heavy jobs. Explicitly require `Merge queue acceptance`, and make the aggregate include the heavy workflow without a circular dependency. Settings changes need explicit authorization; verify the effective branch rules after applying them. See [the incident evidence](../Changes/QueueScorecard.md) and [MergeQueue.md](../../MergeQueue.md).

- **Skipped jobs can expose unevaluated names:** Expected a conditional job name to resolve before a skipped bootstrap was reported; GitHub returned the expression text, causing the aggregate to reject it. Retire one-time bootstrap triggers after installation and use stable names for real gates. See [the repair entry](../Changes/AggregateBootstrap.md).

- **Published CI artifacts can briefly return 404:** Expected the artifact ID returned by a successful upload to be immediately readable; PR #53 failed at metadata and PR #67 failed at both metadata and ZIP download, while later reads of those exact IDs succeeded. The immediate verification client now retries transient API responses up to four times, including 404, while retaining every digest and provenance check. See [the evidence and repair](../Changes/ArtifactPublication.md).

- **PR aggregation reads trusted base code:** Expected a reporter change on a PR branch to change that PR's `CI Agg`; `pull_request_target` loads the base revision. Merge the reporter change through its own reviewed PR before relying on the new exclusions in another PR. See [review provider exclusions](../Changes/ReviewProviderExclusions.md).

- **Scorecard Action rejects merge groups:** Expected `publish_results: false` to permit queue scans; the action still rejects `merge_group` before analysis. Use the pinned CLI for both the full repository scan and the exact candidate's commit-compatible checks. Required Greptile statuses also apply to queue commits where that app reports no status; require the native app result through `CI Agg` on PR heads instead. See [the failure and repair](../Changes/QueueScorecard.md).

If you discover a new gotcha, unexpected API behavior, wrong assumption, or undocumented quirk while working on this codebase, you MUST add it to the bullet list above before finishing your task. This is mandatory, not optional. Future you (or a different agent) will thank you. Format: - Short description of the gotcha, what you expected vs what actually happened, and the fix or workaround.
