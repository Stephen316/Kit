# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections import deque as Deque


# dependency order admits only expressions with proven leaves and no cycles
def GetProvenLinks(Graph: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    Remaining = {ParamId: len(Inputs) for ParamId, Inputs in Graph.items()}
    Dependents: dict[str, list[str]] = {}
    for ParamId, Inputs in Graph.items():
        for InputId in Inputs:
            Dependents.setdefault(InputId, []).append(ParamId)
    Ready = Deque(ParamId for ParamId, Count in Remaining.items() if Count == 0)
    Proven = {}
    while Ready:
        ParamId = Ready.popleft()
        if Graph[ParamId]:
            Proven[ParamId] = Graph[ParamId]
        for TargetId in Dependents.get(ParamId, ()):
            Remaining[TargetId] -= 1
            if Remaining[TargetId] == 0:
                Ready.append(TargetId)
    return Proven
