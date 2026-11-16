<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Assess whether a Fusion reset is due

Add `--reset-assessment` to the [lifetime reset observation](FusionResetEvidence.md). The report compares corroborated completions with the configured job limit, which defaults to 50. An optional `--reset-memory-limit-mib` supplies the owner's resident-memory threshold. A sample strictly above that threshold satisfies the memory trigger. A smaller completion count can leave the job threshold unresolved when earlier failed phases have no retained evidence.

When a threshold is established, the report identifies pending controller or endpoint custody. It checks the counted resource, stored running claims, active restart reservations, spool contents, and visible fence, acknowledgement and grant markers. The controller values come from the completion snapshot. Endpoint and exact-process memory observations occur separately.

The report distinguishes `threshold_unestablished`, `due_with_pending_custody` and `due_readiness_unverified`. The signed-in owner still verifies a healthy, empty, idle application and exact quit authority. The assessment makes no changes to the store, queue, availability, application or owner records. The original report is unchanged without the option.

The expanded hosted fixture uses a disposable exact process, real controller records and a retained test spool. It checks the default response, job-count and resident-memory triggers, and pending custody. Hosted verification and a licensed restart-count or pressure witness remain open.
