# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.AssemblyIndex import AssemblyIndex
from convert.formats.Fusion.Assembly.OccurRecord import OccurRecord
from convert.formats.Fusion.Assembly.OccurTransform import KIdentityMatrix


# a unique reciprocal root establishes the coordinate frame for local child placements
def ResolveAsmRoot(IndexValue: AssemblyIndex) -> OccurRecord:
    Roots = [
        Occurrence
        for Occurrence in IndexValue.Occurrences.values()
        if Occurrence.CollectionId is None
    ]
    Declared = [
        Entry
        for Entry in IndexValue.Components.values()
        if Entry.RootOccurrence is not None
    ]
    if len(Roots) != 1 or len(Declared) != 1:
        raise ValueError("Missing or ambiguous Fusion assembly root")
    (RootValue,) = Roots
    (RootEntry,) = Declared
    if (
        RootEntry.Component.ObjectId != RootValue.ComponentId
        or RootEntry.RootOccurrence != RootValue.ObjectId
    ):
        raise ValueError("Fusion root component and occurrence links disagree")
    if RootValue.Transform != KIdentityMatrix:
        raise ValueError("Nonidentity Fusion assembly root placement")
    return RootValue
