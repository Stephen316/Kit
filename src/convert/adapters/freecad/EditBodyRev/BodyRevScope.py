# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditExtScope import (
    EditSketchInput,
    HasEditState,
    ReadSketchInput,
)
from convert.formats.Fusion.Revolves.SketchAxis import KFrameGuid, KSketchGuid
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchBase, KSketchFeature
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.payloads.PayloadRoles import PayloadRole


# this native route owns exactly two linked solids in the same standalone history
def CheckBodyScope(DocValue: CadDocument, FeatureValue: FeatureStep) -> None:
    if (
        DocValue.source.format_id != "fusion.f3d"
        or DocValue.units != UnitSystem.KMillimeter
        or DocValue.assembly is not None
        or DocValue.brep is None
        or DocValue.meshes
        or len(DocValue.bodies) != 2
        or len(DocValue.feature_timeline) != 4
        or len(DocValue.sketches) != 2
        or len(DocValue.support_planes) != 2
        or len(DocValue.selections) != 1
        or len(DocValue.configurations) != 1
        or any(Value.role != PayloadRole.KDocument for Value in DocValue.brep_payloads)
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve requires two linked solids"
        )
    (Config,) = DocValue.configurations
    if (
        not Config.active
        or Config.parent_id
        or Config.overrides
        or Config.suppressed_feature_ids
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve configuration is unresolved"
        )
    CheckBodyHist(DocValue, FeatureValue)


# history edges identify exactly one sketch per operation and the earlier solid dependency
def CheckBodyHist(DocValue: CadDocument, FeatureValue: FeatureStep) -> None:
    SeedSketch, Extrude, Profile, Revolve = DocValue.feature_timeline
    if (
        len({Value.id for Value in DocValue.feature_timeline}) != 4
        or not SeedSketch.order < Extrude.order < Profile.order < Revolve.order
        or Revolve != FeatureValue
        or Extrude.kind != FeatureKind.KExtrusion
        or Revolve.kind != FeatureKind.KRevolution
        or Extrude.operation != BooleanOp.KCreate
        or Revolve.operation != BooleanOp.KCreate
        or not HasEditState(Extrude)
        or Revolve.suppressed
        or Revolve.configuration_states
        or Revolve.attributes.get("fusion.state_known") is not True
        or Revolve.attributes.get("fusion.rolled_back") is not False
        or Extrude.input_feature_ids != (SeedSketch.id,)
        or Revolve.input_feature_ids != (Profile.id, Extrude.id)
        or Extrude.sketch_id != SeedSketch.sketch_id
        or Revolve.sketch_id != Profile.sketch_id
        or tuple(Value.final_feature_id for Value in DocValue.bodies)
        != (Extrude.id, Revolve.id)
    ):
        raise ValueError("FreeCAD editable body axis Revolve history is unresolved")


# typed fusion sketch and frame provenance excludes a flattened or generated sketch
def ReadBodySketch(
    StepValue: FeatureStep, Sketches: dict[str, Sketch], Planes: dict[str, SupportPlane]
) -> EditSketchInput:
    Input = ReadSketchInput(StepValue, Sketches, Planes)
    if Input is None:
        raise ValueError("FreeCAD editable body axis Revolve sketch link is unresolved")
    SketchValue, PlaneValue = Input.SketchValue, Input.PlaneValue
    SketchOrigin = SketchValue.provenance
    Component = PlaneValue.attributes.get("fusion.component_object_id")
    if (
        type(Component) is not int
        or Component <= 0
        or PlaneValue.attributes.get("fusion.coordinate_space") != "component"
        or SketchOrigin is None
        or SketchValue.id != f"fusion-sketch-{SketchOrigin.native_id}"
        or PlaneValue.id != f"fusion-sketch-frame-{SketchOrigin.native_id}"
        or any(
            Origin is None
            or Origin.adapter != "fusion.f3d"
            or tuple(SpanValue.record_kind for SpanValue in Origin.spans) != Kinds
            for Origin, Kinds in (
                (StepValue.provenance, (KSketchFeature,)),
                (SketchOrigin, (KSketchGuid,)),
                (PlaneValue.provenance, (KFrameGuid, KSketchBase)),
            )
        )
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve sketch provenance disagrees"
        )
    return Input


# both native sketch frames must be independently owned within one component
def ReadBodyInputs(DocValue: CadDocument) -> tuple[EditSketchInput, EditSketchInput]:
    Sketches = {Value.id: Value for Value in DocValue.sketches}
    Planes = {Value.id: Value for Value in DocValue.support_planes}
    SeedSketch, _, Profile, _ = DocValue.feature_timeline
    Source = ReadBodySketch(SeedSketch, Sketches, Planes)
    Result = ReadBodySketch(Profile, Sketches, Planes)
    SourcePlane, ResultPlane = Source.PlaneValue, Result.PlaneValue
    if (
        {Source.SketchValue.id, Result.SketchValue.id} != Sketches.keys()
        or {SourcePlane.id, ResultPlane.id} != Planes.keys()
        or len(Sketches) != 2
        or len(Planes) != 2
        or SourcePlane.attributes["fusion.component_object_id"]
        != ResultPlane.attributes["fusion.component_object_id"]
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve sketches are not independent"
        )
    return Source, Result
