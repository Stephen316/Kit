<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Ignored release directories

A `Release/` folder under maintained documentation might appear unrelated to build output.
The [repository ignore rules](../../../.gitignore) match that directory name at any depth.
Git and formatters that read the ignore rules can omit new documentation in that directory.

Check a missing path with `git check-ignore -v`.
Use a specific source directory name such as `Packaging/`.
