<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# README presentation

## Change

The [README](../../README.md) places a GitHub wiki link and the review-service badge below the project introduction.
It removes the legacy Parashell banner and adds a linked star history graph for `TryUniCAD/Kit`.

The badge uses the review service's hosted SVG and links to its website with the supplied open-source badge campaign parameters.

The graph uses the hosted Star History SVG endpoint in date mode.
Select the graph to open the interactive chart.
No repository credentials or setup are needed.
Image availability and freshness depend on Star History and GitHub's image cache.
The repository does not store the graph.

## Verification

At the original review, the wiki URL returned HTTP 200.
The chart endpoint returned an SVG with the `tryunicad/kit` series and date and GitHub-star axes.
The embed follows the provider's [README documentation](https://www.star-history.com/blog/how-to-use-github-star-history/#how-to-embed-the-chart-in-your-readme).

Markdown formatting and diff inspection are permitted locally.
Tests run only in remote PR CI.
Merge-group acceptance remains deferred until authorized queue enrollment.
