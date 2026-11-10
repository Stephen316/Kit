# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditExtBody import IsEditExtBody
from convert.adapters.freecad.EditExtDepth import GetEditDepth
from convert.adapters.freecad.EditExtProfile import GetCenterPoint, GetEditCircle
from convert.adapters.freecad.EditExtRing import GetEditRing
from convert.adapters.freecad.EditExtScope import IsEditExtScope
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorSpace import SpaceVector


# native extrusion emission and transfer accounting must agree on the same proven controls
@MakeDataClass(frozen=True, slots=True)
class EditExtrude:
    SketchId: str
    ParameterId: str
    DistanceMm: float
    Direction: SpaceVector
    HasFormula: bool = False
    ProfileEditable: bool = False
    LineRing: bool = False


# profile placement belongs to the linked sketch regardless of native object ordering
def FindEditFrame(
    DocValue: CadDocument, SketchId: str | None
) -> tuple[Sketch, SupportPlane] | None:
    Sketches = tuple(Value for Value in DocValue.sketches if Value.id == SketchId)
    if len(Sketches) != 1:
        return None
    SketchValue = Sketches[0]
    Planes = tuple(
        Value
        for Value in DocValue.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    return (SketchValue, Planes[0]) if len(Planes) == 1 else None


# only profiles with a matching saved solid and proven depth controls can become live
def ReadEditExtrude(
    DocValue: CadDocument, FeatureValue: FeatureStep
) -> EditExtrude | None:
    Definition = FeatureValue.definition
    if not isinstance(Definition, DistanceExtrude) or not IsEditExtScope(
        DocValue, FeatureValue
    ):
        return None
    ProfileFrame = FindEditFrame(DocValue, FeatureValue.sketch_id)
    if ProfileFrame is None:
        return None
    SketchValue, PlaneValue = ProfileFrame
    Frame = PlaneValue.transform
    if (
        PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
        or Frame.z_axis != Definition.Direction
    ):
        return None
    try:
        Circle = GetEditCircle(FeatureValue, SketchValue)
        RingValue = GetEditRing(FeatureValue, SketchValue) if Circle is None else None
        Profile = Circle if Circle is not None else RingValue
        DepthMm = GetEditDepth(FeatureValue, Definition, DocValue.parameters)
        if (
            Profile is None
            or DepthMm is None
            or not IsEditExtBody(
                DocValue.bodies[0], DocValue.brep, Profile, Frame, DepthMm
            )
        ):
            return None
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None
    Along = next(
        Value
        for Value in DocValue.parameters
        if Value.id == Definition.AlongParameterId
    )
    return EditExtrude(
        SketchValue.id,
        Definition.AlongParameterId,
        DepthMm,
        Definition.Direction,
        bool(Along.expression and Along.expression.parameter_ids),
        RingValue is not None or GetCenterPoint(SketchValue) is not None,
        RingValue is not None,
    )
