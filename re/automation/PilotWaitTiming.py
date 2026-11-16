# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import math

# only a settlement can begin one of these observable waiting intervals
KWaitOutcomes = ("waiting_application", "waiting_evidence", "waiting_ci")


# the event cutoff bounds waits whose next controller claim is directly observable
class WaitTiming:
    def __init__(self):
        self.pending = {}
        self.blocks = {outcome: [] for outcome in KWaitOutcomes}
        self.superseded = dict.fromkeys(KWaitOutcomes, 0)
        self.opened = dict.fromkeys(KWaitOutcomes, 0)

    # a new definition, invalidation or unexplained settlement breaks wait attribution
    def observe(self, event):
        job = event["job_id"]
        action = event["action"]
        if job is None or action not in {
            "submitted",
            "invalidated",
            "claimed",
            "finished",
        }:
            return
        at = event["at"]
        previous = self.pending.pop(job, None)
        if previous is not None:
            reason, started = previous
            duration = at - started
            if duration < 0 or not math.isfinite(duration):
                raise ValueError("wait timing events are not in chronological order")
            if action == "claimed":
                self.blocks[reason].append(duration)
            else:
                self.superseded[reason] += 1
        if action == "finished":
            outcome = json.loads(event["detail"])["outcome"]
            if outcome in self.opened:
                self.opened[outcome] += 1
                self.pending[job] = outcome, at

    # open or superseded intervals stay outside the measured duration aggregates
    def summary(self):
        result = {}
        for outcome, intervals in self.blocks.items():
            superseded = self.superseded[outcome]
            opened = self.opened[outcome]
            result[outcome] = {
                "started": opened,
                "next_claim_observed": len(intervals),
                "superseded_before_claim": superseded,
                "no_next_claim_observed": opened - len(intervals) - superseded,
                "min_seconds": min(intervals, default=None),
                "max_seconds": max(intervals, default=None),
                "total_seconds": math.fsum(intervals) if intervals else None,
            }
        return result
