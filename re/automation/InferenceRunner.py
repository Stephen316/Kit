# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import sys
from pathlib import Path

from InferenceInputs import (
    SPLITS,
    checksum,
    observations,
    read_input,
    read_json_input,
    read_plan,
    sha256,
)
from InferenceSearch import search_fields
from ReaderEvidence import reader_evidence
from Records import canonical, digest, label
from Sessions import read_bounded, write_private

FIELD_KIND = "inference.fields"
GAP_KIND = "inference.paired-gap"
RESCAN_KIND = "inference.rescan"
FORMATS = {"fusion.f3d", "solidworks.sldprt"}
ARCHIVE_LIMIT = 64 * 1024 * 1024


def evaluate_gap(scope, report, report_sha256):
    sources = report["affected_archives"]
    status = report["status"]
    if (
        type(report["inference_version"]) is not int
        or report["inference_version"] != 1
        or report["scope"] != scope
        or status not in {"refuted", "corroborated", "needs-distinguishing-evidence"}
        or not isinstance(sources, dict)
        or not 2 <= len(sources) <= 48
        or set(sources.values()) != FORMATS
    ):
        raise ValueError("invalid paired discovery gap or archive scope")
    if status != "needs-distinguishing-evidence":
        evidence = report.get(
            "counterexamples" if status == "refuted" else "corroboration"
        )
        if not isinstance(evidence, dict) or not evidence:
            raise ValueError("a resolved observation must record its paired evidence")
        outcome = "completed"
        reason = "recorded the paired evidence for the assessed hypothesis"
    else:
        if (
            not isinstance(report.get("requested_grid"), dict)
            or not report["requested_grid"]
        ):
            raise ValueError("an unresolved gap must identify distinguishing work")
        outcome = "waiting_evidence"
        reason = "shared gap needs the pinned distinguishing application grid"
    records = {
        "inference_version": 1,
        "kind": GAP_KIND,
        "scope": scope,
        "source_sha256": sorted(checksum(pin) for pin in sources),
        "report_sha256": checksum(report_sha256),
        "assessment": report,
    }
    return outcome, reason, records


def evaluate(plan, streams, plan_sha256):
    groups = {split: [] for split in SPLITS}
    for observation in observations(plan):
        sample = {
            key: value
            for key, value in observation.items()
            if key not in {"split", "role"}
        }
        sample["data"] = streams[observation["role"]]
        groups[observation["split"]].append(sample)
    result = search_fields(
        groups["discovery"],
        groups["holdout"],
        challenges=groups["challenge"],
        encodings=plan["encodings"],
        tolerance=plan["tolerance"],
        confounds=plan["confounds"],
    )
    return {
        "inference_version": 1,
        "kind": FIELD_KIND,
        "scope": plan["scope"],
        "quantity": plan["quantity"],
        "plan_sha256": checksum(plan_sha256),
        "provenance": plan["provenance"],
        "source_sha256": sorted({item["sha256"] for item in plan["observations"]}),
        "assessment": result,
    }


def scan_archive(scope, assessment, content, source_format):
    source_hash = sha256(content)
    if (
        source_format not in FORMATS
        or assessment.get("inference_version") != 1
        or assessment.get("kind") not in {FIELD_KIND, GAP_KIND}
        or assessment.get("scope") != scope
        or source_hash not in assessment.get("source_sha256", ())
    ):
        raise ValueError("archive is outside the affected inference scope")
    if assessment["kind"] == GAP_KIND:
        sources = assessment["assessment"]["affected_archives"]
        if not isinstance(sources, dict) or sources.get(source_hash) != source_format:
            raise ValueError("rescan source format differs from its paired assessment")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from convert import open_document

    document = open_document(
        content,
        source_format=source_format,
        strict=source_format == "solidworks.sldprt",
        include_brep=False,
        include_tessellation=False,
    )
    neutral = document.to_json(indent=None)
    evidence = reader_evidence(json.loads(neutral))
    issues = sorted({(item["path"], item["reason"]) for item in evidence["unresolved"]})
    return {
        "inference_version": 1,
        "kind": RESCAN_KIND,
        "scope": scope,
        "source_sha256": source_hash,
        "assessment_sha256": digest(assessment),
        "neutral_sha256": sha256(neutral.encode("utf-8")),
        "counts": evidence["counts"],
        "unresolved": [{"path": path, "reason": reason} for path, reason in issues],
    }


def run(session):
    session = session.resolve()
    packet = read_bounded(session / "job.json")
    job = packet["job"]
    inputs = packet["inputs"]
    options = job["options"]
    scope = label(options["scope"])
    outcome = "completed"
    if type(packet["session_version"]) is not int or packet["session_version"] != 1:
        raise ValueError("unsupported inference session version")
    if job["kind"] == FIELD_KIND and set(options) == {"scope"}:
        records = evaluate(*read_plan(session, inputs, scope))
        reason = "recorded the frozen discovery hypotheses and distinguishing evidence"
    elif (
        job["kind"] == GAP_KIND
        and set(options) == {"scope"}
        and set(inputs) == {"plan"}
    ):
        report = read_json_input(session, inputs["plan"])
        outcome, reason, records = evaluate_gap(scope, report, inputs["plan"]["sha256"])
    elif (
        job["kind"] == RESCAN_KIND
        and set(options) == {"scope", "source_format", "source_sha256"}
        and set(inputs) == {"assessment", "source"}
    ):
        completed = read_json_input(session, inputs["assessment"])
        result = completed.get("result")
        if (
            completed.get("session_version") != 1
            or not isinstance(result, dict)
            or result.get("outcome") != "completed"
            or not isinstance(result.get("records"), dict)
        ):
            raise ValueError("rescan requires a completed inference runner result")
        expected = checksum(options["source_sha256"])
        if inputs["source"]["sha256"] != expected:
            raise ValueError("rescan source differs from its scheduled archive pin")
        assessment = result["records"]
        if (
            assessment.get("kind") not in {FIELD_KIND, GAP_KIND}
            or assessment.get("scope") != scope
        ):
            raise ValueError("rescan assessment differs from the scheduled scope")
        if expected in assessment["source_sha256"]:
            records = scan_archive(
                scope,
                assessment,
                read_input(session, inputs["source"], ARCHIVE_LIMIT),
                options["source_format"],
            )
            reason = "rescanned a pinned source in the affected inference scope"
        else:
            records = {
                "inference_version": 1,
                "kind": RESCAN_KIND,
                "scope": scope,
                "source_sha256": expected,
                "assessment_sha256": digest(assessment),
                "status": "no_longer_affected",
            }
            reason = "the updated inference scope does not include this source"
    else:
        raise ValueError("inference session does not match a registered job kind")
    write_private(
        session / "result.json",
        {
            "outcome": outcome,
            "reason": reason,
            "records": records,
        },
    )


def result_schema():
    return {
        "type": "object",
        "required": ["inference_version", "kind", "scope", "source_sha256"],
        "properties": {
            "inference_version": {"type": "integer", "const": 1},
            "kind": {"enum": [FIELD_KIND, GAP_KIND, RESCAN_KIND]},
            "scope": {"type": "string", "minLength": 1, "maxLength": 128},
            "source_sha256": {
                "type": ["array", "string"],
                "items": {"type": "string", "minLength": 64, "maxLength": 64},
                "minLength": 64,
                "maxLength": 64,
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run a pinned deterministic research inference or rescan"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--schema", action="store_true")
    mode.add_argument("session", nargs="?", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.schema:
            print(canonical(result_schema()))
        else:
            run(arguments.session)
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError) as error:
        parser.exit(1, f"inference refused: {error}\n")


if __name__ == "__main__":
    main()
