# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


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
    capabilities=frozenset(
        {
            Capability.KParameters,
            Capability.KSupportPlanes,
            Capability.KSelections,
            Capability.KBodyStructure,
            Capability.KBrep,
            Capability.KNativePayloads,
            Capability.KProvenance,
        }
    ),
)
