<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Gotchas

- **Fusion research availability differs from public discovery:** Expected the packaged Fusion reader to be advertised as a supported production adapter; discovery deliberately excludes it because coverage is partial. Instantiate the research reader explicitly and do not infer lossless translation from a successful partial read. See [the import entry](../Changes/FusionResearchImport.md).

Read this log before working in an affected area. Keep entries short, searchable, and specific. Add a source or verification link when available. Move a growing topic into a focused PascalCase page in this folder and link it here; keep the bullet format.

- **Reviewer mentions can target regular users:** Expected the configured mention to request automated review; the previous value resolved to [a regular GitHub user](https://api.github.com/users/67). Use the corrected [review configuration](../../.agents/skills/standard-pr-practice/ReviewBot.json), verify the responding account and app identity, and match its review to the current head SHA.

- **Header remediation can leave dependency CI awaiting approval:** Expected the automated SPDX commit to complete PR validation; its current-head workflows can await maintainer approval while the aggregate remains on an older head. Approve the exact current-head runs and restart validation from a maintainer-authored commit when the aggregate did not start. See [PR 61's blocked run](https://github.com/TryUniCAD/Kit/actions/runs/42783888706).
- **Pyright infers literal integer struct formats:** Expected `isinstance` to narrow an unpacked value; Pyright 1.1.414 already knows `H` and `I` return integers and rejects those checks as unnecessary. Return an explicit integer after the existing buffer bounds check. See [the compatibility entry](../Changes/PyrightCompatibility.md).

- **Distribution name differs from the import:** Expected `from kit import convert` after installing the `kit` distribution; the wheel packages `convert` and `interchange`. Use `from convert import convert` and consult [the package metadata](../../pyproject.toml) and [public exports](../../src/convert/__init__.py).
- **Strict reading does not reject carriers:** Expected `strict=True` to ensure vendor-usable output; it only controls reader validation. Pass `allow_carrier=False` separately and inspect output attestations plus target-application evidence. See [ApiConvert](../../src/convert/api/ApiConvert.py).
- **Generated sync paths fail repository naming policy:** Expected generated pages to pass CI; numbered kebab-case page names and lowercase manifest/index stems fail `PTH001`. Import into the PascalCase `Documentation/Reference/` layout, preserve provenance, and repair links before merging. Keep manual docs outside the generator's `docs/` destination.
- **Enabling a wiki does not initialize its Git repository:** Expected `gh repo edit --enable-wiki` to make `Kit.wiki.git` clonable; GitHub returned repository not found until a first page was saved through the website. Create the first page once, then use the separate wiki Git remote. See [GitHub's wiki instructions](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).
- **Case-only directory changes on macOS:** Expected `Docs/` and `docs/` to be distinct; a case-insensitive filesystem treats them as the same directory. Use `Documentation/` for maintained pages, separate from the generator's `docs/` path; use an intermediate path for case-only renames and inspect staged paths before deleting old files.
- **Queue configuration is not live enforcement:** Expected the checked-in queue manifest to establish acceptance gating; the live ruleset required only static `CI Agg`, allowing PR #42 to merge despite failed heavy jobs. Explicitly require `Merge queue acceptance`, and make the aggregate include the heavy workflow without a circular dependency. Settings changes need explicit authorization; verify the effective branch rules after applying them. See [the incident evidence](../Changes/QueueScorecard.md) and [MergeQueue.md](../../MergeQueue.md).

- **Skipped jobs can expose unevaluated names:** Expected a conditional job name to resolve before a skipped bootstrap was reported; GitHub returned the expression text, causing the aggregate to reject it. Retire one-time bootstrap triggers after installation and use stable names for real gates. See [the repair entry](../Changes/AggregateBootstrap.md).

- **Published CI artifacts can briefly return 404:** Expected the artifact ID returned by a successful upload to be immediately readable; PR #53 failed at metadata and PR #67 failed at both metadata and ZIP download, while later reads of those exact IDs succeeded. The immediate verification client now retries transient API responses up to four times, including 404, while retaining every digest and provenance check. See [the evidence and repair](../Changes/ArtifactPublication.md).

- **PR aggregation reads trusted base code:** Expected a reporter change on a PR branch to change that PR's `CI Agg`; `pull_request_target` loads the base revision. Merge the reporter change through its own reviewed PR before relying on the new exclusions in another PR. See [review provider exclusions](../Changes/ReviewProviderExclusions.md).

- **Scorecard Action rejects merge groups:** Expected `publish_results: false` to permit queue scans; the action still rejects `merge_group` before analysis. Use the pinned CLI for both the full repository scan and the exact candidate's commit-compatible checks. Required native-review statuses also apply to queue commits where that app reports no status; require the native app result through `CI Agg` on PR heads instead. See [the failure and repair](../Changes/QueueScorecard.md).

- **Scorecard can exit successfully after a SARIF formatting error:** Version 5.4.0 printed a missing Binary-Artifacts policy error and produced no report. Use the JSON formatter and verify both reports, including the exact candidate SHA. See [the queue failure](https://github.com/TryUniCAD/Kit/actions/runs/43155805818/job/130975329860).
- **Fusion fixture ZIPs need a Zstandard-capable standard library:** Python 3.11 raises NotImplementedError when the complete suite reads those ZIP members. The queue suite uses Python 3.14, which provides ZIP Zstandard support. See [the queue test failure](https://github.com/TryUniCAD/Kit/actions/runs/43155805818/job/130975329739).

- **The scanner group blocks Python 3.14 test setup on Linux:** The locked scanner dependency had no compatible wheel, so installing every dev group failed before pytest. Sync the project dev extra for the full test job and keep the scanners in their existing jobs. See [the setup failure](https://github.com/TryUniCAD/Kit/actions/runs/43161600774/job/130993867779).

- **The generator test needs Black in its own environment:** The project dev extra appeared to cover pytest, but the program generation check launches a subprocess that imports Black. Include the pinned formatter in that extra when isolating the suite from scanner dependencies. See [the review finding](https://github.com/TryUniCAD/Kit/pull/72#discussion_r4546730884).

If you discover a new gotcha, unexpected API behavior, wrong assumption, or undocumented quirk while working on this codebase, you MUST add it to the bullet list above before finishing your task. This is mandatory, not optional. Future you (or a different agent) will thank you. Format: - Short description of the gotcha, what you expected vs what actually happened, and the fix or workaround.

- **Review triggers are not always account mentions:** Expected every integration to accept an account tag; some require a slash command at the start of the comment and a linked write-enabled account. Read each exact `Comment` and its official documentation from [ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json), submit it verbatim, and verify the responding identity and reviewed SHA.

- **Provenance must survive configuration reordering:** Expected a JSON array reference to preserve the imported generator; moving exclusion entries changed its target. Reference the stable `DocumentationSources.InitialWiki.Generator` key in the configuration instead of an array position.

- **Commit-status responses omit the queried ref:** Expected API-shaped fixtures to include a commit field; [the status-list API](https://docs.github.com/en/rest/commits/statuses#list-commit-statuses-for-a-reference) scopes responses by the request path. Strip fixture routing metadata before returning statuses, and let the production reader attach the queried ref so integration coverage detects missing revision attribution.

- **Native reviews can restart on an unchanged head:** Expected passing checks to remain final while the commit SHA stayed fixed; native review checks returned to pending during PR metadata updates. Finish metadata edits before final verification and refresh the latest reports even when the head has not changed. Earlier passing reports cannot replace a newer pending result.
