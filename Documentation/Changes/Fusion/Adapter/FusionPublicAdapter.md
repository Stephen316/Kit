# Qualified public Fusion adapter

The public conversion registry now discovers `fusion.f3d` and its `f3d` alias for reading and writing. The supported source-free route begins with `MakeFusionDoc(DocumentSpec(...))`: it creates actual neutral parameters, expressions, planar sketches, constraints, feature definitions, analytic BRep topology, bodies, and material records. The constructor's supported profiles are parameter-only, circle sketch, rectangular sketch, circular extrusion, cuboid extrusion, and positive-radius circular frustum extrusion.

## Usage

```python
from convert import open_document, write_document
from convert.adapters.Fusion import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

Document = MakeFusionDoc(DocumentSpec(
    "Dimensioned cuboid", "height", 31.0, ProfileKind="cuboid",
    WidthMm=17.0, DepthMm=23.0, ConstrainRectangle=True,
))
write_document(Document, "Cuboid.f3d", destination_format="f3d", allow_carrier=False)
Parsed = open_document("Cuboid.f3d")
Restored = type(Parsed).from_json(Parsed.to_json())
write_document(Restored, "Reemitted.f3d", allow_carrier=False)
```

Length values in the neutral graph are millimetres, and angles are radians. Material density is kilograms per cubic metre, and color channels are floating-point RGBA values between zero and one. `ConstrainRectangle=True` exposes the anchored corner, four horizontal/vertical relations, two dimensions, width/depth user parameters, and their dependent model parameters. Extrusions use `DistanceExtrude` with actual height/taper parameter references. The geometry is built through Kit's independent analytic circular/prism builders, with planar, cylindrical or conical surfaces and complete neutral topology.

`CadDocument.materials` is an optional tuple of typed `MaterialRecord` values. Existing neutral JSON without this field still loads with an empty tuple. The existing body `material_id` contract remains compatible with other adapters. The qualified Fusion graph requires the exact material identity, density and color represented by its constructor. A separate optional `TypedMaterials` writer property defaults to unsupported at the public registry boundary. Only the qualified Fusion writer and neutral JSON writer opt in. Any root or nested component material collection is rejected before staging for other writers, even when they advertise legacy `material_id` support. Density and color cannot silently disappear. Parameter-only documents with a configuration are valid neutral documents even without a feature timeline.

## Two explicit contracts

A constructor-produced document carries `fusion.authoring`, version 1, containing only its semantic specification. Before emission the writer rebuilds the complete neutral graph from that specification and compares every document field. Changed parameters, geometry, constraints, bodies, material values, source fields, capabilities, extra metadata, assemblies, or other unaccounted collections are rejected before output. Rebuild through `MakeFusionDoc` with a changed specification to author a different document. This is a qualified constructor contract, not general recognition of arbitrary `CadDocument` graphs.

The constructor-profile strict route decodes the native document and derives the qualified specification. The route then compares every Design, ACT and Browser entity record against the independently generated semantic profile. Class identities, record inventory, all member values and relationships must agree. The comparison normalizes fresh UUID identity spelling, type-code allocation, material-package creation/update and BRep authoring timestamp provenance and numerical formatting at 14 significant digits. The comparison does not rewrite the retained native state. It also checks the complete typed BRep shape, topology tags, history state and material package. Extra features and unsupported graph variations fail explicitly. Auxiliary-bearing ordinary rectangular extrusions use the separately qualified [reference-driven native rectangle route](FusionNativeRectangleProjection.md). Native full-circle sketches, cylinders and frustums use the [reference-driven circular route](FusionNativeCircularProjection.md).

The resulting `fusion.native_state`, version 1, stores the complete decoded dataclass model through a static allowlist of record/enum types. It contains schemas, members, references, history, geometry, materials and container metadata. It does not retain an F3D archive, a segment byte block, a donor BRep block, dynamic import instructions, or pickle data. The only byte-bearing container values are validated preview images. Nesting, serialized-state size, record fields and version are bounded or checked. Writing reconstructs native bytes from that model and decodes them again. Writing then requires both the full model and the complete neutral projection to agree before touching the destination. Native state never silently overrides a changed neutral field.

`strict=False` preserves the earlier partial-reader behavior, including its partial-history diagnostic and original archive payload. That document is not accepted by the qualified writer. Strict reading requires the full BRep and does not accept history/configuration selection. A registry capability identifies categories available in the format adapter; the per-document contract determines whether a particular graph is writable.

## Verification

The [public API preparation report](../../../../re/Fusion/LocalOracle/PublicAdapter/Preparation.json) records six independently generated files and six byte-identical native re-emissions after neutral JSON serialization. All six used public registry discovery, `write_document(..., allow_carrier=False)`, default strict `open_document`, and typed material serialization. Their neutral parameters, sketches, feature timeline, body summaries, analytic BRep and materials matched the constructor outputs exactly. The [generator](../../../../re/Fusion/Reconstruction/PublicAdapter/Generate.py) consumes dimensions and material specifications, not source archives or templates.

The 26 remote integration cases cover public archive and serialization boundaries, all six profiles, and transactional rejection of inconsistent parameter/material/body/history/metadata/source fields. The cases also cover native-state version/type/extra-field and BRep body/operation/secondary identity rejection at both strict native read and write boundaries. Finally, the cases cover historical JSON without a material collection, full neutral JSON material transport, and rejection before mutation by a legacy writer. Existing discovery, legacy partial-read and isolated-wheel cases are updated to the new catalog. No local tests were run. Remote CI remains a separate verification boundary.

All six byte-identical public re-emissions passed [native Fusion acceptance](../../../../re/Fusion/LocalOracle/PublicAdapter/NativeAcceptance.json), report SHA-256 `9a31b0bacc7d59449b3becdc96c77e5b51dccff269b716800ae353f2c601c4a5`. Fusion verified initial geometry, material density, mass, center, bounds and RGBA 51/102/153/255. Height changed 17→21 mm, the circle radius 12→14 mm, constrained rectangle/cuboid width 19→22 mm and depth 23→29 mm, and frustum taper +5→−3 degrees. Solid rollback, rebuild, native save and reopen passed, with zero documents remaining open. This acceptance concerns the emitted native files; it does not extend strict adapter qualification to every graph Fusion may produce after editing.

See the [contract consistency gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionSemanticContracts.md), [full native codec](../FusionNativeDocumentCodec.md), and [dimensioned rectangle authoring](../FusionConstrainedRectangles.md).
