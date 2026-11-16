# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from collections import Counter
from dataclasses import replace
from math import isclose

from FusionCutExtentEvidence import REVISION, ROOT, SPECIFICATION, SPECIFICATION_SHA256
from FusionRadialMutation import mutation_archive
from PairedCaptureIntake import GitSnapshot, require, sha256
from RectanglePairEvidence import capture

from convert import open_document
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Writer import FusionWriter
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureDistExt import DistanceExtrude

# Pin the four independently read P03 archives and the separately exported repeat.
POSITIVE = {
    "baseline-a": "9f109b98ab7d36abeda8d9f88f9b336277238ce0bb3336d99313253ad47b2745",
    "baseline-b": "1880e585d2ff39dea2d95ef0d04ed9191be2efc921d8a52c6990e735288c1505",
    "edit-width_mm-41": "a7b7f7091b4a3f98ea8b0985dc069147249fcbc23d8cf9c61093d057d57ba093",
    "edit-height_mm-23": "87c5d925651b2b1ffb3b2359886db5ed07d07dba300113ef01f0e268eb53b35d",
    "edit-depth_mm-12": "d00651984f02f6de275fc0fa6d33777e75e1a110ba27a48309e1c37d6953247a",
}

# Adjacent discovery fixtures pin where the constrained positive XY reader stops.
REFUSED = {
    "units-inch": (
        "106767a536e453242e4b202af4db53d27973b16b7cf5f447b99a381cb8e09644",
        "Unsupported native Fusion UnitSystemChoiceById.unitString",
    ),
    "plane-yz": (
        "c14b8c4a791415c5eb356d4c1e4143cb4b76ab856e0f84357c08b4f4da125b3a",
        "Unsupported native Fusion FusionSketchLinearDim.constraintType",
    ),
    "direction-negative": (
        "4cfc1e792d33d48e4b80f9829a4496cf70c2059378ce1b3cfa716b3a1c9e8aab",
        "Native rectangle saved driver values or zero taper disagree",
    ),
}

# Exact native and neutral fingerprints freeze the unrelated writer and vendor read paths.
LEGACY_REVISION = "dcad571aba31b521cb37e7ccc919cf0bb9667936"
LEGACY = {
    "NativePublicAdapter/OrdinaryRectangle.f3d": (
        "0203674063f58504d037a51236a1aff9cc3283ed1b8b107cc8307e1e73f10e92",
        "316a5e0e15d17dc10659d30a6ae6aa24e17434bdc68c133ec9a09c582597bc68",
    ),
    "NativePublicAdapter/SavedCuboid.f3d": (
        "49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31",
        "08102d097d7b95e8cceb414807575f912be8fb3cb382df7e13a503e5ef09f110",
    ),
    "PrismSnapshot/OrdinaryRectangleSnapshot.f3d": (
        "1b70cbd58414d0e5bb8338596d2cbf4edde41be52b8f5f9a6fa86cb47db5486b",
        "d9f8cb7c9985e1edf93e90d17b9cfe94f41e5a84d2a9b52a51df2b02090eff46",
    ),
    "PrismSnapshot/SavedCuboidSnapshot.f3d": (
        "83466b231452394a0d8f0f493da1465a0c3f31b413f135ec6aceb2dfab738d1b",
        "be7aef823d1132b235e9c9166b39205e44646534adced9a44d136838122d0f80",
    ),
    "RotationalDocuments/vendor_NativeCircleControl.f3d": (
        "949acf09b31e2cc9a4cb92a68e19de616e7501b32d80a23c93925c8d1f182d08",
        "b139b16f57de744906dc4de654abd58300457a061246219b9a684f86d14fc18f",
    ),
    "RotationalDocuments/vendor_NativeCircleReemitted.f3d": (
        "d28603eed2249dc9fa17f8eba8e0d1046b1f8b7416133040f5e470f85bf879d0",
        "5e88eecb69d6fafa853e36f771d5e420a274baa1c284a17d2f2d698c85102b80",
    ),
    "RotationalDocuments/vendor_NativeCylinderControl.f3d": (
        "2a1f884592430b0a162aabdd5eeff954d9ea92e7743d65ad7dc415975ad56380",
        "9fef78e86c1ea3ea947104dbdc4920590ac45088136c8936c228a61f13a2babe",
    ),
    "RotationalDocuments/vendor_NativeFrustumControl.f3d": (
        "671a911689fdf648f50e79430e0cc77d2bf26e7ef8c4ae23fea268c10f223e37",
        "0cfcadf8f8c7893f52405e35e947f5b9705385add218cf7bc0fb0ebc843fb0d3",
    ),
}


# Strict refusals must identify the intended policy guard after a successful wire read.
def refusal(operation, expected):
    try:
        operation()
    except ValueError as error:
        require(str(error) == expected, f"Unexpected refusal: {error}")
        return str(error)
    raise ValueError(f"Expected refusal: {expected}")


# Use bytes from the original discovery commit and require both independent custody pins.
def source_bytes(snapshot, asset, digest):
    raw = snapshot.blob(REVISION, asset["path"])
    require(sha256(raw) == asset["sha256"] == digest, "P03 archive identity differs")
    return raw


# Verify named driving parameters, literal expressions and their exact neutral feature owners.
def owned_drivers(document, observed):
    sketch_feature, boss = document.feature_timeline
    width, height, depth, taper = document.parameters
    roster = ("width_mm", "height_mm", "depth_mm", "d4")
    owners = (sketch_feature.id,) * 2 + (boss.id,) * 2
    native = {item["name"]: item for item in observed["parameters"]}
    result = {}
    for parameter, name, owner in zip(document.parameters, roster, owners, strict=True):
        measured = native[name]
        scale = 1 if name == "d4" else 10
        require(
            parameter.name == name
            and parameter.owner_id == owner
            and parameter.role is ParameterRole.KDriving
            and parameter.expression is not None
            and parameter.expression.source == measured["expression"]
            and not parameter.expression.parameter_ids
            and parameter.value.unit == ("rad" if name == "d4" else "mm")
            and isclose(parameter.value.value, measured["value_internal"] * scale),
            "Strict parameter contract differs from native readback",
        )
        result[name] = {
            "id": parameter.id,
            "owner": owner,
            "expression": parameter.expression.source,
            "role": parameter.role.value,
            "unit": parameter.value.unit,
            "value": round(parameter.value.value, 9),
        }
    (sketch,) = document.sketches
    require(
        sketch_feature.sketch_id == boss.sketch_id == sketch.id
        and sketch.parameter_ids
        == sketch_feature.parameter_ids
        == (width.id, height.id)
        and boss.parameter_ids == (depth.id, taper.id)
        and boss.input_feature_ids == (sketch_feature.id,)
        and boss.operation is BooleanOp.KCreate
        and isinstance(boss.definition, DistanceExtrude)
        and boss.definition.SideMode == "one_sided"
        and (
            boss.definition.Direction.x,
            boss.definition.Direction.y,
            boss.definition.Direction.z,
        )
        == (0.0, 0.0, 1.0)
        and boss.definition.AlongParameterId == depth.id
        and boss.definition.TaperParameterId == taper.id
        and taper.value.value == 0.0,
        "Strict first-body operation and separate taper ownership differ",
    )
    return result


# Each emitted relation must use its actual saved native identity and ordered operands.
def sketch_relations(document, graph, context):
    (sketch,) = document.sketches
    by_id = {node.Identity: node for node in graph.Nodes.values()}
    (loop,) = sketch.closed_profile_entity_ids
    require(
        len(loop) == 4
        and set(loop) == {node.Identity for node in graph.ByClass("Line3D")}
        and Counter(relation.kind for relation in sketch.constraints)
        == {
            ConstraintKind.KCoincident: 1,
            ConstraintKind.KHorizontal: 2,
            ConstraintKind.KVertical: 2,
            ConstraintKind.KDistanceX: 1,
            ConstraintKind.KDistanceY: 1,
        },
        "Strict perimeter or relation roster differs",
    )
    relations = []
    for relation in sketch.constraints:
        node = by_id[relation.id]
        refs = tuple(reference.entity_id for reference in relation.references)
        native_refs = tuple(
            graph.Resolve(item).Identity for item in node.Fields["geometries"].Items
        )
        require(
            refs == native_refs and relation.driving and not relation.suppressed,
            "Strict relation operands differ",
        )
        if relation.parameter_id is not None:
            binding = graph.Resolve(node.Fields["dcParameter"])
            require(
                graph.Resolve(binding.Fields["parameter"]).Identity
                == relation.parameter_id
                and graph.Resolve(binding.Fields["rrOwnerFeature"])
                == context.SketchFeature,
                "Strict dimension omitted its reciprocal sketch parameter",
            )
        relations.append(
            {
                "id": relation.id,
                "kind": relation.kind,
                "refs": refs,
                "parameter": relation.parameter_id,
            }
        )
    return {"perimeter": loop, "relations": relations}


# Compare topology and native cache against licensed source and paired target measurements.
def body_match(document, context, observed):
    (body,) = document.bodies
    (material,) = document.materials
    bounds = body.topology.bounding_box
    lower = bounds.minimum
    upper = bounds.maximum
    limits = [
        [round(point.x, 9), round(point.y, 9), round(point.z, 9)]
        for point in (lower, upper)
    ]
    cache = ObjectFields(context.BodyNode.Fields["cache"])
    centroid = [round(amount * 10, 9) for amount in PointCoords(cache["cog"])]
    volume = round(body.topology.volume, 9)
    require(
        body.final_feature_id == document.feature_timeline[1].id
        and body.material_id == material.id
        and material.name == "PrismMaterial-018"
        and material.Density == 7850.0
        and body.topology.valid
        and limits == observed["fusion"]["bodies"][0]["bounding_box_mm"]
        and all(
            witness["body_count"] == 1
            and isclose(witness["volume_mm3"], volume, abs_tol=1e-7)
            and all(
                isclose(left, right, abs_tol=1e-7)
                for left, right in zip(
                    witness["center_of_mass_mm"], centroid, strict=True
                )
            )
            for witness in observed.values()
        ),
        "Strict body, typed material or recorded independent measurements differ",
    )
    return {
        "bounds_mm": limits,
        "centroid_mm": centroid,
        "volume_mm3": volume,
        "material_name": material.name,
        "material_density_kg_m3": material.Density,
    }


# Keep the complete typed native state and exact default partial bytes under their original contracts.
def check_state(raw, document, model):
    contract = document.metadata["fusion.native_state"]
    (retained,) = open_document(raw, strict=False).brep_payloads
    require(
        set(document.metadata) == {"fusion.native_state", "fusion.read_only"}
        and document.metadata["fusion.read_only"] is True
        and contract["version"] == 2
        and CheckContract(contract, "model", 2) == model
        and model.Snapshots
        and model.Graphics is not None
        and model.Materials
        and model.Bodies
        and retained.id == "fusion-source-archive"
        and retained.data == raw
        and retained.sha256 == sha256(raw)
        and not FusionWriter().Supports(document, "unused.f3d"),
        "Typed read-only state or exact partial custody differs",
    )
    return refusal(
        lambda: EncodeDocument(
            replace(document, metadata={"fusion.native_state": contract})
        ),
        "Fusion native-state projection is read-only",
    )


# Allocate one Design entity from typed fields using the active schema index.
def add_design_record(model, class_name, groups, frame):
    segment = next(
        part for part in model.Segments if part.Metadata.Header.SegmentId == 0
    )
    schema = next(item.Value for item in ReadNames() if item.NameValue == class_name)
    classes = list(segment.Metadata.Classes)
    index = next(
        index
        for index, item in enumerate(classes)
        if item.ClassGuid.upper() == schema.ClassGuid.upper()
    )
    row = classes[index]
    identity = segment.Metadata.NextId
    require(
        row.ClassGuid == groups[0].ClassGuid,
        "Design negative class differs from the wire vocabulary",
    )
    classes[index] = replace(row, OwnerIds=(*row.OwnerIds, identity))
    record = EntityRecord(
        identity,
        256 + index,
        True,
        frame,
        groups,
    )
    changed = replace(
        segment,
        Metadata=replace(segment.Metadata, Classes=tuple(classes), NextId=identity + 1),
        Records=(*segment.Records, record),
    )
    raw = EmitParsed(
        replace(
            model,
            Segments=tuple(
                changed if part is segment else part for part in model.Segments
            ),
        )
    )
    require(
        BuildGraph(ReadDocument(raw)).Nodes[(0, identity)].ClassName == class_name,
        "Added Design entity did not survive the wire read",
    )
    return raw, identity


# A third distinct dimension has a real wire class, physical record, and sketch inventory entry.
def third_dimension(model, graph, context):
    original = graph.ByClass("FusionSketchLinearDim")[0]
    raw, identity = add_design_record(
        model, original.ClassName, original.Groups, original.Frame
    )
    model = ReadDocument(raw)
    dimensions = ValueSeries(
        (*context.Sketch.Fields["dimensions"].Items, LocalRef(identity))
    )
    raw = mutation_archive(model, context.Sketch, "dimensions", dimensions)
    changed = BuildGraph(ReadDocument(raw))
    require(
        len(changed.ByClass("FusionSketchLinearDim")) == 3
        and changed.Nodes[(0, context.Sketch.ObjectId)].Fields["dimensions"]
        == dimensions,
        "Third-dimension archive lost its added typed node or link",
    )
    return raw


# Both ends of a nonzero taper binding agree before the strict zero-taper guard.
def nonzero_taper(model, graph, context):
    parameter = graph.Resolve(context.Taper.Fields["parameter"])
    raw = mutation_archive(model, parameter, "expression", "5.729577951308233 deg")
    raw = mutation_archive(ReadDocument(raw), parameter, "value", 0.1)
    raw = mutation_archive(ReadDocument(raw), context.Taper, "value", 0.1)
    changed = BuildGraph(ReadDocument(raw))
    require(
        changed.Nodes[(0, parameter.ObjectId)].Fields["value"]
        == changed.Nodes[(0, context.Taper.ObjectId)].Fields["value"]
        == 0.1,
        "Nonzero taper archive lost its reciprocal parameter values",
    )
    return raw


# Negative variants alter one saved typed field and must remain low-level readable.
def field_mutations(model, graph, context):
    lines = graph.ByClass("Line3D")
    rules = graph.ByClass("SketchGeomConstraint")
    params = {node.Fields["userName"]: node for node in graph.ByClass("Parameter")}
    placement = MatrixValue(
        (1.0, 0.0, 0.0, 0.5, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    )
    mutations = (
        (
            "wrong_endpoint",
            lines[0],
            "rEndPoint",
            lines[1].Fields["rEndPoint"],
            "Native rectangle endpoint links do not form one closed loop",
        ),
        (
            "duplicate_axis",
            rules[1],
            "geometries",
            rules[0].Fields["geometries"],
            "Native rectangle axis rules must identify four distinct sides",
        ),
        (
            "translated_placement",
            context.Plane,
            "transform",
            placement,
            "Native Fusion profile requires identity placement",
        ),
        (
            "reference_driver",
            params["width_mm"],
            "isDriven",
            True,
            "Unsupported native Fusion Parameter.isDriven",
        ),
        (
            "unexpected_rule",
            rules[0],
            "constraintType",
            4096,
            "Unsupported native Fusion SketchGeomConstraint.constraintType",
        ),
    )
    refused = {}
    for label, node, field, value, expected in mutations:
        raw = mutation_archive(model, node, field, value)
        known = BuildGraph(ReadDocument(raw)).Nodes[(node.SegmentId, node.ObjectId)]
        require(
            known.Fields[field] == value,
            f"{label} mutation did not survive the wire read",
        )
        refused[label] = refusal(lambda: open_document(raw, strict=True), expected)
    managed = next(
        item.Value.ClassGuid
        for item in ReadNames()
        if item.NameValue == "ManagedEntity"
    )
    raw, _ = add_design_record(
        model,
        "ManagedEntity",
        (EntityGroup(managed, (NamedValue("rParent", None),)),),
        EntityFrame("", None, None),
    )
    for label, changed, expected in (
        ("unexpected_class", raw, "Unmodeled native Fusion semantic entity class"),
        (
            "third_dimension",
            third_dimension(model, graph, context),
            "Native constrained rectangle requires five rules and two dimensions",
        ),
        (
            "nonzero_taper",
            nonzero_taper(model, graph, context),
            "Native rectangle saved driver values or zero taper disagree",
        ),
    ):
        refused[label] = refusal(lambda: open_document(changed, strict=True), expected)
    return refused


# The original byte and neutral digests detect unintended changes across previous strict families.
def legacy_controls(snapshot):
    result = {}
    for path, (archive_digest, neutral_digest) in LEGACY.items():
        raw = snapshot.blob(LEGACY_REVISION, f"re/Fusion/LocalOracle/{path}")
        document = open_document(raw, strict=True)
        require(
            sha256(raw) == archive_digest
            and sha256(document.to_json(indent=None).encode()) == neutral_digest,
            f"Previous strict reader fingerprint differs for {path}",
        )
        result[path] = {
            "archive_sha256": archive_digest,
            "neutral_sha256": neutral_digest,
        }
    return result


# Replay public entry points from immutable discovery receipts in the repository.
def report():
    snapshot = GitSnapshot(ROOT)
    raw_spec = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(raw_spec) == SPECIFICATION_SHA256, "P03 specification digest differs"
    )
    specification = snapshot.parse_document(raw_spec, SPECIFICATION)
    (recipe,) = [item for item in specification["recipes"] if item["id"] == "P03"]
    applications = ("fusion", "solidworks")
    captures = {
        app: capture(snapshot, recipe, app, specification) for app in applications
    }
    _, assets, _ = captures["fusion"]
    accepted = {}
    for variant, digest in POSITIVE.items():
        raw = source_bytes(snapshot, assets[variant], digest)
        document = open_document(raw, strict=True)
        model = ReadDocument(raw)
        graph = BuildGraph(model)
        context = SelectExtrusion(graph)
        witnesses = {app: captures[app][2][variant] for app in applications}
        accepted[variant] = {
            "archive_sha256": digest,
            "phases": {app: witness[0] for app, witness in witnesses.items()},
            "parameters": owned_drivers(document, witnesses["fusion"][1]),
            "sketch": sketch_relations(document, graph, context),
            "body": body_match(
                document,
                context,
                {app: witness[1] for app, witness in witnesses.items()},
            ),
            "read_only_independent_guard": check_state(raw, document, model),
        }
    adjacent = {}
    for variant, (digest, expected) in REFUSED.items():
        raw = source_bytes(snapshot, assets[variant], digest)
        require(bool(ReadDocument(raw).Segments), f"{variant} wire decode failed")
        adjacent[variant] = {
            "archive_sha256": digest,
            "refusal": refusal(lambda: open_document(raw, strict=True), expected),
        }
    baseline = ReadDocument(
        source_bytes(snapshot, assets["baseline-a"], POSITIVE["baseline-a"])
    )
    graph = BuildGraph(baseline)
    return {
        "schema": 1,
        "revision": REVISION,
        "specification_sha256": SPECIFICATION_SHA256,
        "scope": "Strict source reading for a constrained millimeter XY first blind prism",
        "captures": {
            app: {
                key: entry[0][key]
                for key in (
                    "receipt",
                    "measurements",
                    "application_build",
                    "qualification_blockers",
                )
            }
            for app, entry in captures.items()
        },
        "admitted": accepted,
        "adjacent_refusals": adjacent,
        "valid_native_mutation_refusals": field_mutations(
            baseline, graph, SelectExtrusion(graph)
        ),
        "legacy_revision": LEGACY_REVISION,
        "legacy_controls": legacy_controls(snapshot),
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
