<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Documentation and wiki foundation

## Problem

The initial generated wiki export used filenames that repository policy rejected.
It also contained stale workflow guidance, broken links, and incorrect API and acceptance claims.

## Change

The foundation established `Documentation/` as the maintained source.
It added a getting-started guide, 22 curated reference pages, and an import provenance record.
It also added the change index and mandatory gotchas log.
Agent instructions and the PR template require documentation for repository additions.
The GitHub wiki remains a separate publication surface.

## Use

Use [the index](../Index.md) for navigation.
Use [the publishing procedure](../Publishing.md) for reviewed wiki updates.
Review and normalize generated `docs/` content before importing it.
Do not overwrite maintained pages with an unchecked export.

## Recorded verification

The foundation record identifies static formatting and source/link inspection.
It assigns repository validation to remote PR CI.
No local tests ran.
Documentation publication does not establish CAD acceptance or PR merge status.
See the later [documentation expansion](DocumentationStandards.md) for the current information structure.
