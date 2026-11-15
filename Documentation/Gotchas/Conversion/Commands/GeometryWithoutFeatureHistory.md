# Typed geometry does not establish editable feature history

A valid `CadDocument` can contain B-rep or meshes without a feature timeline.
Its JSON serialization preserves those records, and the JSON writer reports that its own output is usable.
Neither validation nor serialization establishes an editable CAD history.
Adding independent parameters does not supply missing driving features.

The CLI refuses conversion of local geometry without a feature timeline, including geometry in nested documents or local assembly mesh representations.
Use `kit decode` to inspect the records while recovering their feature semantics.
Parameter-only documents and assembly roots without local geometry remain eligible.
A nonempty history still requires the separate parametric, lossless, and target-application acceptance evidence.

See [the change entry](../../../Changes/Commands/HistoryFreeGeometryGuard.md).
