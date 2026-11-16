from collections import deque as Deque


# dependency order admits only expressions with proven leaves and no cycles
def GetProvenLinks(Graph: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    Remaining = {ParamId: len(Inputs) for ParamId, Inputs in Graph.items()}
    Dependents: dict[str, list[str]] = {}
    for ParamId, Inputs in Graph.items():
        for InputId in Inputs:
            Dependents.setdefault(InputId, []).append(ParamId)
    Ready = Deque(ParamId for ParamId, Count in Remaining.items() if Count == 0)
    Proven: dict[str, tuple[str, ...]] = {}
    while Ready:
        ParamId = Ready.popleft()
        if Graph[ParamId]:
            Proven[ParamId] = Graph[ParamId]
        for TargetId in Dependents.get(ParamId, ()):
            Remaining[TargetId] -= 1
            if Remaining[TargetId] == 0:
                Ready.append(TargetId)
    return Proven
