<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Observe the native SOLIDWORKS stock process exit

A direct launch of the pinned SOLIDWORKS 34.4.1.1011 executable opened
and rebuilt both stock controls with their expected body and mass values.
The original process handle reported `0xFFFF7003` on exit. The diagnostic
discarded the batch before opening a candidate. The watchdog still drained
the owned process.

An independent stock-only run through the existing P02 COM activation protocol
confirmed exit code zero from a handle opened while the fresh process was live.
The accepted package diagnostics used the same launch and exit observation.
Use a shared oracle lease, an initially empty application session, a unique
identity bound to the registered executable and process creation time, and
retain the native exit code before admitting measured candidates.

The initial failed watchdog SHA-256 is
`d852829ab1db50e8fce44ec4b643c40c3f416bd99c6c530c5ba43ed1a4792da5`.
The independent stock-only report SHA-256 is
`3409cce09efce68b44a237a64f356ac843038e7ba7f7870ead20c44006911e0e`.
[Measured archive diagnostics](../../../../Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md)
