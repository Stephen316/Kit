# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import os

from ApplicationProtocol import ACKNOWLEDGEMENT, directory


# an existing claim or restart reservation requires the current owner to drain its work
def controller_activity(connection, resource, available):
    claim = connection.execute(
        "SELECT 1 FROM jobs JOIN job_resources ON jobs.id=job_resources.job_id "
        "WHERE job_resources.resource=? AND jobs.state='running' LIMIT 1",
        (resource,),
    ).fetchone()
    has_pairs = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fusion_restart_pairs'"
    ).fetchone()
    restart = None
    if has_pairs is not None:
        restart = connection.execute(
            "SELECT 1 FROM fusion_restart_pairs WHERE resource=? "
            "AND a_receipt IS NOT NULL AND final_evidence IS NULL LIMIT 1",
            (resource,),
        ).fetchone()
    return {
        "resource_available": available,
        "running_claim_recorded": claim is not None,
        "restart_reservation_recorded": restart is not None,
    }


# filesystem observations cannot certify application readiness without the native owner
def endpoint_activity(config):
    try:
        root = directory(config["endpoint"])
        jobs = directory(root / "jobs")
    except FileNotFoundError:
        return {"status": "unavailable"}
    return {
        "status": "observed",
        "spool_retained": any(jobs.iterdir()),
        "owner_marker_present": any(
            os.path.lexists(root / name)
            for name in ("fence.json", ACKNOWLEDGEMENT, "grant.json")
        ),
    }


# only the explicit operator threshold can turn a resident sample into a reset trigger
def assess_memory(resident_bytes, limit_mib):
    if limit_mib is None:
        return {"status": "unconfigured"}
    limit = limit_mib * 1024 * 1024
    status = "unmeasured"
    if resident_bytes is not None:
        status = "over_limit" if resident_bytes > limit else "within_limit"
    return {"status": status, "limit_mib": limit_mib}


# threshold evidence can guide the owner while restart authority stays with the native lifecycle
def reset_assessment(report, controller, config, memory_limit_mib):
    memory = assess_memory(report["native_resident_bytes"], memory_limit_mib)
    endpoint = endpoint_activity(config)
    reasons = []
    if report["verified_count_reaches_limit"]:
        reasons.append("verified_job_limit")
    if memory["status"] == "over_limit":
        reasons.append("resident_memory_limit")
    disposition = "threshold_unestablished"
    if reasons:
        blocked = (
            not controller["resource_available"]
            or controller["running_claim_recorded"]
            or controller["restart_reservation_recorded"]
            or endpoint["status"] != "observed"
            or endpoint["spool_retained"]
            or endpoint["owner_marker_present"]
        )
        disposition = (
            "due_with_pending_custody" if blocked else "due_readiness_unverified"
        )
    return {
        "status": disposition,
        "thresholds_met": reasons,
        "resident_memory": memory,
        "controller_observation": controller,
        "endpoint_observation": endpoint,
        "physical_readiness": "unverified",
    }
