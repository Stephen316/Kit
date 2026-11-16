# Measure both saved automatic-scope regions

Add `--inspect-map` to the [pinned automatic-scope archive replay](ProvisionalScopeArchive.md). After replaying the resolved feature stream, the command independently reads the active `Contents/Config-0-Partition` payload. It follows the typed region, shell, face, loop and edge references. The two closed regions account for every boundary topology record. Each has ten planar faces, 24 edges and sixteen vertices.

The archived geometry distinguishes the regions by their disjoint box bounds. That matches each region to its recipe and the corresponding typed resolved scope row. The decoded partition carries both regions under a single derived carrier and supplies no native Boss ID for either region. The correlation uses the unique spatial bounds.

| Recipe body | Saved bounds in mm | Geometric volume in mm³ | Geometric centroid in mm | Resolved body and feature |
| --- | --- | --- | --- | --- |
| A | (0, 0, 0) to (40, 20, 10) | 7,200 | (20, 10, 5) | 101, 32 |
| B | (10, 5, −10) to (30, 15, −5) | 600 | (20, 10, −7.5) | 102, 40 |

Both ends of each region have a saved inner rectangle spanning X = 15–25 mm and Y = 6–14 mm. The checks identify these openings by their coordinates on the paired cap rings. The signed shell integration matches the independently calculated box-minus-hole volumes and first moments within the recipe tolerances. [Planar cap loop order](../../../../Gotchas/Conversion/SolidWorks/ParasolidLoopOrder.md)

Both exact archives agree on these measurements, topology identities and openings. Their compressed streams and decoded partition payloads have distinct digests. The initial paired geometry replay produced SHA-256 `7597be70a1e9c0637ff6fa1835cb96fff97b1cbd2337fd6e332de2afbaa6d7c6`. With the [packaged loop classification](../../Readers/SolidWorks/ParasolidLoopRoles.md), the decoded labels match the geometry on all four caps in each save. The paired replay with the support sheet and corrected roles produced SHA-256 `0e1a058ce082b09d627a9a2f6c3055d12024f23effaa2d7240b7c54eb1c7ad3f`. Persisted Auto-select and editable conversion still require the explicit-scope and independent licensed controls.
