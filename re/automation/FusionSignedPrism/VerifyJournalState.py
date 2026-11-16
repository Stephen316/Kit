# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
import sys

# Use the original pinned P03 inputs and public reader observations.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "re/automation"))

from FusionConstrainedPrismEvidence import POSITIVE, REFUSED, REVISION, refusal
from PairedCaptureIntake import GitSnapshot, require, sha256
from VerifySignedPrism import body_parts
from convert import open_document, write_document
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


# Archive custody precedes decoding any source semantics.
def pinned_source(snapshot, variant, digest):
    path = (
        f"re/automation/PairedCaptures/P03/fusion-8d53584027ff/P03-fusion-{variant}.f3d"
    )
    raw = snapshot.blob(REVISION, path)
    require(sha256(raw) == digest, "P03 journal-state archive digest differs")
    return raw


# Rebuild the actual archived DocumentModel from a JSON transported V2 state.
def transported_state(raw, model):
    encoded = json.dumps(
        EncodeState(model), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    contract = {"version": 2, "model": json.loads(encoded)}
    decoded = CheckContract(contract, "model", 2)
    require(decoded == model, "V2 JSON did not preserve the complete native model")
    regenerated = EmitParsed(decoded)
    require(
        ReadDocument(regenerated) == model,
        "Regenerated native archive changed the typed model",
    )
    original_parts = body_parts(raw, model)
    require(
        body_parts(regenerated, decoded) == original_parts,
        "Reconstructed history or snapshot bytes differ",
    )
    return contract, {
        "state_sha256": sha256(encoded.encode()),
        "json_bytes": len(encoded.encode()),
        "document_model_equal": True,
        "native_archive_readback_equal": True,
        "history_sha256": sha256(original_parts[0]),
        "snapshot_sha256": sha256(original_parts[1]),
        "native_parts_byte_identical": True,
    }


# Reject a malformed lifecycle after its exact typed record fields have decoded.
def malformed_stream(model, history, stream):
    changed = replace(history, Stream=stream)
    body = replace(model.Bodies[0], History=changed)
    return {"version": 2, "model": EncodeState(replace(model, Bodies=(body,)))}


# Corrupt both typed lifecycle and record framing at the actual V2 input boundary.
def malformed_refusals(model, history, contract):
    bad_stream = malformed_stream(
        model, history, replace(history.Stream, ActiveNode=999)
    )
    bad_stream_type = malformed_stream(model, history, None)
    bad_record = json.loads(json.dumps(contract))
    body = bad_record["model"]["fields"]["Bodies"]["tuple"][0]["fields"]
    states = body["History"]["fields"]["States"]["tuple"]
    board = next(
        board["fields"]
        for state in states
        for board in state["fields"]["Boards"]["tuple"]
    )
    del board["OwnerNode"]
    state_index = next(
        index
        for index, state in enumerate(history.States)
        if state.StateId != history.Stream.CurrentStateId
    )
    bad_states = list(history.States)
    bad_states[state_index] = replace(
        bad_states[state_index], StateId=history.Stream.CurrentStateId
    )
    bad_history = replace(history, States=tuple(bad_states))
    body = replace(model.Bodies[0], History=bad_history)
    duplicate_contract = {
        "version": 2,
        "model": EncodeState(replace(model, Bodies=(body,))),
    }
    return {
        "malformed_stream_type": refusal(
            lambda: CheckContract(bad_stream_type, "model", 2),
            "Malformed Fusion semantic-state journal",
        ),
        "active_node_outside_stream": refusal(
            lambda: CheckContract(bad_stream, "model", 2),
            "Fusion BRep history stream reference is outside its integer domain",
        ),
        "missing_bulletin_board_field": refusal(
            lambda: CheckContract(bad_record, "model", 2),
            "Fusion semantic-state record fields disagree",
        ),
        "duplicate_delta_state": refusal(
            lambda: CheckContract(duplicate_contract, "model", 2),
            "Duplicate Fusion delta-state identity",
        ),
    }


# A caller supplied V2 state must still reach the original read-only or reprojection guard.
def writer_refusals(positive, contract, original_model):
    marked = replace(
        positive, metadata={"fusion.native_state": contract, "fusion.read_only": True}
    )
    stripped = replace(positive, metadata={"fusion.native_state": contract})
    v1 = replace(
        positive,
        metadata={"fusion.native_state": {"version": 1, "model": contract["model"]}},
    )
    unwrapped = replace(original_model, Graphics=None, Snapshots=(), Configurations=())
    v1_no_aux = replace(
        positive,
        metadata={
            "fusion.native_state": {"version": 1, "model": EncodeState(unwrapped)}
        },
    )
    result = {
        "marked_direct_writer": refusal(
            lambda: EncodeDocument(marked),
            "Fusion writing requires a qualified authoring or native-state contract",
        ),
    }
    cases = (
        (
            "marked_public_write",
            marked,
            "fusion.f3d does not support the destination",
            AdapterNotFoundError,
        ),
        (
            "marker_stripped_v2_reprojection",
            stripped,
            REFUSED["direction-negative"][1],
            ValueError,
        ),
        (
            "downgraded_v1",
            v1,
            "Native-state version 1 requires the authored profile",
            ValueError,
        ),
        (
            "stripped_auxiliary_v1",
            v1_no_aux,
            "Configuration parts disagree with Design triggers",
            ValueError,
        ),
    )
    for label, document, expected, error_type in cases:
        buffer = BytesIO()
        result[label] = refusal(
            lambda: write_document(
                document,
                buffer,
                destination_format="fusion.f3d",
                allow_carrier=False,
            ),
            expected,
            error_type,
        )
        require(not buffer.getvalue(), "Refused public write emitted bytes")
    return result


# Pin the scoped codec result and the unchanged source admission behavior.
def report():
    snapshot = GitSnapshot(ROOT)
    digest, refusal_message = REFUSED["direction-negative"]
    raw = pinned_source(snapshot, "direction-negative", digest)
    model = ReadDocument(raw)
    (body,) = model.Bodies
    (part,) = model.Snapshots
    history = body.History
    require(
        isinstance(history, JournalModel) and isinstance(part.Snapshot, GeometryState),
        "The pinned source no longer exercises the two generic saved forms",
    )
    contract, custody = transported_state(raw, model)
    positive = open_document(
        pinned_source(snapshot, "baseline-a", POSITIVE["baseline-a"]), strict=True
    )
    yz_digest, yz_refusal = REFUSED["plane-yz"]
    yz = pinned_source(snapshot, "plane-yz", yz_digest)
    return {
        "schema": 1,
        "source_revision": REVISION,
        "source_archive_sha256": digest,
        "retained_state": custody,
        "states": [row.StateId for row in Materialize(history)],
        "journal_shape": {
            "states": len(history.States),
            "boards": sum(len(row.Boards) for row in history.States),
            "changes": sum(
                len(board.Changes) for row in history.States for board in row.Boards
            ),
        },
        "malformed_state_refusals": malformed_refusals(model, history, contract),
        "strict_reader": {
            "positive_body_count": len(positive.bodies),
            "negative": refusal(
                lambda: open_document(raw, strict=True), refusal_message
            ),
            "alternate_datum": refusal(
                lambda: open_document(yz, strict=True), yz_refusal
            ),
        },
        "writer_refusals": writer_refusals(positive, contract, model),
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
