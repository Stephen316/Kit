# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.Topology.BodyEvidence import (
    GetBodyEvidence,
    KBodyInventoryKey,
)
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import AssemblyData


# bodies belong to reusable definitions even when many occurrences instantiate them
def AttachBodyList(
    Assembly: AssemblyData,
    ComponentIds: dict[str, int],
    Inventory: dict[int, tuple[NativeBody, ...]],
) -> AssemblyData:
    Definitions = []
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
