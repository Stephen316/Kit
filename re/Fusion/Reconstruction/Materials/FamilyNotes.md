# Material family notes

## Question

How does Fusion choose the structural, thermal and appearance schema of a material?
Which fields does each schema write?

## Starting state

The writer in `src/convert/formats/Fusion/DocumentCodec/Materials/MaterialAssets.py` always writes four assets.
Their schemas are `PhysMatSchema`, `StructuralMetalSchema`, `ThermalSolidSchema` and `PrismMetalSchema`.
So every material that Kit writes is a metal.
The old corpus has 1617 material packages, and all of them are metal.

## Controls

`../../LocalOracle/MaterialFamilies/SweepMaterials.py` makes one document per library material.
Each document has the same 10 x 20 x 30 mm box. Only the material changes.
The sweep covers all 356 materials of the Fusion Material, Additive and Nonlinear libraries in Fusion 2706.1.17.
Each control is exported locally with the Fusion archive export. Nothing is saved to the cloud.
The exports are research data and stay out of git. `SweepList.json` lists the inputs.

`DecodeSweep.py` decodes every package with the Kit reader and `TrialGrammar.py`.
All 356 packages decode, and every record ends exactly at its last byte.

## Package content

Every package holds the component default (Steel, `PrismMaterial-018`) and the assigned material.
Each appearance also has a legacy `GenericSchema` partner.
The schema declarations are the same in all 356 packages. Only `core` and `cnx` differ.

## Wire grammar for new schema kinds

| Kind            | Wire form                                        | Evidence                                   |
| --------------- | ------------------------------------------------ | ------------------------------------------ |
| `Distance`      | i32 unit code, then f64 magnitude, as a unit float | 313 untextured packages decode to the end |
| `TextureURI`    | u8 count, then that many length-prefixed texts   | All 43 textured packages decode to the end |
| `PropertyAlias` | No record                                        | Same 43 packages                           |
| Float list      | u32 count, then unit floats                      | 54 fatigue packages                        |

## Unit codes

The code belongs to the stored value, not to the declaration.
`transparent_distance` is declared in inches but is stored with code 8206.

| Unit                     | Code   | Fields that show it                             |
| ------------------------ | ------ | ----------------------------------------------- |
| MilliMeter               | 8206   | `opaque_mfp` in all 258 opaque assets            |
| Inch                     | 8214   | Texture offsets and scales                      |
| InvCelsius               | 274434 | Gas and liquid expansion, 5 of 5                |
| CandelasPerSquareMeter   | 225281 | `opaque_luminance`                              |
| Centipoise               | 188418 | Gas and liquid viscosity                        |
| JoulePerGram             | 299009 | Heat of vaporization                            |
| Pascal                   | 135182 | Vapor pressure and hyperelastic constants       |
| Degree                   | 32770  | Nonlinear friction angle                        |

The other codes match the table in `../MaterialAuthoring/Model.md`.

## Families in the library

| Aspect     | Schemas                                                         |
| ---------- | --------------------------------------------------------------- |
| Structural | Basic, Generic, Metal, Plastic, Wood, Gas, Liquid               |
| Thermal    | Solid, Liquid, Gas, or no thermal aspect                        |
| Appearance | PrismMetal, PrismOpaque, PrismTransparent, PrismLayered          |
| Extra      | Fatigue (54 metals) and Nonlinear (12 materials)                |

There is no concrete material and no `StructuralConcreteSchema` in this library.

## Rules found so far

1. Gas and liquid materials use the gas and liquid structural and thermal schemas. This holds for 4 of 4 gases and 1 of 1 liquid.
2. A solid with a Young's modulus uses an advanced schema: Metal, Plastic, Wood or Generic, by its class.
3. A solid without a Young's modulus uses `StructuralBasicSchema`. No advanced asset in the library has the schema default modulus.
4. Poisson's ratio, yield and tensile strength can be absent. They then keep the schema default.
5. The thermal aspect is optional. 141 of 356 materials have none.
6. The appearance schema does not follow the class. Mirror is glass with a metal appearance.
7. `interior_model` is fixed by the appearance schema: Opaque 0, Metal 1, Layered 2, Transparent 3. This holds for 1355 assets.
8. All colorspace choices inside one appearance are equal: 0 unspecified, 1 sRGB, 2 linear.

## Values that are not derived

These are independent library data, so Kit must take them as inputs:

- The directional copies of isotropic values. 145 of 3310 Young's modulus copies differ from the main value.
- The shear modulus. Only 16 of 662 match E / (2 (1 + nu)).
- The thermal aspect values. About 13 percent differ from the structural values.

## Edit controls

`EditControls.py` copies ABS Plastic and Air and changes one input through the API.
`DiffEdits.py` compares each edit with its base copy.

- Young's modulus, Poisson's ratio, conductivity, expansion and density each change one field.
- No other field moves. Fusion does not derive shear, copies or thermal values from an edit.
- The API writes the main field only. The directional copies keep their old values.
- ABS Plastic has no thermal aspect, so the thermal conductivity edit wrote nothing.
- Gas expansion is stored with `InvCelsius` (274434). The solid one uses `MicrometerPerMeterCelsius` (274435).
- Appearance edits made copies that share one definition id with different definitions. Kit's reader rejects this. It stays open.

## Implementation in src

- `PlanMaterial.py` picks the schemas.
  - Structural: the schema whose `localname` is the class. A class with no schema raises.
  - An advanced schema without a Young's modulus falls back to Basic (rule 3).
  - Thermal: only when thermal values are given. The class schema, else Solid.
  - Appearance: Metal when metallic. Else the first of Opaque, Layered, Transparent that holds every given finish field. None raises.
- `PlaceValue.py` writes a value only where the schema declares it. A value with no place raises. So Basic with a yield strength raises, and a gas with a modulus raises.
- `StoredValue.py` converts SI inputs to the declared unit. Distances are stored in millimeters.
- `MatProperties.py` copies each main value to its directional fields. A `DirectionValue` then overrides one copy. `Behavior` sets `structural_Behavior` by its choice label.
- `MaterialType.py` writes `physmat_Type` from `TypeName`, else from the label equal to the class.
- Schema `type` and `localname` come from the declarations, not from a table of materials.
- `ProjectMaterial.py` reads a package back to the same spec. A distance equal to its schema default reads as absent.
- The vocabulary now holds all 20 declarations the families use. Each is identical in all 356 sweep documents.
- The old and new projections agree on every readable corpus document outside the sweep. 1387 give the same name, density and color. 292 fail in both. 18 do not read.
- A Kit spec leaves unset fields at the schema default. Projection reads them back as values, so a second build gives the same schemas.

## Tests

- `MaterialFamilyTests.py` builds one material per family and checks the chosen schemas.
- It checks that every given input projects back, and that a rebuild is a fixed point.
- `BadFamilies.py` lists inputs that must raise.
- `MaterialTests.py` now expects Basic plus Opaque for the default material.

## Material type

`PhysMatSchema` declares `physmat_Type`, a choice of 14 labels. Examples are Plastic, Metal, Wood, Glass, Stone, Liquid, Gas and Generic. The default is Generic.

| Structural family | Types in the library                                   |
| ----------------- | ------------------------------------------------------ |
| Metal             | Metal 202                                              |
| Plastic           | Plastic 72                                             |
| Wood              | Wood 26                                                |
| Gas, Liquid       | Gas 4, Liquid 1                                        |
| Generic           | Generic 12, Glass 10, Stone 8, Wood 5, Plastic 1       |
| Basic             | Textile 6, Plastic 4, Ceramic 2, Generic 2, Stone 1    |

- So the type is the label equal to the class when such a label exists. That holds for all 305 Metal, Plastic, Wood, Gas and Liquid materials.
- Generic and Basic materials need the type as an input. Kit takes `TypeName`, else the label equal to the class, else the schema default.
- The type does not fix the structural family. The 5 Wood-typed Generic materials are isotropic boards such as MDF and plywood. Silicon Nitride is typed Plastic on the Generic schema.

## Acceptance

- `AcceptList.json` names 18 held-out library materials and W01. None is a control or an edit control. W01 is a Water copy with new values set through the API.
- `AcceptReference.py` observes Fusion's own document for each one, with units.
- `BuildAccept.py` builds a Kit spec from each observation and writes a 10 x 20 x 30 mm cuboid.
  - The class is the type label when it names a structural family, else Generic.
  - Values convert to SI with physical factors written in the script, not Kit's tables.
- `AcceptKit.py` opens each Kit file in Fusion 2706.1.17 and observes it the same way. All 19 opened. No document stayed open.
- `CompareAccept.py` writes `Accept/Summary.json`.

Results for all 19 held-out cases:

- Kit chose the same structural, thermal and appearance schemas as Fusion's library document.
- Material name, appearance name and mass match.
- All 456 appearance values match.
- 945 of 1043 material values match. The listed values all match: density, Young's modulus, Poisson's ratio, yield and tensile strength, conductivity, specific heat and expansion, in both aspects.
- The 98 others are descriptive text: label, classification, source, subclass, external id, wood species and one comment.
- Kit writes the name to `physmat_Label`. Library materials leave it empty.

The first run found two gaps. Jarrah and Maple are orthotropic, with directional Poisson's ratios and wood strengths. Nylon 6 has one directional expansion value that differs from the main value. Kit now takes the behavior choice, per-direction overrides and wood strengths as optional inputs.

## Open items

- Textures are not written. 43 library appearances use them.
- Fatigue and nonlinear aspects are not written.
- Descriptive text is not written: classification, source, subclass, external id, comments, wood species and grade.
- `ThermallyTreated` and the wood construction choice are not inputs.
- The layered family has one textured library material, so no untextured layered acceptance exists.
- The copied-appearance identity check above.
- Six library materials do not follow the type-to-class rule used by the acceptance builder: five wood boards and Silicon Nitride use the Generic schema. Kit needs their class as input.
