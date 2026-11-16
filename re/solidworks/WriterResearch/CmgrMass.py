# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackFields

from convert.adapters.solidworks.container.Archive import ArchiveError, EncodeString
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor

# The no-body constructor clears centroid, volume, area, mass and six moments.
KGeometryLayout = "<12d"
KEmptyGeometry = (0.0,) * 12

# The standalone part carries one initialized flag and a zero accuracy value.
KOptionsLayout = "<5id4i"
KEmptyOptions = (1, 0, 0, 0, 0, 0.0, 0, 0, 0, 0)

# The trailing coordinate frame retains the three initialized Cartesian axes.
KFrameLayout = "<i12diH"
KEmptyFrame = (
    0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    1,
    0,
)


# The enclosing configuration supplies the generation and its body count.
def CheckEmptyMass(Generation: int, BodyCount: int) -> None:
    if type(Generation) is not int or Generation != 19000:
        raise ArchiveError("the empty configuration mass record requires generation 19000")
    if type(BodyCount) is not int or BodyCount != 0:
        raise ArchiveError("the empty configuration mass record requires zero bodies")


# Source defaults suffice for the bounded cache without reading a native archive.
def EncodeEmptyMass(Generation: int, BodyCount: int) -> bytes:
    CheckEmptyMass(Generation, BodyCount)
    return b"".join(
        (
            PackFields(KGeometryLayout, *KEmptyGeometry),
            PackFields(KOptionsLayout, *KEmptyOptions),
            EncodeString(""),
            EncodeString(""),
            PackFields(KFrameLayout, *KEmptyFrame),
        )
    )


# The returned position is the enclosing configuration's next field.
def ReadEmptyMass(
    BlobValue: bytes, Offset: int, Generation: int, BodyCount: int
) -> int:
    CheckEmptyMass(Generation, BodyCount)
    if type(Offset) is not int or Offset < 0:
        raise ArchiveError(f"invalid empty configuration mass offset {Offset}")
    Cursor = FieldCursor(BlobValue, Offset)
    RequireArch(
        Cursor.ReadValue(KGeometryLayout), KEmptyGeometry, "empty mass geometry"
    )
    RequireArch(
        Cursor.ReadValue(KOptionsLayout), KEmptyOptions, "empty mass options"
    )
    for FieldName in ("center coordinate system", "reference coordinate system"):
        NameOffset = Cursor.Offset
        RequireArch(Cursor.ReadText(), "", FieldName)
        RequireArch(Cursor.Offset - NameOffset, 4, f"{FieldName} wide CString")
    RequireArch(Cursor.ReadValue(KFrameLayout), KEmptyFrame, "empty mass frame")
    return Cursor.Offset
