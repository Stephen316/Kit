# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
import json
import math

from Records import canonical

# only a settlement can begin one of these observable waiting intervals
KWaitOutcomes = ("waiting_application", "waiting_evidence", "waiting_ci")


# both reports end a wait at the same kind of controller transition
def wait_transition(event):
    job = event["job_id"]
    action = event["action"]
    if job is None or action not in {"submitted", "invalidated", "claimed", "finished"}:
        return None
    outcome = json.loads(event["detail"])["outcome"] if action == "finished" else None
    return job, action, outcome


# the event cutoff bounds waits whose next controller claim is directly observable
class WaitTiming:
    def __init__(self):
        self.pending = {}
        self.blocks = {outcome: [] for outcome in KWaitOutcomes}
        self.superseded = dict.fromkeys(KWaitOutcomes, 0)
        self.opened = dict.fromkeys(KWaitOutcomes, 0)
        self.last_event = None

    # a new definition, invalidation or unexplained settlement breaks wait attribution
    def observe(self, event):
        self.last_event = (event["id"], event["at"])
        transition = wait_transition(event)
        if transition is None:
            return
        job, action, outcome = transition
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

    # open waits can only age through the last selected controller record
    def open_summary(self, until):
        event_id, boundary = self.last_event or (None, None)
        ages = {outcome: [] for outcome in KWaitOutcomes}
        if boundary is not None:
            for outcome, started in self.pending.values():
                duration = boundary - started
                if duration < 0 or not math.isfinite(duration):
                    raise ValueError("open wait ends before its recorded settlement")
                ages[outcome].append(duration)
        return {
            "last_selected_event": (
                None if event_id is None else {"id": event_id, "at": boundary}
            ),
            "window_seconds_after_last_selected_event": (
                None if boundary is None else until - boundary
            ),
            "settlements": {
                outcome: {
                    "count": len(intervals),
                    "min_seconds": min(intervals, default=None),
                    "max_seconds": max(intervals, default=None),
                    "total_seconds": math.fsum(intervals) if intervals else None,
                }
                for outcome, intervals in ages.items()
            },
        }


# a predecessor replay tracks only waits that were still present when the window began
class CarryInWaitTiming:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.previous_time = None
        self.pending = {}
        self.claimed = {outcome: [] for outcome in KWaitOutcomes}
        self.superseded = dict.fromkeys(KWaitOutcomes, 0)
        self.prefix_identity = sha256()
        self.prefix_count = 0
        self.prefix_end = None
        self.last_event = None

    # carry in attribution requires chronological event evidence across the window boundary
    def observe(self, event):
        instant = event["at"]
        if self.previous_time is not None and instant < self.previous_time:
            raise ValueError("carry-in wait events are not in chronological order")
        self.previous_time = instant
        if instant >= self.end:
            return
        if instant < self.start:
            self.observe_prefix(event)
        else:
            self.observe_selected(event)

    # authenticate the prefix while retaining only the latest standing wait for each job
    def observe_prefix(self, event):
        self.prefix_identity.update(canonical(event).encode("utf-8") + b"\n")
        self.prefix_count += 1
        self.prefix_end = event["id"]
        transition = wait_transition(event)
        if transition is not None:
            job, _, outcome = transition
            self.pending.pop(job, None)
            if outcome in self.claimed:
                self.pending[job] = outcome

    # new settlements may end an inherited wait but only the ordinary report starts them
    def observe_selected(self, event):
        self.last_event = {"id": event["id"], "at": event["at"]}
        transition = wait_transition(event)
        if transition is not None:
            job, action, _ = transition
            outcome = self.pending.pop(job, None)
            if outcome is not None:
                if action == "claimed":
                    self.claimed[outcome].append(event["at"] - self.start)
                else:
                    self.superseded[outcome] += 1

    # clipped carry in measurements end at a claim or at the last selected controller event
    def summary(self):
        boundary = None if self.last_event is None else self.last_event["at"]
        return {
            "prefix": {
                "event_count": self.prefix_count,
                "last_event_id": self.prefix_end,
                "events_sha256": self.prefix_identity.hexdigest(),
            },
            "last_selected_event": self.last_event,
            "window_seconds_after_last_selected_event": (
                None if boundary is None else self.end - boundary
            ),
            "settlements": {
                outcome: self.dispositions(outcome, boundary)
                for outcome in KWaitOutcomes
            },
        }

    # separately count censored waits so their open ages cannot inflate claim timing
    def dispositions(self, outcome, boundary):
        open_count = sum(value == outcome for value in self.pending.values())
        claimed = self.claimed[outcome]
        superseded = self.superseded[outcome]
        open_age = None if not open_count or boundary is None else boundary - self.start
        return {
            "carried_in": len(claimed) + superseded + open_count,
            "next_claim_observed": len(claimed),
            "superseded_before_claim": superseded,
            "no_transition_observed": open_count,
            "next_claim_total_seconds": math.fsum(claimed) if claimed else None,
            "open_age_seconds": open_age,
        }
