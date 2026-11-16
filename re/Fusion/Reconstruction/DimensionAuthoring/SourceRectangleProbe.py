# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Generate private Fusion candidates from exact P01 SOLIDWORKS discovery bindings."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from subprocess import check_output

import ProbeOrigin
import ProbeOwnedDims

from FusionNeutralRectanglePlan import report as source_report
from PairedCaptureIntake import GitSnapshot, require, sha256
from PairedPerimeters import edge_gap, match_perimeters
from RectanglePairEvidence import load_public
from RectanglePairSketch import world

from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Projection.NativeIndex import MakeIndex
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.Sketches.Geometric.GeomRuleKinds import GetGeomRuleKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry

TOLERANCE_MM = 1e-6


# the independent reader retains the original native edge identities through the neutral scope
def source_edges(case):
    _, document = load_public(
        GitSnapshot(ProbeOrigin.ROOT), case["source"], "solidworks"
    )
    (sketch,) = document.sketches
    (plane,) = tuple(
        row for row in document.support_planes if row.id == sketch.support_plane_id
    )
    require(
        sketch.id == case["source"]["sketch_id"] and not document.bodies,
        "Wrong P01 source sketch",
    )
    (profile,) = sketch.closed_profile_entity_ids
    require(
        tuple(profile) == tuple(case["perimeter"]["source_loop"]), "Source loop changed"
    )
    entities = {row.id: row for row in sketch.entities}
    edges = []
    for item in profile:
        geometry = entities[item].geometry
        require(
            isinstance(geometry, LineGeometry),
            "P01 source profile must contain only lines",
        )
        edges.append(
            (
                item,
                (
                    world(plane.transform, geometry.start),
                    world(plane.transform, geometry.end),
                ),
            )
        )
    return edges


# the placed datum and component must certify the exact principal XY world frame
def candidate_frame(graph, sketch):
    fields = graph.Fields[sketch]
    CheckIdentity(graph.FindOne("ComponentInstance")["transform"])
    CheckIdentity(fields["occurrenceTransform"])
    feature = graph.Fields[fields["rDcNode"].ObjectId]
    matrix = graph.Fields[feature["rSketchPlaneMatrix"].ObjectId]
    CheckIdentity(matrix["matrix3d"])
    (reference,) = SeriesItems(matrix["dataRefs"])
    recipe = graph.Fields[graph.Fields[reference.ObjectId]["rRecipe"].ObjectId]
    datum = recipe["m_entityId"]
    plane = ObjectFields(graph.Fields[datum]["plane"])
    require(
        feature["rSketch"].ObjectId == sketch
        and datum in graph.Names["WorkPlane"]
        and matrix["refType"] == 2
        and matrix["isZFlip"] is False
        and plane["normalReversed"] is False
        and PointCoords(plane["origin"]) == (0.0, 0.0, 0.0)
        and PointCoords(plane["uAxis"]) == (1.0, 0.0, 0.0)
        and PointCoords(plane["vAxis"]) == (0.0, 1.0, 0.0),
        "Generated sketch does not resolve to its principal XY datum",
    )
    return {"sketch": sketch, "feature": fields["rDcNode"].ObjectId, "datum": datum}


# the generated archive must independently resolve its sketch lines and directed observers
def candidate_edges(content, witness):
    graph = MakeIndex(ReadDocument(content))
    (sketch,) = graph.Names["MSketch"]
    require(
        sketch == witness["anchor"]["owner"],
        "Decoded sketch differs from the exact anchor owner",
    )
    frame = candidate_frame(graph, sketch)
    points = {
        identity: tuple(
            value * 10.0 for value in PointCoords(graph.Fields[identity]["point"])
        )
        for identity in graph.Names["Point3D"]
    }
    edges, incidence = [], Counter()
    for identity in graph.Names["Line3D"]:
        fields = graph.Fields[identity]
        require(
            fields["rParent"].ObjectId == sketch,
            "A generated line belongs to a different sketch",
        )
        ends = tuple(fields[field].ObjectId for field in ("rStartPoint", "rEndPoint"))
        require(len(set(ends)) == 2, "A generated line collapsed at one point")
        incidence.update(ends)
        edges.append((identity, tuple(points[end] for end in ends)))
    require(
        set(incidence) == set(points) - {witness["anchor"]["origin"]["id"]}
        and len(incidence) == 4
        and all(count == 2 for count in incidence.values()),
        "Generated perimeter does not use one closed loop on four shared vertices",
    )
    return edges, points, frame, sorted(incidence.items())


# the target dimensions must bind the same physical sides as the two measured source drivers
def verify_drivers(case, sizes, proof, points):
    anchor = proof["anchor_evidence"]
    inventory = proof["direct_driver_inventory"]["parameters"]
    require(
        set(inventory) == set(ProbeOwnedDims.NAMES),
        "Unexpected generated driving parameters",
    )
    for name, length, row in zip(
        ProbeOwnedDims.NAMES, sizes, anchor["dimensions"], strict=True
    ):
        parameter = inventory[name]
        first, second = case["dimensions"][name]["source"]["operands_world_mm"]
        require(
            math.isclose(
                parameter["value_cm"] * 10, length, rel_tol=0, abs_tol=TOLERANCE_MM
            )
            and parameter["dimension_id"] == row["id"]
            and edge_gap(
                tuple(points[item] for item in row["arguments"]), (first, second)
            )
            <= TOLERANCE_MM,
            f"Generated driver {name} differs from the measured source side",
        )


# typed target rules must select the same four physical edges as the source axis bindings
def verify_axes(content, case, match, sketch):
    _, rules, _, _ = ProbeOrigin.native_records(content)
    observed = {}
    for rule in rules.values():
        if rule.CodeValue == 1:
            continue
        (line,) = rule.Arguments
        require(
            rule.OwnerId == sketch and line not in observed,
            "Conflicting generated axis relation",
        )
        observed[line] = GetGeomRuleKind(rule.CodeValue, (GeometryKind.KLine,))
    links = dict(match["matched_links"])
    require(
        observed
        == {
            links[edge]: kind
            for edge, kind in case["perimeter"]["source_axis_relations"].items()
        },
        "Generated axis constraints differ from the measured source operands",
    )
    return observed


# each candidate is independently reconstructed from source lengths and then read back
def build_candidate(case):
    sizes = tuple(
        case["dimensions"][name]["source"]["value_mm"] for name in ProbeOwnedDims.NAMES
    )
    content = ProbeOwnedDims.generate(sizes=sizes)
    proof = ProbeOwnedDims.inspect_generated(content)
    target, points, frame, incidence = candidate_edges(
        content, proof["anchor_evidence"]
    )
    matched = match_perimeters(source_edges(case), target, TOLERANCE_MM)
    require(
        matched["status"] == "equal",
        "Generated perimeter differs from the measured source",
    )
    verify_drivers(case, sizes, proof, points)
    axes = verify_axes(content, case, matched, frame["sketch"])
    return content, {
        "variant": case["variant"],
        "source": case["source"],
        "source_drivers": {
            name: row["source"] for name, row in case["dimensions"].items()
        },
        "source_origin": case["anchor"]["source_origin_coincidence"],
        "matched_perimeter": matched,
        "target_frame": frame,
        "target_endpoint_incidence": incidence,
        "target_axis_relations": axes,
        "archive_sha256": sha256(content),
        "archive_bytes": len(content),
        "offline_target": proof,
    }


# prepare all results before creating a caller-owned output directory
def generate_report(output):
    checked = source_report()
    cases = [case for case in checked["cases"] if case["recipe"] == "P01"]
    require(
        len(cases) == 3, "Expected the exact baseline and independent P01 source edits"
    )
    results = [build_candidate(case) for case in cases]
    for index, (_, evidence) in enumerate(results, start=1):
        evidence["file"] = f"P01-Candidate-{index}.f3d"
    evidence = {
        "schema": 1,
        "scope": "offline source-derived positive XY P01 rectangle candidates",
        "source_capture_revision": checked["source_capture_revision"],
        "source_receipt": checked["receipts"]["P01"],
        "codec_revision": check_output(
            ["git", "rev-parse", "HEAD"], cwd=ProbeOrigin.ROOT, text=True
        ).strip(),
        "generator_sha256": sha256(Path(ProbeOwnedDims.__file__).read_bytes()),
        "source_probe_sha256": sha256(Path(__file__).read_bytes()),
        "qualification": "candidate_requires_licensed_target_acceptance",
        "candidates": [item for _, item in results],
    }
    encoded = (
        json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    output.mkdir()
    for content, item in results:
        with (output / item["file"]).open("xb") as target:
            target.write(content)
    with (output / "P01CandidateEvidence.json").open("xb") as target:
        target.write(encoded)
    return sha256(encoded)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(generate_report(parser.parse_args().output))
