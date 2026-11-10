# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.Topology.BodyEvidence import (
    GetBodyEvidence,
    KBodyInventoryKey,
)
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.core.Common import FreezeMapping
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.document.models.DocumentModel import AssemblyData


# bodies belong to reusable definitions even when many occurrences instantiate them
def AttachBodyList(
    Assembly: AssemblyData,
    ComponentIds: dict[str, int],
    Inventory: dict[int, tuple[NativeBody, ...]],
) -> AssemblyData:
    Definitions: list[ComponentDef] = []
    for Definition in Assembly.definitions:
        ComponentId = ComponentIds.get(Definition.id)
        if ComponentId is not None and ComponentId in Inventory:
            Definition = Replace(
                Definition,
                attributes=FreezeMapping(
                    {
                        **Definition.attributes,
                        KBodyInventoryKey: GetBodyEvidence(
                            ComponentId, Inventory[ComponentId], {}
                        ),
                    }
                ),
            )
        Definitions.append(Definition)
    return Replace(Assembly, definitions=tuple(Definitions))
