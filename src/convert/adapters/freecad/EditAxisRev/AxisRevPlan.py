# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from math import degrees as Degrees, dist as Distance, tau as FullTurn

from convert.adapters.freecad.EditableRev import EditRevolve
from convert.adapters.freecad.EditAxisRev.AxisEndpoints import (
    ReadAxisLine,
    WorldAxisLine,
)
from convert.adapters.freecad.EditAxisRev.AxisProfile import ReadAxisProfile
from convert.adapters.freecad.EditAxisRev.AxisRevScope import ReadAxisScope
from convert.adapters.freecad.EditAxisRev.AxisSelect import ReadAxisPick
from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.adapters.freecad.EditRev.RevBodyProof import CheckRevBody
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the live angular feature retains both directed endpoints and original point joins
@MakeDataClass(frozen=True, slots=True)
class AxisRevPlan:
    Revolve: EditRevolve
    AxisSketchId: str
    AxisLineId: str
    AxisStart: SpaceVector
    AxisEnd: SpaceVector
    AxisSense: int
    AxisPointIds: tuple[str, str]
    ProfilePairs: tuple[tuple[str, str], ...]
    AxisFrame: Transform
    ProfileFrame: Transform


# the original directed line and effective sweep axis must describe the same world line
def ReadAxisSense(
    Definition: AngularRevolve, Start: SpaceVector, Direction: SpaceVector
) -> int:
    AxisValue = Definition.AxisDirection
    Sense = 1 if DotVector(Direction, AxisValue) > 0.0 else -1
    if (
        Start != Definition.AxisOrigin
        or Distance(
            (AxisValue.x, AxisValue.y, AxisValue.z),
            (Sense * Direction.x, Sense * Direction.y, Sense * Direction.z),
        )
        > 1e-9
    ):
        raise ValueError(
            "FreeCAD editable Revolve axis disagrees with its selected line"
        )
    return Sense


# exact source linkage and full rebuilt geometry qualify the standalone axis sweep
def ReadAxisRev(DocValue: CadDocument, FeatureValue: FeatureStep) -> AxisRevPlan | None:
    Definition = FeatureValue.definition
    if not isinstance(Definition, AngularRevolve) or Definition.SideMode != "one_sided":
        return None
    try:
        Profile, AxisInput, BodyValue = ReadAxisScope(DocValue, FeatureValue)
        AxisSketch = AxisInput.SketchValue
        AxisFrame = AxisInput.PlaneValue.transform
        LineId = ReadAxisPick(
            FeatureValue, Definition, DocValue.selections[0], AxisSketch
        )
        Geometry, PointIds = ReadAxisLine(AxisSketch, LineId)
        Start, Finish, Direction = WorldAxisLine(Geometry, AxisFrame)
        AxisSense = ReadAxisSense(Definition, Start, Direction)
        Pairs = ReadAxisProfile(FeatureValue, Profile.SketchValue)
        Along, Against = ReadRevAngles(FeatureValue, Definition, DocValue.parameters)
        Interval = GetAngleSpan(Along, Against, Definition.SideMode)
        if Interval[1] - Interval[0] > FullTurn:
            return None
        CheckRevBody(
            BodyValue,
            DocValue,
            FeatureValue,
            Definition,
            Interval,
            Profile.SketchValue,
            Profile.PlaneValue,
        )
    except (AttributeError, IndexError, KeyError, OverflowError, TypeError, ValueError):
        return None
    return AxisRevPlan(
        EditRevolve(
            Profile.SketchValue.id,
            Definition.AxisOrigin,
            Definition.AxisDirection,
            Degrees(Along),
            Definition.AlongParameterId,
        ),
        AxisSketch.id,
        LineId,
        Start,
        Finish,
        AxisSense,
        PointIds,
        Pairs,
        AxisFrame,
        Profile.PlaneValue.transform,
    )
