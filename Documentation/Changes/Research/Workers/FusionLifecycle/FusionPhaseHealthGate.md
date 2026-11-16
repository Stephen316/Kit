<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Require healthy controls for a Fusion phase

The [Fusion application worker](../LocalApplicationDispatch.md) verifies the exact output roster, sealed measurements, save identities and owned process for each completed discovery or scope phase. Both control observations must name the same pinned input and report a successful recompute. The worker also checks the accepted Phase A controls before a repeat phase can use those files.

A control failure rejects the entire phase result before the controller accepts any recipe archive. Phase B still waits for accepted Phase A evidence. The copied private files and the original [acceptance-required spool](../ApplicationAcceptance.md) remain under the installation owner's custody. Reports explicitly marked as disposable fixtures are refused at the same boundary.

The hosted process case uses the real A03 controller, supervisor, queue and Fusion worker with a disposable host. It exercises a hash-matching reply with a failed post-phase control and a healthy-shaped fixture. Both cases require zero accepted artifacts and preserved spool bytes. Hosted execution and licensed verification are pending. This applies to the recipes within one phase. Multi-job batch invalidation and scheduled reset remain open.
