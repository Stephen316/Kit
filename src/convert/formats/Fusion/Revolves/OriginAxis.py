# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isclose as IsClose
from struct import unpack as Unpack

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from interchange.geometry.models.VectorSpace import SpaceVector

# origin and custom axes share a registered geometry class
KAxisGuid = "19031004-3AB6-4D13-ABBF-C51EE214688D"

# reciprocal origin membership distinguishes axes from standalone construction geometry
KOriginGuid = "2972A3B8-3627-49BC-8C3D-18707605EC44"

# typed component identity prevents comparing axes across unrelated coordinate spaces
KComponentGuid = "E03784ED-5E19-4E14-B9F2-3B07017018CD"


# plane limits require a positively identified axis in the same sketch component
def ReadOriginAxis(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    AxisId: int,
    ComponentId: int,
) -> tuple[str, SpaceVector, SpaceVector, int]:
    AxisCursor = SelectCursor(BulkData, Owners, AxisId, KAxisGuid)
    if len(AxisCursor.DataValue) != 186:
        raise ValueError("Unsupported Fusion origin axis layout")
    Attributes = ReadGeomAttrs(AxisCursor)
    Genesis = Attributes.get("EntityGenesis")
    if len(Attributes) != 1 or type(Genesis) is not int or Genesis != 0:
        raise ValueError("Unsupported Fusion origin axis attributes")
    Origin, Direction = (Unpack("<3d", AxisCursor.TakeBytes(24)) for _ in range(2))
    _ = AxisCursor.TakeBytes(26)
    AxisName = AxisCursor.ReadText(True, Maximum=1)
    if AxisName not in ("X", "Y", "Z") or not all(
        IsClose(Value, Expected, rel_tol=0.0, abs_tol=1e-9)
        for Value, Expected in zip(
            (*Origin, *Direction),
            (0.0, 0.0, 0.0, *(float(Label == AxisName) for Label in "XYZ")),
        )
    ):
        raise ValueError("Fusion origin axis name and coefficients disagree")
    AxisCursor.Offset = len(AxisCursor.DataValue) - 11
    ContainerId = ReadNativeRef(AxisCursor)
    Container = SelectCursor(BulkData, Owners, ContainerId, KOriginGuid)
    if len(Container.DataValue) != 96 or Container.TakeBytes(8) != b"\0\0\0\0\7\0\0\0":
        raise ValueError("Unsupported Fusion origin axis container")
    Members = {ReadNativeRef(Container) for _ in range(7)}
    if (
        len(Members) != 7
        or AxisId not in Members
        or ReadNativeRef(Container) != ComponentId
    ):
        raise ValueError("Fusion origin axis is not owned by the sketch component")
    _ = SelectCursor(BulkData, Owners, ComponentId, KComponentGuid)
    return (
        AxisName,
        SpaceVector(*(Value * 10.0 for Value in Origin)),
        SpaceVector(*Direction),
        ContainerId,
    )
