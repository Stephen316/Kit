# A stored material value carries its own unit

Expect a stored material value to use the unit of its schema declaration.
That is not always true.
`PrismTransparentSchema` declares `transparent_distance` in inches, with unit code 8214.
All 46 stored values in the 356-material sweep use millimeters, with unit code 8206.
The API reports these values in millimeters too.

So read the unit code from each stored value.
Do not convert by the declared unit.
Kit writes material distances in millimeters.
When Kit reads a distance equal to its declared default, it treats the value as absent.

Gas and liquid structural schemas declare thermal expansion in `InvCelsius`, with unit code 274434.
Solid schemas declare `MicrometerPerMeterCelsius`, with unit code 274435.
The same field name has a different unit in each family.

Evidence: the [family notes](../../../../../re/Fusion/Reconstruction/Materials/FamilyNotes.md) and the [schema provenance](../../../../../re/Fusion/Reconstruction/Materials/SchemaProvenance.json).
