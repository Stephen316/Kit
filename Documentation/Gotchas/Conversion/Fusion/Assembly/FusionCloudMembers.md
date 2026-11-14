# Cloud bundle members use another container layout

## Expectation

The design members of a native F3Z bundle have the same container layout as an API archive export.

## Actual behavior

The nine members of `re/Fusion/examples/.f3z/example1.f3z` differ from the API exports.

| Item | Members | Observed content |
| --- | --- | --- |
| Previews | 9 | `Previews/small.png` only |
| Graphics scene | 8 | `stream_mesh_000` and `Fusion_mesh_000` beside `world` |
| Dependency members | 9 | `Properties.dat` with JSON, `RedirectionsStream.dat` and `ComponentReferenceData.json` |
| Manifest | 9 | Lineage terminal with display name and lineage URN |

`ReadDocument` raises `Missing directories or unaccounted Fusion container members` for the eight members with mesh streams.
The PCB member has no mesh streams and an empty `Properties.dat` object.
It fails with `Unqualified Fusion native class or schema version`.

## Workaround

Read the dependency members of a cloud bundle with `ReadDocProps` and `ReadRedirects`.
Read the root manifest with `ReadRootWire`.
These readers accept all nine members.
Do not expect `ReadDocument` to read a cloud bundle member until the mesh streams and the PCB classes are qualified.

## Evidence

- [Bundle graph script](../../../../../re/Fusion/Reconstruction/LinksConfigs/BundleGraph.py)
- [Dependency graph change](../../../../Changes/Fusion/Assembly/FusionDependencyGraph.md)
