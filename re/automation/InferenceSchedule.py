# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import sys
from pathlib import Path

from InferenceInputs import checksum
from InferenceRunner import FIELD_KIND, FORMATS, RESCAN_KIND
from Records import canonical, digest, label, read_record, specification

REQUEST_FIELDS = {
    "inference_version",
    "scope",
    "family",
    "rule_version",
    "tool_version",
    "plan_input",
    "stream_inputs",
    "archives",
    "distinguishing_evidence",
    "depends_on",
}


def build_schedule(request):
    if (
        set(request) - {"grids"} != REQUEST_FIELDS
        or type(request["inference_version"]) is not int
        or request["inference_version"] != 1
    ):
        raise ValueError("inference scheduling request does not match version 1")
    scope = label(request["scope"])
    family = label(request["family"])
    streams = request["stream_inputs"]
    archives = request["archives"]
    evidence = request["distinguishing_evidence"]
    dependencies = request["depends_on"]
    if (
        not isinstance(streams, dict)
        or not 1 <= len(streams) <= 63
        or "plan" in streams
    ):
        raise ValueError("schedule must select 1–63 streams and a distinct plan")
    if not isinstance(archives, dict) or not 1 <= len(archives) <= 63:
        raise ValueError("schedule must identify 1–63 affected archives")
    if not isinstance(evidence, list) or len(evidence) > 63:
        raise ValueError("schedule must bound the distinguishing evidence list")
    if not isinstance(dependencies, list):
        raise ValueError("schedule prerequisite IDs must be a list")
    evidence = sorted({label(item) for item in evidence})
    grids = request.get("grids", [])
    if not isinstance(grids, list) or len(grids) > 63:
        raise ValueError("schedule must bound the experiment grid list")
    grid_jobs, grid_priorities, required_grids = [], [], []
    for grid in grids:
        if not isinstance(grid, dict) or set(grid) != {"job", "class", "installation"}:
            raise ValueError("grid requires a job, class, and installation")
        spec = specification(grid["job"])
        if grid["class"] not in {"requested", "standard"}:
            raise ValueError("unsupported inference grid class")
        installation = label(grid["installation"])
        if installation not in spec["resources"]:
            raise ValueError("inference grid must require its installation")
        if grid["class"] == "requested":
            required_grids.append(spec["id"])
        grid_jobs.append(spec)
        grid_priorities.append(
            {
                "id": spec["id"],
                "family": family,
                "documents": sorted(archives),
                "distinguishing_evidence": evidence,
                "grid": grid["class"],
                "installation": installation,
            }
        )
    version = {
        "rule_version": label(request["rule_version"]),
        "tool_version": label(request["tool_version"]),
    }
    assessment_id = "inference:" + digest(scope)
    jobs = [
        specification(
            {
                **version,
                "id": assessment_id,
                "kind": FIELD_KIND,
                "inputs": {"plan": request["plan_input"], **streams},
                "depends_on": [*dependencies, *required_grids],
                "options": {"scope": scope},
            }
        )
    ]
    priority = [
        {
            "id": assessment_id,
            "family": family,
            "documents": sorted(checksum(item) for item in archives),
            "distinguishing_evidence": evidence,
        }
    ]
    for source_sha256, archive in sorted(archives.items()):
        if (
            not isinstance(archive, dict)
            or set(archive) != {"binding", "format"}
            or archive["format"] not in FORMATS
        ):
            raise ValueError(
                "schedule archive must select a binding and supported format"
            )
        job_id = "rescan:" + digest([scope, source_sha256])
        jobs.append(
            specification(
                {
                    **version,
                    "id": job_id,
                    "kind": RESCAN_KIND,
                    "inputs": {
                        "assessment": {"dependency": assessment_id},
                        "source": label(archive["binding"]),
                    },
                    "depends_on": [assessment_id],
                    "options": {
                        "scope": scope,
                        "source_format": archive["format"],
                        "source_sha256": source_sha256,
                    },
                }
            )
        )
        priority.append(
            {
                "id": job_id,
                "family": family,
                "documents": [source_sha256],
                "distinguishing_evidence": [],
            }
        )
    return {
        "schedule_version": 1,
        "jobs": [*grid_jobs, *jobs],
        "priority": [*grid_priorities, *priority],
    }


def build_batch(request):
    if set(request) != {"requests"}:
        return build_schedule(request)
    requests = request["requests"]
    if not isinstance(requests, list) or not 1 <= len(requests) <= 63:
        raise ValueError("inference batch must have 1–63 scopes")
    batch = {"schedule_version": 1, "jobs": [], "priority": []}
    for item in requests:
        planned = build_schedule(item)
        batch["jobs"].extend(planned["jobs"])
        batch["priority"].extend(planned["priority"])
    return batch


def main():
    parser = argparse.ArgumentParser(
        description="Plan an A03 assessment and affected-file rescans"
    )
    parser.add_argument("request", type=Path)
    arguments = parser.parse_args()
    try:
        print(canonical(build_batch(read_record(arguments.request))))
    except (OSError, ValueError, TypeError, KeyError) as error:
        sys.stderr.write(f"inference schedule refused: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
