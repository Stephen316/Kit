# Native sheet measurements differ from solid measurements

A native Fusion BRep body can be valid and have `isSolid == False`. Requesting its solid volume through the public API can raise instead of returning zero. Both original open tetrahedron controls exhibit this behavior; it is not evidence that a re-emitted document failed to load.

For open sheets, compare the body's solid/sheet classification, face/edge/vertex counts, surface types, area, explicit vertex coordinates and bounding box. Keep unsupported solid volume and mass-center observations absent. Do not silently replace them with zero or infer a closed solid from single-sided face flags.

The complete document acceptance driver applies the same observation rule to each original control and its typed re-emission. The driver then compares every rollback, rebuild and save/reopen stage. [NativeAcceptance.json](../../../../../re/Fusion/LocalOracle/DocumentGeometry/NativeAcceptance.json) records the open sheets with area 13 cm², three faces, six edges and four vertices, and explicit null volume/center values. See [the typed document geometry entry](../../../../Changes/Fusion/Geometry/FusionDocumentGeometry.md).
