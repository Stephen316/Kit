# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.brep.curves.BrepCurves import BrepEntity
from interchange.brep.validation.BrepView import BrepView


# identity indexing centralizes duplicate and empty identifier diagnostics
def GetBrepIds(
    ModelValue: BrepView,
) -> tuple[dict[str, frozenset[str]], tuple[str, ...]]:
    ErrorValues: list[str] = []
    IdentitySets: dict[str, frozenset[str]] = {}
    IdentityGroups: tuple[tuple[str, tuple[BrepEntity, ...]], ...] = (
        ("Curves", ModelValue.curves),
        ("Pcurves", ModelValue.pcurves),
        ("Surfaces", ModelValue.surfaces),
        ("Vertices", ModelValue.vertices),
        ("Edges", ModelValue.edges),
        ("Coedges", ModelValue.coedges),
        ("Loops", ModelValue.loops),
        ("Wires", ModelValue.wires),
        ("Faces", ModelValue.faces),
        ("FaceUses", ModelValue.face_uses),
        ("Shells", ModelValue.shells),
        ("ShellUses", ModelValue.shell_uses),
        ("Regions", ModelValue.regions),
        ("Bodies", ModelValue.bodies),
    )
    for GroupName, ItemValues in IdentityGroups:
        Identifiers = tuple(ItemValue.EntityId for ItemValue in ItemValues)
        if any(not Identifier for Identifier in Identifiers):
            ErrorValues.append(f"B-rep {GroupName} contains an empty id")
        if len(Identifiers) != len(set(Identifiers)):
            ErrorValues.append(f"B-rep {GroupName} contains duplicate ids")
        IdentitySets[GroupName] = frozenset(Identifiers)
    return IdentitySets, tuple(ErrorValues)
