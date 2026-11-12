from convert.formats.Fusion.Assembly.NativeOccurrence import NativeOccur


# graph qualification detects cycles and excessive expansion without instantiating paths
def VerifyAsmGraph(
    RootId: int, ComponentIds: set[int], Occurrences: tuple[NativeOccur, ...]
) -> None:
    Children: dict[int, list[int]] = {Identity: [] for Identity in ComponentIds}
    for Occurrence in Occurrences:
        Children[Occurrence.OwnerId].append(Occurrence.ComponentId)
    Active: set[int] = set()
    Complete: dict[int, tuple[int, int]] = {}

    # memoized subtree limits preserve repeated components without exponential traversal
    def VisitBranch(ComponentId: int, Depth: int) -> tuple[int, int]:
        if ComponentId in Active or Depth > 128:
            raise ValueError("Cyclic or excessively nested Fusion assembly")
        Known = Complete.get(ComponentId)
        if Known is not None:
            return Known
        Active.add(ComponentId)
        SizeValue, Height = 1, 0
        for ChildId in Children[ComponentId]:
            ChildSize, ChildHeight = VisitBranch(ChildId, Depth + 1)
            SizeValue += ChildSize
            Height = max(Height, ChildHeight + 1)
            if SizeValue > 10001 or Height > 128:
                raise ValueError("Fusion assembly expansion exceeds limit")
        Active.remove(ComponentId)
        Complete[ComponentId] = SizeValue, Height
        return SizeValue, Height

    _ = VisitBranch(RootId, 0)
    if Complete.keys() != ComponentIds:
        raise ValueError("Unreachable Fusion assembly component")
