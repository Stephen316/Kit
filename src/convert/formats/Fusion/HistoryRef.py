# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.MetaCursor import MetaCursor


# native references must remain typed and bounded within their parent record
def ReadNativeRef(Cursor: MetaCursor) -> int:
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Invalid Fusion history reference tag")
    Identity = Cursor.ReadLong()
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Invalid Fusion history reference suffix")
    return Identity


# optional references share the same bounded wire format as required references
def ReadOptRefMut(Cursor: MetaCursor) -> int | None:
    if Cursor.TakeBytes(1) == b"\0":
        return None
    Cursor.Offset -= 1
    return ReadNativeRef(Cursor)
