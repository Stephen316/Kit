# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from struct import pack as PackStruct
from sys import float_info as FloatInfo

from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    EncodeClassRef,
    EncodeNull,
    EncodeString,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# the name and value are prepared before allocating either owned archive node
def DepthFields(NameValue: str, DepthMm: float) -> tuple[bytes, bytes]:
    if not isinstance(NameValue, str) or not NameValue.strip() or "\0" in NameValue:
        raise ValueError("the depth parameter requires a nonempty local name")
    if type(DepthMm) not in (int, float) or not 0 < DepthMm <= FloatInfo.max:
        raise ValueError(
            "the depth parameter requires a finite positive millimetre value"
        )
    DepthMetres = DepthMm / 1000
    if DepthMetres == 0:
        raise ValueError("the depth parameter underflows its metre value")
    CleanState, NeedsDocId, MissingDocId, ClearSecondary = 0, 0x40000000, -1, 0
    return EncodeString(NameValue), (
        PackStruct("<iIiI", CleanState, NeedsDocId, MissingDocId, ClearSecondary)
        + EncodeString("")
        + EncodeNull()
        + PackStruct("<dB", DepthMetres, 0)
    )


# existing distinct compact class indexes keep this fragment in the normal archive route
def DepthClasses(ClassIndexes: Mapping[str, int]) -> tuple[int, int]:
    ParamClass = ClassIndexes.get("moLengthParameter_c", 0)
    NameClass = ClassIndexes.get("moNodeName_c", 0)
    if ParamClass == NameClass or not all(
        type(Index) is int and 0 < Index < KBigObjectTag
        for Index in (ParamClass, NameClass)
    ):
        raise ValueError(
            "the depth node requires two distinct compact class allocations"
        )
    return ParamClass, NameClass


# the standalone fragment encodes the same compact references as the tracking writer
def EncodeDepth(
    NameValue: str, DepthMm: float, ClassIndexes: Mapping[str, int]
) -> bytes:
    NameBytes, ValueBytes = DepthFields(NameValue, DepthMm)
    ParamClass, NameClass = DepthClasses(ClassIndexes)
    return (
        EncodeClassRef(ParamClass) + EncodeClassRef(NameClass) + NameBytes + ValueBytes
    )


# each class reference creates a real object in the enclosing archive map
def WriteDepthMut(Writer: ArchiveWriter, NameBytes: bytes, ValueBytes: bytes) -> None:
    Writer.begin_object("moLengthParameter_c", 1)
    Writer.begin_object("moNodeName_c", 1)
    Writer.raw(NameBytes)
    Writer.raw(ValueBytes)
