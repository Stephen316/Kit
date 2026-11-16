<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Retain native phase entry through a timeout

The Fusion counterpart seals `phase-native-entry.json` in its existing private request spool after phase admission and immediately before invoking the capture tool. It contains the exact admitted request, full process lifetime identity and observed time. A phase that is already fenced, cancelled or past its deadline cannot create the observation.

The [queued phase audit](../FusionPhaseAudit.md) exposes a `native_entry` observation for a timed-out phase when the retained marker, original request digest, pinned healthy probe and process identity agree. The same observation can survive the transition from a running request to its expired reply. A previous spool without this marker keeps its existing audit output.

The observation records entry to the native capture boundary. Completion, accepted artifacts and native editability still require their existing evidence. Spool fences, cancellation and resource reactivation keep their existing ownership. A complete lifetime job count also needs a custody policy for earlier failed phases and a safe restart path between ordinary jobs.

The hosted disposable counterpart case exercises the real worker, timeout ledger and read-only audit. It checks both spool states and refusal of a changed process birth value. Hosted verification remains pending.
