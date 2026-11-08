# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# a complete metadata table cannot alias identities or physical record positions
def CheckWireBody(Value: MetaSegment) -> None:
    Owners: set[int] = set()
    ClassGuids: set[str] = set()
    for Entry in Value.Classes:
        if not Entry.ClassGuid or Entry.ClassGuid in ClassGuids:
            raise ValueError("Missing or duplicate Fusion class GUID")
        ClassGuids.add(Entry.ClassGuid)
        for Identity in Entry.OwnerIds:
            if Identity in Owners:
                raise ValueError("Duplicate primary Fusion object identity")
            Owners.add(Identity)
    Primary = {Entry.ObjectId for Entry in Value.Primary}
    if (
        len(Primary) != len(Value.Primary)
        or Primary != Owners
        or (Owners and Value.NextId <= max(Owners))
        or any(Entry.ObjectId not in Owners for Entry in Value.Continuations)
    ):
        raise ValueError("Fusion index and class registry disagree")
    Offsets = {Entry.Offset for Entry in Value.Primary}
    Offsets.update(Entry.Offset for Entry in Value.Continuations)
    if len(Offsets) != len(Value.Primary) + len(Value.Continuations):
        raise ValueError("Duplicate Fusion MetaStream record offset")
    if len({Entry.PropName for Entry in Value.Properties}) != len(Value.Properties):
        raise ValueError("Duplicate Fusion metadata property")
