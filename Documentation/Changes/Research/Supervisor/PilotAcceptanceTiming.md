<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Measure elapsed time to independent acceptance

In a pinned [private pilot acceptance attestation](PrivatePilotEvidence.md), add an optional `readiness` object to an accepted candidate's case. Supply `ready_at` as the observed Unix time when the job became ready and `evidence_sha256` as the digest of the retained readiness observation for that same document and route. Retain the observation with the underlying baseline and candidate acceptance receipts. Use the attestation's `at` for the independently observed acceptance time.

A case belongs to the report window containing its acceptance. Its readiness may predate the window. The report refuses readiness after acceptance, a missing or malformed evidence pin, conflicting observations for the same case, and timing claims for a candidate recorded as unaccepted.

When the window contains at least one timed acceptance, the acceptance report adds `readiness_to_acceptance`. Each row covers one feature family, format version and conversion direction. It records accepted and timed case counts, minimum, maximum and total elapsed seconds, and coverage as `measured`, `partial` or `unmeasured`. Cases with missing readiness stay in the coverage denominator. With no timed samples, existing reports keep their previous shape. Case and document gain counts continue to come from the independent baseline and candidate attestations.

The report validates the private manifest, source pins and observation shape. The authority that provides each observation retains and verifies its referenced evidence. Forecasts use the measured coverage alongside controller dependency times, interventions and CI observations.

The existing pilot evidence process case exercises duplicate samples, partial and unmeasured routes, readiness before the window, preserved legacy output, and rejection of malformed observations. Hosted verification and the two-week operating pilot remain pending.
