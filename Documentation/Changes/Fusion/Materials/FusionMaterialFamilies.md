# Fusion material families

## Behavior

Kit used to write every material as a metal.
It always wrote `StructuralMetalSchema`, `ThermalSolidSchema` and `PrismMetalSchema`.
Now Kit picks each schema from the material class and the properties it is given.
It covers every family in Fusion's material libraries.
A material that the rules cannot place raises `ValueError`.

The rules are:

1. The structural schema is the one whose `localname` equals the class. The classes are Basic, Generic, Metal, Plastic, Wood, Gas and Liquid.
2. A class with no structural schema raises. Concrete is one such class.
3. An advanced schema without a Young's modulus falls back to `StructuralBasicSchema`.
4. A thermal aspect is written only when thermal values are given. It uses the Gas or Liquid schema for those classes, else `ThermalSolidSchema`.
5. The appearance is `PrismMetalSchema` when the finish is metallic. Else it is the first of Opaque, Layered and Transparent that holds every given finish field.
6. A value goes only where its schema declares it. A value with no place raises. So a gas with a Young's modulus raises.
7. `interior_model` follows the appearance schema: Opaque 0, Metal 1, Layered 2, Transparent 3.
8. A given colorspace goes to every colorspace field of the appearance.
9. `physmat_Type` is the given type label. Else it is the label equal to the class, when one exists.
10. Each main mechanical value is copied to its directional fields. A `DirectionValue` overrides one copy. `Behavior` sets the isotropic, orthotropic or transverse isotropic choice.

Schema type and local name come from the declarations themselves.
No table of materials decides the family.

## API

`MaterialSpec` keeps its first three fields: name, density and color.
It adds `ClassName`, `Mechanics`, `Thermal`, `Finish` and `TypeName`.
Inputs use SI units, except distances in millimeters.
Kit converts them to each field's declared unit.

| Part           | Fields                                                                                                                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `MechanicSpec` | Young's and shear modulus, Poisson's ratio, yield and tensile strength, conductivity, specific heat, expansion, damping, wood strengths, behavior, directional overrides                               |
| `ThermalSpec`  | Density, conductivity, specific heat, emissivity, resistivity, permeability, porosity, reflectivity, light transmission, compressibility, viscosity, vapor pressure, heat of vaporization              |
| `FinishSpec`   | Appearance name, metallic flag, colorspace, roughness, anisotropy, rotation, tint, reflectance, translucency, scatter distance and color, refraction, color depth, layer color, fraction and roughness |

Every part field is optional.
An absent field keeps its schema default.
Thermal density, conductivity and specific heat default to the structural values.

```python
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import MechanicSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import ThermalSpec
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue

Glass = MaterialSpec(
    "Clear glass",
    2500.0,
    ColorValue(0.96, 0.96, 0.95, 1.0),
    "Generic",
    MechanicSpec(YoungModulus=7.0e10, PoissonRatio=0.22),
    ThermalSpec(Emissivity=0.9, TransmitsLight=True),
    FinishSpec(Refraction=1.52, ColorDepth=50.0),
    "Glass",
)
```

The example describes the API; it is not an executed verification record.

Old authoring states without the new fields still decode.
They get the Generic class with no extra values.

## Evidence

A local sweep exported one body per library material: 356 materials from three libraries in Fusion 2706.1.17.
The schema declarations are identical in all 356 documents.
Kit's vocabulary now holds the 20 declarations that the families use.

| Aspect     | Library families                                                      |
| ---------- | --------------------------------------------------------------------- |
| Structural | Metal 202, Plastic 72, Generic 36, Wood 26, Basic 15, Gas 4, Liquid 1 |
| Thermal    | Solid, Gas or Liquid; 141 materials have none                         |
| Appearance | Metal 203, Opaque 129, Transparent 23, Layered 1                      |

- All 4 gases and the 1 liquid use the gas and liquid schemas.
- No advanced structural asset has the default Young's modulus. Basic has no elastic fields.
- The appearance does not follow the class. Mirror is glass with a metal appearance.
- `interior_model` matches the appearance schema in 1355 assets.
- All 305 Metal, Plastic, Wood, Gas and Liquid materials have the type label of their class.
- Single-input API edits change one field. Fusion derives no shear, copy or thermal value from them.

Shear modulus, directional copies and thermal values are not derived from other values in the library.
Only 16 of 662 shear moduli match E / (2 (1 + ν)).
So Kit takes them as inputs.

The [family notes](../../../../re/Fusion/Reconstruction/Materials/FamilyNotes.md) record each count and script.
Twenty scrubbed [controls](../../../../re/Fusion/LocalOracle/MaterialFamilies/Controls/) cover each family.

## Reader changes

The material reader now handles `Distance`, `TextureURI` and `PropertyAlias` fields, and `Float` lists.
It reads and re-writes all 356 sweep packages.
See [texture list counts](../../../Gotchas/Conversion/Fusion/Materials/TextureListCount.md) and [value units](../../../Gotchas/Conversion/Fusion/Materials/MaterialValueUnits.md).

The adapter projects a package back to a `MaterialSpec`.
On every readable corpus document, it gives the same name, density and color as before.

## Fusion acceptance

Nineteen held-out cases were accepted in local Fusion 2706.1.17.
None of them is one of the 20 controls or the edit controls.
Eighteen are library materials. The nineteenth is a Water copy with new values set through the API, because the library has one liquid.

| Family     | Held-out materials                                                 |
| ---------- | ------------------------------------------------------------------ |
| Basic      | Polyisocyanurate, Slate                                            |
| Gas        | Nitrogen, Oxygen                                                   |
| Generic    | Marble, Glass Clear Glazing, PTFE, Tin                             |
| Liquid     | Water copy with new values                                         |
| Metal      | Aluminum 1100-O, Copper, Titanium 6Al-4V, Steel Paint Finish Blue  |
| Plastic    | Nylon 6, Polycarbonate Clear, SAN, Acetal Resin Black              |
| Wood       | Maple, Jarrah                                                      |

For each case, Fusion assigned the library material to a 10 × 20 × 30 mm box, and the API read every value with its unit.
A research script turned that reading into a Kit spec in SI units.
The class was the type label when it names a structural family, else Generic.
Kit wrote the cuboid, and Fusion opened it and read it the same way.

- Kit chose the same structural, thermal and appearance schemas as Fusion's own document in all 19 cases.
- Material name, appearance name and mass matched in all 19.
- All 456 appearance values matched.
- 945 of 1043 material values matched. This includes density, Young's modulus, Poisson's ratio, yield and tensile strength, conductivity, specific heat and expansion, in both aspects.
- The other 98 are descriptive text. Kit also writes the name to `physmat_Label`, which library materials leave empty.

The first run exposed two gaps. Maple and Jarrah are orthotropic, with directional Poisson's ratios and wood strengths. Nylon 6 has one directional expansion value that differs from its main value.
The behavior choice, directional overrides and wood strengths fixed both.
Every document was closed after the run.

The [acceptance summary](../../../../re/Fusion/LocalOracle/MaterialFamilies/Accept/Summary.json) lists each comparison and the hash of each Kit file.

## Limits

- Kit does not write textures. 43 library appearances use them.
- Kit does not write fatigue or nonlinear aspects.
- Kit does not write descriptive text such as classification, source, subclass, comments or wood species.
- `ThermallyTreated` and the wood construction choice are not inputs.
- Kit needs the class as input. The type label alone does not fix it: five wood boards and Silicon Nitride use the Generic schema.
- The library has no untextured layered material, so layered output has no Fusion acceptance.
- Concrete has no structural schema in this Fusion version.

## Verification

Static checks passed on the changed modules.
New tests cover each family, each refused input, the projection fixed point and old states.
Tests run in remote CI only.
