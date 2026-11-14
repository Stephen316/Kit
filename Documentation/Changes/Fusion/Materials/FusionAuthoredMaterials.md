# Independent physical materials for authored Fusion bodies

## Behavior

The cylinder and cuboid document profiles now construct physical materials and appearances with fresh identities.
The writer derives each property from an explicit specification or a registered schema default.
It serializes the four material assets and their package through the production material codec.

The body references the new physical and appearance instances.
Its `ProteinAssetManager` identifies the package part and records both asset references and their reference counts.
The component's default physical material remains unchanged.

This repairs a physical-property gap in the earlier authored solids.
Their geometry was valid, but their undefined materials caused zero density, mass, inertia, and centre of mass.
The [native diagnosis](../../../../re/Fusion/LocalOracle/RectangleAuthoring/MassProbe.json) demonstrates the cause independently of the writer change.

## API

`DocumentSpec.Material` accepts an immutable `MaterialSpec`.
The default name is `Kit Generic Material`, with density `1000 kg/m³` and RGBA color `(0.8, 0.8, 0.8, 1)`.
Density must be finite, positive, and at most `25000 kg/m³`.
Color channels must be finite values from zero through one.

```python
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue

Material = MaterialSpec(
    NameValue="Authored material",
    Density=2870.0,
    Color=ColorValue(0.2, 0.4, 0.6, 1.0),
)
Specification = DocumentSpec(
    "Material cuboid",
    "bodyHeight",
    31.0,
    ProfileKind="cuboid",
    WidthMm=17.0,
    DepthMm=23.0,
    Material=Material,
)
Path("MaterialCuboid.f3d").write_bytes(EmitDocument(Specification))
```

The example describes the API; it is not an executed verification record.
Parameter-only and sketch-only profiles do not create a material package.

## Semantic construction

This entry first created `PhysMatSchema`, `StructuralMetalSchema`, `ThermalSolidSchema`, and `PrismMetalSchema` assets for every material.
[Material families](FusionMaterialFamilies.md) now choose the structural, thermal and appearance schemas from the material class and its values.
The default material now uses `StructuralBasicSchema` and `PrismOpaqueSchema`, with no thermal aspect.
The physical asset connects to the other three assets through `physmat_aspects`.
Structural and thermal density use the specified value with native unit code `69633`, representing kilograms per cubic metre.
Appearance reflectance uses the supplied RGBA color.

Nine declarative schemas include the required bases and their property defaults, units, choice enumerations, bounds, and interface metadata.
The packaged vocabulary contains no material instances, source identities, source paths, archive payloads, or recorded definition values.
[Schema provenance](../../../../re/Fusion/Reconstruction/Materials/SchemaProvenance.json) identifies the observed declarations.
The [authoring model](../../../../re/Fusion/Reconstruction/MaterialAuthoring/Model.md) describes the construction rules and identity joins.

Unspecified structural and thermal properties retain their registered schema defaults.
The generic material is not a certified engineering material definition.
External textures and other material schema families remain outside this authoring profile.

## Verification

Four integration cases write actual cylinder and cuboid archives with default and custom densities.
They read the archives, verify body-to-package identities and property values, then re-emit and reopen them.
They preserve the complete typed material package, Design records, and body history.
Tests execute in remote CI only.
Run `43236096421` executed 868 cases: 864 passed and the four new material cases failed because the assertion helper expected an optional wrapper.
The body schema declares both material fields as direct objects.
The helper now requires that exact decoded shape.
The next remote run `43237059628` reached the manager-reference assertion and exposed another fixture mismatch: same-segment references decode as `LocalRef`, while the helper expected `SegmentRef`.
The helper now requires the authored local-reference shape and retains all identity, density, package and reconstruction assertions.
Remote run [43237855649](https://github.com/TryUniCAD/Kit/actions/runs/43237855649) on revision `9f6753ce885eff64fdcc907361175ff65253fb6d` passed all 885 cases, including all four material-document cases.

Black, Ruff, Pyright, Mypy, and steering checks passed for the 30 changed authoring and integration modules.
The schema vocabulary and maintained documentation pass the pinned formatter check.

[Native cuboid acceptance](../../../../re/Fusion/LocalOracle/RectangleAuthoring/NativeAcceptance.json) passed with the independently authored package in Fusion 2706.1.17.
At 31 mm height, the body reports volume 12.121 cm³, mass 0.012121 kg, and centre `(0.85, 1.15, 1.55)` cm.
Its reported density is 0.001 kg/cm³, equal to the specified 1000 kg/m³.
After a 37 mm height edit, mass is 0.014467 kg and centre is `(0.85, 1.15, 1.85)` cm.
Rollback, restore, rebuild, native save, and reopen preserve the intended feature behavior and physical properties.

Accepted cuboid source SHA-256: `9a8bef0ec7d6d0a9012bfb282da594baf3527076b40274a988068d62aa1ece41`.
Native saved SHA-256: `62c03b7aa11ce2c79193e51376e4405e6bbfd34aa5ab8097b72043ad49f38683`.
[Strict cylinder acceptance](../../../../re/Fusion/LocalOracle/Authored/ProductionMaterialDocumentAcceptance.json) also passed.
At 17.25 mm height, volume is 8.467573949 cm³, mass is 0.008467573949 kg, and centre Z is 0.8625 cm.
After editing to 23 mm, volume is 11.290098599 cm³, mass is 0.011290098599 kg, and centre Z is 1.15 cm.
The same material identity and name survive native save and reopen.

Accepted cylinder source SHA-256: `9f2d11fc13dd407c4b07711be7c6d11811bda336a8fc45d872b263db2dc00359`.
Native saved SHA-256: `1a2ace125ada2843a80fac604239ba51d9626963ba9e51d02f9427c41ff2ad70`.
