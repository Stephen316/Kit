# A Fusion edge can have three or four coedge uses

## Expectation

A live edge has one coedge use on an open boundary or two uses on a manifold boundary. Two uses refer to each other as partners.

## Actual behavior

A two-sided thin extrude writes a solid where two walls meet along 4 edges. Each of these edges has 4 coedge uses in one shell. Kit raised `ValueError("Unsupported Fusion nonmanifold edge-use count")` for this file.

The census counted the live uses of every edge in each saved geometry and each journal state under `re/`. It read all but 2 files.

| Uses | Saved geometry edges | Journal state edges |
| --- | --- | --- |
| 0 | 20 | 6 |
| 1 | 6635 | 3064 |
| 2 | 9214 | 23646 |
| 3 | 0 | 64 |
| 4 | 4 | 8 |

Every edge with 3 or 4 uses has these properties:

- The partner references make one ring through all of its coedges.
- The ring has coedges of both senses.
- The edge refers to one of its coedges.

The senses alternate along the ring only for the 4 thin extrude edges.

| Uses | Edges | Source | Sense pattern |
| --- | --- | --- | --- |
| 4 | 4 per stream | `closed_two_sides_mixed.f3d` | Alternating |
| 3 | 64 | Eight `boundaryfills` journals | Two of one sense and one of the other |
| 4 | 4 | `boundaryfills/plane_first.f3d` | Two of each sense, with equal senses next to each other |

The `boundaryfills` rings are in older journal states. A boundary fill builds cell bodies before it keeps the selected cells, and these edges belong to those cells. All faces at these edges are single-sided. Three uses cannot alternate, so Kit raised `ValueError("Unsupported Fusion nonmanifold edge-use count")` for 8 files. Kit raised `ValueError("Fusion nonmanifold edge senses do not alternate")` for `plane_first.f3d`.

## Workaround

Accept 1, 2, 3 or 4 uses. For 3 or 4 uses, `CheckUseCycle` requires one partner ring through all uses and both coedge senses. Reject more than 4 uses. `TestEdgeRing` sets all four uses of a ring to one sense and checks the rejection. `TestJournalTrip` round-trips the nine `boundaryfills` files.

## Evidence

- [Edge-use rings](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/UseCycles.json)
- [Census delta](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/CensusDelta.json)
