# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
import json
from math import isclose

from FusionCircularDimensionEvidence import (
    CONTROLS,
    FOLDER,
    MEASUREMENTS,
    REVISION,
    ROOT,
)
from FusionRadialMutation import mutation_archive
from PairedCaptureIntake import GitSnapshot, require, sha256
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.adapters.Fusion.Adapter import FusionReader
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.Fusion.Native.Circular.RadialSpecs import KRadialSpecs
from convert.adapters.Fusion.Native.Circular.ReadRadialBinding import ReadSizeLinks
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.SelectSketch import SelectSketch
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.adapters.Fusion.Writer import FusionWriter
from convert.adapters.base.ReadOptions import ReadOptions
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.document.Models.DocumentModel import CadDocument

# Pin the established strict circle behavior against the source of those public controls.
BASELINE = "f601764c407daea48c3c22ba20aee92de6807a25"

# Independent vendor and reemitted circles exercise unchanged strict admission.
UNCONSTRAINED = {
    "vendor_NativeCircleControl.f3d": (
        "949acf09b31e2cc9a4cb92a68e19de616e7501b32d80a23c93925c8d1f182d08",
        "b139b16f57de744906dc4de654abd58300457a061246219b9a684f86d14fc18f",
    ),
    "vendor_NativeCircleReemitted.f3d": (
        "d28603eed2249dc9fa17f8eba8e0d1046b1f8b7416133040f5e470f85bf879d0",
        "5e88eecb69d6fafa853e36f771d5e420a274baa1c284a17d2f2d698c85102b80",
    ),
}


# A negative case must reach the intended guard instead of failing elsewhere.
def refusal(callback, expected):
    try:
        callback()
    except ValueError as error:
        require(expected in str(error), f"Unexpected refusal: {error}")
        return str(error)
    raise ValueError(f"Missing refusal: {expected}")


# Verify that even caller-supplied native state cannot turn this projection into a write route.
def inspectable_document(document, model):
    document.AssertValid()
    encoded = document.to_json(indent=None)
    round_trip = CadDocument.from_json(encoded)
    require(
        round_trip.to_json(indent=None) == encoded,
        "Research neutral JSON did not round-trip",
    )
    require(
        not round_trip.metadata
        and not FusionWriter().Supports(round_trip, "radial.f3d"),
        "Strict radial read was advertised as native writer input",
    )
    forged = replace(
        round_trip,
        metadata={"fusion.native_state": {"version": 2, "model": EncodeState(model)}},
    )
    rejection = refusal(
        lambda: EncodeDocument(forged), "Fusion native-state projection is read-only"
    )
    return sha256(encoded.encode("utf-8")), rejection


# Preserve the other members in the inherited native value object.
def updated_info(dimension_info, name, value):
    require(name in ObjectFields(dimension_info), "Missing radial cache member")
    return replace(
        dimension_info,
        Groups=tuple(
            replace(
                group,
                Fields=tuple(
                    replace(field, Value=value) if field.FieldName == name else field
                    for field in group.Fields
                ),
            )
            for group in dimension_info.Groups
        ),
    )


# Each temporary archive mutation must reach the intended public strict invariant.
def tampered_links(model, context, records):
    dimension = records.Dimension
    binding = records.Binding
    parameter = records.Parameter
    update = records.Update
    _, spec = KRadialSpecs[dimension.ClassName]
    info_key = f"{spec.RolePrefix}DimensionInfo"
    dimension_info = dimension.Fields[info_key]
    mode = parameter.Fields["isDriven"]
    radius = ObjectFields(dimension_info)["radius"]
    changes = (
        (
            "circle_operand",
            dimension,
            "geometries",
            ValueSeries((records.Circle.Fields["rCenterPoint"],)),
            "Native radial dimension must target the sole circular curve",
        ),
        (
            "dimension_parent",
            dimension,
            "rParent",
            None,
            f"{dimension.ClassName}.rParent",
        ),
        (
            "parameter_binding",
            parameter,
            "dcParameter",
            None,
            "Parameter.dcParameter",
        ),
        (
            "binding_owner",
            binding,
            "rrOwnerFeature",
            None,
            "DcDoubleParameter.rrOwnerFeature",
        ),
        (
            "dynamic_owner",
            update,
            "rOwnerNode",
            LocalRef(context.SketchFeature.ObjectId),
            "DynamicUpdateData.rOwnerNode",
        ),
        (
            "driving_mode",
            dimension,
            info_key,
            updated_info(dimension_info, "bDriven", not mode),
            "Native radial dimension and parameter driving modes disagree",
        ),
        (
            "binding_value",
            binding,
            "value",
            binding.Fields["value"] + 0.1,
            "Native Fusion saved geometry or parameter values disagree",
        ),
        (
            "cached_radius",
            dimension,
            info_key,
            updated_info(dimension_info, "radius", radius + 0.1),
            "Native Fusion saved geometry or parameter values disagree",
        ),
        (
            "parameter_parent",
            parameter,
            "rParent",
            None,
            "Parameter.rParent",
        ),
        (
            "binding_slot",
            binding,
            "rparamId",
            2,
            "Native radial dimension parameter allocation disagrees",
        ),
    )
    results = {}
    for name, node, field, value, expected in changes:
        changed = mutation_archive(model, node, field, value)
        results[name] = refusal(
            lambda: FusionReader().Read(changed, ReadOptions(strict=True)), expected
        )
    return results


# Compare the graph result with observations from the original licensed capture.
def prototype_case(payload, sample, kind, driving):
    model = ReadDocument(payload)
    graph = BuildGraph(model)
    context = SelectSketch(graph)
    (dimension,) = (node for name in KRadialSpecs for node in graph.ByClass(name))
    records = ReadSizeLinks(graph, context, dimension)
    document = FusionReader().Read(payload, ReadOptions(strict=True))
    (sketch,) = document.sketches
    (relation,) = sketch.constraints
    (parameter,) = document.parameters
    (circle,) = (row for row in sketch.entities if row.kind == GeometryKind.KCircle)
    shape = circle.geometry
    original = sample["dimension"]
    (geometry,) = sample["geometry"]
    radius_mm = geometry["radius_cm"] * 10.0
    require(
        sample["kind"] == relation.kind == kind
        and relation.id == dimension.Identity
        and relation.parameter_id == parameter.id
        and sketch.closed_profile_entity_ids == ((circle.id,),)
        and circle.id == records.Circle.Identity
        and not document.diagnostics
        and original["is_driving"] is relation.driving is driving
        and parameter.name == original["parameter_name"]
        and parameter.expression.source == original["parameter_expression"]
        and isclose(
            parameter.value.value,
            original["parameter_value"] * 10.0,
            abs_tol=1e-6,
            rel_tol=0.0,
        )
        and isclose(shape.radius, radius_mm, abs_tol=1e-6, rel_tol=0.0)
        and all(
            isclose(actual, value * 10.0, abs_tol=1e-6, rel_tol=0.0)
            for actual, value in zip(
                (shape.center.x, shape.center.y, 0.0),
                geometry["center_cm"],
                strict=True,
            )
        ),
        "Prototype disagrees with the independent dimension and circle measurements",
    )
    document_hash, writer_refusal = inspectable_document(document, model)
    role = parameter.role.value
    return {
        "archive_sha256": sha256(payload),
        "neutral_sha256": document_hash,
        "relation": {
            "id": relation.id,
            "kind": kind,
            "driving": relation.driving,
            "curve_id": circle.id,
        },
        "ownership": {
            "sketch": context.Sketch.Identity,
            "owner_feature": parameter.owner_id,
            "dimension_object": dimension.ObjectId,
            "model_parameter_object": records.Parameter.ObjectId,
            "binding_object": records.Binding.ObjectId,
            "dynamic_update_object": records.Update.ObjectId,
        },
        "parameter": {
            "id": parameter.id,
            "name": parameter.name,
            "role": role,
            "expression": parameter.expression.source,
            "value_mm": parameter.value.value,
        },
        "geometry_mm": {
            "center": (shape.center.x, shape.center.y, 0.0),
            "radius": shape.radius,
        },
        "snapshot": {
            "member": model.Snapshots[0].Name,
            "closed_profile_entity_ids": sketch.closed_profile_entity_ids,
        },
        "tampered_archive_refusals": tampered_links(model, context, records),
        "forged_writer_state_refusal": writer_refusal,
    }


# Use the exact previously admitted archives for before-and-after controls.
def stock_inputs(snapshot):
    prefix = "re/Fusion/LocalOracle/RotationalDocuments/"
    inputs = {name: snapshot.blob(BASELINE, prefix + name) for name in UNCONSTRAINED}
    require(
        all(
            sha256(payload) == UNCONSTRAINED[name][0]
            for name, payload in inputs.items()
        ),
        "Previously accepted unconstrained control pin differs",
    )
    return inputs


# Compare full neutral serializations so changes outside the expected new class still surface.
def stock_reads(inputs):
    reader = FusionReader()
    results = {}
    for name, payload in inputs.items():
        doc = reader.Read(payload, ReadOptions(strict=True))
        (sketch,) = doc.sketches
        require(
            len(sketch.closed_profile_entity_ids) == 1
            and not sketch.constraints
            and not doc.bodies
            and not doc.diagnostics,
            "Previously accepted strict circle lost its unconstrained sketch",
        )
        digest = sha256(doc.to_json(indent=None).encode("utf-8"))
        require(
            digest == UNCONSTRAINED[name][1],
            "Previously accepted strict circle neutral serialization changed",
        )
        results[name] = {
            "archive_sha256": sha256(payload),
            "neutral_sha256": digest,
        }
    return results


# Keep the historical research replay independent of the later licensed measurement receipt.
def report():
    snapshot = GitSnapshot(ROOT)
    stock = stock_inputs(snapshot)
    before = stock_reads(stock)
    path = FOLDER + "ground_truth.json"
    raw = snapshot.blob(REVISION, path)
    require(sha256(raw) == MEASUREMENTS, "Historical Fusion observations differ")
    measured = snapshot.parse_document(raw, path)
    require(
        measured["fusion_version"] == "2705.1.30" and not measured["errors"],
        "Historical Fusion capture state differs",
    )
    samples = {
        row["file"]: row for row in measured["samples"] if row["file"] in CONTROLS
    }
    require(set(samples) == set(CONTROLS), "Historical circle roster differs")
    cases = {}
    for name, (kind, driving, size, digest) in CONTROLS.items():
        payload = snapshot.blob(REVISION, FOLDER + name)
        require(
            len(payload) == size and sha256(payload) == digest,
            "Circular control archive pin differs",
        )
        cases[name] = {
            "public_strict": "read-only",
            **prototype_case(payload, samples[name], kind, driving),
        }
    after = stock_reads(stock)
    require(
        before == after,
        "A previously accepted public strict control changed during replay",
    )
    return {
        "schema": 2,
        "scope": "packaged historical circular strict-read replay",
        "qualification": "strict read-only",
        "strict_baseline": BASELINE,
        "source_capture_revision": REVISION,
        "measurement_sha256": MEASUREMENTS,
        "historical_native_profile_loop_readback": "not captured",
        "historical_native_evaluator_bounds": "not captured",
        "native_archive_retained": False,
        "readable_unconstrained_controls": after,
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
