<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Audit recorded Fusion phase busy time

Pass an increasing past Unix-time window to the [queued Fusion phase audit](../FusionPhaseAudit.md).

```sh
python3 re/automation/ApplicationWorkers/AuditFusionPhases.py \
  --store /private/fusion/ResearchStore \
  --queue-receipt /private/fusion/Queue/Pair.json \
  --busy-window 1730000000 1730003600
```

The audit uses the observed start and end times from each completed, controller-accepted Fusion phase report. The times cover the operation on the application main thread, including the phase's controls and owned-document cleanup. The audit binds them to the pinned plan and healthy controls, the exact app process, the accepted attempt and the dispatch completion. An inconsistent clock order or changed control pin refuses the report.

The report clips the union of the accepted phase intervals to the requested window and gives the recorded busy seconds and fraction as lower bounds. Counts identify intersecting measured phases, missing timing observations, disposable fixtures and uncompleted phases. A settled phase outside the window contributes no seconds. The selected pair cannot measure the time spent on other queued requests, open or failed phases, application startup or separate readiness probes. An installation-wide utilization claim requires coverage of those periods and its runnable queue.

The existing disposable owner restart process case checks that its accepted fixture contributes zero native time, rejects a reversed time window and preserves the ledger bytes. Hosted execution of the changed case and a licensed controller-accepted timing witness remain pending.
