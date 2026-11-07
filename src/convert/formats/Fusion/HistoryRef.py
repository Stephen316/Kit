# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
def ReadOptionalRef(Cursor: MetaCursor) -> int | None:
    if Cursor.TakeBytes(1) == b"\0":
        return None
    Cursor.Offset -= 1
    return ReadNativeRef(Cursor)
