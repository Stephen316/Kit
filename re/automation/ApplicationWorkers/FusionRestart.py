import os
import re
import subprocess
import time

from ApplicationProtocol import (
    ACKNOWLEDGEMENT,
    WaitingApplication,
    directory,
    identity,
    record,
    require,
)


def accepted_handoff(config, records, plan_hash):
    handoff = records.get("restart_handoff")
    host = records.get("host")
    require(
        isinstance(handoff, dict)
        and set(handoff)
        == {"installation", "job_id", "reason", "host", "plan_sha256", "at", "owner"}
        and handoff["installation"] == config["installation"]
        and handoff["plan_sha256"] == plan_hash
        and handoff["reason"] == "restart_required"
        and handoff["owner"] == "external_application_owner"
        and isinstance(handoff["job_id"], str)
        and re.fullmatch("[0-9a-f]{32}", handoff["job_id"])
        and type(handoff["at"]) in (int, float)
        and 0 < handoff["at"] <= time.time()
        and isinstance(host, dict)
        and set(host) == {"pid", "started"}
        and type(host["pid"]) is int
        and host["pid"] > 0
        and isinstance(host["started"], str)
        and 0 < len(host["started"]) <= 128
        and handoff["host"] == host,
        "accepted Fusion phase A has no valid restart handoff for this installation and plan",
    )
    return handoff


def wait_for_restart(config, records, plan_hash, deadline):
    handoff = accepted_handoff(config, records, plan_hash)
    host = handoff["host"]
    root = directory(config["endpoint"])
    while time.time() < deadline:
        if os.path.lexists(root / ACKNOWLEDGEMENT):
            raise WaitingApplication("Fusion phase A acknowledgement is still pending")
        try:
            fence = record(root / "fence.json")
        except FileNotFoundError:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                old = identity(host["pid"], timeout=min(5, remaining))
            except subprocess.TimeoutExpired as error:
                raise WaitingApplication(
                    "the prior Fusion process exit could not be verified"
                ) from error
            if old is not None:
                raise WaitingApplication("the prior Fusion process has not exited")
            if time.time() < deadline:
                return
            break
        if fence != handoff:
            raise WaitingApplication(
                "installation is fenced by another application disposition"
            )
        time.sleep(min(0.2, max(0, deadline - time.time())))
    raise WaitingApplication(
        "the required Fusion restart was not observed before the dispatch deadline"
    )
