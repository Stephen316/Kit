# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.MetaCursor import MetaCursor


# capture registry ownership so bulk headers cannot assign their own record classes
def ReadMetaIndex(
    MetaData: bytes,
) -> tuple[
    dict[int, tuple[str, str, str]],
    dict[int, int],
    list[tuple[int, int, bool]],
]:
    Cursor = MetaCursor(MetaData)
    KindValue = Cursor.ReadText()
    _ = Cursor.ReadWord(), Cursor.ReadText(True)
    Magic, Version, _, _ = (Cursor.ReadWord() for _ in range(4))
    Repeated, _ = Cursor.ReadText(), Cursor.ReadText()
    Storage = Cursor.ReadWord(), Cursor.ReadWord()
    if (
        KindValue != "FusionDesignSegmentType"
        or Repeated != KindValue
        or Magic != 1234
        or Version != 8
        or Storage != (1, 0)
    ):
        raise ValueError("Unsupported Fusion design MetaStream")

    Classes: dict[int, tuple[str, str, str]] = {}
    Owners: dict[int, int] = {}
    KnownGuids: set[str] = set()
    for CodeValue in range(256, 256 + Cursor.ReadCount(100000)):
        ClassGuid, BaseGuid = Cursor.ReadText(), Cursor.ReadText()
        _ = Cursor.ReadWord()
        ClassSpace = Cursor.ReadText()
        if not ClassGuid or ClassGuid in KnownGuids:
            raise ValueError("Missing or duplicate Fusion class GUID")
        KnownGuids.add(ClassGuid)
        Classes[CodeValue] = ClassGuid, BaseGuid, ClassSpace
        for _ in range(Cursor.ReadCount(1000000)):
            Identity = Cursor.ReadLong()
            if Identity in Owners:
                raise ValueError("Duplicate primary Fusion object identity")
            Owners[Identity] = CodeValue

    _ = Cursor.TakeBytes(8 * Cursor.ReadCount(1000000))
    Entries: list[tuple[int, int, bool]] = []
    PrimaryIds: set[int] = set()
    for IsPrimary in (True, False):
        for _ in range(Cursor.ReadCount(1000000)):
            Identity, Offset = Cursor.ReadLong(), Cursor.ReadLong()
            if Identity not in Owners or (IsPrimary and Identity in PrimaryIds):
                raise ValueError("Fusion index and class registry disagree")
            if IsPrimary:
                PrimaryIds.add(Identity)
            Entries.append((Offset, Identity, IsPrimary))
    NextId, _ = Cursor.ReadLong(), Cursor.ReadWord()
    if PrimaryIds != Owners.keys() or (Owners and NextId <= max(Owners)):
        raise ValueError("Invalid Fusion primary identity index")
    Properties: set[str] = set()
    for _ in range(Cursor.ReadCount(1024)):
        NameValue, _ = Cursor.ReadText(), Cursor.ReadWord()
        if NameValue in Properties:
            raise ValueError("Duplicate Fusion metadata property")
        Properties.add(NameValue)
    if Cursor.Offset != len(MetaData):
        raise ValueError("Trailing Fusion MetaStream data")
    return Classes, Owners, Entries
