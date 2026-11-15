# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from Records import label, specification

# Lanes let a requested grid take precedence without changing experiment definitions.
LANES = {None: 1, "requested": 0, "standard": 2}


# Counting canonical identities avoids inflating a priority with duplicate evidence.
def identities(items):
    if not isinstance(items, list) or len(items) > 256:
        raise ValueError("schedule identities must be an array of at most 256 labels")
    return sorted({label(item) for item in items})


# Validating the whole plan first prevents a malformed batch from partially queuing jobs.
def schedule_plan(value):
    if (
        set(value) != {"schedule_version", "jobs", "priority"}
        or type(value["schedule_version"]) is not int
        or value["schedule_version"] != 1
        or not isinstance(value["jobs"], list)
        or not 1 <= len(value["jobs"]) <= 10_000
        or not isinstance(value["priority"], list)
        or len(value["priority"]) != len(value["jobs"])
    ):
        raise ValueError(
            "schedule must use version 1 and bind every job to one priority"
        )
    jobs = {}
    for item in value["jobs"]:
        spec = specification(item)
        if spec["id"] in jobs:
            raise ValueError("schedule contains duplicate job identifiers")
        jobs[spec["id"]] = spec
    metadata = {}
    required = {"id", "family", "documents", "distinguishing_evidence"}
    for item in value["priority"]:
        if not isinstance(item, dict) or set(item) not in (
            required,
            required | {"grid", "installation"},
        ):
            raise ValueError("schedule priority fields do not match version 1")
        job_id = label(item["id"])
        if job_id not in jobs or job_id in metadata:
            raise ValueError("each priority must name a different scheduled job")
        grid = item.get("grid")
        installation = None
        if "grid" in item:
            if grid not in ("requested", "standard"):
                raise ValueError("unknown schedule grid class")
            installation = label(item["installation"])
            if installation not in jobs[job_id]["resources"]:
                raise ValueError("grid job must require the declared installation")
        metadata[job_id] = (
            LANES[grid],
            label(item["family"]),
            identities(item["documents"]),
            identities(item["distinguishing_evidence"]),
            installation,
        )
    return jobs, metadata
