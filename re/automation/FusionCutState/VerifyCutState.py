# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from dataclasses import replace
from io import BytesIO
import json
from math import isclose
from pathlib import Path
import sys

# Use shared research decoders and receipt helpers from the repository root.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "re/automation"))

from CutHistoryGraph import (
    body_metrics,
    effective_axis,
    extent,
    plane_metrics,
    read_history,
)
from CutHistorySketch import measure_profile
from FusionCutExtentEvidence import REVISION, SPECIFICATION, SPECIFICATION_SHA256
from P04FinalBodyEvidence import compare, compare_mass, fusion_body
from PairedCaptureIntake import GitSnapshot, canonical_digest, require, sha256
from ReadCutRims import read_cut_rims
from convert import open_document, write_document
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Records.NativeAuxiliary import (
    KAuxiliarySchemas,
)

# Digest pins bind only the approved original sources and their independent observations.
CAPTURES = {
    "fusion": (
        "fusion-9cf53a55ea8b",
        "8f0c62e6e12cca0b41e91009f929e5d8d823b8977d6344856e6c56a630e05080",
        "5efff06b0d0fd871623e41a5b17c4fc5fc15e29bedbe7cc0ea4cc2e5be3b3b35",
        "2706.1.17",
        ".f3d",
    ),
    "solidworks": (
        "solidworks-c1986308375a",
        "7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5",
        "05755f809550c9c2c09bbc9fde248291fa4179063d9ca0aa4df6aa5ca5ca0ab4",
        "34.4.1",
        ".SLDPRT",
    ),
}

# The two blind baselines and through-all control are the sole native archive inputs.
CASES = {
    "baseline-a": (
        "e3165726242feb336dd4d5476206375daa052d04f92dd2a748b465d7704f14d1",
        "c1986308375aaf68ebac6f8de61e70a47b9b33535c94271bab2e4bd00504c59d",
        "fa4f88057f761674f6c52797213c957d96721a21d4effd0f509b06a383b31db8",
        "4f689737eb80588a9ba066cd888df0efd0c9c62529af61904701b8b0c41e353c",
        "588099f3062515dcc2b8650f5d699520cdaa91fb3fc798f02b09c9d2ec3a18c1",
    ),
    "baseline-b": (
        "f51c3da580b8e3b49dc391a507f508aac4499af53dc566f4144053313125c22f",
        "2a3c1eea9b9fa29aca158426b0fd810d64d8f5d4f37355a76135b295b9d5a421",
        "1c76e15ce3f4bfcefa6bba79f5208a0238cd74a3dd68275040dc8d7026a042a1",
        "022fec15fa683c92ad8cdd6cf99ce265381d43ae4359d304bceb164e3852e07a",
        "588099f3062515dcc2b8650f5d699520cdaa91fb3fc798f02b09c9d2ec3a18c1",
    ),
    "termination-through-all": (
        "5aacebd98ea8fa101d070572091fbd1b2270b496c2facc7e9125049082b2506f",
        "e1f431f1f21ae294fbd3711503ce386bec4fb4916c3cc83b57c876f1ae283149",
        "663e7bf37d06e10a3f0620321cef78057749a909ec37ef3c7637dfd526efb87d",
        "1122da462ae4f7e9eba5fce6f205cb3f4d399616d91fca51248027afcf6bc641",
        "9a2ed1a80e641846a35ff778f6d34144307304fb35d8891b93a0370611b1228b",
    ),
}


# Receipt custody precedes the requested native input and retains original capture boundaries.
def load_capture(git, recipe, app):
    name, receipt_hash, measurement_hash, build, suffix = CAPTURES[app]
    folder = f"re/automation/PairedCaptures/P04/{name}"
    receipt_path = f"{folder}/receipt.json"
    measurement_path = f"{folder}/measurements.json"
    receipt_raw = git.blob(REVISION, receipt_path)
    measured_raw = git.blob(REVISION, measurement_path)
    require(
        (sha256(receipt_raw), sha256(measured_raw)) == (receipt_hash, measurement_hash),
        "P04 original capture digest differs",
    )
    receipt = git.parse_document(receipt_raw, receipt_path)
    measured = git.parse_document(measured_raw, measurement_path)
    require(
        receipt["recipe_id"] == measured["recipe_id"] == recipe["id"] == "P04"
        and receipt["errors"] == 0
        and not measured["errors"]
        and receipt["measurement_receipt_sha256"] == measurement_hash
        and receipt["measurements"] == "measurements.json"
        and receipt["native_files"] == measured["saves"]
        and measured["exact_application_build"] == build
        and measured["authoring_recipe_sha256"] == canonical_digest(recipe)
        and measured["specifications_sha256"] == SPECIFICATION_SHA256,
        "P04 original receipt and authored recipe disagree",
    )
    origin = git.introduction(REVISION, receipt_path)
    current, introduced = git.tree(REVISION), git.tree(origin)
    require(
        all(
            current[path] == introduced[path]
            for path in (receipt_path, measurement_path)
        ),
        "P04 observation changed since its original introduction",
    )
    return {
        "folder": folder,
        "suffix": suffix,
        "measurement": measured,
        "entries": {row["file"]: row for row in receipt["native_files"]},
        "origin": origin,
        "evidence": {
            "application_build": build,
            "receipt_sha256": receipt_hash,
            "measurement_sha256": measurement_hash,
        },
    }


# No other native roster entry is read by this proof.
def selected_input(git, capture, app, variant, digest):
    name = f"P04-{app}-{variant}{capture['suffix']}"
    row = capture["entries"][name]
    path = f"{capture['folder']}/{name}"
    raw = git.blob(REVISION, path)
    require(
        git.tree(REVISION)[path] == git.tree(capture["origin"])[path]
        and sha256(raw) == digest == row["sha256"]
        and len(raw) == row["size_bytes"]
        and row.get("save_errors", 0) == row.get("save_warnings", 0) == 0,
        "P04 selected archive custody failed",
    )
    return raw, name


# The original measurement phase is kept distinct from qualification.
def native_observations(captures, variant, names):
    fusion = captures["fusion"]["measurement"]["observations"]
    solidworks = captures["solidworks"]["measurement"]
    if variant == "baseline-a":
        phase, observation = "same_process_reopen", fusion["fresh_reopen"]
    elif variant == "baseline-b":
        phase, observation = "before_repeat_export", fusion["unchanged_rebuild"]
    else:
        (row,) = [
            item for item in fusion["variants"] if item["export"] == names["fusion"]
        ]
        phase, observation = "same_process_reopen", row["reopened"]
    require(
        solidworks["authoring_process_id"] != solidworks["reopen_process_id"],
        "P04 original SOLIDWORKS reopen lacks a distinct process",
    )
    return {
        "fusion": (phase, observation),
        "solidworks": (
            "original_separate_process_reopen",
            solidworks["observations"]["reopened_files"][names["solidworks"]],
        ),
    }


# Strict vocabulary absence stays different from successful typed wire decoding.
def strict_inventory(model):
    catalog = {row.Value.ClassGuid.upper() for row in ReadNames()}
    auxiliary = {row.ClassGuid.upper() for row in KAuxiliarySchemas}
    unknown = []
    for segment in model.Segments:
        identifier = segment.Metadata.Header.SegmentId
        for record in segment.Records:
            if not record.IsPrimary:
                continue
            guid = record.Groups[0].ClassGuid.upper()
            if guid not in catalog and (identifier == 0 or guid not in auxiliary):
                unknown.append((identifier, record.ObjectId, guid))
    first = (0, 338, "5662F619-2281-4AD9-93DC-1FCFDA1062E7")
    counts = Counter(guid for _, _, guid in unknown)
    require(
        unknown and unknown[0] == first and len(counts) == 8,
        "P04 strict vocabulary gap differs",
    )
    return {"first_unknown": first, "unknown_class_counts": dict(counts)}


# Retain exactly the named native history and snapshot from each typed package.
def native_parts(raw, model):
    members = {part.Name: part.Payload for part in ReadContainer(raw).Parts}
    (history,) = model.Bodies
    (snapshot,) = model.Snapshots
    return members[history.PartName], members[snapshot.Name]


# The JSON transport and reconstructed package carry all native typed state.
def state_transport(raw, model, pins):
    history_data, snapshot_data = native_parts(raw, model)
    history, snapshot = model.Bodies[0].History, model.Snapshots[0].Snapshot
    require(
        (sha256(history_data), sha256(snapshot_data)) == pins[1:]
        and EmitJournal(history) == history_data
        and EmitGeometry(snapshot) == snapshot_data,
        "P04 original typed geometry did not re-emit exact bytes",
    )
    value = json.dumps(
        EncodeState(model), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    require(sha256(value) == pins[0], "P04 full V2 state digest differs")
    contract = {"version": 2, "model": json.loads(value)}
    rebuilt = CheckContract(contract, "model", 2)
    require(rebuilt == model, "P04 typed JSON omitted native state")
    output = EmitParsed(rebuilt)
    require(
        ReadDocument(output) == model
        and native_parts(output, rebuilt) == (history_data, snapshot_data),
        "P04 reconstructed archive changed typed state or native geometry parts",
    )
    return contract, {
        "state_sha256": sha256(value),
        "state_json_bytes": len(value),
        "history_sha256": sha256(history_data),
        "snapshot_sha256": sha256(snapshot_data),
        "exact_models_and_native_parts": True,
    }


# The current and previous journal bodies each own exactly one integral actor timestamp.
def owner_clock(table, slot):
    (clock,) = [
        value.UnixMicros
        for index in table.LiveSlots
        if isinstance((value := table.Entities[index]), TimeAttrib)
        and StableRef(table, value.Links.OwnerRef) == slot
    ]
    require(
        0 < clock < 2**53 and clock.is_integer(),
        "P04 body actor clock is not an exact integer",
    )
    return int(clock)


# Connect the prior closed body, cap tag and current actor to the actual partial selection route.
def history_ownership(history, roles):
    active, previous, initial = Materialize(history)
    old_table = MakeLiveTable(history, previous.StateId)
    new_table = MakeLiveTable(history, active.StateId)
    (prior,) = ReadPlanarState(history, previous.StateId)
    require(
        not ReadPlanarState(history, initial.StateId),
        "P04 initial journal state carries a body",
    )
    (current_slot,) = [
        slot
        for slot in new_table.LiveSlots
        if isinstance(new_table.Entities[slot], BodyNode)
    ]
    result = read_cut_rims(new_table, current_slot)
    clocks = owner_clock(old_table, prior.BodyRef), owner_clock(new_table, current_slot)
    support = roles.support
    require(
        clocks
        == (
            support.attributes["fusion.history_body_source_clock"],
            support.attributes["fusion.history_body_result_clock"],
        ),
        "P04 typed body actor clocks disagree with the saved target and support",
    )
    require(
        prior.EntityTag
        == result.handle
        == support.attributes["fusion.history_body_handle"]
        and roles.target.query["native_body_id"]
        == support.query["native_body_id"]
        == 309
        and roles.target.query["native_source_id"]
        == support.query["native_source_id"]
        == 277
        and support.query["native_face_name"] == "2"
        and len(prior.FaceRefs) == 6
        and len(prior.VertexRefs) == 8
        and prior.VolumeCm3 == 8.0,
        "P04 Cut target or prior cap identity disagrees with typed journal ownership",
    )
    cap_slots = [
        StableRef(old_table, value.Links.OwnerRef)
        for index in old_table.LiveSlots
        if isinstance((value := old_table.Entities[index]), TagAttrib)
        and any(
            tag.PrimaryId == "2" and tag.OperationIds == (301,) for tag in value.Groups
        )
    ]
    require(
        len(cap_slots) == 1 and cap_slots[0] in prior.FaceRefs,
        "P04 support cap tag does not identify one prior body face",
    )
    (cap_slot,) = cap_slots
    ring = prior.Rings[prior.FaceRefs.index(cap_slot)]
    require(
        {prior.PointsCm[index][2] for index in ring} == {1.0},
        "P04 prior support cap is on the wrong world plane",
    )
    return (
        new_table,
        result,
        {
            "states": [
                (row.StateId, len(row.Versions)) for row in (active, previous, initial)
            ],
            "prior_body_handle": prior.EntityTag,
            "result_body_handle": result.handle,
            "body_clocks": clocks,
            "prior_planar_cap_slot": cap_slot,
            "design_boss": support.query["native_source_id"],
            "design_body": support.query["native_body_id"],
            "support_face_tag": support.query["native_face_name"],
            "feature": roles.cut.feature.id,
            "target_selection": roles.target.id,
            "support_selection": support.id,
        },
    )


# The final Face with an opening must match the original selected cut section on the prior cap.
def verify_openings(body, role, mode):
    boundary = {
        frozenset((point[0], point[1]) for point in pair) for _, pair in role.perimeter
    }
    openings = []
    floors = []
    for face in body.faces:
        for ring in face.rings:
            coords = tuple(
                tuple(value * 10 for value in point) for point in ring.points_cm
            )
            stations = {point[2] for point in coords}
            footprint = {
                frozenset((start[:2], end[:2]))
                for start, end in zip(coords, (*coords[1:], coords[0]), strict=True)
            }
            if ring.signed_area_cm2 < 0.0:
                require(
                    footprint == boundary and len(stations) == 1,
                    "P04 typed opening does not own the selected Cut perimeter",
                )
                (exterior,) = [
                    candidate
                    for candidate in face.rings
                    if candidate.signed_area_cm2 > 0.0
                ]
                openings.append(
                    (
                        next(iter(stations)),
                        face.slot,
                        ring.slot,
                        exterior.slot,
                        round(ring.signed_area_cm2, 9),
                        round(exterior.signed_area_cm2, 9),
                        [item.slot for item in face.rings],
                    )
                )
            elif footprint == boundary and len(stations) == 1:
                floors.extend(stations)
    blind = mode == ("blind", 4.0)
    through = mode == ("through_all", None)
    require(
        (
            blind
            and body.counts == (11, 24, 16)
            and sorted(floors) == [6.0]
            and [row[0] for row in openings] == [10.0]
        )
        or (
            through
            and body.counts == (10, 24, 16)
            and not floors
            and sorted(row[0] for row in openings) == [0.0, 10.0]
        ),
        "P04 saved openings and floor disagree with the claimed Cut termination",
    )
    face_count, edge_count, vertex_count = body.counts
    euler = vertex_count - edge_count + face_count - len(openings)
    require(
        euler == (2 if blind else 0),
        "P04 typed Cut shell has unexpected Euler characteristic",
    )
    return {
        "openings_mm": [
            {
                "z_mm": station,
                "face_slot": face,
                "negative_ring_slot": ring,
                "positive_ring_slot": exterior,
                "negative_area_cm2": area,
                "positive_area_cm2": exterior_area,
                "wire_ring_order": order,
            }
            for station, face, ring, exterior, area, exterior_area, order in sorted(
                openings
            )
        ],
        "floor_planes_mm": floors,
        "euler_characteristic": euler,
    }


# The snapshot contains a closed subtracting tool and separate Boss-sized solids.
def snapshot_geometry(snapshot, active, result, mode):
    indices = tuple(range(len(snapshot.Entities)))
    table = LiveTable(active, snapshot.Entities, indices, indices, indices)
    tool = read_cut_rims(table, 1)
    blind = mode[0] == "blind"
    known = (9,) if blind else (2, 10)
    candidates = [read_cut_rims(table, index) for index in known]
    require(
        snapshot.Header.RootCount == (12 if blind else 13)
        and len(snapshot.Entities) == (427 if blind else 524)
        and tool.counts == (6, 12, 8)
        and tool.bounds_mm == ((15.0, 6.0, 6.0 if blind else 0.0), (25.0, 14.0, 10.0))
        and isclose(
            tool.volume_mm3 + result.volume_mm3, 8000.0, rel_tol=0.0, abs_tol=1e-7
        )
        and all(
            body.counts == (6, 12, 8)
            and body.bounds_mm == result.bounds_mm
            and isclose(body.volume_mm3, 8000.0, rel_tol=0.0, abs_tol=1e-7)
            for body in candidates
        ),
        "P04 typed snapshot tool and Boss-sized sibling geometry disagree",
    )
    return {
        "record_count": len(snapshot.Entities),
        "root_count": snapshot.Header.RootCount,
        "tool_geometry_slot": tool.slot,
        "tool_volume_mm3": round(tool.volume_mm3, 9),
        "boss_sized_geometry_slots": known,
    }


# Volumes from signed boundary integration are compared with archived public and application observations.
def measured_comparison(result, roles, sw_roles, observations, tolerances):
    metrics = {
        "counts": list(result.counts),
        "bounds_mm": list(result.bounds_mm),
        "volume_mm3": result.volume_mm3,
        "center_of_mass_mm": result.centroid_mm,
    }
    comparisons = {
        "fusion_partial": compare(
            metrics, body_metrics(roles.body, "fusion"), tolerances
        ),
        "solidworks_partial": compare(
            metrics, body_metrics(sw_roles.body, "solidworks"), tolerances
        ),
        "fusion_observed": compare(
            metrics, fusion_body(observations["fusion"][1]), tolerances
        ),
    }
    sw = observations["solidworks"][1]
    mass = compare_mass(metrics, sw, tolerances)
    require(
        all(
            value["counts_exact"] and value["within_declared_tolerances"]
            for value in comparisons.values()
        )
        and sw["body_count"] == 1
        and mass["within_declared_tolerances"],
        "P04 typed Cut metrics disagree with the original paired observations",
    )
    for app, history in (("fusion", roles), ("solidworks", sw_roles)):
        for current in (history.base, history.cut):
            _, outcome = measure_profile(
                current, observations[app][1], app, tolerances["length_mm_absolute"]
            )
            require(
                outcome["status"] == "equal",
                "P04 partial selected perimeter disagrees with native measurements",
            )
    return {
        **metrics,
        "volume_mm3": round(metrics["volume_mm3"], 9),
        "center_of_mass_mm": tuple(
            round(value, 9) for value in metrics["center_of_mass_mm"]
        ),
        "matches_both_historical_measures": True,
    }


# Assumed or active Cut termination selections cannot replace the one saved target route.
def check_extent(document, roles, sw_roles):
    mode = extent(roles.cut, roles.parameters, True)
    direction = effective_axis(roles.cut, roles.parameters)
    require(
        mode == extent(sw_roles.cut, sw_roles.parameters, True)
        and direction
        == effective_axis(sw_roles.cut, sw_roles.parameters)
        == (0.0, 0.0, -1.0)
        and plane_metrics(roles.cut.plane) == ((0.0, 0.0, 1.0), 10.0),
        "P04 Cut direction or start and end controls disagree",
    )
    ends = [
        item
        for item in document.selections
        if item.query.get("role") == "extent_reference"
    ]
    if mode[0] == "through_all":
        require(
            len(ends) == 1
            and ends[0].id in roles.cut.feature.selection_ids
            and ends[0].query["native_body_id"] == roles.target.query["native_body_id"]
            and ends[0].query["native_source_id"]
            == roles.target.query["native_source_id"],
            "P04 through-all end does not select the same historical target",
        )
    else:
        require(
            not ends, "P04 blind Cut unexpectedly contains a through-all end selection"
        )
    return mode, {
        "mode": mode[0],
        "distance_mm": mode[1],
        "world_direction": direction,
        "end_selection": ends[0].id if ends else None,
    }


# Negative controls distinguish decodable typed records from the verified geometry and actor claims.
def refusal(operation, expected):
    try:
        operation()
    except ValueError as error:
        require(str(error) == expected, f"Unexpected P04 refusal: {error}")
        return str(error)
    raise ValueError(f"P04 expected refusal: {expected}")


# Keep each wire-valid tamper in memory and verify it through the actual generic parser.
def change_record(history, record, changed):
    entities = tuple(changed if item is record else item for item in history.Entities)
    require(
        sum(item is record for item in history.Entities) == 1,
        "P04 typed mutation did not identify one exact wire record",
    )
    model = replace(history, Entities=entities)
    decoded = ReadJournal(EmitJournal(model))
    require(decoded == model, "P04 tamper did not survive the typed wire")
    return decoded


# Reversing a real opening and shifting the active BODY timestamp must fail the separate proofs.
def negative_controls(history, table, body, roles, mode):
    opening = next(face for face in body.faces if len(face.rings) == 2)
    face = table.Entities[opening.slot]
    require(
        isinstance(face, FaceNode), "P04 opening mutation did not select a typed face"
    )
    reversed_history = change_record(
        history, face, replace(face, Reversed=not face.Reversed)
    )
    reversed_table = MakeLiveTable(reversed_history, table.StateId)
    (timestamp,) = [
        value
        for slot in table.LiveSlots
        if isinstance((value := table.Entities[slot]), TimeAttrib)
        and StableRef(table, value.Links.OwnerRef) == body.slot
    ]
    wrong_actor = change_record(
        history, timestamp, replace(timestamp, UnixMicros=timestamp.UnixMicros + 1.0)
    )
    other = ("through_all", None) if mode[0] == "blind" else ("blind", 4.0)
    wrong_target = replace(
        roles,
        target=replace(
            roles.target, query={**roles.target.query, "native_body_id": 310}
        ),
    )
    return {
        "wire_valid_opening_winding": refusal(
            lambda: read_cut_rims(reversed_table, body.slot),
            "Typed Cut opening is outside its own exterior ring",
        ),
        "wire_valid_body_actor": refusal(
            lambda: history_ownership(wrong_actor, roles),
            "P04 typed body actor clocks disagree with the saved target and support",
        ),
        "wrong_termination_claim": refusal(
            lambda: verify_openings(body, roles.cut, other),
            "P04 saved openings and floor disagree with the claimed Cut termination",
        ),
        "wrong_target_claim": refusal(
            lambda: history_ownership(history, wrong_target),
            "P04 Cut target or prior cap identity disagrees with typed journal ownership",
        ),
    }


# Full typed transport does not grant either a strict source read or a public write route.
def public_guards(raw, document, contract, mode):
    expected = "native or unresolved required semantics cannot be exported: : feature fusion-feature-35-207 kind (native); : feature fusion-feature-35-334 kind (native)"
    if mode[0] == "through_all":
        expected += "; : feature fusion-feature-35-446 length (depthless extrusion reconstruction is unqualified)"
    result = {
        "strict": refusal(
            lambda: open_document(raw, strict=True),
            "Unknown native Fusion entity class",
        )
    }
    for name, item in (
        ("partial_writer", document),
        (
            "typed_state_writer",
            replace(document, metadata={"fusion.native_state": contract}),
        ),
    ):
        output = BytesIO()
        result[name] = refusal(
            lambda: write_document(
                item, output, destination_format="fusion.f3d", allow_carrier=False
            ),
            expected,
        )
        require(not output.getvalue(), "Refused P04 public writer emitted bytes")
    return result


# One report describes only the original typed carrier, ownership and physical result.
def case_report(git, captures, variant, pins, tolerances):
    raw, name = selected_input(git, captures["fusion"], "fusion", variant, pins[0])
    sw_raw, sw_name = selected_input(
        git, captures["solidworks"], "solidworks", variant, pins[1]
    )
    observed = native_observations(
        captures, variant, {"fusion": name, "solidworks": sw_name}
    )
    model = ReadDocument(raw)
    contract, state = state_transport(raw, model, pins[2:])
    document = open_document(raw, strict=False)
    require(
        document.brep is None
        and len(document.brep_payloads) == 1
        and document.brep_payloads[0].data == raw,
        "P04 partial source did not retain the exact archive",
    )
    fusion = read_history(document)
    solidworks = read_history(open_document(sw_raw, strict=False))
    history = model.Bodies[0].History
    table, body, owners = history_ownership(history, fusion)
    mode, control = check_extent(document, fusion, solidworks)
    return {
        "archive_sha256": {"fusion": pins[0], "solidworks": pins[1]},
        "measurement_phase": {app: phase for app, (phase, _) in observed.items()},
        "strict_inventory": strict_inventory(model),
        "ordinary_planar_result_refusal": refusal(
            lambda: ReadPlanarState(history, table.StateId),
            "Fusion planar face requires one owned outer loop",
        ),
        "state": state,
        "journal_owners": owners,
        "cut": control,
        "opening_and_floor": verify_openings(body, fusion.cut, mode),
        "snapshot_geometry": snapshot_geometry(
            model.Snapshots[0].Snapshot, table.StateId, body, mode
        ),
        "body": measured_comparison(body, fusion, solidworks, observed, tolerances),
        "proof_refusals": negative_controls(history, table, body, fusion, mode),
        "public_guards": public_guards(raw, document, contract, mode),
    }


# Original P04 discovery is the only cohort for the typed opening proof.
def report():
    git = GitSnapshot(ROOT)
    data = git.blob(REVISION, SPECIFICATION)
    require(
        sha256(data) == SPECIFICATION_SHA256, "P04 paired specification digest differs"
    )
    spec = git.parse_document(data, SPECIFICATION)
    (recipe,) = [item for item in spec["recipes"] if item["id"] == "P04"]
    require(
        recipe["split"] == "discovery", "P04 proof requires original discovery inputs"
    )
    captures = {app: load_capture(git, recipe, app) for app in CAPTURES}
    cases = {
        variant: case_report(
            git, captures, variant, pins, spec["comparison_tolerances"]
        )
        for variant, pins in CASES.items()
    }
    return {
        "schema": 1,
        "source_revision": REVISION,
        "specification_sha256": SPECIFICATION_SHA256,
        "scope": "typed saved P04 openings evidence",
        "native_receipts": {
            app: capture["evidence"] for app, capture in captures.items()
        },
        "cases": cases,
        "fresh_fusion_reopen_qualification": "unverified",
        "fresh_relation_dimension_and_support_identities": "unverified",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
