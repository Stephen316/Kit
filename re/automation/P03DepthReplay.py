"""Index the Fusion P03 depth proof and select affected A03 archive rescans."""

import argparse
import json
from pathlib import Path

from FieldSearch import ENCODINGS, patterns
from P03DepthSearch import CONTROLS, RECEIPT_SHA256, REVISION, ROLES
from PairedCaptureIntake import require, sha256
from Records import canonical, digest, read_record

PROOF_SHA256 = "beffd2fe7ad6fa085973ea65ab273b396083f74cf04f0ca6520bdb449ca44ac5"
MODELS = {model.label: model for model in ENCODINGS}


def limited_read(path, limit):
    with path.open("rb") as source:
        content = source.read(limit + 1)
    require(len(content) <= limit, "replay input exceeds its byte limit")
    return content


def prior_proof(content):
    require(
        sha256(content) == PROOF_SHA256, "P03 field report differs from the exact prior proof"
    )
    proof = json.loads(content)
    require(
        proof["schema"] == 1
        and proof["claim"] == "known_field_search_commissioning"
        and proof["qualification"] is False
        and proof["recipe"] == "P03"
        and proof["split"] == "discovery"
        and proof["source_revision"] == REVISION
        and proof["receipt"]["sha256"] == RECEIPT_SHA256
        and set(proof["samples"]) == set(CONTROLS)
        and set(proof["search"]) == set(ROLES),
        "prior proof is outside the Fusion P03 discovery workload",
    )
    return proof


def indexed_fields(proof):
    fields = {}
    for role, scan in proof["search"].items():
        (candidate,) = scan["candidates"]
        require(
            candidate["corroborates_existing_reader"], "prior has no confirmed field location"
        )
        fields[role] = {
            "retained": candidate["encoding"],
            "alignments": candidate["alignments"],
            "rejected": {row["encoding"]: row for row in scan["rejected"]},
        }
    return fields


def replay_plan(proof, role, encoding):
    fields = indexed_fields(proof)
    field = fields[role]
    prior = MODELS[field["retained"]]
    proposed = MODELS[encoding]
    previous_counterexample = field["rejected"].get(encoding, {})
    known_contradictions = (
        previous_counterexample["examples"]
        if previous_counterexample.get("reason") == "predicted_bytes_absent"
        else ()
    )
    retained = proof["search"][role]["candidates"][0]["samples"]
    observations = {}
    depth_counts = {}
    for sample in proof["samples"].values():
        depth = sample["search_grid_depth_mm"]
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    for variant in CONTROLS:
        sample = proof["samples"][variant]
        depth = sample["search_grid_depth_mm"]
        before = patterns(prior, depth)
        after = patterns(proposed, depth)
        prior_bytes = bytes.fromhex(retained[variant]["bytes_hex"])
        observations[variant] = {
            "source": sample["source"],
            "record": sample["records"][role],
            "prior_observation": retained[variant],
            "measurement_phase": sample["observation_phase"],
            "measured_signed_depth_mm": sample["measured_signed_depth_mm"],
            "search_grid_depth_mm": depth,
            "equal_grid_controls": depth_counts[depth],
            "prior_counterexample": variant in known_contradictions,
            "previous_patterns": sorted(value.hex() for value in before),
            "proposed_patterns": sorted(value.hex() for value in after),
            "proposed_matches_prior_bytes": prior_bytes[: proposed.width] in after,
            "decision": (
                "reuse_prior" if before == after else "replay" if after else "unrepresentable"
            ),
        }
    ranked = sorted(
        (variant for variant, row in observations.items() if row["decision"] == "replay"),
        key=lambda variant: (
            not observations[variant]["prior_counterexample"],
            observations[variant]["equal_grid_controls"],
            variant,
        ),
    )
    return {
        "schema": 1,
        "scope": "fusion-p03-discovery",
        "qualification": False,
        "proof_sha256": PROOF_SHA256,
        "source_revision": proof["source_revision"],
        "application_build": proof["application_build"],
        "receipt": proof["receipt"],
        "measurements": proof["measurements"],
        "specification_sha256": proof["specification_sha256"],
        "fields": fields,
        "change": {"role": role, "previous": prior.label, "proposed": encoding},
        "saves": observations,
        "ranked_replay": ranked,
    }


def select_schedule(request, plan):
    from InferenceSchedule import build_schedule

    rows = plan["saves"]
    all_sources = {row["source"]["sha256"] for row in rows.values()}
    archives = request["archives"]
    require(
        request["scope"] == "p03-blind-boss.fusion"
        and set(archives) == all_sources
        and all(row["format"] == "fusion.f3d" for row in archives.values())
        and set(request["stream_inputs"]) == {f"p03-fusion-{variant}" for variant in rows}
        and not request.get("grids"),
        "rescan request must use the full pinned Fusion P03 assessment roster",
    )
    variants = plan["ranked_replay"]
    if not variants:
        return None
    selected = {rows[variant]["source"]["sha256"]: rows[variant] for variant in variants}
    # Keep the assessment and its exact bound evidence intact. Fresh rescan IDs
    # leave already accepted ordinary rescans available for the unchanged saves.
    schedule = build_schedule(request)
    assessment, *rescans = schedule["jobs"]
    priorities = {row["id"]: row for row in schedule["priority"]}
    jobs = {job["options"]["source_sha256"]: job for job in rescans}
    schedule["jobs"] = [assessment]
    schedule["priority"] = [priorities[assessment["id"]]]
    for checksum, row in selected.items():
        job = jobs[checksum]
        priority = priorities[job["id"]]
        selection = digest([plan["proof_sha256"], plan["change"], row])
        job_id = f"p03-depth-rescan:{selection}"
        evidence = [
            name
            for name, available in (
                ("archived-counterexample", row["prior_counterexample"]),
                ("distinct-depth-control", row["equal_grid_controls"] == 1),
            )
            if available
        ]
        schedule["jobs"].append({**job, "id": job_id})
        schedule["priority"].append(
            {**priority, "id": job_id, "distinguishing_evidence": evidence}
        )
    return schedule


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proof", type=Path)
    parser.add_argument("role", choices=ROLES)
    parser.add_argument("encoding", choices=MODELS, metavar="ENCODING")
    parser.add_argument("--schedule-request", type=Path)
    args = parser.parse_args()
    try:
        content = limited_read(args.proof, 1024 * 1024)
        plan = replay_plan(prior_proof(content), args.role, args.encoding)
        output = (
            select_schedule(read_record(args.schedule_request), plan)
            if args.schedule_request is not None
            else plan
        )
        print(canonical(output))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"P03 depth replay refused: {error}\n")


if __name__ == "__main__":
    main()
