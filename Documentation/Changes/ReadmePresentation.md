<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# README presentation

The [README](../../README.md) now places a direct GitHub wiki link and the Greptile badge below the project introduction, removes the legacy Parashell banner, and embeds a linked star history graph for `TryUniCAD/Kit`.

The badge uses Greptile's hosted SVG and links to its website with the supplied open-source badge campaign parameters.

The graph uses the hosted Star History SVG endpoint in date mode. Clicking it opens the interactive chart. No repository credentials or setup are needed. Image availability and freshness depend on Star History and GitHub's image cache; the graph is not stored in this repository.

## Verification

The wiki URL returned HTTP 200. The chart endpoint returned an SVG with the `tryunicad/kit` series and date and GitHub-star axes. The embed follows the provider's [README documentation](https://www.star-history.com/blog/how-to-use-github-star-history/#how-to-embed-the-chart-in-your-readme).

Markdown formatting and diff inspection are performed locally. Tests run only in remote PR CI; merge-group acceptance remains deferred until authorized queue enrollment.
