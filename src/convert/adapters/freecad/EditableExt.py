# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditExtBody import IsEditExtBody
from convert.adapters.freecad.EditExtDepth import GetEditDepth
from convert.adapters.freecad.EditExtProfile import GetEditCircle
from convert.adapters.freecad.EditExtScope import IsEditExtScope
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.VectorSpace import SpaceVector


# native extrusion emission and transfer accounting must agree on the same proven controls
@MakeDataClass(frozen=True, slots=True)
class EditExtrude:
    SketchId: str
    ParameterId: str
    DistanceMm: float
    Direction: SpaceVector


# only profiles with a matching saved solid and an exact literal depth can become live
def ReadEditExtrude(
    DocValue: CadDocument, FeatureValue: FeatureStep
) -> EditExtrude | None:
    Definition = FeatureValue.definition
    if not isinstance(Definition, DistanceExtrude) or not IsEditExtScope(
        DocValue, FeatureValue
    ):
        return None
    SketchValue = DocValue.sketches[0]
    PlaneValue = DocValue.support_planes[0]
    Frame = PlaneValue.transform
    if (
        PlaneValue.id != SketchValue.support_plane_id
        or PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
        or Frame.z_axis != Definition.Direction
    ):
        return None
    try:
        Profile = GetEditCircle(FeatureValue, SketchValue)
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
    return EditExtrude(
        SketchValue.id, Definition.AlongParameterId, DepthMm, Definition.Direction
    )
