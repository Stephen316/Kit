<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Analysis on a snapshot base

A PR into a snapshot branch might appear to run the same checks as a PR into `main`. In [PR #73](https://github.com/TryUniCAD/Kit/pull/73), two expected analysis jobs had no runs on the snapshot base. The aggregate remained pending. Check expected job names as well as reported results after a base change. Revalidate the current head against the intended target. Do not remove missing jobs from the required inventory.
