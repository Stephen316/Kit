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
from math import dist, isclose
from pathlib import Path
import sys
from types import SimpleNamespace

# Existing sealed P03 receipt and signed archive helpers remain the source authorities.
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "re/automation"),
    str(ROOT / "re/automation/FusionSignedPrism"),
]

from FusionConstrainedPrismEvidence import POSITIVE, REFUSED, refusal
from FusionCutExtentEvidence import REVISION, SPECIFICATION, SPECIFICATION_SHA256
from FusionRadialMutation import mutation_archive
from PairedCaptureIntake import GitSnapshot, require, sha256
from ReadDatumParts import (
    HISTORY_SHA256,
    SNAPSHOT_SHA256,
    match_face_tags,
    read_datum_parts,
    snapshot_table,
    world_point,
)
from RectanglePairEvidence import capture
from VerifySignedPrism import (
    body_identity,
    body_parts,
    design_curves,
    face_and_body_tags,
)
from convert import open_document, write_document
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    NumberValue,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import (
    ProjectFeatures,
    ProjectSketch,
)
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadRectangle import ReadRectangle
from convert.adapters.Fusion.Native.Rectangle.ReadRectDims import (
    CheckDimFrame,
    CheckDimLayout,
    CheckRectBind,
    CheckRectDeps,
    CheckRectIndex,
)
from convert.adapters.Fusion.Native.Rectangle.ReadRectRules import (
    ReadRectAnchor,
    ReadRectAxes,
    ReadRectUnits,
)
from convert.adapters.Fusion.Native.Rectangle.RectSketchProof import RectSketchProof
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import CheckSignedMass
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapRegion import (
    MapRegion,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange import CadDocument
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordTopology import TopologyCounts


# Resolve both geometric matrix carriers, the scoped recipe, and the owned global origin datum.
def read_frame(graph, context, model):
    matrix = ResolveField(
        graph, context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (reference,) = LinkedNodes(graph, matrix, "dataRefs")
    SameNodes((reference,), graph.ByClass("EntityDataRef"))
    recipe = ResolveField(graph, reference, "rRecipe", "EntityRecipe")
    datum = graph.ResolveId(recipe.Fields["m_entityId"])
    origin = ResolveField(
        graph, context.Component, "m_rOriginWorkGeometry", "OriginWorkGeometry"
    )
    require(
        datum.ClassName == "WorkPlane"
        and datum in LinkedNodes(graph, origin, "children")
        and graph.Resolve(datum.Fields["rParent"]) == origin
        and graph.Resolve(origin.Fields["rParent"]) == context.Component
        and datum.Fields["originName"] == "YZ"
        and datum.Fields["isOrigin"] is True,
        "YZ matrix recipe does not select the owned origin datum",
    )
    saved = context.Plane.Fields["transform"]
    require(
        isinstance(saved, MatrixValue)
        and saved == matrix.Fields["matrix3d"]
        and saved.Entries is not None,
        "YZ CoordinateSystem and DRMatrix disagree about placement",
    )
    values = saved.Entries
    axes = tuple(
        tuple(values[row * 4 + column] for row in range(3)) for column in range(3)
    )
    translation = tuple(values[row * 4 + 3] for row in range(3))
    require(
        axes == ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
        and translation == (0.0, 0.0, 0.0)
        and values[12:] == (0.0, 0.0, 0.0, 1.0),
        "YZ native frame is outside the measured rigid basis",
    )
    check_frame_owners(graph, context, matrix, reference, datum, model)
    return Transform(
        x_axis=SpaceVector(*axes[0]),
        y_axis=SpaceVector(*axes[1]),
        z_axis=SpaceVector(*axes[2]),
    ), {
        "coordinate_system": context.Plane.ObjectId,
        "sketch_matrix": matrix.ObjectId,
        "datum_reference": reference.ObjectId,
        "datum_recipe": recipe.ObjectId,
        "origin_datum": datum.ObjectId,
        "matrix_row_major": values,
        "world_axes": axes,
        "datum_u": [0.0, 1.0, 0.0],
        "datum_v": [0.0, 0.0, 1.0],
    }


# The placement recipe retains the same sketch owner and the physical axis is a saved feature field.
def check_frame_owners(graph, context, matrix, reference, datum, model):
    instance = graph.OneClass("ComponentInstance")
    require(
        graph.Resolve(context.Sketch.Fields["UCS"]) == context.Plane
        and graph.Resolve(context.Plane.Fields["rParent"]) == context.Component
        and graph.Resolve(context.Sketch.Fields["rDcNode"]) == context.SketchFeature
        and graph.Resolve(instance.Fields["rTargetComponent"]) == context.Component,
        "YZ source frame does not belong to the selected sketch and component",
    )
    CheckIdentity(instance.Fields["transform"])
    CheckIdentity(context.Sketch.Fields["occurrenceTransform"])
    for owner in (matrix, reference):
        update = ResolveField(graph, owner, "rDynamicUpdateData", "DynamicUpdateData")
        require(
            graph.Resolve(owner.Fields["rParentFeature"]) == context.SketchFeature
            and graph.Resolve(update.Fields["rOwnerNode"]) == owner,
            "YZ frame graph has a competing feature or update owner",
        )
    RequireFields(
        matrix,
        {
            "refType": 2,
            "isZFlip": False,
            "isInferredXAxis": False,
            "isInferredZAxis": False,
            "oldRotation": 0.0,
        },
    )
    RequireFields(
        context.Extrude,
        {
            "booleanOperation": 4,
            "directionType": 1,
            "isFlipDirection": False,
            "side1ExtentType": 1,
            "side2ExtentType": 0,
        },
    )
    plane = ObjectFields(datum.Fields["plane"])
    require(
        plane["normalReversed"] is False
        and PointCoords(plane["origin"]) == (0.0, 0.0, 0.0)
        and PointCoords(plane["uAxis"]) == (0.0, 1.0, 0.0)
        and PointCoords(plane["vAxis"]) == (0.0, 0.0, 1.0)
        and PointCoords(context.Extrude.Fields["profileNormal"]) == (1.0, 0.0, 0.0),
        "YZ datum or extrusion normal differs from this saved origin basis",
    )
    CheckScopes(graph, context, model.Asset.AssetId)
    CheckSceneRefs(graph, model.Graphics)


# The admitted XY binding extractors still prove all four reciprocal native owners.
def read_dimensions(graph, context):
    require(
        ReadRectUnits(graph) is UnitSystem.KMillimeter,
        "YZ proof requires metric display",
    )
    rules = LinkedNodes(graph, context.Sketch, "constraints")
    dimensions = LinkedNodes(graph, context.Sketch, "dimensions")
    SameNodes(rules, graph.ByClass("SketchGeomConstraint"))
    SameNodes(dimensions, graph.ByClass("FusionSketchLinearDim"))
    require(
        (len(rules), len(dimensions)) == (5, 2), "YZ sketch relation inventory differs"
    )
    lines = OrderLines(graph, graph.ByClass("Line3D"))
    anchor_rule, anchor, origin = ReadRectAnchor(graph, context, rules, lines)
    axes = ReadRectAxes(graph, context, rules, anchor_rule, lines)
    bindings = LinkedNodes(graph, context.SketchFeature, "dcParameters")
    full = (*bindings, context.Along, context.Taper)
    SameNodes(full, graph.ByClass("DcDoubleParameter"))
    table = ResolveField(graph, context.Component, "rParameterTable", "ParameterTable")
    nodes = ResolveField(graph, context.Fragment, "rNodes", "DcNodes")
    children = LinkedNodes(graph, nodes, "children")
    require(
        all(children.count(binding) == 1 for binding in full),
        "YZ dimension binding does not have one fragment owner",
    )
    owners = (context.SketchFeature,) * 2 + (context.Extrude,) * 2
    parameters = tuple(
        CheckRectBind(graph, binding, owner, table, nodes, index)
        for index, (binding, owner) in enumerate(zip(full, owners, strict=True), 1)
    )
    CheckRectIndex(graph, context, table, parameters)
    CheckRectDeps(graph, context, bindings)
    attached = []
    evidence = []
    for index, (dimension, binding, parameter) in enumerate(
        zip(dimensions, bindings, parameters[:2], strict=True)
    ):
        relation, measured = read_local_dim(
            graph, context, dimension, binding, parameter, lines, anchor, index
        )
        attached.append(relation)
        evidence.append(measured)
    coincidence = SketchRelation(
        anchor_rule.Identity,
        ConstraintKind.KCoincident,
        (ConstraintRef(anchor.Identity), ConstraintRef(origin.Identity)),
    )
    proof = RectSketchProof(
        rules,
        dimensions,
        bindings,
        parameters[:2],
        anchor,
        origin,
        (*axes, coincidence, *attached),
        UnitSystem.KMillimeter,
    )
    neutral = ReadParameters(graph, context, Rectangle=proof)
    require(
        [
            (
                item.name,
                item.value.value,
                item.value.unit,
                item.expression.source,
                item.owner_id,
            )
            for item in neutral
        ]
        == [
            ("width_mm", 40.0, "mm", "40 mm", context.SketchFeature.Identity),
            ("height_mm", 20.0, "mm", "20 mm", context.SketchFeature.Identity),
            ("depth_mm", 10.0, "mm", "10 mm", context.Extrude.Identity),
            ("d4", 0.0, "rad", "0.0 deg", context.Extrude.Identity),
        ]
        and all(not item.expression.parameter_ids for item in neutral),
        "YZ owned literal drivers differ from the exact P03 roles",
    )
    return proof, neutral, evidence


# Width is local positive Y while the second dimension measures from local negative X to the shared anchor.
def read_local_dim(graph, context, dimension, binding, parameter, lines, anchor, index):
    axis = (1, 0)[index]
    kind = (ConstraintKind.KDistanceY, ConstraintKind.KDistanceX)[index]
    RequireFields(
        dimension,
        {
            "constraintType": 1 << (22 + axis),
            "ParentNode": LocalRef(context.Sketch.ObjectId),
            "rParent": LocalRef(context.Sketch.ObjectId),
            "dcParameter": LocalRef(binding.ObjectId),
            "isSick": False,
            "isVisible": False,
            "rClientObject": None,
        },
    )
    operands = LinkedNodes(graph, dimension, "geometries")
    matching = [
        line
        for line in lines
        if (
            graph.Resolve(line.Fields["rStartPoint"]),
            graph.Resolve(line.Fields["rEndPoint"]),
        )
        == operands
    ]
    require(
        len(operands) == 2 and operands[index] == anchor and len(matching) == 1,
        "YZ dimension is not on its exact ordered anchored side",
    )
    start, end = (PointCoords(operand.Fields["point"]) for operand in operands)
    amount = NumberValue(parameter.Fields["value"])
    expected = (
        ((0.0, 0.0, 0.0), (0.0, amount, 0.0))
        if index == 0
        else ((-amount, 0.0, 0.0), (0.0, 0.0, 0.0))
    )
    require(
        (start, end) == expected and amount == dist(start, end),
        "YZ dimension local axis or signed operand order differs",
    )
    CheckDimFrame(graph, dimension, operands, anchor, index == 0)
    require(
        dimension.Frame.Subjects[0].ObserverIndex == 4 + index,
        "YZ dimension settings observer has the wrong rank",
    )
    check_dim_cache(dimension, parameter, start, end, axis, amount)
    return SketchRelation(
        dimension.Identity,
        kind,
        tuple(ConstraintRef(node.Identity) for node in operands),
        parameter_id=parameter.Identity,
    ), {
        "dimension": dimension.ObjectId,
        "local_kind": kind.value,
        "parameter": parameter.ObjectId,
        "binding": binding.ObjectId,
        "operands": [node.ObjectId for node in operands],
        "endpoints_local_cm": [start, end],
        "expression": parameter.Fields["expression"],
    }


# The display annotation lives in the local sketch frame and independently measures the same ordered points.
def check_dim_cache(dimension, parameter, start, end, axis, amount):
    info = ObjectFields(dimension.Fields["LinearDimensionInfo"])
    plane = ObjectFields(info["plane"])
    extension = PointCoords(info["extnStartPoint"])
    require(
        info["bDriven"] is False
        and info["hasTextPoint"] is True
        and info["isSingleArrow"] is False
        and info["prefix"] == ""
        and info["text"] == parameter.Fields["expression"]
        and NumberValue(info["length"]) == amount
        and PointCoords(info["startPoint"]) == start
        and PointCoords(info["endPoint"]) == end
        and extension == start
        and plane["normalReversed"] is False
        and PointCoords(plane["origin"]) == (0.0, 0.0, 0.0)
        and PointCoords(plane["uAxis"]) == (1.0, 0.0, 0.0)
        and PointCoords(plane["vAxis"]) == (0.0, 1.0, 0.0)
        and SeriesItems(dimension.Fields["RefPositions"]) == (0.0, 1.0),
        "YZ dimension annotation disagrees with its retained local driver",
    )
    CheckDimLayout(info, start, end, axis)


# The existing neutral builder can instantiate the checked plane without native state loss.
def neutral_body(raw, model, graph, context, frame, shape, proof, parameters):
    sketch_feature, boss = ProjectFeatures(graph, context, proof)
    boss = replace(boss, definition=replace(boss.definition, Direction=frame.z_axis))
    stations = GetDistValues(
        boss, boss.definition, {item.id: item for item in parameters}
    )
    require(
        (stations.LowerMm, stations.UpperMm, stations.TaperRadians) == (0.0, 10.0, 0.0),
        "YZ positive blind station differs",
    )
    brep, volume, area, bounds = BuildPrism(
        context.BodyNode.Identity,
        frame,
        shape.Lines,
        stations.LowerMm,
        stations.UpperMm,
    )
    material = ReadMaterial(graph, context, model)
    counts = TopologyCounts(
        1,
        len(brep.shells),
        len(brep.faces),
        len(brep.edges),
        len(brep.vertices),
        volume,
        area,
        bounds,
        True,
    )
    body = DesignBody(context.BodyNode.Identity, "", boss.id, counts, material.id)
    partial = open_document(raw, strict=False)
    (payload,) = partial.brep_payloads
    require(
        payload.data == raw and payload.sha256 == sha256(raw),
        "YZ public partial read lost exact original state",
    )
    state = json.dumps(
        EncodeState(model), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    contract = {"version": 2, "model": json.loads(state)}
    require(
        CheckContract(contract, "model", 2) == model,
        "YZ complete V2 typed state failed JSON transport",
    )
    document = CadDocument(
        partial.source,
        (Configuration("default", "", True),),
        parameters,
        (SupportPlane(context.Plane.Identity, "YZ", frame),),
        (ProjectSketch(context, shape, proof),),
        (),
        (sketch_feature, boss),
        (body,),
        brep=brep,
        materials=(material,),
        metadata={"fusion.native_state": contract, "fusion.read_only": True},
    )
    document.AssertValid()
    return document, {
        "json_bytes": len(state.encode()),
        "sha256": sha256(state.encode()),
        "complete_typed_model_equal": True,
    }


# The capture comparison checks actual world line endpoints and the two independently measured mass properties.
def compare_native(witnesses, document, axes, curves):
    fusion, solidworks = (witnesses[app][1] for app in ("fusion", "solidworks"))
    (sketch,) = fusion["sketches"]
    fusion_curves = frozenset(
        frozenset(
            tuple(value / 10 for value in item[key])
            for key in ("start_world_mm", "end_world_mm")
        )
        for item in sketch["curves"]
    )
    (sw_sketch,) = solidworks["sketches"]
    sw_curves = frozenset(
        frozenset(
            tuple(value / 10 for value in item[key])
            for key in ("start_world_mm", "end_world_mm")
        )
        for item in sw_sketch["entities"]
    )
    (body,) = document.bodies
    lower, upper = (
        body.topology.bounding_box.minimum,
        body.topology.bounding_box.maximum,
    )
    bounds = [[point.x, point.y, point.z] for point in (lower, upper)]
    centroid = [(a + b) / 2 for a, b in zip(*bounds, strict=True)]
    require(
        sketch["support_name"] == "YZ"
        and sketch["fully_constrained"]
        and sw_sketch["fully_defined"]
        and sketch["x_direction"] == list(axes[0])
        and sketch["y_direction"] == list(axes[1])
        and sketch["origin_world_mm"] == [0.0, 0.0, 0.0]
        and sketch["profile_areas_mm2"] == [800.0]
        and sw_sketch["section_area_mm2"] == 800.0
        and fusion_curves == sw_curves == frozenset(curves.values())
        and bounds == fusion["bodies"][0]["bounding_box_mm"]
        and all(
            evidence["body_count"] == 1
            and isclose(
                evidence["volume_mm3"], body.topology.volume, rel_tol=0, abs_tol=1e-7
            )
            and all(
                isclose(a, b, rel_tol=0, abs_tol=1e-7)
                for a, b in zip(centroid, evidence["center_of_mass_mm"], strict=True)
            )
            for evidence in (fusion, solidworks)
        ),
        "YZ neutral pose or body does not match the licensed P03 observations",
    )
    return {
        "bounds_world_mm": bounds,
        "volume_mm3": body.topology.volume,
        "area_mm2": body.topology.surface_area,
        "centroid_world_mm": centroid,
        "faces_edges_vertices": (
            body.topology.face_count,
            body.topology.edge_count,
            body.topology.vertex_count,
        ),
    }


# A valid wire changed section must still fail the physical edge ownership proof for its own frame.
def change_section(raw, model, root, first, attr):
    (part,) = model.Snapshots
    snapshot = part.Snapshot
    wire = snapshot_table(body_parts(raw, model)[1], snapshot)
    mapping = MapRegion(wire, root, first, attr)
    slots = list(snapshot.Entities)
    original, other = (slots[mapping[attr + index]] for index in (0, 1))
    require(
        isinstance(original, SketchAttrib)
        and isinstance(other, SketchAttrib)
        and original.SourceLink.PrimaryId != other.SourceLink.PrimaryId,
        "YZ section mutation requires distinct typed edge links",
    )
    slots[mapping[attr]] = replace(
        original,
        SourceLink=replace(original.SourceLink, PrimaryId=other.SourceLink.PrimaryId),
    )
    changed = replace(snapshot, Entities=tuple(slots))
    mutated = EmitParsed(replace(model, Snapshots=(replace(part, Snapshot=changed),)))
    result = ReadDocument(mutated)
    require(
        result.Snapshots[0].Snapshot == changed,
        "YZ mutated section did not survive the wire",
    )
    return mutated, result


# The original placement, dimension and section rules fail on independent wire-valid changes.
def mutation_evidence(raw, model, graph, context, frame, world_curves):
    matrix = ResolveField(
        graph, context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (reference,) = LinkedNodes(graph, matrix, "dataRefs")
    recipe = ResolveField(graph, reference, "rRecipe", "EntityRecipe")
    xy = next(
        node for node in graph.ByClass("WorkPlane") if node.Fields["originName"] == "XY"
    )
    width, _ = LinkedNodes(graph, context.Sketch, "dimensions")
    results = {}
    cases = (
        (
            "single_matrix_changed",
            mutation_archive(model, matrix, "matrix3d", MatrixValue(None)),
            read_frame,
            "YZ CoordinateSystem and DRMatrix disagree about placement",
        ),
        (
            "different_origin_datum",
            mutation_archive(model, recipe, "m_entityId", xy.ObjectId),
            read_frame,
            "YZ matrix recipe does not select the owned origin datum",
        ),
        (
            "wrong_width_local_axis",
            mutation_archive(model, width, "constraintType", 1 << 22),
            read_dimensions,
            "Unsupported native Fusion FusionSketchLinearDim.constraintType",
        ),
    )
    for label, changed, reader, expected in cases:
        decoded = ReadDocument(changed)
        changed_graph = BuildGraph(decoded)
        changed_context = SelectExtrusion(changed_graph)
        args = (
            (changed_graph, changed_context, decoded)
            if reader is read_frame
            else (changed_graph, changed_context)
        )
        results[label] = refusal(lambda: reader(*args), expected)
    for label, root, first, attr in (
        ("world_section_curve", 2, 88, 152),
        ("local_section_curve", 3, 113, 160),
    ):
        changed, decoded = change_section(raw, model, root, first, attr)
        results[label] = refusal(
            lambda: read_datum_parts(
                changed, decoded, frame, world_curves, 1.0, 8000.0
            ),
            "YZ section omits a selected curve",
        )
    return results


# Existing refusal, partial archive custody and writer routing stay public consequences of the source boundary.
def public_guards(snapshot, raw, document):
    control = snapshot.blob(
        REVISION,
        "re/automation/PairedCaptures/P03/fusion-8d53584027ff/P03-fusion-baseline-a.f3d",
    )
    require(
        sha256(control) == POSITIVE["baseline-a"]
        and len(open_document(control, strict=True).bodies) == 1,
        "Established positive XY strict control differs",
    )
    target = BytesIO()
    writer = refusal(
        lambda: write_document(
            document, target, destination_format="fusion.f3d", allow_carrier=False
        ),
        "fusion.f3d does not support the destination",
        AdapterNotFoundError,
    )
    require(
        not target.getvalue(),
        "Research-only document unexpectedly reached the public writer",
    )
    stripped = replace(
        document,
        metadata={"fusion.native_state": document.metadata["fusion.native_state"]},
    )
    stripped_writer = refusal(
        lambda: write_document(
            stripped, target, destination_format="fusion.f3d", allow_carrier=False
        ),
        REFUSED["plane-yz"][1],
    )
    require(
        not target.getvalue(), "Marker-stripped YZ research state emitted archive bytes"
    )
    return {
        "yz_strict": refusal(
            lambda: open_document(raw, strict=True), REFUSED["plane-yz"][1]
        ),
        "partial_exact_archive": True,
        "xy_strict_body_count": 1,
        "research_document_public_writer": writer,
        "marker_stripped_v2_writer": stripped_writer,
    }


# Compare the original sealed save and both native observer receipts without emitting a new archive.
def report():
    snapshot = GitSnapshot(ROOT)
    spec_data = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(spec_data) == SPECIFICATION_SHA256, "YZ P03 specification digest differs"
    )
    spec = snapshot.parse_document(spec_data, SPECIFICATION)
    (recipe,) = [item for item in spec["recipes"] if item["id"] == "P03"]
    captures = {
        app: capture(snapshot, recipe, app, spec) for app in ("fusion", "solidworks")
    }
    asset = captures["fusion"][1]["plane-yz"]
    raw = snapshot.blob(REVISION, asset["path"])
    require(
        sha256(raw) == asset["sha256"] == REFUSED["plane-yz"][0],
        "YZ source archive digest differs",
    )
    observations = {app: data[2]["plane-yz"] for app, data in captures.items()}
    require(
        {app: value[0] for app, value in observations.items()}
        == {"fusion": "same_process_reopen", "solidworks": "separate_process_reopen"},
        "YZ licensed observation phases differ",
    )
    model = ReadDocument(raw)
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    frame, frame_evidence = read_frame(graph, context, model)
    proof, drivers, dimensions = read_dimensions(graph, context)
    shape = ReadRectangle(graph, context, proof)
    local, sides, progenitor = design_curves(graph, context, model.Asset.AssetId)
    curves = {
        tag: frozenset(world_point(frame, (*point, 0.0)) for point in edge)
        for tag, edge in local.items()
    }
    extent = NumberValue(context.Along.Fields["value"])
    parts = read_datum_parts(
        raw, model, frame, curves, extent, observations["fusion"][1]["volume_mm3"]
    )
    require(
        (parts.evidence["history_sha256"], parts.evidence["snapshot_sha256"])
        == (HISTORY_SHA256, SNAPSHOT_SHA256),
        "YZ original native geometry custody differs",
    )
    tag = face_and_body_tags(parts.journal_table)[parts.journal.BodyRef]
    identity = body_identity(
        graph,
        context,
        model,
        SimpleNamespace(journal_solid=parts.journal, history=model.Bodies[0].History),
        progenitor,
        tag,
    )
    faces = match_face_tags(parts, identity["operation_id"], extent, sides, curves)
    document, state = neutral_body(
        raw, model, graph, context, frame, shape, proof, drivers
    )
    observed = compare_native(
        observations, document, frame_evidence["world_axes"], curves
    )
    CheckSignedMass(
        context,
        tuple(value / 10 for value in observed["bounds_world_mm"][0]),
        tuple(value / 10 for value in observed["bounds_world_mm"][1]),
    )
    return {
        "schema": 1,
        "source_revision": REVISION,
        "archive_sha256": sha256(raw),
        "specification_sha256": SPECIFICATION_SHA256,
        "scope": "saved P03 metric YZ proof only",
        "native_receipts": {
            app: {
                **{
                    key: data[0][key]
                    for key in (
                        "receipt",
                        "measurements",
                        "application_build",
                        "qualification_blockers",
                    )
                },
                "phase": observations[app][0],
            }
            for app, data in captures.items()
        },
        "frame": frame_evidence,
        "sketch_local_base_mm": shape.BasePoint,
        "dimensions": dimensions,
        "driver_literals": {item.name: item.expression.source for item in drivers},
        "positive_depth_cm": extent,
        "owner": identity,
        "world_faces_cm": faces,
        "body": observed,
        "saved_geometry": parts.evidence,
        "state": state,
        "wire_valid_mutation_refusals": mutation_evidence(
            raw, model, graph, context, frame, curves
        ),
        "public_guards": public_guards(snapshot, raw, document),
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
