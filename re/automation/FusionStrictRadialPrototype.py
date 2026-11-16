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
from FusionRadialGraph import SPECS, change_field, registered_graph, verified_circle
from PairedCaptureIntake import GitSnapshot, require, sha256
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.adapters.Fusion.Adapter import FusionReader
from convert.adapters.Fusion.Native.Circular.ProjectCircle import (
    CircleFeature,
    CircleSketch,
)
from convert.adapters.Fusion.Writer import FusionWriter
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.registry.ResearchWrite import CheckResearch, KResearchReadStatus
from interchange.Core.Common import FreezeMapping
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform

# Pin the established strict circle behavior against the source of those public controls.
BASELINE = "f601764c407daea48c3c22ba20aee92de6807a25"

# Independent vendor and reemitted circles exercise unchanged strict admission.
UNCONSTRAINED = {
    "vendor_NativeCircleControl.f3d": "949acf09b31e2cc9a4cb92a68e19de616e7501b32d80a23c93925c8d1f182d08",
    "vendor_NativeCircleReemitted.f3d": "d28603eed2249dc9fa17f8eba8e0d1046b1f8b7416133040f5e470f85bf879d0",
}


# A negative case must reach the intended guard instead of failing elsewhere.
def refusal(callback, expected):
    try:
        callback()
    except ValueError as error:
        require(expected in str(error), f"Unexpected refusal: {error}")
        return str(error)
    raise ValueError(f"Missing refusal: {expected}")


# Exercise interchange serialization and both export gates with an explicitly unqualified document.
def inspectable_document(payload, model, context, shape, parameter, relation):
    sketch = replace(
        CircleSketch(context, shape),
        constraints=(relation,),
        parameter_ids=(parameter.id,),
    )
    feature = replace(CircleFeature(context), parameter_ids=(parameter.id,))
    title = dict(model.Asset.Properties).get("documentName", "")
    document = CadDocument(
        source=CadSource("fusion.f3d", "", sha256(payload)),
        configurations=(Configuration("default", title, True),),
        parameters=(parameter,),
        support_planes=(SupportPlane(context.Plane.Identity, "XY", Transform()),),
        sketches=(sketch,),
        feature_timeline=(feature,),
        selections=(),
        bodies=(),
        metadata=FreezeMapping({KResearchReadStatus: "unqualified"}),
    )
    document.AssertValid()
    encoded = document.to_json(indent=None)
    round_trip = CadDocument.from_json(encoded)
    require(
        round_trip.to_json(indent=None) == encoded,
        "Research neutral JSON did not round-trip",
    )
    require(
        not FusionWriter().Supports(round_trip, "prototype.f3d"),
        "Prototype was advertised as writer input",
    )
    refusal(
        lambda: CheckResearch(round_trip),
        "unqualified research documents cannot be exported",
    )
    return sketch, sha256(encoded.encode("utf-8"))


# Each mutation invalidates one typed source invariant without changing the archive bytes.
def tampered_links(model, graph, schemas, context, shape, nodes):
    dimension, binding, parameter, update = nodes
    info_key = SPECS[dimension.ClassName][1]
    dimension_info = dimension.Fields[info_key]
    mode = parameter.Fields["isDriven"]
    changed_info = replace(
        dimension_info,
        Groups=tuple(
            replace(
                group,
                Fields=tuple(
                    (
                        replace(field, Value=not mode)
                        if field.FieldName == "bDriven"
                        else field
                    )
                    for field in group.Fields
                ),
            )
            for group in dimension_info.Groups
        ),
    )
    changes = (
        (
            "circle_operand",
            dimension,
            "geometries",
            ValueSeries((LocalRef(shape.CenterNode.ObjectId),)),
            "Dimension does not target the sole circular curve",
        ),
        (
            "dimension_parent",
            dimension,
            "rParent",
            LocalRef(context.SketchFeature.ObjectId),
            "Dimension owner or model binding differs",
        ),
        (
            "parameter_binding",
            parameter,
            "dcParameter",
            LocalRef(dimension.ObjectId),
            "Model parameter and sketch-feature binding are not reciprocal",
        ),
        (
            "binding_owner",
            binding,
            "rrOwnerFeature",
            LocalRef(context.Sketch.ObjectId),
            "Model parameter and sketch-feature binding are not reciprocal",
        ),
        (
            "dynamic_owner",
            update,
            "rOwnerNode",
            LocalRef(context.SketchFeature.ObjectId),
            "Dynamic update data does not return to its binding",
        ),
        (
            "driving_mode",
            dimension,
            info_key,
            changed_info,
            "Dimension and model parameter driving modes disagree",
        ),
        (
            "binding_value",
            binding,
            "value",
            binding.Fields["value"] + 0.1,
            "Circular dimension binding value differs",
        ),
    )
    results = {}
    for name, node, field, value, expected in changes:
        changed = change_field(graph, node, field, value)
        results[name] = refusal(
            lambda: verified_circle(model, changed, schemas), expected
        )
    return results


# Compare the graph result with observations from the original licensed capture.
def prototype_case(payload, sample, kind, driving):
    model = ReadDocument(payload)
    graph, schemas = registered_graph(model)
    context, shape, parameter, relation, nodes = verified_circle(model, graph, schemas)
    original = sample["dimension"]
    (geometry,) = sample["geometry"]
    radius_mm = geometry["radius_cm"] * 10.0
    require(
        sample["kind"] == relation.kind == kind
        and original["is_driving"] is relation.driving is driving
        and parameter.name == original["parameter_name"]
        and parameter.expression.source == original["parameter_expression"]
        and isclose(
            parameter.value.value,
            original["parameter_value"] * 10.0,
            abs_tol=1e-6,
            rel_tol=0.0,
        )
        and isclose(shape.Geometry.radius, radius_mm, abs_tol=1e-6, rel_tol=0.0)
        and all(
            isclose(actual, value * 10.0, abs_tol=1e-6, rel_tol=0.0)
            for actual, value in zip(
                (shape.Geometry.center.x, shape.Geometry.center.y, 0.0),
                geometry["center_cm"],
                strict=True,
            )
        ),
        "Prototype disagrees with the independent dimension and circle measurements",
    )
    sketch, document_hash = inspectable_document(
        payload, model, context, shape, parameter, relation
    )
    dimension, binding, raw_parameter, update = nodes
    role = parameter.role.value
    return {
        "archive_sha256": sha256(payload),
        "neutral_sha256": document_hash,
        "relation": {
            "id": relation.id,
            "kind": kind,
            "driving": relation.driving,
            "curve_id": shape.CurveNode.Identity,
        },
        "ownership": {
            "sketch": context.Sketch.Identity,
            "owner_feature": parameter.owner_id,
            "dimension_object": dimension.ObjectId,
            "model_parameter_object": raw_parameter.ObjectId,
            "binding_object": binding.ObjectId,
            "dynamic_update_object": update.ObjectId,
        },
        "parameter": {
            "id": parameter.id,
            "name": parameter.name,
            "role": role,
            "expression": parameter.expression.source,
            "value_mm": parameter.value.value,
        },
        "geometry_mm": {
            "center": (shape.Geometry.center.x, shape.Geometry.center.y, 0.0),
            "radius": shape.Geometry.radius,
        },
        "snapshot": {
            "member": model.Snapshots[0].Name,
            "closed_profile_entity_ids": sketch.closed_profile_entity_ids,
        },
        "tampered_typed_graph_refusals": tampered_links(
            model, graph, schemas, context, shape, nodes
        ),
    }


# Use the exact previously admitted archives for before-and-after controls.
def stock_inputs(snapshot):
    prefix = "re/Fusion/LocalOracle/RotationalDocuments/"
    inputs = {name: snapshot.blob(BASELINE, prefix + name) for name in UNCONSTRAINED}
    require(
        all(sha256(payload) == UNCONSTRAINED[name] for name, payload in inputs.items()),
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
        results[name] = {
            "archive_sha256": sha256(payload),
            "neutral_sha256": sha256(doc.to_json(indent=None).encode("utf-8")),
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
        message = refusal(
            lambda: FusionReader().Read(payload, ReadOptions(strict=True)),
            "Unknown native Fusion entity class",
        )
        cases[name] = {
            "public_strict": message,
            **prototype_case(payload, samples[name], kind, driving),
        }
    after = stock_reads(stock)
    require(
        before == after, "Prototype changed a previously accepted public strict control"
    )
    return {
        "schema": 1,
        "scope": "isolated historical circular strict-read prototype",
        "qualification": "unqualified",
        "strict_baseline": BASELINE,
        "source_capture_revision": REVISION,
        "measurement_sha256": MEASUREMENTS,
        "historical_native_profile_loop_readback": "not captured",
        "historical_native_evaluator_bounds": "not captured",
        "native_archive_generated": False,
        "readable_unconstrained_controls": after,
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
