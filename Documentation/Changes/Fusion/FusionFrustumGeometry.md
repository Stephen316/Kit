# Independent Fusion frustum geometry

The new `convert.formats.Fusion.GeometryCodec.Frustum` modules independently author one closed circular frustum as standalone SMT or SMB. Inputs are positive lower and upper radii, a positive height and a bottom-center position, all in millimetres. The axis is +Z. Expanding, contracting and equal-radius cases share an explicit three-face, two-edge, two-vertex topology.

```python
from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmb import EmitFrustumSmb
from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmt import EmitFrustumSmt
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

Model = FrustumBody(10.0, 14.0, 17.0, (20.0, -30.0, 5.0))
Stamp = GeometryStamp("Kit", "Frustum authoring", "2026-11-12T00:00:00Z")
Binary = EmitFrustumSmb(Model, Stamp)
Textual = EmitFrustumSmt(Model, Stamp)
```

The writer computes cone angles, radii, cap planes, seam vertices and topology from those semantic inputs. It reads no source archive, donor records, templates or research data and requires no CAD runtime. Existing cylinder serialization remains unchanged. Invalid or numerically collapsed dimensions raise `ValueError` before file output.

The recovered model and exact evidence are in [FrustumModel.md](../../../re/Fusion/Reconstruction/FrustumModel/FrustumModel.md). The native cone's parameter scale is a length, not a second radius; [FusionConeParameterScale](../../Gotchas/Conversion/Fusion/Geometry/FusionConeParameterScale.md) documents that distinction.

This API authors standalone geometry. It does not yet author parametric tapered-extrusion feature/history, apex cones, noncircular cones, arbitrary axes or general imported cone surfaces. It does not establish lossless conversion of unsupported source features. Binary import uses the [temporary BRep route](../../Gotchas/Conversion/Fusion/FusionBinaryGeometryImport.md).

## Verification

Added remote integration and compatibility coverage for expanding, contracting and equal-radius files and for semantic cone/rim recovery. The coverage also includes pointer and coedge consistency, text unit scaling, invalid dimensions and the native controlled 7-degree tapered-extrusion archive. The native fixture's binary fields agree with the signed cone-angle equations and dimensional parameter-scale interpretation. No tests were run locally.

Scoped Black formatting, Ruff, mypy, Pyright and the repository steering checker passed during implementation. Pyright reported no source errors or warnings and noted three existing unrecognized repository configuration keys. Remote CI for this addition remains pending publication.

Fusion 2706.1.17 accepted all six independently produced artifacts. The artifacts are SMT and SMB for an expanding frustum `(10, 14, 17)` mm, a contracting frustum `(14, 8, 23)` mm, and the equal-radius limit `(9, 9, 11)` mm. Each artifact has a translated base. Every result was one solid with three faces, two edges and two vertices. Native volume, surface area, center of mass and bounds matched the analytic expectations before and after F3D save/reopen. The oracle closed every controlled document.

[Preparation.json](../../../re/Fusion/LocalOracle/Frustums/Preparation.json) records exact inputs, expected measurements and source hashes; [NativeAcceptance.json](../../../re/Fusion/LocalOracle/Frustums/NativeAcceptance.json) records native observations and saved-file hashes. This verifies the standalone geometry contract; it does not qualify tapered parametric feature/history authoring.

Remote compatibility run `43233457278` on revision `2fbad758d47c38a69ecbfb9756e5dccf333e5759` passed all 853 cases in 51.84 seconds, including all nineteen new frustum cases. No local test suite ran.
