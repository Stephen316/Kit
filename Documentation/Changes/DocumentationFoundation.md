<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Documentation and wiki foundation

The initial generated wiki export used filenames rejected by repository path policy and included stale steering instructions, broken source links, and incorrect public API and production-acceptance guidance.

The documentation now lives in `Documentation/`, with a getting-started guide, 22 curated reference pages, an import provenance record, this change-entry index, and a mandatory gotchas log. Root agent instructions and the PR template require documentation entries for additions and discovery notes before a task finishes. The GitHub wiki is a separately published reading surface.

Use [the index](../Index.md) to navigate and [the publishing guide](../Publishing.md) to refresh the wiki. The generator remains an optional generation source; its `docs/` sync output must be reviewed and normalized before importing, and must not overwrite maintained documentation.

Verification consists of static formatting and source/link inspection plus remote PR CI. No local tests were run. Publishing documentation does not establish CAD runtime acceptance or a successful PR merge; consult the PR and queue results for those states.
