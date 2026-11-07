# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as Pack, unpack_from as UnpackFrom

from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.RecordSpan import RecordSpan

# the registry distinguishes the two observed numeric binding representations
KBindingWidths = {
    "D91D429C-1BB5-4640-B49F-69AF14F463E9": 85,
    "A085449A-5144-4B2B-B455-7F7035A40559": 82,
}


# native owner claims require matching parameter identity owner copies and cached value
def ResolveOwner(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ParamData: NativeParam,
    ParamSpan: RecordSpan,
) -> tuple[RecordSpan, RecordSpan] | None:
    if ParamData.BindingId is None:
        return None
    Binding = Owners.get(ParamData.BindingId)
    if Binding is None or Binding.ClassGuid not in KBindingWidths:
        raise ValueError(
            "Fusion numeric binding record is missing or has an unknown class"
        )
    BodyValue = BulkData[Binding.PayloadOffset + 4 : Binding.EndOffset]
    Width = KBindingWidths[Binding.ClassGuid]
    ParamOffset = 30 if Width == 85 else 27
    if (
        len(BodyValue) != Width
        or BodyValue[:6] != b"\1\1\0\0\0\1"
        or BodyValue[ParamOffset - 1] != 1
        or BodyValue[-11] != 1
        or BodyValue[-2:] != bytes(2)
    ):
        raise ValueError("Invalid Fusion numeric binding framing")
    OwnerId = int(UnpackFrom("<Q", BodyValue, 6)[0])
    OwnerSpan = Owners.get(OwnerId)
    if (
        OwnerSpan is None
        or OwnerId in (Binding.ObjectId, ParamSpan.ObjectId)
        or UnpackFrom("<Q", BodyValue, Width - 10)[0] != OwnerId
        or UnpackFrom("<Q", BodyValue, ParamOffset)[0] != ParamSpan.ObjectId
    ):
        raise ValueError("Fusion numeric binding owner or parameter identity disagrees")
    if Width == 85:
        Matches = BodyValue[21:29] == Pack("<d", ParamData.Number)
    else:
        Matches = (
            BodyValue[21] == 1
            and UnpackFrom("<I", BodyValue, 22)[0] == ParamData.Number
        )
    if not Matches:
        raise ValueError("Fusion numeric binding value disagrees")
    return OwnerSpan, Binding
