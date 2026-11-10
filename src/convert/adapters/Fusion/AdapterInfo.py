# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.adapters.base.AdapterInfo import AdapterInfo
from interchange.enums.EnumDocument import Capability

# registration advertises only categories represented in the partial native reader
KReaderInfo = AdapterInfo(
    format_id="fusion.f3d",
    name="Autodesk Fusion",
    version="1.0",
    aliases=("f3d",),
    extensions=(".f3d",),
    part_extensions=(".f3d",),
    assembly_extensions=(".f3d",),
    capabilities=frozenset(
        {
            Capability.KParameters,
            Capability.KSupportPlanes,
            Capability.KSelections,
            Capability.KBodyStructure,
            Capability.KBrep,
            Capability.KAssemblies,
            Capability.KComponentDocs,
            Capability.KNativePayloads,
            Capability.KProvenance,
        }
    ),
)
