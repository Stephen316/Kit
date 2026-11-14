# Boundary uses and body roots are independent of solid profiles

A valid Fusion coedge can have partner -1. The open tetrahedron controls have three such boundary uses; a circular sheet has one. Their face-loop next/prior pointers remain reciprocal. Single-sided face flags occur in both open and closed controls, so neither that flag nor a familiar entity count proves shell closure.

Validate actual edge incidence: one use requires no partner, while two uses require reciprocal partners. The edge's owner must be one of those uses. Keep closed-volume computation behind an explicit closed-shell geometry check. Merely permitting null partners without checking incidence would accept damaged closed solids.

The binary header counts the ASM header plus all body roots. A two-body mesh conversion therefore declares three roots. Multiple bodies share one entity table and journal; they are not separate files or historical revisions. Snapshot root count four can instead describe a solid and two planar sheets. Preserve each body's topology and face flags explicitly.

Native open base-feature geometry also assigns generic tags to vertices. Applying an attribute owner-class list inferred only from closed extrusion controls incorrectly rejects those valid references. The vertex allowance is specific to the proved generic-tag family; it does not make arbitrary pointer targets valid.

[Exact source/member evidence](../../../../../re/Fusion/Reconstruction/DocumentGeometry/Inventory.json), [the typed data model](../../../../../re/Fusion/Reconstruction/DocumentGeometry/Model.md) and [the feature entry](../../../../Changes/Fusion/Geometry/FusionDocumentGeometry.md) describe supported fields, limits and acceptance boundaries.
