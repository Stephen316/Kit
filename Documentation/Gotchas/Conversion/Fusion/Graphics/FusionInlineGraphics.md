# Graphics class names do not imply object handles

The expectation that every named OGS object has a shared resource handle is false. Each class has its own framing. `PrimitiveLODGeometryNode` writes its node-data selector immediately after the class name. `SimpleMesh`, `VertexBuffer` and `CircleArc<double>` write a resource identity before their fields. A repeated resource writes its class/identity link without duplicating its definition.

The ordinary primitive LOD also differs from the body LOD: it writes a general mesh link and omits the body-specific display-item discriminator. Generic `SimpleMesh` uses shared vertex resources and six float32 model bounds; its LOD world bounds are six float64 values. Fusion's `OgsSimpleMesh` is a different class with an inline vertex-buffer payload and a planarity flag.

Use class-specific typed dispatch and preserve the three framing decisions independently. Do not infer identities from names or reuse a similarly named body serializer. Decoding of the three circular controls and their [whole-document acceptance](../../../../../re/Fusion/LocalOracle/RotationalDocuments/NativeAcceptance.json) establish these distinctions.
