# Sketch dimension graphics use triangle-strip meshes

## Expectation

Fusion graphics meshes use only lines, line strips and triangle lists. These are primitive codes 2, 3 and 4.

## Actual behavior

Fusion 2706.1.17 writes `OgsSimpleMesh` geometry with primitive code 5 in documents that hold sketch dimensions. The code follows the OGS primitive order: 2 is lines, 3 is a line strip, 4 is triangles and 5 is a triangle strip.

Each observed strip has four vertices and no index buffer. Each strip is a flat rectangle at Z 0 beside a dimension, about 0.98 cm by 0.42 cm. The reader rejected eight saved documents with `ValueError("Unsupported graphics primitive topology")`. Each of these documents holds two or four strips. The documents are in `DimensionAuthoring`, `PublicAdapter`, `RectangleConstraints` and `RectangleDimensions`.

## Workaround

`XferMeshMut` accepts codes 2, 3, 4 and 5. The vertex data and the index rule are the same for all four codes. `XferRenderMut` keeps 2, 3 and 4 because no render mesh in the corpus uses a strip. Other codes still raise `ValueError`. `TestStripMesh` reads and re-emits the strips. `TestStripReject` changes one strip to code 6 and checks the rejection.

## Evidence

- [Mesh transfer](../../../../../src/convert/formats/Fusion/GraphicsCodec/Geometry/XferMeshMut.py)
- [Stream range script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/StreamRanges.py)
- [Native acceptance cases `StripCuboid` and `StripRectangle`](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
- [Change entry](../../../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md)
