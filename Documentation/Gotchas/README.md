<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Gotchas

Read this log before working in an affected area. Keep entries short, searchable, and specific. Add a source or verification link when available. Move a growing topic into a focused PascalCase page in this folder and link it here; keep the bullet format.

- **Distribution name differs from the import:** Expected `from kit import convert` after installing the `kit` distribution; the wheel packages `convert` and `interchange`. Use `from convert import convert` and consult [the package metadata](../../pyproject.toml) and [public exports](../../src/convert/__init__.py).
- **Strict reading does not reject carriers:** Expected `strict=True` to ensure vendor-usable output; it only controls reader validation. Pass `allow_carrier=False` separately and inspect output attestations plus target-application evidence. See [ApiConvert](../../src/convert/api/ApiConvert.py).
- **Cubic sync paths fail repository naming policy:** Expected generated pages to pass CI; numbered kebab-case page names and lowercase manifest/index stems fail `PTH001`. Import into the PascalCase `Documentation/Reference/` layout, preserve provenance, and repair links before merging. Keep manual docs outside Cubic's `docs/` destination.
- **Enabling a wiki does not initialize its Git repository:** Expected `gh repo edit --enable-wiki` to make `Kit.wiki.git` clonable; GitHub returned repository not found until a first page was saved through the website. Create the first page once, then use the separate wiki Git remote. See [GitHub's wiki instructions](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).
- **Case-only directory changes on macOS:** Expected `Docs/` and `docs/` to be distinct; a case-insensitive filesystem treats them as the same directory. Use `Documentation/` for maintained pages, separate from Cubic's `docs/` path; use an intermediate path for case-only renames and inspect staged paths before deleting old files.
- **Queue configuration is not live enforcement:** Expected the checked-in queue manifest to establish acceptance gating; GitHub rulesets are configured separately and can differ. Read the current rules before enrollment and require `Merge queue acceptance`; report discrepancies without changing protections. See [MergeQueue.md](../../MergeQueue.md).

- **Skipped jobs can expose unevaluated names:** Expected a conditional job name to resolve before a skipped bootstrap was reported; GitHub returned the expression text, causing the aggregate to reject it. Retire one-time bootstrap triggers after installation and use stable names for real gates. See [the repair entry](../Changes/AggregateBootstrap.md).

If you discover a new gotcha, unexpected API behavior, wrong assumption, or undocumented quirk while working on this codebase, you MUST add it to the bullet list above before finishing your task. This is mandatory, not optional. Future you (or a different agent) will thank you. Format: - Short description of the gotcha, what you expected vs what actually happened, and the fix or workaround.
