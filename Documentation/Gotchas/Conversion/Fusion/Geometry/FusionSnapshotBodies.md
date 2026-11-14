# Snapshot bodies have separate roles from history

A native `.smb` snapshot may contain three bodies even when the document has one solid. The qualified circular and rectangular extrusion snapshots contain the solved solid, a double-sided planar profile and a single-sided sketch sheet. The header root count is four because it includes the ASM header. Treating it as four solid bodies, or treating either sheet as a historical revision, misreads the file.

For the ordinary rectangular profile, the snapshot has 168 records. Its solved solid retains six generic face attributes and eight coedge sketch attributes but omits the history's timestamp and generic body attributes. Each of its two planar regions has four coedges, four edges and eight sketch attributes. The `.smbh` history instead has 102 initial records and its insertion journal.

Keep these models separate. Snapshot body keys are -1, while solved-history identity and operation joins belong to Design and `.smbh`. Preserve explicit vertex ownership, line direction scale, parameter bounds and the profile/sketch face flags. Do not reuse the history record layout by changing only the header or dropping arbitrary records.

The typed snapshot reader maps the complete native allocation to semantic roles and validates every regenerated field and reference. Unsupported layouts remain errors. See the [field-level evidence](../../../../../re/Fusion/Reconstruction/NativeAuxiliary/SnapshotModel.md), [native archive inventory](../../../../../re/Fusion/Reconstruction/NativeAuxiliary/Inventory.json) and [feature entry](../../../../Changes/Fusion/FusionNativeSnapshots.md).
