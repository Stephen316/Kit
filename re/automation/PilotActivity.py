import argparse
import hashlib
import json
import math
import sqlite3
import sys
import time
from pathlib import Path

from EventHistory import event_window
from PilotDependencyTiming import dependency_timing
from PilotWaitTiming import WaitTiming
from Records import canonical

ACTIONS = {
    "submitted": "submission_events",
    "claimed": "claims",
    "expired": "expired_claims",
    "invalidated": "invalidations",
    "supervisor_owner_rotated": "owner_rotations",
    "resource_recovery_required": "resource_recovery_required",
    "application_timeout_hold": "application_timeout_holds",
    "application_timeout_rearmed": "application_timeout_rearms",
    "application_archived_fusion_probe_retry": "archived_fusion_retry_requests",
}
OUTCOMES = (
    "completed",
    "retry",
    "rejected",
    "waiting_evidence",
    "waiting_ci",
    "waiting_application",
)


def activity_tally():
    return {
        **dict.fromkeys(ACTIONS.values(), 0),
        "settled_outcomes": dict.fromkeys(OUTCOMES, 0),
        "resource_transitions": {"available": 0, "unavailable": 0},
        "exhausted_settlement_retries": 0,
        "provisional_completions": 0,
        "other_events": 0,
    }


def tally_event(activity, event):
    action = event["action"]
    if action in ACTIONS:
        activity[ACTIONS[action]] += 1
    elif action == "finished":
        detail = json.loads(event["detail"])
        outcome = detail["outcome"]
        if outcome not in OUTCOMES:
            raise ValueError("a settlement event has an unsupported outcome")
        activity["settled_outcomes"][outcome] += 1
        if outcome == "completed" and detail.get("waiting_ci_inputs"):
            activity["provisional_completions"] += 1
        activity["exhausted_settlement_retries"] += (
            outcome == "retry" and detail["state"] == "failed"
        )
    elif action == "resource":
        available = json.loads(event["detail"])["available"]
        if type(available) is not bool:
            raise ValueError("a resource event has invalid availability evidence")
        counter = "available" if available else "unavailable"
        activity["resource_transitions"][counter] += 1
    else:
        activity["other_events"] += 1


def operating_report(
    store,
    start,
    end,
    after,
    through,
    *,
    time_dependencies=False,
    time_waits=False,
    time_open_waits=False,
):
    if not (0 <= start < end <= time.time() and math.isfinite(end)):
        raise ValueError("request an increasing past Unix-time window")
    cursor, scanned, selected = after, 0, 0
    activity = activity_tally()
    identity = hashlib.sha256()
    receipts = {}
    waits = WaitTiming() if time_waits or time_open_waits else None
    while True:
        page = event_window(store, None, cursor, through)
        through = page["through"]
        for event in page["events"]:
            instant = event["at"]
            if not math.isfinite(instant):
                raise ValueError("a controller event has an invalid timestamp")
            scanned += 1
            if start <= instant < end:
                identity.update(canonical(event).encode("utf-8") + b"\n")
                tally_event(activity, event)
                if waits is not None:
                    waits.observe(event)
                if time_dependencies and event["action"] == "finished":
                    detail = json.loads(event["detail"])
                    if detail["outcome"] == "completed" and not detail.get(
                        "waiting_ci_inputs"
                    ):
                        if detail["receipt"] in receipts:
                            raise ValueError(
                                "duplicate accepted dependency timing event"
                            )
                        receipts[detail["receipt"]] = event
                selected += 1
        cursor = page["next_after"]
        if cursor is None:
            break
    report = {
        "report_version": 1,
        "scope": "a03_controller_pre_pilot_activity",
        "from_unix_seconds": start,
        "until_unix_seconds": end,
        "window_seconds": end - start,
        "after_event_id": after,
        "through_event_id": through,
        "scanned_event_count": scanned,
        "selected_event_count": selected,
        "selected_events_sha256": identity.hexdigest(),
        "activity": activity,
    }
    if time_dependencies:
        report["dependency_timing"] = dependency_timing(store, receipts)
    if waits is not None:
        if time_waits:
            report["settlement_to_next_claim"] = waits.summary()
        if time_open_waits:
            report["open_wait_to_last_event"] = waits.open_summary(end)
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Read a reproducible A03 pre-pilot activity window"
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--from-unix", type=float, required=True)
    parser.add_argument("--until-unix", type=float, required=True)
    parser.add_argument("--after", type=int, default=0)
    parser.add_argument("--through", type=int)
    parser.add_argument("--dependency-timing", action="store_true")
    parser.add_argument("--wait-timing", action="store_true")
    parser.add_argument("--open-wait-timing", action="store_true")
    args = parser.parse_args()
    try:
        output = operating_report(
            args.store,
            args.from_unix,
            args.until_unix,
            args.after,
            args.through,
            time_dependencies=args.dependency_timing,
            time_waits=args.wait_timing,
            time_open_waits=args.open_wait_timing,
        )
        print(canonical(output))
        return 0
    except ValueError as error:
        print(f"controller activity report refused: {error}", file=sys.stderr)
        return 1
    except (OSError, KeyError, TypeError, sqlite3.Error) as error:
        print(
            f"controller activity report could not read event evidence ({type(error).__name__})",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
