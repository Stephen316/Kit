# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping, Set as AbstractSet

from convert.adapters.freecad.BrepGraph import ModelGraph, Unsupported
from interchange.brep.topology.BrepModel import BrepModel


# shared edge parity alone cannot decide the outward side of newly supported curved shells
def CheckCurvedUse(
    Model: BrepModel,
    Graph: ModelGraph,
    CurvedFaces: AbstractSet[str],
    FaceReversals: Mapping[str, bool],
    ShellReversals: Mapping[str, bool],
) -> None:
    if not CurvedFaces:
        return
    for ShellUse in Model.shell_uses:
        Shell = Graph.shells[ShellUse.shell_id]
        FaceUses = tuple(Graph.face_uses[UseId] for UseId in Shell.face_use_ids)
        if not any(Value.face_id in CurvedFaces for Value in FaceUses):
            continue
        if ShellReversals[ShellUse.id] != ShellUse.reversed or any(
            FaceReversals[Value.id]
            != ((not Graph.faces[Value.face_id].same_sense) != Value.reversed)
            for Value in FaceUses
        ):
            Unsupported(f"curved shell {Shell.id} has conflicting source orientations")
