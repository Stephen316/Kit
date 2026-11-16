# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
import json
from pathlib import Path
import sys
from uuid import UUID

# Import the original paired receipt entry point without adding a second capture catalog.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "re/automation"))

from FusionConstrainedPrismEvidence import POSITIVE
from FusionNeutralRectanglePlan import (
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    VARIANTS,
)
from FusionP03BossLogical import read_inverse_source
from InverseP03BossPackage import verify_inverse_package
from PairedCaptureIntake import GitSnapshot, require, sha256
from RectanglePairEvidence import capture
from VerifyFreshBoss import ParseContext

# Only the baseline and independently measured positive width height and depth edits enter.
CASES = VARIANTS["P03"]

# Bound caller context separately from the pinned vendor archive size.
CONTEXT_LIMIT = 1024 * 1024


# Duplicate fields would permit ambiguous save and license metadata in the same context.
def unique_fields(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "Duplicate key in authored save context")
    return result


# Keep fresh synthetic presentation and metadata independent of the source archives.
def synthetic_context():
    shared_time = "2026-07-09T12:30:28"
    contexts = {}
    for index, variant in enumerate(CASES, start=1):
        ids = tuple(
            str(UUID(int=100 * index + slot, version=4)) for slot in range(1, 11)
        )
        contexts[variant] = {
            "saved_path": rf"C:\KitFixture\P03-{variant}.SLDPRT",
            "created_utc": "2026-07-09T12:30:26+00:00",
            "appearance_asset": r"C:\KitFixture\data\graphics\materials\color.p2m",
            "block_id": ids[0],
            "calendar": {"date": "2026-07-09", "utc_offset_minutes": 0},
            "license": {
                "package_code": 4,
                "license_type": 2,
                "visible_sketches": True,
                "terminal_flag": 1,
            },
            "definition": {
                "camera": [0.0, 0.0, 0.0, 1.0],
                "journal": {"name": "", "time": 0, "state": 0},
                "terminal_value": 7850.0,
            },
            "config_exchange": {"id": ids[1], "created": shared_time},
            "object_exchange": {
                "folder": ids[2],
                "planes": ids[3:6],
                "document": ids[6],
                "created": shared_time,
                "index_order": [2, 0, 1],
            },
            "pmi": {"keys": ids[7:10], "created": shared_time},
            "content": {
                "material_name": "Steel",
                "material_id": "fixture-steel",
                "body_visible": True,
            },
        }
    return canonical_context(contexts)


# Stable context serialization provides a reproducible per case input hash.
def canonical_context(context):
    return json.dumps(
        context, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


# Bind the caller supplied bytes before interpreting them as a four case context.
def read_contexts(data, expected):
    require(
        0 < len(data) <= CONTEXT_LIMIT and sha256(data) == expected,
        "Authored save context byte count or SHA-256 differs",
    )
    contexts = json.loads(data, object_pairs_hook=unique_fields)
    require(
        isinstance(contexts, dict) and set(contexts) == set(CASES),
        "Expected an explicit save context for each of the four P03 cases",
    )
    return contexts


# Reconcile an exact source proof and the independently read regenerated package for each case.
def report(context_data, context_digest, mode):
    contexts = read_contexts(context_data, context_digest)
    snapshot = GitSnapshot(ROOT)
    raw_spec = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(raw_spec) == SPECIFICATION_SHA256, "P03 specification digest differs"
    )
    specification = snapshot.parse_document(raw_spec, SPECIFICATION)
    (recipe,) = [row for row in specification["recipes"] if row["id"] == "P03"]
    receipt, assets, observations = capture(snapshot, recipe, "fusion", specification)
    cases = []
    for variant in CASES:
        source_ref = assets[variant]
        require(
            source_ref["sha256"] == POSITIVE[variant],
            "P03 archived asset digest differs",
        )
        phase, witness = observations[variant]
        require(phase == "same_process_reopen", "P03 source observation phase differs")
        context_bytes = canonical_context(contexts[variant])
        context = ParseContext(context_bytes.decode())
        source = read_inverse_source(
            snapshot.blob(REVISION, source_ref["path"]),
            source_ref["sha256"],
            witness,
            configuration="Default",
        )
        cases.append(
            {
                "variant": variant,
                "source_path": source_ref["path"],
                "source_observation_phase": phase,
                "authored_context_sha256": sha256(context_bytes),
                "authored_target": {
                    "saved_path": context.SavedPath,
                    "creation_utc": context.Created.isoformat(),
                    "appearance_material_label": context.Content.MaterialName,
                },
                "source": source.evidence,
                "target": verify_inverse_package(source, context),
            }
        )
    return {
        "schema": 1,
        "scope": "Research only positive XY Fusion P03 into an ordinary SOLIDWORKS first Boss",
        "source_capture_revision": REVISION,
        "source_specification_sha256": SPECIFICATION_SHA256,
        "source_receipt": receipt["receipt"],
        "source_measurements": receipt["measurements"],
        "source_application_build": receipt["application_build"],
        "source_qualification_blockers": receipt["qualification_blockers"],
        "authored_context_sha256": context_digest,
        "authored_context_mode": mode,
        "licensed_target_verification": "unobserved",
        "target_admission": "unqualified",
        "cases": cases,
    }


# The research command emits evidence JSON and keeps every generated native package in memory.
def main():
    parser = ArgumentParser(
        description="Read four exact P03 Fusion sources and verify in-memory SOLIDWORKS research candidates"
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--synthetic-context",
        action="store_true",
        help="use explicitly synthetic archival save inputs",
    )
    input_group.add_argument(
        "--contexts",
        type=str,
        help="four variant keyed ordinary save contexts or - for stdin",
    )
    parser.add_argument(
        "--contexts-sha256", help="required exact SHA-256 for supplied context bytes"
    )
    options = parser.parse_args()
    if options.synthetic_context:
        if options.contexts_sha256 is not None:
            parser.error("--contexts-sha256 is for caller-supplied context only")
        data = synthetic_context()
        expected = sha256(data)
        mode = "synthetic archive context"
    else:
        if options.contexts_sha256 is None:
            parser.error("--contexts requires --contexts-sha256")
        if options.contexts == "-":
            data = sys.stdin.buffer.read(CONTEXT_LIMIT + 1)
        else:
            with Path(options.contexts).open("rb") as stream:
                data = stream.read(CONTEXT_LIMIT + 1)
        expected = options.contexts_sha256
        mode = "caller supplied and digest checked archive context"
    print(
        json.dumps(
            report(data, expected, mode), indent=2, sort_keys=True, allow_nan=False
        )
    )


if __name__ == "__main__":
    main()
