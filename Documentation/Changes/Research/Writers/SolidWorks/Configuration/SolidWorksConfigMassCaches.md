<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construct SOLIDWORKS configuration mass caches

The generation-19000 [cache-list writer](../../../../../../re/solidworks/WriterResearch/ConfigMass/CacheList.py) files the generated solid's atom ID, body update stamp and density. It calculates the mass, center, volume, surface area and inertia tensor using the existing [254-byte mass-property serializer](../../../../../../re/solidworks/WriterResearch/CmgrMiddle.md#mass-property-record). The surrounding configuration retains its archive allocation map.

In the pinned SOLIDWORKS `34.4.1.1011` `sldmodu.dll`, the model writer at `0x4c235499` through `0x4c2354fe` counts the occupied cache slots in order. When both slots exist it also writes the next replacement index. `getMultiMassProps` advances that index at `0x4bc258fa` through `0x4bc25938`. During serialization, `moMassPropCache_c` checks each referenced kernel body against the current atom at `0x4bc1cf53` through `0x4bc1cfac`. An invalidated cache writes an empty count and keeps its position in the list. The live cache writes its body stamp and density, then calls the same `moMassProp_c::Serialize` routine used by `CMgr`. The cache constructor reads the stamp through `gcBody_w::getTimeStamp(0)` at `0x4bc1c192`. [Executable pin](../../../../../../re/solidworks/records/P04ArchiveWalk.md#inputs)

The [constructive archive replay](../../../../../../re/solidworks/WriterResearch/VerifyConfigMassCaches.py) checked six P01 sketch-only lists, four P03 single-cache lists and four P03 lists with an invalidated first slot. Their respective widths are 4, 278 and 286 bytes. The comparison verifies the inherited allocation map and exact framing, atom identities, replacement indices and mass settings. The computed physical values match within the established kernel tolerances. A separate cuboid with different geometry, density, atom ID and stamp also round-tripped through the cache codec.

The replay digest is `382f78cdb1a9f801781b0c397bb9d272f210f4a03bbeb71ba4f845d103502542`. Complete Config-0 generation and licensed native opening of a generated part remain pending.
