# Reference-driven native rectangle projection

Strict public Fusion reading now accepts two additional complete native rectangular extrusion profiles. The projector follows saved entity references instead of comparing their records with a newly authored document.

The qualified graph has one root component, one unconstrained XY rectangle, and one additive positive-Z distance extrusion. It preserves actual entity identities, parameter names, expressions, feature references, materials, and the complete decoded native state. This route accepts native graphics, prism snapshots, and empty configuration parts.

## Public usage

Use an archive within the qualified profile. The following calls preserve its decoded native graph through neutral JSON:

```python
from convert import open_document, write_document
from interchange import CadDocument

Document = open_document("NativeRectangle.f3d")
Restored = CadDocument.from_json(Document.to_json())
write_document(Restored, "Reemitted.f3d", allow_carrier=False)
```

Native-state contract version 2 identifies this route. Version 1 remains the existing constructor-shaped profile. Source-free `MakeFusionDoc` authoring and explicit `strict=False` partial reading remain unchanged.

The writer rejects inconsistent neutral edits before destination mutation. Extra contract metadata fails public adapter selection with `AdapterNotFoundError`; inconsistent fields inside a recognized contract raise `ValueError`. Create a new supported specification to author changed geometry. The contract does not authorize arbitrary edits to its decoded record tree.

## Semantic projection and checks

Entity identities use `fusion:<segment>:<entity>`. The ordinary control retains body `fusion:0:311`; the saved cuboid retains body `fusion:0:1140`. Neither allocation is an eligibility constant.

The creation-order controller must reference exactly the projected sketch and extrusion. All feature-derived entities must belong to that timeline. The projector rejects unknown classes, unknown saved members, extra geometry, populated unsupported collections, suppression, grouping, and unsupported construction features.

The rectangle contains its distinct fixed origin, four unfixed corner points, and four lines. Endpoint incidence defines the profile loop. Carrier coordinates, direction, placement, positive side lengths, and counterclockwise winding must agree. The profile recipe's native tag-list order remains unchanged.

The parameter table is projected completely. Parameters retain their actual names, comments, units, ownership, and expression text. Supported expressions are dimensionally checked literals or a direct compatible user-parameter reference. The ordinary control has only `d1` and `d2`; no user parameter is invented.

The extrusion requires one solid distance extent and zero taper. Its body serializer, body key, operation maps, UUID links, progenitor tags, profile scopes, and history boundaries must agree. Snapshot solids and planar regions must match the current history. Cached volume, area, center, and complete inertia tensor are checked against the analytic prism.

Material references resolve through their actual manager and package. The `_Post2015` appearance alias remains distinct in retained state. The neutral material uses the stored physical label or `UIName`, structural density, and effective floating-point appearance color. Library-localized display names are not fabricated.

Graphics retain their typed scene objects, vertex/index values, styles, and node data. Every graphic entity reference must resolve to the decoded semantic graph. Graphics do not determine solid geometry. This rectangle extension introduced 30 scene classes, bringing the static state registry to 115 record/enum types at that revision. The subsequent [circular extension](FusionNativeCircularProjection.md) adds the mixed-snapshot geometry closure. Raw graphics streams remain outside that registry.

## Limits

This route currently requires axis-aligned counterclockwise rectangular geometry, identity component/sketch placement, one closed profile, and no sketch dimensions or geometric constraints. It rejects tapered, thin, symmetric, two-sided, subtractive, assembled, external, or multi-body variants. Nonempty mesh bodies remain unsupported by the strict public projector, although the lower document codec can represent them.

The existing constructor route still supports its separately qualified circle, constrained rectangle, cylinder, cuboid, and frustum profiles. The new route does not extend every constructor profile to arbitrary native post-save graphs. The separately qualified [circular route](FusionNativeCircularProjection.md) handles native circle/cylinder/frustum saves.

All decoded fields remain in native state. Explicit UI, display, cache, and provenance classes can vary without creating a new modeled feature. Schema membership and modeled references are validated separately. No original archive, segment payload, generated source template, or runtime CAD dependency is retained.

Older native-state records that omit the newly added `DocumentModel.Meshes` field receive only its empty-tuple default. Unknown or other missing fields still fail. Version-1 contracts remain restricted to their original profile.

## Evidence

[Public artifact preparation](../../../../re/Fusion/LocalOracle/NativePublicAdapter/Preparation.json) used `open_document`, neutral JSON serialization, and `write_document`. Both resulting archives exactly match the previously accepted lower-codec outputs:

| Native source                       | Neutral parameters           | Native output SHA-256                                              |
| ----------------------------------- | ---------------------------- | ------------------------------------------------------------------ |
| Ordinary rectangle, 40 × 30 × 25 mm | `d1`, `d2`                   | `0203674063f58504d037a51236a1aff9cc3283ed1b8b107cc8307e1e73f10e92` |
| Saved cuboid, 17 × 23 × 37 mm       | `authoredLength`, `d2`, `d3` | `49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31` |

[Native acceptance](../../../../re/Fusion/LocalOracle/NativeDocuments/NativeAcceptance.json) covers these exact output bytes. Fusion loaded both solids, verified geometry/material properties, rolled the timeline back and restored it, then rebuilt after height edits. The ordinary height changed to 37 mm; the saved cuboid height changed to 43 mm. Native save/reopen passed with zero documents remaining open. No additional native run is claimed for identical files.

The 18 new remote integration cases cover both source archives, complete typed-model equality, public neutral serialization and preserved identities. The cases also cover graph/history corruption, transactional write rejection, and legacy empty-mesh defaults. Black, Ruff, mypy, strict Pyright, and repository steering checks passed. No local tests were run. Remote CI results remain separate evidence.

See the [earlier public adapter](FusionPublicAdapter.md), [native semantic-contract limits](../../../Gotchas/Conversion/Fusion/Api/FusionSemanticContracts.md), and [stored material-label gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionStoredMaterialLabels.md).
