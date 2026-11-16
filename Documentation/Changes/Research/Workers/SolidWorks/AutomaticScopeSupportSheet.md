# Read the saved Cut support sheet

The [automatic-scope replay](ProvisionalScopeArchive.md) with `--inspect-map` decodes the bounded 1,205-byte kernel packet in the resolved Cut profile at byte 20,381. A one-byte prefix precedes a zlib-wrapped Parasolid payload. The wrapper accounts for the rest of the packet and expands to 2,247 bytes in schema `SCH_3701250_37102_13006`.

The decoded sheet has one planar face, four straight edges and four vertices. It covers the 40 × 20 mm support cap of body A at Z = 10 mm. The face sense converts its saved surface normal to the same +Z normal as the independently decoded support reference. The authored Cut sketch separately contains its 10 × 8 mm rectangle. The [active partition](AutomaticScopePartitionGeometry.md) contains the two final solids and their openings.

The exact packet SHA-256 is `453d5988ee6b47aa23a74049e553d1f46fb6b35c3f97eb776e30c4b6b7003a28` in both saves. The decoded sheet SHA-256 is `30a5ed2932dc23bd04bebc526decb2a5634dd7a84b3bfce4de90ed83935e038e`. The paired report with both geometry sections initially produced SHA-256 `d6d0610cb6b2e4ab1daba1420b4b2830aa6c5884cb3ab15487017b0919e73ef6`. The geometry match describes these two archives. Kernel field authority, cache regeneration and native conversion qualification remain open.
