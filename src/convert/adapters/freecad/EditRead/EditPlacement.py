# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos as Cosine, hypot as Hypot, isclose as IsClose, sin as SineValue

from convert.adapters.freecad.EditRead.XmlField import EditChild, EditFloat
from convert.adapters.freecad.Native import IsTransformNear, NativeObject, TransformA
from interchange.geometry.models.Transform import Transform

# freecad serializes both quaternion and axis angle representations of the same transform
KEditFrameTol = 1e-9


# agreeing placement representations rule out a hidden change in the saved profile frame
def CheckEditFrame(
    ObjectValue: NativeObject,
    NameValue: str,
    Expected: Transform,
    Optional: bool = False,
) -> None:
    if Optional and NameValue not in ObjectValue.properties:
        return
    Placement = EditChild(
        ObjectValue, NameValue, "App::PropertyPlacement", "PropertyPlacement"
    )
    for Field in ("Px", "Py", "Pz"):
        EditFloat(Placement, Field)
    Quaternion = tuple(
        EditFloat(Placement, Field) for Field in ("Q0", "Q1", "Q2", "Q3")
    )
    if not IsClose(Hypot(*Quaternion), 1.0, rel_tol=0.0, abs_tol=KEditFrameTol):
        raise ValueError(
            f"FreeCAD editable {ObjectValue.name}.{NameValue} quaternion is invalid"
        )
    AxisKeys = ("A", "Ox", "Oy", "Oz")
    if any(Field in Placement.attrib for Field in AxisKeys):
        Angle, *AxisValue = (EditFloat(Placement, Field) for Field in AxisKeys)
        HalfAngle = Angle * 0.5
        FromAngle = tuple(
            SineValue(HalfAngle) * Component for Component in AxisValue
        ) + (Cosine(HalfAngle),)
        if not any(
            all(
                abs(Value - SignValue * Other) <= KEditFrameTol
                for Value, Other in zip(Quaternion, FromAngle)
            )
            for SignValue in (-1.0, 1.0)
        ):
            raise ValueError(
                f"FreeCAD editable {ObjectValue.name}.{NameValue} placement values disagree"
            )
    if not IsTransformNear(TransformA(Placement), Expected, KEditFrameTol):
        raise ValueError(
            f"FreeCAD editable {ObjectValue.name}.{NameValue} placement changed"
        )
