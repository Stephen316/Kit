# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditShape.OpenSketchGeom import ReadOpenGeom
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.payloads.PayloadRoles import PayloadRole


# each sketch only timeline step owns one exact sketch and support pair
@MakeDataClass(frozen=True, slots=True)
class EditSketchInput:
    StepValue: FeatureStep
    SketchValue: Sketch
    PlaneValue: SupportPlane


# partial timeline state cannot establish an independent modeling input
def HasEditState(FeatureValue: FeatureStep) -> bool:
    return (
        not (
            FeatureValue.suppressed
            or FeatureValue.configuration_states
            or FeatureValue.selection_ids
        )
        and FeatureValue.attributes.get("fusion.state_known") is True
        and FeatureValue.attributes.get("fusion.rolled_back") is False
    )


# unrelated feature geometry remains safe only in the single body standalone scope
def HasEditDoc(DocValue: CadDocument, FeatureValue: FeatureStep) -> bool:
    if (
        DocValue.source.format_id != "fusion.f3d"
        or DocValue.units != UnitSystem.KMillimeter
        or DocValue.assembly is not None
        or DocValue.brep is None
        or DocValue.meshes
        or DocValue.selections
        or len(DocValue.bodies) != 1
        or len(DocValue.feature_timeline) < 2
        or len(DocValue.configurations) != 1
        or any(Value.role != PayloadRole.KDocument for Value in DocValue.brep_payloads)
    ):
        return False
    Config = DocValue.configurations[0]
    return (
        DocValue.feature_timeline[-1] == FeatureValue
        and DocValue.bodies[0].final_feature_id == FeatureValue.id
        and len(FeatureValue.input_feature_ids) == 1
        and HasEditState(FeatureValue)
        and Config.active
        and not (Config.parent_id or Config.overrides or Config.suppressed_feature_ids)
    )


# a prior step can be skipped only when it is a known independent sketch input
def ReadSketchInput(
    StepValue: FeatureStep,
    Sketches: dict[str, Sketch],
    Planes: dict[str, SupportPlane],
) -> EditSketchInput | None:
    if (
        StepValue.kind != FeatureKind.KNative
        or StepValue.operation is not None
        or StepValue.definition is not None
        or StepValue.input_feature_ids
        or StepValue.parameter_ids
        or not HasEditState(StepValue)
    ):
        return None
    SketchValue = Sketches.get(StepValue.sketch_id or "")
    if SketchValue is None:
        return None
    PlaneValue = Planes.get(SketchValue.support_plane_id)
    if (
        PlaneValue is None
        or PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
    ):
        return None
    try:
        CheckPrismFrame(PlaneValue.transform)
    except (TypeError, ValueError, OverflowError):
        return None
    return EditSketchInput(StepValue, SketchValue, PlaneValue)


# all retained geometry must map to original sketch steps and exactly one driving dependency
def ReadEditScope(
    DocValue: CadDocument, FeatureValue: FeatureStep
) -> tuple[EditSketchInput, ...] | None:
    if not HasEditDoc(DocValue, FeatureValue):
        return None
    Timeline = DocValue.feature_timeline
    if len({Value.id for Value in Timeline}) != len(Timeline) or any(
        First.order >= Second.order for First, Second in zip(Timeline, Timeline[1:])
    ):
        return None
    Sketches = {Value.id: Value for Value in DocValue.sketches}
    Planes = {Value.id: Value for Value in DocValue.support_planes}
    if len(Sketches) != len(DocValue.sketches) or len(Planes) != len(
        DocValue.support_planes
    ):
        return None
    Inputs: list[EditSketchInput] = []
    DriverId = FeatureValue.input_feature_ids[0]
    HasDriver = False
    for StepValue in Timeline[:-1]:
        Input = ReadSketchInput(StepValue, Sketches, Planes)
        if Input is None:
            return None
        if StepValue.id == DriverId:
            if Input.SketchValue.id != FeatureValue.sketch_id:
                return None
            HasDriver = True
        elif ReadOpenGeom(Input.SketchValue) is None:
            return None
        Inputs.append(Input)
    SketchIds = {Value.SketchValue.id for Value in Inputs}
    PlaneIds = {Value.PlaneValue.id for Value in Inputs}
    if (
        not HasDriver
        or len(SketchIds) != len(Inputs)
        or SketchIds != set(Sketches)
        or PlaneIds != set(Planes)
    ):
        return None
    return tuple(Inputs)


# the editable writer and saved readback must agree on the same disconnected scope
def IsEditExtScope(DocValue: CadDocument, FeatureValue: FeatureStep) -> bool:
    return ReadEditScope(DocValue, FeatureValue) is not None
