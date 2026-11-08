# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid


# body variants put the reciprocal key after the optional typed genesis reference
def ReadBodyOffset(
    BulkData: bytes, OwnerSpan: RecordSpan, Owners: dict[int, RecordSpan]
) -> int:
    Finish = min(OwnerSpan.PayloadOffset + 67, OwnerSpan.EndOffset)
    Cursor = MetaCursor(BulkData[OwnerSpan.PayloadOffset : Finish])
    Header = Cursor.TakeBytes(6)
    if Header == bytes(6):
        return Cursor.Offset
    if Header != bytes(5) + b"\1":
        raise ValueError("Unsupported Fusion ACT body route prefix")
    if Cursor.ReadCount(1) == 0:
        return Cursor.Offset
    if (
        Cursor.ReadText(Maximum=24)
        not in ("BASEFEAT_PM_BODY_REF", "BASEFEAT_DM_BODY_REF")
        or Cursor.ReadText(Maximum=18) != "PassiveRefMetaType"
    ):
        raise ValueError("Unsupported Fusion ACT body route attribute")
    Target = Owners.get(ReadNativeRef(Cursor))
    if Target is None or (Target.ClassGuid, Target.ClassSpace) != (KBodyGuid, "Body"):
        raise ValueError("Fusion ACT body route attribute has no typed body")
    return Cursor.Offset
