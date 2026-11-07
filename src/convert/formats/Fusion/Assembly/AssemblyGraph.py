# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.NativeOccurrence import NativeOccurrence


# graph qualification detects cycles and excessive expansion without instantiating paths
def VerifyAsmGraph(
    RootId: int, ComponentIds: set[int], Occurrences: tuple[NativeOccurrence, ...]
) -> None:
    Children: dict[int, list[int]] = {Identity: [] for Identity in ComponentIds}
    for Occurrence in Occurrences:
        Children[Occurrence.OwnerId].append(Occurrence.ComponentId)
    Active = set()
    Complete: dict[int, tuple[int, int]] = {}

    # memoized subtree limits preserve repeated components without exponential traversal
    def VisitBranch(ComponentId: int, Depth: int) -> tuple[int, int]:
        if ComponentId in Active or Depth > 128:
            raise ValueError("Cyclic or excessively nested Fusion assembly")
        Known = Complete.get(ComponentId)
        if Known is not None:
            return Known
        Active.add(ComponentId)
        Size, Height = 1, 0
        for ChildId in Children[ComponentId]:
            ChildSize, ChildHeight = VisitBranch(ChildId, Depth + 1)
            Size += ChildSize
            Height = max(Height, ChildHeight + 1)
            if Size > 10001 or Height > 128:
                raise ValueError("Fusion assembly expansion exceeds limit")
        Active.remove(ComponentId)
        Complete[ComponentId] = Size, Height
        return Size, Height

    VisitBranch(RootId, 0)
    if Complete.keys() != ComponentIds:
        raise ValueError("Unreachable Fusion assembly component")
