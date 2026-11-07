# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.AssemblyIndex import AssemblyIndex
from convert.formats.Fusion.Assembly.NativeOccurrence import NativeOccurrence


# exact collection ownership supplies child order without expanding reused definitions
def LinkOccurrences(IndexValue: AssemblyIndex) -> tuple[NativeOccurrence, ...]:
    Linked = []
    Claimed = set()
    ByOwner = set()
    for CollectionId, (OwnerId, Members) in IndexValue.Collections.items():
        Owner = IndexValue.Components.get(OwnerId)
        if Owner is None or Owner.CollectionId != CollectionId or OwnerId in ByOwner:
            raise ValueError(
                "Fusion component and occurrence collection links disagree"
            )
        ByOwner.add(OwnerId)
        Siblings = set()
        for Order, MemberId in enumerate(Members):
            Occurrence = IndexValue.Occurrences.get(MemberId)
            if (
                Occurrence is None
                or Occurrence.CollectionId != CollectionId
                or MemberId in Claimed
            ):
                raise ValueError(
                    "Fusion occurrence and parent collection links disagree"
                )
            Component = IndexValue.Components.get(Occurrence.ComponentId)
            if Component is None:
                raise ValueError("Fusion occurrence has no local component")
            InstanceKey = (Occurrence.ComponentId, Occurrence.InstanceNumber)
            if InstanceKey in Siblings:
                raise ValueError("Duplicate Fusion sibling instance number")
            Siblings.add(InstanceKey)
            Claimed.add(MemberId)
            NameValue = Occurrence.Name
            if not NameValue and Component.Component.Name:
                NameValue = f"{Component.Component.Name}:{Occurrence.InstanceNumber}"
            Linked.append(
                NativeOccurrence(
                    MemberId,
                    Occurrence.ComponentId,
                    OwnerId,
                    NameValue,
                    Occurrence.InstanceNumber,
                    Occurrence.NativeGuid,
                    Order,
                    Occurrence.Transform,
                )
            )
    if ByOwner != IndexValue.Components.keys():
        raise ValueError("Missing Fusion component occurrence collection")
    if Claimed != {
        Record.ObjectId
        for Record in IndexValue.Occurrences.values()
        if Record.CollectionId is not None
    }:
        raise ValueError("Fusion occurrence is absent from its declared collection")
    return tuple(Linked)
