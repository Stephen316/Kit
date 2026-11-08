# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from uuid import UUID as ParseUuid

from convert.formats.Fusion.MetaCursor import MetaCursor


# manifest fields share the native counted string grammar and exact record boundaries
class ManifestCursor(MetaCursor):

    # canonical nonzero tokens permit exact identity comparisons across records
    def ReadGuid(Cursor) -> str:
        Value = Cursor.ReadText(True, Maximum=36)
        GuidValue = ParseUuid(Value)
        if GuidValue.int == 0 or str(GuidValue) != Value:
            raise ValueError("Invalid Fusion manifest GUID")
        return Value

    # fixed property keys keep unrelated version values from satisfying a manifest schema
    def ReadVersions(Cursor, KeysValue: tuple[str, ...]) -> tuple[tuple[str, int], ...]:
        if Cursor.ReadCount(len(KeysValue)) != len(KeysValue):
            raise ValueError("Invalid Fusion manifest version count")
        Values = tuple((Cursor.ReadText(), Cursor.ReadWord()) for KeyName in KeysValue)
        if tuple(KeyName for KeyName, Version in Values) != KeysValue:
            raise ValueError("Invalid Fusion manifest version keys")
        return Values

    # unknown trailing fields must keep the current schema from being observed
    def CheckEnd(Cursor) -> None:
        if Cursor.Offset != len(Cursor.DataValue):
            raise ValueError("Unexpected Fusion manifest trailing data")
