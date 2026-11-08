# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActFields import (
    KActFieldsGuid,
    ReadActFields,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRoute import ActRoute


# a bijective fields inventory blocks duplicate or unindexed evidence
def ReadActRoutes(
    ActData: bytes,
    ActSpans: tuple[RecordSpan, ...],
    Entries: tuple[tuple[int, str, int, int], ...],
) -> tuple[ActRoute, ...]:
    Fields: dict[int, RecordSpan] = {}
    for FieldSpan in ActSpans:
        if FieldSpan.ClassGuid != KActFieldsGuid:
            continue
        if FieldSpan.ObjectId in Fields:
            raise ValueError("Duplicate Fusion ACT fields identity")
        Fields[FieldSpan.ObjectId] = FieldSpan
    if len(Fields) != len(Entries):
        raise ValueError("Fusion ACT table and fields inventory disagree")
    Routes: list[ActRoute] = []
    for FieldsId, KeyValue, Prefix, OwnerId in Entries:
        FieldSpan = Fields.pop(FieldsId, None)
        if FieldSpan is None:
            raise ValueError("Missing or duplicate Fusion ACT fields reference")
        Roles, Residual = ReadActFields(ActData, FieldSpan, KeyValue)
        Routes.append(ActRoute(KeyValue, Prefix, OwnerId, FieldSpan, Roles, Residual))
    return tuple(Routes)
