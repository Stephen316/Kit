# Fusion BRep corpus classification

## Behavior

The read-only BRep inventory now accounts for all 1,170 embedded streams across 582 of the 712 source archives. The inventory counts 605 snapshots, 565 histories, and 1,083 distinct blob hashes. Every stream passes structural token framing. The inventory records archive/member digests, record-type counts, root and journal structure, and conservative ownership-based planar/box candidates.

Initial tables contain 22,303 straight curves, 11,086 planes, 2,475 ellipse curves, 748 cone surfaces, 1,242 intersection curves, and 475 spline surfaces. These counts include repeated blobs and selection caches; they are not visible body counts or claims of supported semantic geometry.

## Usage

Run `python re/Fusion/Reconstruction/BrepCoverage/InventoryBrep.py` for read-only research extraction. `InspectCuboid.py` records the existing controlled ordinary rectangular extrusion and its complete insertion-board structure. These scripts are research tools; production code does not import them or read their fixtures.

[The summary](../../../re/Fusion/Reconstruction/BrepCoverage/Summary.json) and [compressed inventory](../../../re/Fusion/Reconstruction/BrepCoverage/Inventory.json.xz) bind the observations to source digests. [The expansion plan](../../../re/Fusion/Reconstruction/BrepCoverage/ExpansionPlan.md) specifies the concrete field contracts and next implementation boundaries.

## Qualified findings and limits

Eighty-three history members contain exactly one axis-aligned box candidate. Sixty members across 40 archives also have two delta states and only the three studied attribute types. These are candidates, not completed semantic acceptance: current-body selection, every attribute, reciprocal orientation, and every journal operation still require validation.

The ordinary rectangle control has 102 initial records and 101 insertion triples covering every entity except the ASM header. Its archived native ground truth describes a healthy 40×30×25 mm solid with volume 30 cm³. A separate newly authorized native capture records a translated 12×18×24 mm cuboid with six faces, twelve edges, eight vertices, and volume 5.184 cm³. The capture's SMT/F3D digests are recorded in [the capture manifest](../../../re/Fusion/LocalOracle/Brep/CuboidCapture.json).

The first semantic expansion is a planar cuboid. Multiple bodies, variable attribute chains, archived journal revisions, mixed curved solids, splines, intersection curves, and tolerant topology remain separate modeling requirements. A generic token reader does not establish complete BRep understanding or lossless history conversion.

## Verification

The inventory performs read-only research decoding and static classification. It does not execute production-code tests. The controlled cuboid was generated and exported inside the explicitly authorized local Fusion 2706.1.17 session, with zero documents left open. That capture is source evidence, not acceptance of a Kit-authored cuboid.
