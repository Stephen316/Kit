# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from interchange.geometry.models.VectorPlane import PlaneVector


# curve endpoint references must resolve inside the owning sketch point table
def ReadPointRef(
    BodyValue: bytes, Offset: int, Points: dict[int, PlaneVector]
) -> tuple[int, PlaneVector]:
    Cursor = MetaCursor(BodyValue)
    Cursor.Offset = Offset
    Identity = ReadNativeRef(Cursor)
    PointValue = Points.get(Identity)
    if PointValue is None:
        raise ValueError("Missing same-sketch Fusion curve point")
    return Identity, PointValue
