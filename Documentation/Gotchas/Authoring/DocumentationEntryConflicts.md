<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Documentation entry conflicts

Adding unrelated records might appear safe when each record is a separate bullet.
Git can report a conflict when two branches append bullets at the same location.
This affected the gotcha log and change index in the [conflict audit](../../Changes/IndependentDocumentationEntries.md#conflict-audit).
Add each record in a separate file.
Use a specific filename to avoid an add/add conflict with another change.
