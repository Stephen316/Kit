# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.MetaIndex import ReadMetaIndex, SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan


# continuation records belong only to classes in the registered primary lineage
def IsAncestor(ClassGuid: str, BaseGuid: str, Parents: dict[str, str]) -> bool:
    Visited: set[str] = set()
    while BaseGuid in Parents and BaseGuid not in Visited:
        if ClassGuid == BaseGuid:
            return True
        Visited.add(BaseGuid)
        BaseGuid = Parents[BaseGuid]
    return False


# downstream decoders need verified payload boundaries and stable native ownership
def ReadBulkSpans(
    BulkData: bytes, MetaData: bytes, *, Segment: SegmentKind = SegmentKind.KDesign
) -> tuple[RecordSpan, ...]:
    Classes, Owners, Entries = ReadMetaIndex(MetaData, Segment=Segment)
    Entries.sort()
    if not Entries or Entries[0][0] != 0:
        raise ValueError("Missing initial Fusion BulkStream record")
    Parents = {ClassGuid: BaseGuid for ClassGuid, BaseGuid, _ in Classes.values()}
    Records: list[RecordSpan] = []
    for Index, (Start, Identity, IsPrimary) in enumerate(Entries):
        Finish = Entries[Index + 1][0] if Index + 1 < len(Entries) else len(BulkData)
        if not Start + 4 <= Finish <= len(BulkData):
            raise ValueError("Invalid Fusion BulkStream record extent")
        CodeLength = int(UnpackFrom("<I", BulkData, Start)[0])
        Payload = Start + 12 + CodeLength
        if not 1 <= CodeLength <= 8 or Payload > Finish:
            raise ValueError("Invalid Fusion BulkStream record header")
        CodeBytes = BulkData[Start + 4 : Payload - 8]
        if not CodeBytes.isdigit():
            raise ValueError("Invalid Fusion BulkStream class code")
        CodeValue = int(CodeBytes)
        ClassData = Classes.get(CodeValue)
        if ClassData is None or str(CodeValue).encode("ascii") != CodeBytes:
            raise ValueError("Unregistered Fusion BulkStream class code")
        ClassGuid, _, ClassSpace = ClassData
        StoredId = int(UnpackFrom("<Q", BulkData, Payload - 8)[0])
        OwnerCode = Owners[Identity]
        if StoredId != Identity or (
            CodeValue != OwnerCode
            if IsPrimary
            else not IsAncestor(ClassGuid, Classes[OwnerCode][1], Parents)
        ):
            raise ValueError("Fusion BulkStream header and index disagree")
        Records.append(
            RecordSpan(
                Start,
                Payload,
                Finish,
                Identity,
                CodeValue,
                ClassGuid,
                ClassSpace,
                IsPrimary,
            )
        )
    return tuple(Records)
