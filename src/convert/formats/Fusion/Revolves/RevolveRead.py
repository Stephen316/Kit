# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptionalRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Revolves.RevolveInput import RevolveInput
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs

# operation codes describe source intent independently of generated bodies
KOperations = {1: "join", 2: "cut", 3: "intersect", 4: "new_body"}


# distinguish inactive angle bindings from actual extent controls on the wire
def ReadRevInputs(BodyValue: bytes) -> RevolveInput:
    Cursor = MetaCursor(BodyValue)
    if BodyValue[:2] == b"\0\1":
        ReadGeomAttrs(Cursor)
    elif Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion Revolve prefix")
    Operation = KOperations.get(Cursor.ReadWord())
    ExtentCode = Cursor.ReadWord()
    if Operation is None or ExtentCode not in (1, 2) or Cursor.TakeBytes(1) != b"\0":
        raise ValueError("Unsupported Fusion Revolve operation or extent")
    Flags = Cursor.TakeBytes(4)
    if any(Flag not in (0, 1) for Flag in Flags):
        raise ValueError("Unsupported Fusion Revolve flags")
    Projected, Solid, Symmetric, TwoSided = Flags
    AgainstId = ReadOptionalRef(Cursor)
    AlongId = ReadOptionalRef(Cursor)
    AxisId = ReadNativeRef(Cursor)
    TargetTwo = ReadOptionalRef(Cursor)
    ReadNativeRef(Cursor)
    TargetOne = ReadOptionalRef(Cursor)
    if AlongId is None:
        raise ValueError("Missing Fusion Revolve along-angle binding")
    if ExtentCode == 1:
        if Symmetric or TwoSided or AgainstId is not None or TargetOne is None:
            raise ValueError("Fusion Revolve entity extent disagrees with its controls")
        Targets = (TargetOne,) if TargetTwo is None else (TargetOne, TargetTwo)
        ModeValue = "one_sided" if TargetTwo is None else "two_sided"
    else:
        if (
            TargetOne is not None
            or TargetTwo is not None
            or (Symmetric and TwoSided)
            or bool(Symmetric or TwoSided) != (AgainstId is not None)
        ):
            raise ValueError("Fusion Revolve angle extent disagrees with its controls")
        Targets = ()
        ModeValue = (
            "symmetric" if Symmetric else "two_sided" if TwoSided else "one_sided"
        )
    return RevolveInput(
        Operation,
        "to_entity" if Targets else "angle",
        ModeValue,
        bool(Projected),
        bool(Solid),
        AlongId,
        AgainstId,
        AxisId,
        Targets,
    )
