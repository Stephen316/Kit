<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Release concurrency

A branch-wide group might appear to serialize every release. The default queue replaces a pending run when another enters that group. Group GitHub releases by commit SHA. Group PyPI uploads by package version. See [concurrency rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
